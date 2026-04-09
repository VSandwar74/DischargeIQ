"""
DischargeIQ Supervisor Agent

Orchestrates the discharge workflow by coordinating the Prior Auth, Placement,
and Compliance agents. Acts as the central controller for discharge coordination.

HIPAA: All patient identifiers are hashed before audit logging. Raw PHI is never logged.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from src.security.hashing import hash_identifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvalidStateTransition(Exception):
    """Raised when an invalid workflow state transition is attempted."""
    pass


# ---------------------------------------------------------------------------
# Utility classes
# ---------------------------------------------------------------------------

class DotDict(dict):
    """Dict that allows attribute access."""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class SupervisorAgent:
    """
    Top-level agent that orchestrates the discharge coordination workflow.

    Coordinates between Prior Auth, Placement, and Compliance agents
    to automate the hospital discharge process for SNF placements.
    """

    VALID_TRANSITIONS = {
        "INITIATED": ["AUTH_PENDING", "PLACEMENT_SEARCHING"],
        "AUTH_PENDING": ["AUTH_APPROVED", "AUTH_DENIED", "ESCALATED"],
        "AUTH_APPROVED": ["PLACEMENT_SEARCHING", "PLACEMENT_CONFIRMED", "ESCALATED"],
        "AUTH_DENIED": ["APPEAL_SUBMITTED", "ESCALATED"],
        "PLACEMENT_SEARCHING": ["PLACEMENT_CONFIRMED", "ESCALATED"],
        "PLACEMENT_CONFIRMED": ["TRANSPORT_SCHEDULED", "DISCHARGED", "ESCALATED"],
        "TRANSPORT_SCHEDULED": ["DISCHARGED", "ESCALATED"],
        "APPEAL_SUBMITTED": ["AUTH_APPROVED", "AUTH_DENIED", "ESCALATED"],
        "ESCALATED": ["AUTH_PENDING", "PLACEMENT_SEARCHING"],
        "DISCHARGED": [],  # terminal state
    }

    def __init__(
        self,
        epic=None,
        repo=None,
        prior_auth_agent=None,
        placement_agent=None,
        compliance_agent=None,
    ):
        """
        Initialize the Supervisor Agent with injected dependencies.

        Args:
            epic: Epic FHIR client for patient data retrieval.
            repo: Workflow repository for persistence.
            prior_auth_agent: PriorAuthAgent instance.
            placement_agent: PlacementAgent instance.
            compliance_agent: ComplianceAgent instance.
        """
        if epic is None:
            from src.integrations.epic_fhir import EpicFHIRClient
            epic = EpicFHIRClient()
        if prior_auth_agent is None:
            from src.agents.prior_auth import PriorAuthAgent
            prior_auth_agent = PriorAuthAgent()
        if placement_agent is None:
            from src.agents.placement import PlacementAgent
            placement_agent = PlacementAgent()
        if compliance_agent is None:
            from src.agents.compliance import ComplianceAgent
            compliance_agent = ComplianceAgent()

        self.epic = epic
        self.repo = repo
        self.prior_auth_agent = prior_auth_agent
        self.placement_agent = placement_agent
        self.compliance_agent = compliance_agent

    # ------------------------------------------------------------------
    # Discharge Trigger
    # ------------------------------------------------------------------

    async def handle_discharge_trigger(
        self,
        patient_id: str,
        trigger: dict,
    ) -> dict:
        """
        Handle a new discharge trigger event.

        Creates a workflow record, checks for existing active workflows,
        fetches patient data, determines PA requirements, and kicks off
        PA submission and placement matching in parallel.

        Args:
            patient_id: Patient identifier.
            trigger: Trigger event dict (type, user_id, etc.).

        Returns:
            Workflow dict with status INITIATED.
        """
        patient_id_hash = hash_identifier(patient_id)
        trigger_event = trigger.get("type", trigger.get("event", "discharge_order"))
        user_id = trigger.get("user_id", "system_agent")
        session_id = str(uuid.uuid4())

        logger.info(
            "Discharge trigger received for patient_hash=%s trigger=%s",
            patient_id_hash,
            trigger_event,
        )

        # Check for existing active workflow
        if self.repo:
            try:
                existing = await self.repo.get_active_by_patient(patient_id)
                if existing:
                    logger.info(
                        "Active workflow already exists for patient_hash=%s",
                        patient_id_hash,
                    )
                    return existing
            except Exception:
                pass

        # Create new workflow
        workflow_id = str(uuid.uuid4())
        workflow = {
            "id": workflow_id,
            "workflow_id": workflow_id,
            "patient_id": patient_id,
            "status": "INITIATED",
            "trigger_event": trigger_event,
            "created_at": datetime.utcnow().isoformat(),
        }

        if self.repo:
            try:
                await self.repo.create(workflow)
            except Exception:
                logger.warning("Failed to persist workflow %s", workflow_id)

        # Fetch patient data from Epic
        try:
            patient_data = await self.epic.get_patient(patient_id)
            coverage = await self.epic.get_coverage(patient_id)
        except Exception:
            patient_data = {"id": patient_id}
            coverage = {}

        payer_id = ""
        if isinstance(coverage, dict):
            payors = coverage.get("payor", [])
            if payors and isinstance(payors, list):
                payer_id = payors[0].get("reference", payors[0].get("id", ""))
            elif isinstance(coverage.get("payer_id"), str):
                payer_id = coverage.get("payer_id", "")

        insurance_info = {
            "payer_id": payer_id,
            "coverage_type": coverage.get("type", {}).get("text", "Medicare Advantage")
            if isinstance(coverage, dict) else "Medicare Advantage",
        }

        # Check if PA is required
        try:
            pa_required = await self.prior_auth_agent.check_if_required(payer_id, "SNF")
        except Exception:
            pa_required = True  # safe default

        # Run PA submission and placement matching in parallel
        async def run_auth():
            if pa_required:
                try:
                    return await self.prior_auth_agent.submit(patient_data, insurance_info)
                except Exception:
                    return None
            return None

        async def run_placement():
            try:
                return await self.placement_agent.find_matches(patient_data)
            except Exception:
                return []

        auth_result, facility_matches = await asyncio.gather(
            run_auth(), run_placement()
        )

        # Log compliance audit trail
        actions = [f"discharge_triggered:{trigger_event}"]
        if pa_required:
            actions.append("prior_auth_submitted")
        actions.append(f"facilities_matched:{len(facility_matches) if facility_matches else 0}")

        try:
            audit_entry = self.compliance_agent.log_workflow(
                patient_id=patient_id,
                actions=actions,
                outcome="workflow_initiated",
                agent="supervisor_agent",
                user_id=user_id,
                session_id=session_id,
                workflow_id=workflow_id,
            )
        except Exception:
            audit_entry = None

        workflow.update({
            "pa_required": pa_required,
            "prior_auth": auth_result,
            "placement_options": facility_matches,
            "facility_matches": facility_matches,
            "audit_entry": audit_entry,
        })

        logger.info(
            "Workflow %s created for patient_hash=%s status=%s",
            workflow_id,
            patient_id_hash,
            workflow["status"],
        )

        return workflow

    # ------------------------------------------------------------------
    # Workflow Event Handlers
    # ------------------------------------------------------------------

    async def on_pa_submitted(self, workflow_id: str, pa_result: dict):
        """
        Handle PA submission event. Updates workflow status to AUTH_PENDING.

        Args:
            workflow_id: Workflow identifier.
            pa_result: PA submission result dict.
        """
        if self.repo:
            await self.repo.update(workflow_id, status="AUTH_PENDING")

    async def on_pa_status_change(self, workflow_id: str, new_status: dict):
        """
        Handle PA status change event.

        Updates workflow to AUTH_APPROVED or AUTH_DENIED based on PA decision.

        Args:
            workflow_id: Workflow identifier.
            new_status: Status dict with 'status' key.
        """
        status_value = new_status.get("status", "") if isinstance(new_status, dict) else getattr(new_status, "status", "")

        if status_value == "APPROVED":
            if self.repo:
                await self.repo.update(workflow_id, status="AUTH_APPROVED")
        elif status_value == "DENIED":
            if self.repo:
                await self.repo.update(workflow_id, status="AUTH_DENIED")

    async def on_placement_accepted(self, workflow_id: str, referral: dict):
        """
        Handle placement acceptance event.

        Args:
            workflow_id: Workflow identifier.
            referral: Accepted referral details.
        """
        if self.repo:
            await self.repo.update(workflow_id, status="PLACEMENT_CONFIRMED")

    # ------------------------------------------------------------------
    # Stalled Workflow Detection
    # ------------------------------------------------------------------

    async def check_stalled_workflows(self, workflows: list) -> list:
        """
        Check for stalled workflows and escalate those stuck for over 72 hours.

        Args:
            workflows: List of workflow dicts with hours_in_status field.

        Returns:
            Updated workflow list with stalled workflows set to ESCALATED.
        """
        for workflow in workflows:
            hours = workflow.get("hours_in_status", 0)
            if hours > 72:
                workflow["status"] = "ESCALATED"
                if self.repo:
                    wf_id = workflow.get("id", workflow.get("workflow_id"))
                    if wf_id:
                        try:
                            await self.repo.update(wf_id, status="ESCALATED")
                        except Exception:
                            pass
        return workflows

    # ------------------------------------------------------------------
    # State Transition Validation
    # ------------------------------------------------------------------

    async def transition(self, workflow_id: str, from_status: str, to_status: str):
        """
        Validate and execute a workflow state transition.

        Args:
            workflow_id: Workflow identifier.
            from_status: Current status.
            to_status: Target status.

        Raises:
            InvalidStateTransition: If the transition is not allowed.
        """
        valid_targets = self.VALID_TRANSITIONS.get(from_status, [])
        if to_status not in valid_targets:
            raise InvalidStateTransition(
                f"Cannot transition from {from_status} to {to_status}. "
                f"Valid targets: {valid_targets}"
            )

        if self.repo:
            await self.repo.update(workflow_id, status=to_status)

    # ------------------------------------------------------------------
    # Observation Status Check
    # ------------------------------------------------------------------

    async def check_observation_status(self, patient_id: str) -> Optional[DotDict]:
        """
        Check if a patient is under observation status with traditional Medicare.

        Delegates to the compliance agent after fetching encounter and coverage
        data from Epic.

        Args:
            patient_id: Patient identifier.

        Returns:
            Alert DotDict if compliance issue detected, None otherwise.
        """
        try:
            encounter = await self.epic.get_encounter(patient_id)
            coverage = await self.epic.get_coverage(patient_id)
        except Exception:
            return None

        # Extract encounter class code
        encounter_class = encounter.get("class", {})
        if isinstance(encounter_class, dict):
            encounter_status = encounter_class.get("code", "inpatient")
        else:
            encounter_status = str(encounter_class)

        # Extract coverage type — build a descriptive string from FHIR Coverage
        coverage_type = ""
        if isinstance(coverage, dict):
            # Try type.coding[0].display first (e.g. "Medicare Advantage", "Medicare")
            cov_type = coverage.get("type", {})
            if isinstance(cov_type, dict):
                coding = cov_type.get("coding", [])
                if coding and isinstance(coding, list):
                    coverage_type = coding[0].get("display", cov_type.get("text", ""))
                else:
                    coverage_type = cov_type.get("text", "")
            elif isinstance(cov_type, str):
                coverage_type = cov_type

            # Check payor display to distinguish traditional Medicare from MA
            payors = coverage.get("payor", [])
            if payors and isinstance(payors, list):
                payor_display = payors[0].get("display", "")
                # "Medicare FFS" = traditional Medicare (Fee For Service)
                if "ffs" in payor_display.lower() or "traditional" in payor_display.lower():
                    coverage_type = "traditional_medicare"
                elif "medicare" in payor_display.lower() and "advantage" not in coverage_type.lower():
                    # Plain "Medicare" without "Advantage" = traditional
                    if "advantage" not in payor_display.lower():
                        coverage_type = "traditional_medicare"

        alert = self.compliance_agent.check_observation_status(
            encounter_status, coverage_type
        )

        if alert:
            return DotDict(alert)
        return None

    # ------------------------------------------------------------------
    # Placement Proposal (Human-in-the-Loop)
    # ------------------------------------------------------------------

    async def propose_placement(self, workflow_id: str, facility: dict) -> DotDict:
        """
        Propose a facility placement for case manager approval.

        Placements are NEVER auto-submitted -- always require human approval.

        Args:
            workflow_id: Workflow identifier.
            facility: Facility details dict.

        Returns:
            DotDict with status AWAITING_CM_APPROVAL.
        """
        return DotDict({
            "workflow_id": workflow_id,
            "facility": facility,
            "status": "AWAITING_CM_APPROVAL",
            "auto_submitted": False,
            "proposed_at": datetime.utcnow().isoformat(),
        })

    async def override_placement(
        self,
        workflow_id: str,
        agent_recommended: str,
        cm_selected: str,
        cm_reason: str,
    ) -> DotDict:
        """
        Log a case manager override of the agent-recommended facility.

        Args:
            workflow_id: Workflow identifier.
            agent_recommended: Facility ID the agent recommended.
            cm_selected: Facility ID the case manager selected instead.
            cm_reason: Reason for the override.

        Returns:
            DotDict with override details and override_logged=True.
        """
        logger.info(
            "Placement override on workflow %s: agent=%s -> cm=%s",
            workflow_id,
            agent_recommended,
            cm_selected,
        )

        return DotDict({
            "workflow_id": workflow_id,
            "agent_recommended": agent_recommended,
            "selected_facility": cm_selected,
            "cm_reason": cm_reason,
            "override_logged": True,
            "overridden_at": datetime.utcnow().isoformat(),
        })

    # ------------------------------------------------------------------
    # Appeal Management (Human-in-the-Loop)
    # ------------------------------------------------------------------

    async def get_appeal_draft(self, workflow_id: str) -> DotDict:
        """
        Get the current appeal draft for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            DotDict with appeal text and status DRAFT.
        """
        return DotDict({
            "workflow_id": workflow_id,
            "status": "DRAFT",
            "text": "",
            "created_at": datetime.utcnow().isoformat(),
        })

    async def submit_appeal(self, workflow_id: str, cm_approved: bool) -> DotDict:
        """
        Submit or hold an appeal based on case manager approval.

        Appeals are NEVER auto-submitted -- require explicit CM approval.

        Args:
            workflow_id: Workflow identifier.
            cm_approved: Whether the case manager approved submission.

        Returns:
            DotDict with status APPEAL_SUBMITTED (if approved) or DRAFT.
        """
        if cm_approved:
            if self.repo:
                try:
                    await self.repo.update(workflow_id, status="APPEAL_SUBMITTED")
                except Exception:
                    pass
            return DotDict({
                "workflow_id": workflow_id,
                "status": "APPEAL_SUBMITTED",
                "submitted_at": datetime.utcnow().isoformat(),
            })
        else:
            return DotDict({
                "workflow_id": workflow_id,
                "status": "DRAFT",
            })
