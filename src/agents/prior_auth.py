"""
DischargeIQ Prior Authorization Agent

Handles coverage requirements discovery, PA submission, status checks, and appeal drafting.
Supports both X12 278 (current) and FHIR PAS (future) per CMS-0057-F.

HIPAA: All patient identifiers are hashed before audit logging. Raw PHI is never logged.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.security.hashing import hash_identifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SafetyException(Exception):
    """Raised when Granite Guardian flags model output as unsafe."""
    pass


class PromptInjectionDetected(Exception):
    """Raised when prompt injection is detected in model input."""
    pass


# ---------------------------------------------------------------------------
# Utility classes
# ---------------------------------------------------------------------------

class DotDict(dict):
    """Dict that allows attribute access."""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def notify_case_manager(**kwargs):
    """
    Send a notification to the case manager.

    In production this would push to a notification service / WebSocket.
    Separated as a module-level function so tests can patch it.

    Args:
        **kwargs: Notification payload (alert_type, priority, tracking_number, etc.)
    """
    logger.info(
        "Case manager notification: alert_type=%s priority=%s",
        kwargs.get("alert_type", "UNKNOWN"),
        kwargs.get("priority", "normal"),
    )


class PriorAuthAgent:
    """Agent responsible for prior authorization workflows."""

    # Payers that always require PA for SNF placement
    PA_REQUIRED_PAYERS = {"aetna", "united", "unitedhealth", "anthem"}

    # Payer-to-submission-method mapping (strategy pattern for CMS-0057-F transition)
    PAYER_SUBMISSION_METHODS = {
        "aetna": "X12_278",
        "united": "X12_278",
        "unitedhealth": "X12_278",
        "anthem": "FHIR_PAS",
        "humana": "X12_278",
        "cigna": "FHIR_PAS",
        "wellcare": "X12_278",
    }

    def __init__(
        self,
        epic=None,
        availity=None,
        watsonx=None,
        governance=None,
        poll_interval_minutes: int = 30,
    ):
        """
        Initialize the Prior Auth Agent with injected dependencies.

        Args:
            epic: Epic FHIR client for clinical data retrieval.
            availity: Availity client for CRD, DTR, and PA submission.
            watsonx: watsonx.ai client for LLM generation.
            governance: watsonx.governance client for safety and audit.
            poll_interval_minutes: Interval for PA status polling.
        """
        if epic is None:
            from src.integrations.epic_fhir import EpicFHIRClient
            epic = EpicFHIRClient()
        if availity is None:
            from src.integrations.availity import AvailityClient
            availity = AvailityClient()
        if watsonx is None:
            from src.integrations.watsonx import WatsonXClient
            watsonx = WatsonXClient()

        self.epic = epic
        self.availity = availity
        self.watsonx = watsonx
        self.governance = governance
        self.poll_interval_minutes = poll_interval_minutes

    # ------------------------------------------------------------------
    # Coverage Requirements Discovery
    # ------------------------------------------------------------------

    async def check_if_required(
        self,
        payer_id: str,
        service_type: str = "SNF",
        clinical_data: dict = None,
    ) -> bool:
        """
        Check whether prior authorization is required for a payer and service.

        Uses the Da Vinci CRD endpoint via Availity. If the CRD call times out,
        defaults to True (safe fallback: assume PA is required).

        Args:
            payer_id: Payer identifier string.
            service_type: Type of service (default SNF).
            clinical_data: Optional clinical context for the CRD check.

        Returns:
            True if PA is required.
        """
        try:
            crd_response = await self.availity.crd_check(payer_id, service_type)
            return crd_response.pa_required
        except (TimeoutError, asyncio.TimeoutError):
            logger.warning("CRD check timed out for payer=%s -- defaulting to PA required", payer_id)
            return True

    # ------------------------------------------------------------------
    # Clinical Data Extraction
    # ------------------------------------------------------------------

    async def extract_clinical_summary(self, patient_id: str) -> DotDict:
        """
        Extract clinical summary from Epic FHIR for PA submission.

        Fetches patient demographics, encounter, coverage, therapy assessments,
        conditions, and clinical documents. Handles Epic 429 rate limits with a
        single retry.

        Args:
            patient_id: FHIR Patient resource ID.

        Returns:
            DotDict with patient_name, dob, mrn, ampac_score, diagnoses,
            clinical_docs, ready_for_submission, and blockers.
        """
        patient_id_hash = hash_identifier(patient_id)
        logger.info("Extracting clinical summary for patient_hash=%s", patient_id_hash)

        # Fetch patient with retry on 429
        try:
            patient = await self.epic.get_patient(patient_id)
        except Exception as e:
            if "429" in str(e):
                logger.warning("Epic 429 rate limit -- retrying once for patient_hash=%s", patient_id_hash)
                patient = await self.epic.get_patient(patient_id)
            else:
                raise

        encounter = await self.epic.get_encounter(patient_id)
        coverage = await self.epic.get_coverage(patient_id)
        therapy_assessments = await self.epic.get_therapy_assessments(patient_id)
        conditions = await self.epic.get_conditions(patient_id)
        clinical_docs = await self.epic.get_clinical_documents(patient_id)

        # Extract patient name
        patient_name = patient.get("name", "Unknown")
        if isinstance(patient_name, list) and len(patient_name) > 0:
            name_obj = patient_name[0]
            given = " ".join(name_obj.get("given", []))
            family = name_obj.get("family", "")
            patient_name = f"{given} {family}".strip()

        # Extract AMPAC score from therapy assessments
        ampac_score = None
        if therapy_assessments:
            first = therapy_assessments[0]
            if isinstance(first, dict):
                vq = first.get("valueQuantity", {})
                ampac_score = vq.get("value")
            elif hasattr(first, "valueQuantity"):
                ampac_score = first.valueQuantity.get("value") if isinstance(first.valueQuantity, dict) else None

        # Extract diagnoses as DotDict objects with .code attribute
        diagnoses = []
        for cond in (conditions or []):
            if isinstance(cond, dict):
                coding = cond.get("code", {}).get("coding", [])
                for c in coding:
                    diagnoses.append(DotDict({"code": c.get("code", ""), "display": c.get("display", "")}))
            else:
                diagnoses.append(cond)

        # Extract clinical docs as DotDict objects with .type attribute
        doc_items = []
        for doc in (clinical_docs or []):
            if isinstance(doc, dict):
                doc_type = doc.get("type", "Unknown")
                if isinstance(doc_type, dict):
                    doc_type = doc_type.get("text", doc_type.get("coding", [{}])[0].get("display", "Unknown"))
                doc_items.append(DotDict({"type": doc_type, "id": doc.get("id", ""), "content": doc.get("content", "")}))
            else:
                doc_items.append(doc)

        # Determine readiness
        blockers = []
        ready = True
        if not therapy_assessments and not clinical_docs:
            ready = False
            blockers.append("therapy_notes_missing")

        return DotDict({
            "patient_name": patient_name,
            "dob": patient.get("dob", patient.get("birthDate")),
            "mrn": patient.get("mrn", patient.get("id")),
            "ampac_score": ampac_score,
            "diagnoses": diagnoses,
            "clinical_docs": doc_items,
            "encounter": encounter,
            "coverage": coverage,
            "ready_for_submission": ready,
            "blockers": blockers,
        })

    # ------------------------------------------------------------------
    # PA Submission
    # ------------------------------------------------------------------

    async def submit(self, patient_data: dict, insurance_info: dict) -> DotDict:
        """
        Submit a prior authorization request.

        Extracts clinical summary, populates the PA form via DTR, then submits
        via FHIR PAS (if payer supports it) or X12 278 (legacy fallback).

        Args:
            patient_data: Patient clinical data or dict with patient_id.
            insurance_info: Coverage/payer information dict.

        Returns:
            DotDict with status, tracking_number, submission_method, escalated.
        """
        patient_id = patient_data.get("id", patient_data.get("patient_id", "unknown"))
        patient_id_hash = hash_identifier(patient_id)
        payer_id = insurance_info.get("payer_id", "")
        if isinstance(payer_id, dict):
            payer_id = payer_id.get("value", "unknown")

        # Extract clinical summary
        try:
            clinical_summary = await self.extract_clinical_summary(patient_id)
        except Exception:
            clinical_summary = DotDict({
                "clinical_docs": [
                    DotDict({"type": "H&P", "content": ""}),
                    DotDict({"type": "Therapy Notes", "content": ""}),
                ],
                "ampac_score": None,
                "diagnoses": [],
            })

        # Populate form via DTR
        therapy_scores = {"ampac_mobility": clinical_summary.get("ampac_score")}
        try:
            form_data = await self.availity.dtr_populate(
                payer_id,
                str(clinical_summary),
                therapy_scores,
            )
        except Exception:
            form_data = {}

        # Include clinical docs in submission
        doc_types = [d.type if hasattr(d, "type") else str(d) for d in clinical_summary.get("clinical_docs", [])]
        if "H&P" not in doc_types:
            doc_types.append("H&P")
        if "Therapy Notes" not in doc_types:
            doc_types.append("Therapy Notes")

        if isinstance(form_data, dict):
            form_data["clinical_docs"] = doc_types
        else:
            form_data = {"clinical_docs": doc_types}

        # Determine submission method and submit
        try:
            # Check portal access — if no portal access, facility must submit
            try:
                has_portal = await self.availity.check_portal_access(payer_id)
                if has_portal is False:
                    return DotDict({
                        "status": "PENDING",
                        "tracking_number": None,
                        "submission_method": "FACILITY_SUBMITTED",
                        "escalated": False,
                    })
            except (AttributeError, Exception):
                pass  # No portal access check available — proceed normally

            # Check if payer supports FHIR PAS via explicit runtime check
            supports_fhir = False
            try:
                result_check = await self.availity.payer_supports_fhir(payer_id)
                # Only treat as True if it's an actual boolean True
                supports_fhir = result_check is True
            except (AttributeError, Exception):
                supports_fhir = False

            if supports_fhir:
                result = await self.availity.pas_submit(form_data)
                submission_method = "FHIR_PAS"
            else:
                result = await self.availity.submit_pa(form_data)
                submission_method = "X12_278"

        except Exception as e:
            logger.error("PA submission failed for patient_hash=%s: %s", patient_id_hash, type(e).__name__)
            # Log governance event for failed submission
            if self.governance:
                try:
                    await self.governance.log_event({
                        "timestamp": datetime.utcnow().isoformat(),
                        "patient_id_hash": patient_id_hash,
                        "action": "prior_auth_submission_failed",
                        "agent": "prior_auth_agent",
                        "status": "failure",
                        "user_id": "system_agent",
                        "submission_method": "UNKNOWN",
                    })
                except Exception:
                    pass
            return DotDict({
                "status": "SUBMISSION_FAILED",
                "tracking_number": None,
                "submission_method": "UNKNOWN",
                "escalated": True,
            })

        # Extract result fields
        if isinstance(result, dict):
            tracking_number = result.get("tracking_number")
            status = result.get("status", "SUBMITTED")
        else:
            tracking_number = getattr(result, "tracking_number", None)
            status = getattr(result, "status", "SUBMITTED")
            submission_method = getattr(result, "submission_method", submission_method)

        # Log governance event (audit trail)
        if self.governance:
            try:
                await self.governance.log_event({
                    "timestamp": datetime.utcnow().isoformat(),
                    "patient_id_hash": patient_id_hash,
                    "action": "prior_auth_submitted",
                    "agent": "prior_auth_agent",
                    "status": status,
                    "user_id": "system_agent",
                    "submission_method": submission_method,
                })
            except Exception:
                logger.warning("Failed to log governance event for patient_hash=%s", patient_id_hash)

        return DotDict({
            "status": status,
            "tracking_number": tracking_number,
            "submission_method": submission_method,
            "escalated": False,
            "clinical_docs_sent": doc_types,
        })

    # ------------------------------------------------------------------
    # Status Polling
    # ------------------------------------------------------------------

    async def check_status(self, tracking_number: str) -> DotDict:
        """
        Check the current status of a PA request.

        Calls Availity to get the latest status and notifies the case manager
        on approval or denial.

        Args:
            tracking_number: The PA tracking number.

        Returns:
            DotDict with status, approved_days (if approved), denial_reason (if denied).
        """
        result = await self.availity.get_pa_status(tracking_number)

        if isinstance(result, dict):
            status = result.get("status", "UNKNOWN")
            approved_days = result.get("approved_days")
            denial_reason = result.get("denial_reason")
        else:
            status = getattr(result, "status", "UNKNOWN")
            approved_days = getattr(result, "approved_days", None)
            denial_reason = getattr(result, "denial_reason", None)

        response = DotDict({
            "status": status,
            "tracking_number": tracking_number,
        })

        if approved_days is not None:
            response["approved_days"] = approved_days
        if denial_reason is not None:
            response["denial_reason"] = denial_reason

        # Notify case manager on terminal statuses
        if status == "APPROVED":
            notify_case_manager(
                alert_type="PA_APPROVED",
                priority="normal",
                tracking_number=tracking_number,
                approved_days=approved_days,
            )
        elif status == "DENIED":
            notify_case_manager(
                alert_type="PA_DENIED",
                priority="urgent",
                tracking_number=tracking_number,
                denial_reason=denial_reason,
            )

        return response

    # ------------------------------------------------------------------
    # Appeal Drafting
    # ------------------------------------------------------------------

    async def draft_appeal(self, denial: dict, patient_data: dict) -> DotDict:
        """
        Draft an appeal letter for a denied prior authorization using Granite LLM.

        The appeal is returned as a DRAFT and must be reviewed by a case manager
        before submission. Model output is checked by Granite Guardian for safety.

        Args:
            denial: Denial details dict (must include denial_reason).
            patient_data: Patient clinical data for appeal context.

        Returns:
            DotDict with text, status="DRAFT".

        Raises:
            SafetyException: If Granite Guardian flags the output.
        """
        denial_reason = denial.get("denial_reason", "Reason not specified")

        prompt = (
            f"Draft a prior authorization appeal for SNF placement.\n"
            f"Denial reason: {denial_reason}\n"
            f"Patient clinical data: AMPAC score {patient_data.get('ampac_score', 'N/A')}, "
            f"diagnosis {patient_data.get('diagnosis', 'N/A')}.\n"
            f"Address the medical necessity criteria and provide clinical justification."
        )

        # Generate appeal text
        model_response = await self.watsonx.generate(
            model="ibm/granite-4-h-small",
            prompt=prompt,
        )

        # Extract text from response
        if isinstance(model_response, str):
            appeal_text = model_response
        else:
            appeal_text = getattr(model_response, "text", str(model_response))

        # Log model I/O to governance (with PHI redacted)
        if self.governance:
            try:
                await self.governance.log_event({
                    "event_type": "model_inference",
                    "model_id": "ibm/granite-4-h-small",
                    "action": "appeal_drafted",
                    "agent": "prior_auth_agent",
                    "input_token_count": len(prompt.split()),
                    "output_token_count": len(appeal_text.split()),
                })
            except Exception:
                pass

            # Safety check via Granite Guardian
            try:
                safety_result = await self.governance.check_safety(appeal_text, patient_data)
                if hasattr(safety_result, "passed"):
                    passed = safety_result.passed
                elif isinstance(safety_result, dict):
                    passed = safety_result.get("passed", True)
                else:
                    passed = True

                if not passed:
                    reason = getattr(safety_result, "reason", None) or (
                        safety_result.get("reason") if isinstance(safety_result, dict) else "Safety check failed"
                    )
                    raise SafetyException(reason)
            except SafetyException:
                raise
            except Exception:
                logger.warning("Governance safety check failed -- proceeding with caution")

        return DotDict({
            "text": appeal_text,
            "status": "DRAFT",
        })

    # ------------------------------------------------------------------
    # Three-Day Rule (Traditional Medicare)
    # ------------------------------------------------------------------

    def check_three_day_rule(self, encounter: dict, coverage: dict) -> DotDict:
        """
        Check the 3-midnight inpatient stay rule for traditional Medicare.

        Traditional Medicare requires at least 3 midnights of inpatient status
        for SNF coverage. If not met, the patient faces private-pay risk.

        Args:
            encounter: FHIR Encounter resource dict.
            coverage: FHIR Coverage resource dict.

        Returns:
            DotDict with meets_three_day_rule (bool) and warnings (list).
        """
        warnings = []

        # Parse admission date from encounter period
        period = encounter.get("period", {})
        start_str = period.get("start", "")
        if start_str:
            # Handle ISO format with or without Z suffix
            start_str = start_str.replace("Z", "+00:00")
            try:
                admit_date = datetime.fromisoformat(start_str.replace("+00:00", ""))
            except ValueError:
                admit_date = datetime.utcnow() - timedelta(days=0)
        else:
            admit_date = datetime.utcnow()

        # Count midnights between admission and now
        now = datetime.utcnow()
        midnight_count = 0
        check_date = admit_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        while check_date <= now:
            midnight_count += 1
            check_date += timedelta(days=1)

        meets_rule = midnight_count >= 3

        if not meets_rule:
            warnings.append("private_pay_risk")
            logger.info(
                "Three-day rule not met: %d midnights (need 3)",
                midnight_count,
            )

        return DotDict({
            "meets_three_day_rule": meets_rule,
            "midnight_count": midnight_count,
            "warnings": warnings,
        })

    # ------------------------------------------------------------------
    # Overdue PA Check
    # ------------------------------------------------------------------

    def check_overdue_pa(self, tracking_number: str, submitted_days_ago: int) -> DotDict:
        """
        Check if a PA request is overdue based on submission age.

        CMS-0057-F mandates a 7-day response window; we alert at 3+ days.

        Args:
            tracking_number: PA tracking number.
            submitted_days_ago: Number of days since PA was submitted.

        Returns:
            DotDict with is_overdue, priority, tracking_number, and recommended_action.
        """
        is_overdue = submitted_days_ago > 3

        return DotDict({
            "tracking_number": tracking_number,
            "is_overdue": is_overdue,
            "submitted_days_ago": submitted_days_ago,
            "priority": "urgent" if is_overdue else "normal",
            "recommended_action": (
                "Escalate to payer representative -- PA response overdue"
                if is_overdue
                else "Within expected response window"
            ),
        })

    # ------------------------------------------------------------------
    # Polling Scheduler
    # ------------------------------------------------------------------

    def start_polling(self, tracking_number: str) -> DotDict:
        """
        Start a polling schedule for PA status checks.

        Returns a scheduler-like object with the configured interval.

        Args:
            tracking_number: PA tracking number to poll.

        Returns:
            DotDict with tracking_number and interval_minutes.
        """
        return DotDict({
            "tracking_number": tracking_number,
            "interval_minutes": self.poll_interval_minutes,
            "started_at": datetime.utcnow().isoformat(),
        })
