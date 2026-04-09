"""Tests for DischargeIQ compliance agent. All data is synthetic."""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("AUDIT_SALT", "test-salt-for-unit-tests")

from src.agents.compliance import ComplianceAgent


class TestComplianceAgent:
    def setup_method(self):
        self.agent = ComplianceAgent()

    def test_observation_status_detection(self):
        alert = self.agent.check_observation_status(
            encounter_status="observation",
            coverage_type="medicare_ffs"
        )
        assert alert is not None
        assert alert["level"] == "CRITICAL"
        assert "observation" in alert["message"].lower()

    def test_observation_status_inpatient_ok(self):
        alert = self.agent.check_observation_status(
            encounter_status="inpatient",
            coverage_type="medicare_advantage"
        )
        assert alert is None

    def test_audit_log_no_raw_phi(self):
        entry = self.agent.log_workflow(
            patient_id="12345678",
            actions=["prior_auth_submitted"],
            outcome="success"
        )
        # Should contain hash, not raw patient ID
        assert "12345678" not in str(entry)
        assert "patient_id_hash" in entry
        assert len(entry["patient_id_hash"]) == 64  # SHA-256 hex length

    def test_phi_validation_catches_violations(self):
        data = {"message": "Patient SSN is 123-45-6789", "note": "Clean data"}
        violations = self.agent.validate_phi_handling(data)
        assert len(violations) > 0
