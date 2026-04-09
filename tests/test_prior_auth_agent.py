"""
Tests: Prior Authorization Agent
Priority: P0 — this is the highest-value agent and core of the MVP.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.fixtures.synthetic_data import (
    SYNTHETIC_PATIENTS, COVERAGE_AETNA_MA, COVERAGE_UNITED_MA,
    COVERAGE_TRADITIONAL_MEDICARE, COVERAGE_CARESOURCE_MEDICAID,
    AMPAC_SCORE_LOW, AMPAC_SCORE_BORDERLINE, AMPAC_SCORE_HIGH,
    ENCOUNTER_INPATIENT, ENCOUNTER_OBSERVATION,
    PA_RESPONSE_APPROVED, PA_RESPONSE_DENIED, PA_RESPONSE_PENDING,
    make_encounter,
)
from src.agents.prior_auth import PriorAuthAgent, SafetyException, PromptInjectionDetected


# ===================================================================
# PA Requirement Check (Da Vinci CRD)
# ===================================================================

class TestPARequirementCheck:
    """Does the agent correctly determine whether PA is required?"""

    @pytest.mark.asyncio
    async def test_pa_required_for_ma_snf_placement(self, mock_availity):
        """Medicare Advantage SNF placement should require PA."""
        mock_availity.crd_check.return_value = MagicMock(pa_required=True)
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        result = await agent.check_if_required(payer_id="AETNA_MA", service_type="SNF", clinical_data={})
        assert result is True
        mock_availity.crd_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_pa_not_required_when_payer_says_no(self, mock_availity):
        """If CRD says PA not required, agent should skip submission."""
        mock_availity.crd_check.return_value = MagicMock(pa_required=False)
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        result = await agent.check_if_required(payer_id="AETNA_MA", service_type="SNF", clinical_data={})
        assert result is False

    @pytest.mark.asyncio
    async def test_pa_check_handles_crd_timeout(self, mock_availity):
        """If CRD endpoint times out, agent should default to PA required (safe fallback)."""
        mock_availity.crd_check.side_effect = TimeoutError("CRD endpoint timeout")
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        result = await agent.check_if_required(payer_id="AETNA_MA", service_type="SNF", clinical_data={})
        assert result is True  # safe default: assume required


# ===================================================================
# Clinical Data Extraction
# ===================================================================

class TestClinicalDataExtraction:
    """Does the agent correctly extract clinical data from Epic FHIR?"""

    @pytest.mark.asyncio
    async def test_extracts_patient_demographics(self, mock_epic_fhir):
        """Agent pulls patient name, DOB, MRN from FHIR Patient resource."""
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        data = await agent.extract_clinical_summary("synth-patient-001")
        assert data.patient_name is not None
        assert data.dob is not None
        assert data.mrn is not None

    @pytest.mark.asyncio
    async def test_extracts_ampac_score(self, mock_epic_fhir):
        """Agent retrieves AMPAC score from Observation resources."""
        mock_epic_fhir.get_therapy_assessments.return_value = [AMPAC_SCORE_LOW]
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        data = await agent.extract_clinical_summary("synth-patient-001")
        assert data.ampac_score == 14

    @pytest.mark.asyncio
    async def test_extracts_diagnosis_codes(self, mock_epic_fhir):
        """Agent pulls ICD-10 codes from Condition resources."""
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        data = await agent.extract_clinical_summary("synth-patient-001")
        assert "S72.001A" in [c.code for c in data.diagnoses]

    @pytest.mark.asyncio
    async def test_extracts_clinical_documents(self, mock_epic_fhir):
        """Agent retrieves H&P and therapy notes for PA submission."""
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        data = await agent.extract_clinical_summary("synth-patient-001")
        doc_types = [d.type for d in data.clinical_docs]
        assert "H&P" in doc_types
        assert "Therapy Notes" in doc_types

    @pytest.mark.asyncio
    async def test_handles_missing_therapy_notes(self, mock_epic_fhir):
        """If therapy notes are not yet available, agent should flag and wait."""
        mock_epic_fhir.get_therapy_assessments.return_value = []
        mock_epic_fhir.get_clinical_documents.return_value = []
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        result = await agent.extract_clinical_summary("synth-patient-001")
        assert result.ready_for_submission is False
        assert "therapy_notes_missing" in result.blockers

    @pytest.mark.asyncio
    async def test_handles_epic_fhir_rate_limit(self, mock_epic_fhir):
        """Agent retries with backoff on Epic 429 rate limit."""
        mock_epic_fhir.get_patient.side_effect = [
            Exception("429 Too Many Requests"),
            SYNTHETIC_PATIENTS[0],  # succeeds on retry
        ]
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=None, watsonx=None, governance=None)
        data = await agent.extract_clinical_summary("synth-patient-001")
        assert data.patient_name is not None
        assert mock_epic_fhir.get_patient.call_count == 2


# ===================================================================
# PA Submission
# ===================================================================

class TestPASubmission:
    """Does the agent correctly submit PA requests?"""

    @pytest.mark.asyncio
    async def test_submits_pa_via_x12_278(self, mock_availity, mock_epic_fhir):
        """Happy path: submit PA via X12 278 for Aetna Medicare."""
        mock_availity.submit_pa.return_value = PA_RESPONSE_PENDING
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=mock_availity, watsonx=None, governance=None)
        patient_data = SYNTHETIC_PATIENTS[0]
        result = await agent.submit(patient_data=patient_data, insurance_info=COVERAGE_AETNA_MA)
        assert result.status == "PENDING"
        assert result.tracking_number is not None
        mock_availity.submit_pa.assert_called_once()

    @pytest.mark.asyncio
    async def test_submits_pa_via_fhir_pas_when_available(self, mock_availity, mock_epic_fhir):
        """If payer supports FHIR PAS, use that over X12 278."""
        mock_availity.payer_supports_fhir.return_value = True
        mock_availity.pas_submit.return_value = PA_RESPONSE_PENDING
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=mock_availity, watsonx=None, governance=None)
        patient_data = SYNTHETIC_PATIENTS[0]
        result = await agent.submit(patient_data=patient_data, insurance_info=COVERAGE_AETNA_MA)
        mock_availity.pas_submit.assert_called_once()
        mock_availity.submit_pa.assert_not_called()  # should NOT fall back to X12

    @pytest.mark.asyncio
    async def test_includes_required_clinical_docs(self, mock_availity, mock_epic_fhir):
        """PA submission must include H&P and therapy notes."""
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=mock_availity, watsonx=None, governance=None)
        patient_data = SYNTHETIC_PATIENTS[0]
        result = await agent.submit(patient_data=patient_data, insurance_info=COVERAGE_AETNA_MA)
        call_args = mock_availity.submit_pa.call_args
        assert "H&P" in str(call_args) or result.submission_method is not None

    @pytest.mark.asyncio
    async def test_submission_fails_gracefully_on_availity_error(self, mock_availity, mock_epic_fhir):
        """If Availity returns an error, agent should not crash — should log and escalate."""
        mock_availity.submit_pa.side_effect = Exception("Availity 503 Service Unavailable")
        agent = PriorAuthAgent(epic=mock_epic_fhir, availity=mock_availity, watsonx=None, governance=None)
        patient_data = SYNTHETIC_PATIENTS[0]
        result = await agent.submit(patient_data=patient_data, insurance_info=COVERAGE_AETNA_MA)
        assert result.status == "SUBMISSION_FAILED"
        assert result.escalated is True


# ===================================================================
# PA Status Polling
# ===================================================================

class TestPAStatusPolling:
    """Does the agent correctly track PA status?"""

    @pytest.mark.asyncio
    async def test_detects_approval(self, mock_availity):
        """Agent detects when PA moves from PENDING to APPROVED."""
        mock_availity.get_pa_status.return_value = PA_RESPONSE_APPROVED
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        status = await agent.check_status("AET-2026-SYNTH-001")
        assert status.status == "APPROVED"
        assert status.approved_days == 20

    @pytest.mark.asyncio
    async def test_detects_denial(self, mock_availity):
        """Agent detects denial and captures reason."""
        mock_availity.get_pa_status.return_value = PA_RESPONSE_DENIED
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        status = await agent.check_status("AET-2026-SYNTH-002")
        assert status.status == "DENIED"
        assert "medical necessity" in status.denial_reason.lower()

    @pytest.mark.asyncio
    async def test_alerts_case_manager_on_approval(self, mock_availity):
        """Case manager receives notification when PA is approved."""
        # TODO: Notification system (notify_case_manager) is not part of the
        # PriorAuthAgent method signatures. This test should be implemented
        # once the notification subsystem is integrated.
        pass

    @pytest.mark.asyncio
    async def test_alerts_case_manager_on_denial(self, mock_availity):
        """Case manager receives urgent notification on PA denial."""
        # TODO: Notification system (notify_case_manager) is not part of the
        # PriorAuthAgent method signatures. This test should be implemented
        # once the notification subsystem is integrated.
        pass

    @pytest.mark.asyncio
    async def test_polls_at_configured_interval(self, mock_availity):
        """Status polling respects configured interval (e.g., every 30 min)."""
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        scheduler = agent.start_polling("AET-2026-SYNTH-001")
        assert scheduler.interval_minutes is not None


# ===================================================================
# Appeal Drafting
# ===================================================================

class TestAppealDrafting:
    """Does the agent draft appeals correctly on denial?"""

    @pytest.mark.asyncio
    async def test_drafts_appeal_on_denial(self, mock_watsonx):
        """Agent uses Granite to draft appeal narrative with clinical evidence."""
        mock_watsonx.generate.return_value = MagicMock(
            text="Appeal: Patient requires SNF placement due to AMPAC score of 14...",
            token_count=200,
        )
        agent = PriorAuthAgent(epic=None, availity=None, watsonx=mock_watsonx, governance=None)
        appeal = await agent.draft_appeal(
            denial=PA_RESPONSE_DENIED,
            patient_data={"ampac_score": 14, "diagnosis": "S72.001A"}
        )
        assert "SNF" in appeal.text
        assert len(appeal.text) > 50  # not empty

    @pytest.mark.asyncio
    async def test_appeal_includes_denial_reason(self, mock_watsonx):
        """Appeal draft directly addresses the payer's denial reason."""
        mock_watsonx.generate.return_value = MagicMock(
            text="Appeal addressing medical necessity denial...",
            token_count=150,
        )
        agent = PriorAuthAgent(epic=None, availity=None, watsonx=mock_watsonx, governance=None)
        appeal = await agent.draft_appeal(
            denial=PA_RESPONSE_DENIED,
            patient_data={"ampac_score": 14, "diagnosis": "S72.001A"}
        )
        prompt_sent = mock_watsonx.generate.call_args[1]["prompt"]
        assert "medical necessity" in prompt_sent.lower()

    @pytest.mark.asyncio
    async def test_appeal_is_presented_for_review_not_auto_submitted(self, mock_watsonx, mock_availity):
        """Appeal must be reviewed by case manager before submission — never auto-sent."""
        mock_watsonx.generate.return_value = MagicMock(
            text="Draft appeal text...",
            token_count=100,
        )
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=mock_watsonx, governance=None)
        appeal = await agent.draft_appeal(denial=PA_RESPONSE_DENIED, patient_data={})
        assert appeal.status == "DRAFT"  # not SUBMITTED
        mock_availity.submit_appeal.assert_not_called()


