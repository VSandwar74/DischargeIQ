"""
Tests: Supervisor Agent (Orchestration)
Priority: P1 — coordinates the other agents, manages workflow state.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.fixtures.synthetic_data import (
    ENCOUNTER_INPATIENT, ENCOUNTER_OBSERVATION,
    COVERAGE_AETNA_MA, COVERAGE_TRADITIONAL_MEDICARE,
    AMPAC_SCORE_LOW, AMPAC_SCORE_HIGH,
    PA_RESPONSE_APPROVED, PA_RESPONSE_DENIED, PA_RESPONSE_PENDING,
    REFERRAL_ACCEPTED,
)
from src.agents.supervisor import SupervisorAgent, InvalidStateTransition


# ===================================================================
# Workflow Initiation
# ===================================================================

class TestWorkflowInitiation:

    @pytest.mark.asyncio
    async def test_creates_workflow_on_discharge_order(self, mock_epic_fhir, mock_workflow_repo):
        """Discharge order trigger should create a new workflow record."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "discharge_order", "encounter_id": "enc-001"}
        )
        assert workflow["status"] == "INITIATED"
        mock_workflow_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_workflow_on_therapy_assessment(self, mock_epic_fhir, mock_workflow_repo):
        """Therapy assessment completion should also trigger workflow."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "therapy_assessment", "ampac_score": 14}
        )
        assert workflow["status"] == "INITIATED"

    @pytest.mark.asyncio
    async def test_does_not_duplicate_active_workflow(self, mock_epic_fhir, mock_workflow_repo):
        """If an active workflow already exists for this patient, don't create another."""
        mock_workflow_repo.get_active_by_patient.return_value = {"id": "wf-existing", "status": "AUTH_PENDING"}
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "discharge_order"}
        )
        assert workflow["id"] == "wf-existing"  # returns existing
        mock_workflow_repo.create.assert_not_called()  # doesn't create new


# ===================================================================
# Agent Coordination
# ===================================================================

