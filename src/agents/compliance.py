"""
DischargeIQ Compliance Agent

Audit logging, observation status checks, and PHI handling validation.
All patient identifiers are hashed before audit storage per HIPAA requirements.
Raw PHI is NEVER stored in audit records.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from src.security.hashing import hash_identifier
from src.security.phi_redactor import PHIRedactor


class ComplianceAgent:
    """Agent responsible for compliance monitoring and audit trail management."""

    def __init__(self, governance=None):
        """
        Initialize the Compliance Agent with optional governance client.

        Args:
            governance: watsonx.governance client for safety checks and audit.
        """
        self._redactor = PHIRedactor()
        self.governance = governance

    def log_workflow(
        self,
        patient_id: str,
        actions: list,
        outcome: str,
        agent: str = "compliance_agent",
        user_id: str = "system_agent",
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> dict:
        """
        Create an audit entry for a workflow action.

        Patient identifiers are hashed with SHA-256 + salt. Raw PHI is NEVER stored.
        The patient_id_hash is always a 64-character hex string (SHA-256 digest).

        Args:
            patient_id: Raw patient ID (will be hashed, never stored raw).
            actions: List of action descriptions.
            outcome: Outcome of the actions.
            agent: Agent that performed the action.
            user_id: User who triggered/approved the action.
            session_id: Session identifier.
            workflow_id: Associated workflow ID.
            model_version: LLM model version used, if applicable.

        Returns:
            Audit entry dict with hashed patient ID (64-char SHA-256 hex).
        """
        return {
            "id": str(uuid.uuid4()),
            "patient_id_hash": hash_identifier(patient_id),
            "workflow_id": workflow_id,
            "action": "; ".join(actions),
            "agent": agent,
            "details": {
                "actions": actions,
                "outcome": outcome,
            },
            "model_version": model_version,
            "status": "success" if outcome != "failure" else "failure",
            "user_id": user_id,
            "session_id": session_id or str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
        }

    def check_observation_status(
        self, encounter_status: str, coverage_type: str
    ) -> Optional[dict]:
        """
        Check for observation status + traditional Medicare combination.

        This is a critical compliance check: patients under observation status
        with traditional Medicare may not qualify for SNF coverage, creating
        financial risk and requiring immediate case manager attention.

        Handles both human-readable status ("observation") and FHIR class codes
        ("OBSENC" -- FHIR encounter class for observation encounters).

        Args:
            encounter_status: The encounter status (e.g., "observation", "OBSENC", "inpatient").
            coverage_type: Coverage type (e.g., "traditional_medicare", "medicare_advantage").

        Returns:
            Alert dict if a compliance issue is detected, None otherwise.
        """
        # Normalize encounter status: both "observation" and FHIR class code "OBSENC"
        is_observation = (
            encounter_status.lower() == "observation"
            or encounter_status == "OBSENC"
        )

        ct_lower = coverage_type.lower()
        is_traditional_medicare = (
            ("traditional" in ct_lower and "medicare" in ct_lower)
            or "medicare_ffs" in ct_lower
            or ct_lower == "traditional_medicare"
            or (ct_lower == "medicare")
        )

        if is_observation and is_traditional_medicare:
            return {
                "id": str(uuid.uuid4()),
                "level": "CRITICAL",
                "title": "Observation Status Alert",
                "message": (
                    "Patient is under observation status with traditional Medicare coverage. "
                    "SNF placement will NOT be covered — patient faces private pay risk. "
                    "Recommend immediate physician review for status conversion to inpatient."
                ),
                "created_at": datetime.utcnow().isoformat(),
            }
        return None

    def validate_phi_handling(self, data: Any) -> list:
        """
        Validate that data does not contain common PHI patterns.

        Scans the string representation of the data for SSNs, phone numbers,
        emails, dates, and MRN-like identifiers.

        Args:
            data: Data to validate (will be converted to string for scanning).

        Returns:
            List of violation descriptions. Empty list means no issues found.
        """
        text = str(data)
        violations = []

        detected = self._redactor.detect(text)
        pattern_descriptions = {
            "SSN": "Social Security Number pattern detected in data",
            "PHONE": "Phone number pattern detected in data",
            "EMAIL": "Email address pattern detected in data",
            "DATE": "Date of birth pattern detected in data",
            "MRN": "Medical Record Number pattern detected in data",
        }

        for pattern_name in detected:
            desc = pattern_descriptions.get(
                pattern_name, f"PHI pattern '{pattern_name}' detected in data"
            )
            violations.append(desc)

        return violations