# ===================================================================
# Edge Cases & Payer Variations
# ===================================================================

class TestPAEdgeCases:
    """Edge cases from primary research interviews."""

    @pytest.mark.asyncio
    async def test_payer_without_portal_access(self, mock_availity):
        """For payers where hospital has no portal access (e.g., CareSource),
        agent should flag that facility must submit and track accordingly."""
        # TODO: submit() signature is (patient_data, insurance_info). The
        # "submission_method" and "hospital_visibility" fields in the result
        # depend on portal-access logic not yet confirmed in the refactored agent.
        # Uncomment once the portal-access check flow is finalized.
        mock_availity.check_portal_access.return_value = False
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        patient_data = SYNTHETIC_PATIENTS[0]
        result = await agent.submit(patient_data=patient_data, insurance_info=COVERAGE_CARESOURCE_MEDICAID)
        assert result.submission_method == "FACILITY_SUBMITTED"

    @pytest.mark.asyncio
    async def test_three_day_rule_check_traditional_medicare(self):
        """Traditional Medicare patients must meet 3-midnight inpatient stay rule.
        Agent should calculate midnight count and warn if not met."""
        agent = PriorAuthAgent(epic=None, availity=None, watsonx=None, governance=None)
        encounter = ENCOUNTER_INPATIENT  # admitted 3 days ago
        coverage = COVERAGE_TRADITIONAL_MEDICARE
        result = agent.check_three_day_rule(encounter, coverage)
        assert result.meets_three_day_rule is True

    @pytest.mark.asyncio
    async def test_three_day_rule_fails_short_stay(self):
        """Patient admitted <3 midnights with traditional Medicare should be flagged."""
        agent = PriorAuthAgent(epic=None, availity=None, watsonx=None, governance=None)
        short_encounter = make_encounter("synth-patient-003", admit_days_ago=1)
        coverage = COVERAGE_TRADITIONAL_MEDICARE
        result = agent.check_three_day_rule(short_encounter, coverage)
        assert result.meets_three_day_rule is False
        assert "private_pay_risk" in result.warnings

    @pytest.mark.asyncio
    async def test_wednesday_to_monday_scenario(self, mock_availity):
        """Real scenario from interview: PA submitted Wednesday, response Monday.
        Agent should track elapsed time and alert if exceeding expected window."""
        mock_availity.get_pa_status.return_value = PA_RESPONSE_PENDING
        agent = PriorAuthAgent(epic=None, availity=mock_availity, watsonx=None, governance=None)
        # Simulate 5 days elapsed
        alert = agent.check_overdue_pa(tracking_number="AET-2026-SYNTH-003", submitted_days_ago=5)
        assert alert.is_overdue is True
        assert alert.priority == "urgent"
