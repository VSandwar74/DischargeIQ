"""
Shared pytest fixtures for DischargeIQ test suite.
"""
import os
os.environ.setdefault("ENCRYPTION_KEY", "H1AUtHiZBOdOQyxunrAEKJGZaaNzVZtW1S4LR6tEIzM=")
os.environ.setdefault("AUDIT_SALT", "test-salt-for-unit-tests")

import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.fixtures.synthetic_data import (
    SYNTHETIC_PATIENTS, SYNTHETIC_FACILITIES,
    ENCOUNTER_INPATIENT, ENCOUNTER_OBSERVATION, ENCOUNTER_LONG_STAY,
    COVERAGE_AETNA_MA, COVERAGE_UNITED_MA, COVERAGE_TRADITIONAL_MEDICARE, COVERAGE_CARESOURCE_MEDICAID,
    AMPAC_SCORE_LOW, AMPAC_SCORE_BORDERLINE, AMPAC_SCORE_HIGH,
    CONDITION_HIP_FRACTURE, CONDITION_KNEE_REPLACEMENT,
    PA_RESPONSE_APPROVED, PA_RESPONSE_DENIED, PA_RESPONSE_PENDING,
    REFERRAL_ACCEPTED, REFERRAL_DECLINED_INSURANCE, REFERRAL_DECLINED_BEHAVIORAL, REFERRAL_DECLINED_NO_BEDS,
)


# ---------------------------------------------------------------------------
# Mock Integration Clients
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_epic_fhir():
    """Mock Epic FHIR client."""
    client = AsyncMock()
    client.get_patient.return_value = SYNTHETIC_PATIENTS[0]
    client.get_encounter.return_value = ENCOUNTER_INPATIENT
    client.get_coverage.return_value = COVERAGE_AETNA_MA
    client.get_therapy_assessments.return_value = [AMPAC_SCORE_LOW]
    client.get_conditions.return_value = [CONDITION_HIP_FRACTURE]
    client.get_clinical_documents.return_value = [
        {"id": "doc-001", "type": "H&P", "content": "Synthetic clinical summary..."},
        {"id": "doc-002", "type": "Therapy Notes", "content": "Synthetic therapy notes..."},
    ]
    return client


@pytest.fixture
def mock_availity():
    """Mock Availity payer integration client."""
    client = AsyncMock()
    client.check_pa_required.return_value = True
    client.submit_pa.return_value = PA_RESPONSE_PENDING
    client.get_pa_status.return_value = PA_RESPONSE_PENDING
    client.crd_check.return_value = MagicMock(pa_required=True)
    client.dtr_populate.return_value = {"form_data": "populated"}
    return client


@pytest.fixture
def mock_careport():
    """Mock WellSky/CarePort referral client."""
    client = AsyncMock()
    client.search_facilities.return_value = SYNTHETIC_FACILITIES
    client.send_referral.return_value = REFERRAL_ACCEPTED
    return client


@pytest.fixture
def mock_watsonx():
    """Mock watsonx.ai inference client."""
    client = AsyncMock()
    client.generate.return_value = MagicMock(
        text="Synthetic model output for testing purposes.",
        token_count=42,
        model="granite-4-h-small",
    )
    return client


@pytest.fixture
def mock_watsonx_governance():
    """Mock watsonx.governance client."""
    client = AsyncMock()
    client.log_event.return_value = {"status": "logged", "event_id": "evt-synth-001"}
    client.check_safety.return_value = MagicMock(passed=True, reason=None)
    return client


# ---------------------------------------------------------------------------
# Database / Repository Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_workflow_repo():
    """Mock workflow repository."""
    repo = AsyncMock()
    repo.create.return_value = {
        "id": "wf-synth-001",
        "patient_id": "synth-patient-001",
        "status": "INITIATED",
        "prior_auth": None,
        "placement_options": [],
        "audit_trail": [],
    }
    repo.get.return_value = repo.create.return_value
    repo.get_active_by_patient.return_value = None  # no existing workflow by default
    repo.update.return_value = None
    return repo


# ---------------------------------------------------------------------------
# Auth / User Context
# ---------------------------------------------------------------------------

@pytest.fixture
def case_manager_context():
    """Authenticated case manager context."""
    return {
        "user_id": "cm-synth-001",
        "role": "case_manager",
        "name": "Test CaseManager",
        "assigned_patients": ["synth-patient-001", "synth-patient-002", "synth-patient-003"],
    }


@pytest.fixture
def admin_context():
    """Authenticated admin context."""
    return {
        "user_id": "admin-synth-001",
        "role": "admin",
        "name": "Test Admin",
    }


@pytest.fixture
def unauthorized_context():
    """User without access to any patients."""
    return {
        "user_id": "cm-synth-999",
        "role": "case_manager",
        "name": "Unassigned CaseManager",
        "assigned_patients": [],
    }