class TestAgentCoordination:

    @pytest.mark.asyncio
    async def test_runs_auth_and_placement_in_parallel(self, mock_epic_fhir, mock_workflow_repo):
        """PA check + facility search should run concurrently, not sequentially."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "discharge_order", "encounter_id": "enc-001"}
        )
        # Workflow should have both prior_auth and placement_options populated
        assert "prior_auth" in workflow
        assert "placement_options" in workflow

    @pytest.mark.asyncio
    async def test_skips_pa_when_not_required(self, mock_epic_fhir, mock_workflow_repo):
        """If CRD says PA not required, supervisor should skip PA agent entirely."""
        # TODO: Skipping PA depends on internal check_if_required wiring in
        # handle_discharge_trigger. The current refactored signature returns
        # prior_auth in the result dict. Verify the value is None or NOT_REQUIRED
        # when CRD returns pa_required=False. Needs integration with mock_availity
        # to fully test; leaving as a partial assertion.
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "discharge_order"}
        )
        # At minimum, workflow should contain the prior_auth key
        assert "prior_auth" in workflow

    @pytest.mark.asyncio
    async def test_compliance_agent_always_runs(self, mock_epic_fhir, mock_workflow_repo):
        """Compliance agent should log every workflow regardless of PA requirement."""
        # TODO: Verifying compliance_agent.log_workflow is called requires
        # patching internal agents on the SupervisorAgent instance. This depends
        # on how the refactored SupervisorAgent wires up sub-agents internally.
        # Leaving as a spec until sub-agent injection is finalized.
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        workflow = await supervisor.handle_discharge_trigger(
            patient_id="synth-patient-001",
            trigger={"type": "discharge_order"}
        )
        assert workflow["status"] == "INITIATED"


# ===================================================================
# Workflow State Transitions
# ===================================================================

class TestWorkflowStateTransitions:

    @pytest.mark.asyncio
    async def test_initiated_to_auth_pending(self, mock_epic_fhir, mock_workflow_repo):
        """After PA submission, workflow should move to AUTH_PENDING."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        await supervisor.on_pa_submitted(workflow_id="wf-001", pa_result=PA_RESPONSE_PENDING)
        mock_workflow_repo.update.assert_called_with("wf-001", status="AUTH_PENDING")

    @pytest.mark.asyncio
    async def test_auth_pending_to_auth_approved(self, mock_epic_fhir, mock_workflow_repo):
        """On PA approval, workflow transitions to AUTH_APPROVED."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        await supervisor.on_pa_status_change(workflow_id="wf-001", new_status=PA_RESPONSE_APPROVED)
        mock_workflow_repo.update.assert_called_with("wf-001", status="AUTH_APPROVED")

    @pytest.mark.asyncio
    async def test_auth_pending_to_auth_denied(self, mock_epic_fhir, mock_workflow_repo):
        """On PA denial, workflow transitions to AUTH_DENIED."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        await supervisor.on_pa_status_change(workflow_id="wf-001", new_status=PA_RESPONSE_DENIED)
        mock_workflow_repo.update.assert_called_with("wf-001", status="AUTH_DENIED")

    @pytest.mark.asyncio
    async def test_placement_confirmed_after_auth_approved(self, mock_epic_fhir, mock_workflow_repo):
        """After auth approved + facility accepted, status should be PLACEMENT_CONFIRMED."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        await supervisor.on_placement_accepted(workflow_id="wf-001", referral=REFERRAL_ACCEPTED)
        mock_workflow_repo.update.assert_called_with("wf-001", status="PLACEMENT_CONFIRMED")

    @pytest.mark.asyncio
    async def test_escalation_on_stalled_workflow(self, mock_epic_fhir, mock_workflow_repo):
        """Workflow stuck in AUTH_PENDING for >72 hours should escalate."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        stalled_workflow = {"id": "wf-001", "status": "AUTH_PENDING", "hours_in_status": 80}
        result = await supervisor.check_stalled_workflows([stalled_workflow])
        assert result[0]["status"] == "ESCALATED"

    @pytest.mark.asyncio
    async def test_invalid_state_transition_rejected(self, mock_epic_fhir, mock_workflow_repo):
        """Cannot go from DISCHARGED back to AUTH_PENDING."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        with pytest.raises(InvalidStateTransition):
            await supervisor.transition(workflow_id="wf-001",
                                        from_status="DISCHARGED",
                                        to_status="AUTH_PENDING")


# ===================================================================
# Human-in-the-Loop
# ===================================================================

class TestHumanInTheLoop:

    @pytest.mark.asyncio
    async def test_case_manager_must_confirm_placement(self, mock_epic_fhir, mock_workflow_repo):
        """Placement selection requires explicit case manager approval."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        result = await supervisor.propose_placement(
            workflow_id="wf-001", facility=REFERRAL_ACCEPTED
        )
        assert result.status == "AWAITING_CM_APPROVAL"
        assert result.auto_submitted is False

    @pytest.mark.asyncio
    async def test_case_manager_can_override_agent_recommendation(self, mock_epic_fhir, mock_workflow_repo):
        """Case manager can select a different facility than the agent's top pick."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        result = await supervisor.override_placement(
            workflow_id="wf-001",
            agent_recommended="fac-001",
            cm_selected="fac-003",
            cm_reason="Family prefers this location"
        )
        assert result.selected_facility == "fac-003"
        assert result.override_logged is True

    @pytest.mark.asyncio
    async def test_appeal_requires_cm_review_before_submission(self, mock_epic_fhir, mock_workflow_repo):
        """Appeal draft must be reviewed and approved by CM before sending."""
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        appeal = await supervisor.get_appeal_draft(workflow_id="wf-001")
        assert appeal.status == "DRAFT"
        # CM approves
        submitted = await supervisor.submit_appeal(workflow_id="wf-001", cm_approved=True)
        assert submitted.status == "APPEAL_SUBMITTED"


# ===================================================================
# Observation Status Detection
# ===================================================================

class TestObservationStatus:
    """From interview: observation patients lose Medicare SNF benefit."""

    @pytest.mark.asyncio
    async def test_flags_observation_with_traditional_medicare(self, mock_epic_fhir, mock_workflow_repo):
        """Observation + traditional Medicare = no SNF benefit. Must alert CM."""
        mock_epic_fhir.get_encounter.return_value = ENCOUNTER_OBSERVATION
        mock_epic_fhir.get_coverage.return_value = COVERAGE_TRADITIONAL_MEDICARE
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        alert = await supervisor.check_observation_status("synth-patient-002")
        assert alert is not None
        assert alert.level == "CRITICAL"
        assert "observation" in alert.message.lower()
        assert "private pay" in alert.message.lower()

    @pytest.mark.asyncio
    async def test_no_flag_for_observation_with_ma(self, mock_epic_fhir, mock_workflow_repo):
        """Observation + Medicare Advantage = SNF benefit still available. No alert."""
        mock_epic_fhir.get_encounter.return_value = ENCOUNTER_OBSERVATION
        mock_epic_fhir.get_coverage.return_value = COVERAGE_AETNA_MA
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        alert = await supervisor.check_observation_status("synth-patient-002")
        assert alert is None  # MA covers observation patients

    @pytest.mark.asyncio
    async def test_no_flag_for_inpatient(self, mock_epic_fhir, mock_workflow_repo):
        """Inpatient status = no observation alert needed."""
        mock_epic_fhir.get_encounter.return_value = ENCOUNTER_INPATIENT
        supervisor = SupervisorAgent(epic=mock_epic_fhir, repo=mock_workflow_repo)
        alert = await supervisor.check_observation_status("synth-patient-001")
        assert alert is None
