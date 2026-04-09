"""
DischargeIQ In-Memory Data Store

Synthetic demo data for 10 patients, 10 workflows, prior auth records,
facility matches, and audit trail entries.

ALL data is synthetic. No real patient information is used anywhere.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.security.encryption import encrypt_phi
from src.security.hashing import hash_identifier

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _uuid() -> str:
    return str(uuid.uuid4())


def _iso(dt: datetime) -> str:
    return dt.isoformat()


_now = datetime(2026, 4, 9, 14, 0, 0)

# ---------------------------------------------------------------------------
# Patients (10) — all synthetic
# ---------------------------------------------------------------------------

_patient_ids = [_uuid() for _ in range(10)]

PATIENTS = [
    {
        "id": _patient_ids[0],
        "name": "Margaret Chen",
        "mrn": "MRN-30491827",
        "dob": "1948-06-12",
        "name_encrypted": encrypt_phi("Margaret Chen"),
        "mrn_encrypted": encrypt_phi("MRN-30491827"),
        "dob_encrypted": encrypt_phi("1948-06-12"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[0][:8]}"),
        "coverage_payer_id": "aetna-ma-001",
        "coverage_payer_name": "Aetna Medicare Advantage",
        "created_at": _iso(_now - timedelta(days=5)),
        "updated_at": _iso(_now - timedelta(hours=3)),
    },
    {
        "id": _patient_ids[1],
        "name": "Robert Williams",
        "mrn": "MRN-30582946",
        "dob": "1941-11-03",
        "name_encrypted": encrypt_phi("Robert Williams"),
        "mrn_encrypted": encrypt_phi("MRN-30582946"),
        "dob_encrypted": encrypt_phi("1941-11-03"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[1][:8]}"),
        "coverage_payer_id": "uhc-ma-002",
        "coverage_payer_name": "UnitedHealthcare Medicare",
        "created_at": _iso(_now - timedelta(days=4)),
        "updated_at": _iso(_now - timedelta(hours=6)),
    },
    {
        "id": _patient_ids[2],
        "name": "Dorothy Johnson",
        "mrn": "MRN-30674183",
        "dob": "1944-02-28",
        "name_encrypted": encrypt_phi("Dorothy Johnson"),
        "mrn_encrypted": encrypt_phi("MRN-30674183"),
        "dob_encrypted": encrypt_phi("1944-02-28"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[2][:8]}"),
        "coverage_payer_id": "anthem-ma-003",
        "coverage_payer_name": "Anthem Blue Cross Medicare",
        "created_at": _iso(_now - timedelta(days=3)),
        "updated_at": _iso(_now - timedelta(hours=1)),
    },
    {
        "id": _patient_ids[3],
        "name": "James Patterson",
        "mrn": "MRN-30785291",
        "dob": "1952-09-17",
        "name_encrypted": encrypt_phi("James Patterson"),
        "mrn_encrypted": encrypt_phi("MRN-30785291"),
        "dob_encrypted": encrypt_phi("1952-09-17"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[3][:8]}"),
        "coverage_payer_id": "humana-ma-004",
        "coverage_payer_name": "Humana Gold Plus",
        "created_at": _iso(_now - timedelta(days=6)),
        "updated_at": _iso(_now - timedelta(hours=12)),
    },
    {
        "id": _patient_ids[4],
        "name": "Helen Garcia",
        "mrn": "MRN-30896472",
        "dob": "1937-04-05",
        "name_encrypted": encrypt_phi("Helen Garcia"),
        "mrn_encrypted": encrypt_phi("MRN-30896472"),
        "dob_encrypted": encrypt_phi("1937-04-05"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[4][:8]}"),
        "coverage_payer_id": "cigna-ma-005",
        "coverage_payer_name": "Cigna Medicare Advantage",
        "created_at": _iso(_now - timedelta(days=2)),
        "updated_at": _iso(_now - timedelta(hours=4)),
    },
    {
        "id": _patient_ids[5],
        "name": "William Thompson",
        "mrn": "MRN-30912638",
        "dob": "1950-12-22",
        "name_encrypted": encrypt_phi("William Thompson"),
        "mrn_encrypted": encrypt_phi("MRN-30912638"),
        "dob_encrypted": encrypt_phi("1950-12-22"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[5][:8]}"),
        "coverage_payer_id": "wellcare-ma-006",
        "coverage_payer_name": "WellCare Medicare",
        "created_at": _iso(_now - timedelta(days=7)),
        "updated_at": _iso(_now - timedelta(hours=8)),
    },
    {
        "id": _patient_ids[6],
        "name": "Patricia Davis",
        "mrn": "MRN-31023749",
        "dob": "1946-07-30",
        "name_encrypted": encrypt_phi("Patricia Davis"),
        "mrn_encrypted": encrypt_phi("MRN-31023749"),
        "dob_encrypted": encrypt_phi("1946-07-30"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[6][:8]}"),
        "coverage_payer_id": "aetna-ma-001",
        "coverage_payer_name": "Aetna Medicare Advantage",
        "created_at": _iso(_now - timedelta(days=3)),
        "updated_at": _iso(_now - timedelta(hours=2)),
    },
    {
        "id": _patient_ids[7],
        "name": "Thomas Anderson",
        "mrn": "MRN-31134856",
        "dob": "1958-01-14",
        "name_encrypted": encrypt_phi("Thomas Anderson"),
        "mrn_encrypted": encrypt_phi("MRN-31134856"),
        "dob_encrypted": encrypt_phi("1958-01-14"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[7][:8]}"),
        "coverage_payer_id": "uhc-ma-002",
        "coverage_payer_name": "UnitedHealthcare Medicare",
        "created_at": _iso(_now - timedelta(days=1)),
        "updated_at": _iso(_now - timedelta(minutes=30)),
    },
    {
        "id": _patient_ids[8],
        "name": "Barbara Martinez",
        "mrn": "MRN-31245967",
        "dob": "1943-08-09",
        "name_encrypted": encrypt_phi("Barbara Martinez"),
        "mrn_encrypted": encrypt_phi("MRN-31245967"),
        "dob_encrypted": encrypt_phi("1943-08-09"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[8][:8]}"),
        "coverage_payer_id": "anthem-ma-003",
        "coverage_payer_name": "Anthem Blue Cross Medicare",
        "created_at": _iso(_now - timedelta(days=4)),
        "updated_at": _iso(_now - timedelta(hours=5)),
    },
    {
        "id": _patient_ids[9],
        "name": "Richard Lee",
        "mrn": "MRN-31357078",
        "dob": "1955-05-19",
        "name_encrypted": encrypt_phi("Richard Lee"),
        "mrn_encrypted": encrypt_phi("MRN-31357078"),
        "dob_encrypted": encrypt_phi("1955-05-19"),
        "epic_patient_id_encrypted": encrypt_phi(f"epic-{_patient_ids[9][:8]}"),
        "coverage_payer_id": "humana-ma-004",
        "coverage_payer_name": "Humana Gold Plus",
        "created_at": _iso(_now - timedelta(days=2)),
        "updated_at": _iso(_now - timedelta(hours=7)),
    },
]

# ---------------------------------------------------------------------------
# Workflow IDs
# ---------------------------------------------------------------------------

_wf_ids = [_uuid() for _ in range(10)]

# ---------------------------------------------------------------------------
# Prior Auth Records
# ---------------------------------------------------------------------------

_pa_ids = [_uuid() for _ in range(7)]

PRIOR_AUTH_RECORDS = [
    # WF 0 — AUTH_PENDING (Margaret Chen, Aetna)
    {
        "id": _pa_ids[0],
        "workflow_id": _wf_ids[0],
        "payer_id": "aetna-ma-001",
        "payer_name": "Aetna Medicare Advantage",
        "submission_method": "X12_278",
        "status": "PENDING_REVIEW",
        "tracking_number": "AVL-2026-40128",
        "submitted_at": _iso(_now - timedelta(hours=26)),
        "response_at": None,
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Discharge Summary Draft"],
        "created_at": _iso(_now - timedelta(hours=26)),
    },
    # WF 1 — AUTH_PENDING (Robert Williams, UHC)
    {
        "id": _pa_ids[1],
        "workflow_id": _wf_ids[1],
        "payer_id": "uhc-ma-002",
        "payer_name": "UnitedHealthcare Medicare",
        "submission_method": "X12_278",
        "status": "PENDING_REVIEW",
        "tracking_number": "AVL-2026-40235",
        "submitted_at": _iso(_now - timedelta(hours=18)),
        "response_at": None,
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Functional Status Assessment"],
        "created_at": _iso(_now - timedelta(hours=18)),
    },
    # WF 2 — AUTH_APPROVED (Dorothy Johnson, Anthem) — but then denied, see below
    # Actually let's make WF 2 AUTH_DENIED
    {
        "id": _pa_ids[2],
        "workflow_id": _wf_ids[2],
        "payer_id": "anthem-ma-003",
        "payer_name": "Anthem Blue Cross Medicare",
        "submission_method": "FHIR_PAS",
        "status": "DENIED",
        "tracking_number": "AVL-2026-40347",
        "submitted_at": _iso(_now - timedelta(days=2)),
        "response_at": _iso(_now - timedelta(hours=6)),
        "denial_reason": "Medical necessity not established — insufficient therapy documentation",
        "appeal_draft": (
            "APPEAL: We respectfully request reconsideration of the denial for SNF placement. "
            "The patient's AM-PAC Basic Mobility score of 16.3 and Daily Activity score of 20.1 "
            "demonstrate significant functional limitations requiring 24-hour skilled nursing care. "
            "Additional therapy evaluation attached."
        ),
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Discharge Summary Draft", "Physician Letter of Medical Necessity"],
        "created_at": _iso(_now - timedelta(days=2)),
    },
    # WF 3 — AUTH_APPROVED (James Patterson, Humana)
    {
        "id": _pa_ids[3],
        "workflow_id": _wf_ids[3],
        "payer_id": "humana-ma-004",
        "payer_name": "Humana Gold Plus",
        "submission_method": "X12_278",
        "status": "APPROVED",
        "tracking_number": "AVL-2026-40456",
        "submitted_at": _iso(_now - timedelta(days=3)),
        "response_at": _iso(_now - timedelta(days=1)),
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Discharge Summary Draft"],
        "created_at": _iso(_now - timedelta(days=3)),
    },
    # WF 4 — AUTH_APPROVED (Helen Garcia, Cigna)
    {
        "id": _pa_ids[4],
        "workflow_id": _wf_ids[4],
        "payer_id": "cigna-ma-005",
        "payer_name": "Cigna Medicare Advantage",
        "submission_method": "FHIR_PAS",
        "status": "APPROVED",
        "tracking_number": "AVL-2026-40567",
        "submitted_at": _iso(_now - timedelta(days=2)),
        "response_at": _iso(_now - timedelta(hours=20)),
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Functional Status Assessment"],
        "created_at": _iso(_now - timedelta(days=2)),
    },
    # WF 6 — PLACEMENT_CONFIRMED (Patricia Davis, Aetna)
    {
        "id": _pa_ids[5],
        "workflow_id": _wf_ids[6],
        "payer_id": "aetna-ma-001",
        "payer_name": "Aetna Medicare Advantage",
        "submission_method": "X12_278",
        "status": "APPROVED",
        "tracking_number": "AVL-2026-40789",
        "submitted_at": _iso(_now - timedelta(days=4)),
        "response_at": _iso(_now - timedelta(days=3)),
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Discharge Summary Draft"],
        "created_at": _iso(_now - timedelta(days=4)),
    },
    # WF 7 — DISCHARGED (Thomas Anderson, UHC)
    {
        "id": _pa_ids[6],
        "workflow_id": _wf_ids[7],
        "payer_id": "uhc-ma-002",
        "payer_name": "UnitedHealthcare Medicare",
        "submission_method": "X12_278",
        "status": "APPROVED",
        "tracking_number": "AVL-2026-40890",
        "submitted_at": _iso(_now - timedelta(days=5)),
        "response_at": _iso(_now - timedelta(days=4)),
        "denial_reason": None,
        "appeal_draft": None,
        "clinical_docs_sent": ["History & Physical", "Therapy Evaluation (AM-PAC)", "Discharge Summary Draft", "Transport Order"],
        "created_at": _iso(_now - timedelta(days=5)),
    },
]

# ---------------------------------------------------------------------------
# Facility Matches
# ---------------------------------------------------------------------------

_fm_ids = [_uuid() for _ in range(15)]

FACILITY_MATCHES = [
    # WF 3 — PLACEMENT_SEARCHING (James Patterson) — auth approved, now searching
    {
        "id": _fm_ids[0],
        "workflow_id": _wf_ids[3],
        "facility_name": "Maple Grove Skilled Nursing",
        "careport_referral_id": "CP-401234",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 92,
        "distance_miles": 4.2,
        "referral_status": "SENT",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(hours=20)),
    },
    {
        "id": _fm_ids[1],
        "workflow_id": _wf_ids[3],
        "facility_name": "Sunrise Senior Care",
        "careport_referral_id": "CP-401235",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 87,
        "distance_miles": 6.8,
        "referral_status": "SENT",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(hours=20)),
    },
    {
        "id": _fm_ids[2],
        "workflow_id": _wf_ids[3],
        "facility_name": "Oak Hill Rehabilitation Center",
        "careport_referral_id": "CP-401236",
        "bed_available": False,
        "accepts_insurance": True,
        "match_score": 78,
        "distance_miles": 12.3,
        "referral_status": "DECLINED",
        "decline_reason": "No beds available",
        "created_at": _iso(_now - timedelta(hours=20)),
    },
    # WF 4 — PLACEMENT_SEARCHING (Helen Garcia) — auth approved, searching
    {
        "id": _fm_ids[3],
        "workflow_id": _wf_ids[4],
        "facility_name": "Brookdale Health & Rehab",
        "careport_referral_id": "CP-401340",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 90,
        "distance_miles": 5.1,
        "referral_status": "SENT",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(hours=16)),
    },
    {
        "id": _fm_ids[4],
        "workflow_id": _wf_ids[4],
        "facility_name": "Heritage Park Nursing Center",
        "careport_referral_id": "CP-401341",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 85,
        "distance_miles": 8.7,
        "referral_status": "SENT",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(hours=16)),
    },
    {
        "id": _fm_ids[5],
        "workflow_id": _wf_ids[4],
        "facility_name": "Silver Lake SNF",
        "careport_referral_id": "CP-401342",
        "bed_available": False,
        "accepts_insurance": False,
        "match_score": 62,
        "distance_miles": 18.5,
        "referral_status": "DECLINED",
        "decline_reason": "Does not accept Cigna Medicare Advantage",
        "created_at": _iso(_now - timedelta(hours=16)),
    },
    # WF 6 — PLACEMENT_CONFIRMED (Patricia Davis)
    {
        "id": _fm_ids[6],
        "workflow_id": _wf_ids[6],
        "facility_name": "Maple Grove Skilled Nursing",
        "careport_referral_id": "CP-401450",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 94,
        "distance_miles": 3.8,
        "referral_status": "ACCEPTED",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(days=2)),
    },
    {
        "id": _fm_ids[7],
        "workflow_id": _wf_ids[6],
        "facility_name": "Sunrise Senior Care",
        "careport_referral_id": "CP-401451",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 88,
        "distance_miles": 7.2,
        "referral_status": "NO_RESPONSE",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(days=2)),
    },
    # WF 7 — DISCHARGED (Thomas Anderson)
    {
        "id": _fm_ids[8],
        "workflow_id": _wf_ids[7],
        "facility_name": "Lakewood Recovery Center",
        "careport_referral_id": "CP-401560",
        "bed_available": True,
        "accepts_insurance": True,
        "match_score": 91,
        "distance_miles": 5.5,
        "referral_status": "ACCEPTED",
        "decline_reason": None,
        "created_at": _iso(_now - timedelta(days=3)),
    },
    # WF 8 — ESCALATED (Barbara Martinez) — facilities declining
    {
        "id": _fm_ids[9],
        "workflow_id": _wf_ids[8],
        "facility_name": "Oak Hill Rehabilitation Center",
        "careport_referral_id": "CP-401670",
        "bed_available": False,
        "accepts_insurance": True,
        "match_score": 83,
        "distance_miles": 11.2,
        "referral_status": "DECLINED",
        "decline_reason": "No beds available",
        "created_at": _iso(_now - timedelta(days=3)),
    },
    {
        "id": _fm_ids[10],
        "workflow_id": _wf_ids[8],
        "facility_name": "Silver Lake SNF",
        "careport_referral_id": "CP-401671",
        "bed_available": False,
        "accepts_insurance": True,
        "match_score": 71,
        "distance_miles": 19.3,
        "referral_status": "DECLINED",
        "decline_reason": "Patient acuity too high",
        "created_at": _iso(_now - timedelta(days=3)),
    },
    {
        "id": _fm_ids[11],
        "workflow_id": _wf_ids[8],
        "facility_name": "Brookdale Health & Rehab",
        "careport_referral_id": "CP-401672",
        "bed_available": True,
        "accepts_insurance": False,
        "match_score": 68,
        "distance_miles": 14.7,
        "referral_status": "DECLINED",
        "decline_reason": "Does not accept Anthem Blue Cross Medicare",
        "created_at": _iso(_now - timedelta(days=2)),
    },
]

# ---------------------------------------------------------------------------
# Workflows (10)
# ---------------------------------------------------------------------------

WORKFLOWS = [
    # 0 — AUTH_PENDING (Margaret Chen)
    {
        "id": _wf_ids[0],
        "patient_id": _patient_ids[0],
        "patient_name": "Margaret Chen",
        "patient_mrn": "MRN-30491827",
        "payer_name": "Aetna Medicare Advantage",
        "status": "AUTH_PENDING",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": _pa_ids[0],
        "selected_facility_id": None,
        "avoidable_days": 1,
        "created_at": _iso(_now - timedelta(days=2)),
        "updated_at": _iso(_now - timedelta(hours=3)),
    },
    # 1 — AUTH_PENDING (Robert Williams)
    {
        "id": _wf_ids[1],
        "patient_id": _patient_ids[1],
        "patient_name": "Robert Williams",
        "patient_mrn": "MRN-30582946",
        "payer_name": "UnitedHealthcare Medicare",
        "status": "AUTH_PENDING",
        "trigger_event": "case_manager_initiated",
        "prior_auth_id": _pa_ids[1],
        "selected_facility_id": None,
        "avoidable_days": 0,
        "created_at": _iso(_now - timedelta(days=1)),
        "updated_at": _iso(_now - timedelta(hours=6)),
    },
    # 2 — AUTH_DENIED (Dorothy Johnson)
    {
        "id": _wf_ids[2],
        "patient_id": _patient_ids[2],
        "patient_name": "Dorothy Johnson",
        "patient_mrn": "MRN-30674183",
        "payer_name": "Anthem Blue Cross Medicare",
        "status": "AUTH_DENIED",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": _pa_ids[2],
        "selected_facility_id": None,
        "avoidable_days": 2,
        "created_at": _iso(_now - timedelta(days=3)),
        "updated_at": _iso(_now - timedelta(hours=6)),
    },
    # 3 — PLACEMENT_SEARCHING (James Patterson) — auth approved
    {
        "id": _wf_ids[3],
        "patient_id": _patient_ids[3],
        "patient_name": "James Patterson",
        "patient_mrn": "MRN-30785291",
        "payer_name": "Humana Gold Plus",
        "status": "PLACEMENT_SEARCHING",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": _pa_ids[3],
        "selected_facility_id": None,
        "avoidable_days": 1,
        "created_at": _iso(_now - timedelta(days=4)),
        "updated_at": _iso(_now - timedelta(hours=12)),
    },
    # 4 — PLACEMENT_SEARCHING (Helen Garcia) — auth approved
    {
        "id": _wf_ids[4],
        "patient_id": _patient_ids[4],
        "patient_name": "Helen Garcia",
        "patient_mrn": "MRN-30896472",
        "payer_name": "Cigna Medicare Advantage",
        "status": "PLACEMENT_SEARCHING",
        "trigger_event": "utilization_review_flag",
        "prior_auth_id": _pa_ids[4],
        "selected_facility_id": None,
        "avoidable_days": 0,
        "created_at": _iso(_now - timedelta(days=2)),
        "updated_at": _iso(_now - timedelta(hours=4)),
    },
    # 5 — AUTH_APPROVED (William Thompson) — no PA needed for WellCare in this case
    {
        "id": _wf_ids[5],
        "patient_id": _patient_ids[5],
        "patient_name": "William Thompson",
        "patient_mrn": "MRN-30912638",
        "payer_name": "WellCare Medicare",
        "status": "AUTH_APPROVED",
        "trigger_event": "case_manager_initiated",
        "prior_auth_id": None,
        "selected_facility_id": None,
        "avoidable_days": 3,
        "created_at": _iso(_now - timedelta(days=5)),
        "updated_at": _iso(_now - timedelta(hours=8)),
    },
    # 6 — PLACEMENT_CONFIRMED (Patricia Davis)
    {
        "id": _wf_ids[6],
        "patient_id": _patient_ids[6],
        "patient_name": "Patricia Davis",
        "patient_mrn": "MRN-31023749",
        "payer_name": "Aetna Medicare Advantage",
        "status": "PLACEMENT_CONFIRMED",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": _pa_ids[5],
        "selected_facility_id": _fm_ids[6],
        "avoidable_days": 1,
        "created_at": _iso(_now - timedelta(days=4)),
        "updated_at": _iso(_now - timedelta(hours=2)),
    },
    # 7 — DISCHARGED (Thomas Anderson)
    {
        "id": _wf_ids[7],
        "patient_id": _patient_ids[7],
        "patient_name": "Thomas Anderson",
        "patient_mrn": "MRN-31134856",
        "payer_name": "UnitedHealthcare Medicare",
        "status": "DISCHARGED",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": _pa_ids[6],
        "selected_facility_id": _fm_ids[8],
        "avoidable_days": 0,
        "created_at": _iso(_now - timedelta(days=5)),
        "updated_at": _iso(_now - timedelta(minutes=30)),
    },
    # 8 — ESCALATED (Barbara Martinez) — all facilities declined
    {
        "id": _wf_ids[8],
        "patient_id": _patient_ids[8],
        "patient_name": "Barbara Martinez",
        "patient_mrn": "MRN-31245967",
        "payer_name": "Anthem Blue Cross Medicare",
        "status": "ESCALATED",
        "trigger_event": "physician_discharge_order",
        "prior_auth_id": None,
        "selected_facility_id": None,
        "avoidable_days": 4,
        "created_at": _iso(_now - timedelta(days=5)),
        "updated_at": _iso(_now - timedelta(hours=5)),
    },
    # 9 — AUTH_APPROVED (Richard Lee)
    {
        "id": _wf_ids[9],
        "patient_id": _patient_ids[9],
        "patient_name": "Richard Lee",
        "patient_mrn": "MRN-31357078",
        "payer_name": "Humana Gold Plus",
        "status": "AUTH_APPROVED",
        "trigger_event": "utilization_review_flag",
        "prior_auth_id": None,
        "selected_facility_id": None,
        "avoidable_days": 1,
        "created_at": _iso(_now - timedelta(days=2)),
        "updated_at": _iso(_now - timedelta(hours=7)),
    },
]

# ---------------------------------------------------------------------------
# Audit Trail Entries (20) — all use hashed patient IDs
# ---------------------------------------------------------------------------

AUDIT_ENTRIES = [
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[0],
        "patient_id_hash": hash_identifier(_patient_ids[0]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "physician_discharge_order", "payer": "Aetna Medicare Advantage"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=2)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[0],
        "patient_id_hash": hash_identifier(_patient_ids[0]),
        "action": "prior_auth_submitted",
        "agent": "prior_auth_agent",
        "details": {"tracking_number": "AVL-2026-40128", "method": "X12_278"},
        "model_version": "granite-4-h-small-v1.2",
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=26)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[1],
        "patient_id_hash": hash_identifier(_patient_ids[1]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "case_manager_initiated", "payer": "UnitedHealthcare Medicare"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=1)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[1],
        "patient_id_hash": hash_identifier(_patient_ids[1]),
        "action": "prior_auth_submitted",
        "agent": "prior_auth_agent",
        "details": {"tracking_number": "AVL-2026-40235", "method": "X12_278"},
        "model_version": "granite-4-h-small-v1.2",
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=18)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[2],
        "patient_id_hash": hash_identifier(_patient_ids[2]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "physician_discharge_order", "payer": "Anthem Blue Cross Medicare"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=3)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[2],
        "patient_id_hash": hash_identifier(_patient_ids[2]),
        "action": "prior_auth_submitted",
        "agent": "prior_auth_agent",
        "details": {"tracking_number": "AVL-2026-40347", "method": "FHIR_PAS"},
        "model_version": "granite-4-h-small-v1.2",
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=2)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[2],
        "patient_id_hash": hash_identifier(_patient_ids[2]),
        "action": "prior_auth_denied",
        "agent": "prior_auth_agent",
        "details": {"denial_reason": "Medical necessity not established", "tracking_number": "AVL-2026-40347"},
        "model_version": None,
        "status": "failure",
        "user_id": "system_agent",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=6)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[2],
        "patient_id_hash": hash_identifier(_patient_ids[2]),
        "action": "appeal_draft_generated",
        "agent": "prior_auth_agent",
        "details": {"model_used": "granite-4-h-small"},
        "model_version": "granite-4-h-small-v1.2",
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=5)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[3],
        "patient_id_hash": hash_identifier(_patient_ids[3]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "physician_discharge_order", "payer": "Humana Gold Plus"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=4)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[3],
        "patient_id_hash": hash_identifier(_patient_ids[3]),
        "action": "prior_auth_approved",
        "agent": "prior_auth_agent",
        "details": {"tracking_number": "AVL-2026-40456", "approved_days": 21},
        "model_version": None,
        "status": "success",
        "user_id": "system_agent",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=1)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[3],
        "patient_id_hash": hash_identifier(_patient_ids[3]),
        "action": "facility_search_initiated",
        "agent": "placement_agent",
        "details": {"facilities_found": 3, "referrals_sent": 3},
        "model_version": None,
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=20)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[4],
        "patient_id_hash": hash_identifier(_patient_ids[4]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "utilization_review_flag", "payer": "Cigna Medicare Advantage"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=2)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[4],
        "patient_id_hash": hash_identifier(_patient_ids[4]),
        "action": "facility_search_initiated",
        "agent": "placement_agent",
        "details": {"facilities_found": 3, "referrals_sent": 3},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=16)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[6],
        "patient_id_hash": hash_identifier(_patient_ids[6]),
        "action": "placement_confirmed",
        "agent": "placement_agent",
        "details": {"facility": "Maple Grove Skilled Nursing", "referral_id": "CP-401450"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=2)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[7],
        "patient_id_hash": hash_identifier(_patient_ids[7]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "physician_discharge_order", "payer": "UnitedHealthcare Medicare"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=5)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[7],
        "patient_id_hash": hash_identifier(_patient_ids[7]),
        "action": "patient_discharged",
        "agent": "supervisor_agent",
        "details": {"facility": "Lakewood Recovery Center", "transport": "scheduled"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(minutes=30)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[8],
        "patient_id_hash": hash_identifier(_patient_ids[8]),
        "action": "workflow_escalated",
        "agent": "compliance_agent",
        "details": {"reason": "All matched facilities declined referral", "avoidable_days": 4},
        "model_version": None,
        "status": "failure",
        "user_id": "system_agent",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(hours=5)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[5],
        "patient_id_hash": hash_identifier(_patient_ids[5]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "case_manager_initiated", "payer": "WellCare Medicare"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-michael-brown",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=5)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[7],
        "patient_id_hash": hash_identifier(_patient_ids[7]),
        "action": "observation_status_check",
        "agent": "compliance_agent",
        "details": {"encounter_status": "inpatient", "coverage_type": "Medicare Advantage", "alert": False},
        "model_version": None,
        "status": "success",
        "user_id": "system_agent",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=4, hours=12)),
    },
    {
        "id": _uuid(),
        "workflow_id": _wf_ids[9],
        "patient_id_hash": hash_identifier(_patient_ids[9]),
        "action": "discharge_triggered",
        "agent": "supervisor_agent",
        "details": {"trigger": "utilization_review_flag", "payer": "Humana Gold Plus"},
        "model_version": None,
        "status": "success",
        "user_id": "cm-sarah-jones",
        "session_id": _uuid(),
        "created_at": _iso(_now - timedelta(days=2)),
    },
]

# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

ALERTS = [
    {
        "id": _uuid(),
        "level": "URGENT",
        "title": "PA Denied — Appeal Window Closing",
        "message": "PA denied for Dorothy Johnson — appeal window closes in 48hrs. Review and submit appeal.",
        "workflow_id": _wf_ids[2],
        "created_at": _iso(_now - timedelta(hours=6)),
    },
    {
        "id": _uuid(),
        "level": "WARNING",
        "title": "PA Pending >24hrs",
        "message": "PA pending >24hrs for Margaret Chen (Aetna Medicare Advantage). Consider follow-up with payer.",
        "workflow_id": _wf_ids[0],
        "created_at": _iso(_now - timedelta(hours=2)),
    },
    {
        "id": _uuid(),
        "level": "WARNING",
        "title": "Observation Status Flag",
        "message": "Thomas Anderson was flagged for observation status review. Verify inpatient status conversion was completed.",
        "workflow_id": _wf_ids[7],
        "created_at": _iso(_now - timedelta(days=4)),
    },
    {
        "id": _uuid(),
        "level": "URGENT",
        "title": "Escalated — All Facilities Declined",
        "message": "Barbara Martinez: all 3 matched facilities declined referral. Manual placement coordination required. Avoidable days: 4.",
        "workflow_id": _wf_ids[8],
        "created_at": _iso(_now - timedelta(hours=5)),
    },
    {
        "id": _uuid(),
        "level": "INFO",
        "title": "Placement Confirmed",
        "message": "Patricia Davis confirmed at Maple Grove Skilled Nursing. Transport scheduling in progress.",
        "workflow_id": _wf_ids[6],
        "created_at": _iso(_now - timedelta(hours=2)),
    },
    {
        "id": _uuid(),
        "level": "SUCCESS",
        "title": "Discharge Complete",
        "message": "Thomas Anderson successfully discharged to Lakewood Recovery Center. Workflow complete.",
        "workflow_id": _wf_ids[7],
        "created_at": _iso(_now - timedelta(minutes=30)),
    },
]


# ---------------------------------------------------------------------------
# Query Functions
# ---------------------------------------------------------------------------


def get_all_patients() -> list:
    """Return all patients with decrypted display fields."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "mrn": p["mrn"],
            "dob": p["dob"],
            "coverage_payer_id": p["coverage_payer_id"],
            "coverage_payer_name": p["coverage_payer_name"],
            "created_at": p["created_at"],
            "updated_at": p["updated_at"],
        }
        for p in PATIENTS
    ]


def get_patient(patient_id: str) -> Optional[dict]:
    """Return a single patient by ID."""
    for p in PATIENTS:
        if p["id"] == patient_id:
            return {
                "id": p["id"],
                "name": p["name"],
                "mrn": p["mrn"],
                "dob": p["dob"],
                "coverage_payer_id": p["coverage_payer_id"],
                "coverage_payer_name": p["coverage_payer_name"],
                "created_at": p["created_at"],
                "updated_at": p["updated_at"],
            }
    return None


def _get_prior_auth_for_workflow(workflow_id: str) -> Optional[dict]:
    """Get the prior auth record for a workflow, if any."""
    for pa in PRIOR_AUTH_RECORDS:
        if pa["workflow_id"] == workflow_id:
            return pa
    return None


def _get_facility_matches_for_workflow(workflow_id: str) -> list:
    """Get all facility matches for a workflow."""
    return [fm for fm in FACILITY_MATCHES if fm["workflow_id"] == workflow_id]


def _get_audit_trail_for_workflow(workflow_id: str) -> list:
    """Get all audit entries for a workflow, sorted by time."""
    entries = [ae for ae in AUDIT_ENTRIES if ae["workflow_id"] == workflow_id]
    return sorted(entries, key=lambda e: e["created_at"], reverse=True)


def _enrich_workflow(wf: dict) -> dict:
    """Add nested prior_auth, facility_matches, and audit_trail to a workflow."""
    enriched = dict(wf)
    enriched["prior_auth"] = _get_prior_auth_for_workflow(wf["id"])
    enriched["facility_matches"] = _get_facility_matches_for_workflow(wf["id"])
    enriched["audit_trail"] = _get_audit_trail_for_workflow(wf["id"])
    return enriched


def get_all_workflows(status_filter: Optional[str] = None) -> list:
    """Return all workflows, optionally filtered by status."""
    results = []
    for wf in WORKFLOWS:
        if status_filter and wf["status"] != status_filter:
            continue
        results.append(_enrich_workflow(wf))
    return results


def get_workflow(workflow_id: str) -> Optional[dict]:
    """Return a single enriched workflow by ID."""
    for wf in WORKFLOWS:
        if wf["id"] == workflow_id:
            return _enrich_workflow(wf)
    return None


def get_patient_workflows(patient_id: str) -> list:
    """Return all workflows for a specific patient."""
    return [
        _enrich_workflow(wf)
        for wf in WORKFLOWS
        if wf["patient_id"] == patient_id
    ]


def get_dashboard_summary() -> dict:
    """Return dashboard summary metrics."""
    auth_pending = sum(1 for wf in WORKFLOWS if wf["status"] == "AUTH_PENDING")
    placed_today = sum(
        1 for wf in WORKFLOWS
        if wf["status"] in ("PLACEMENT_CONFIRMED", "DISCHARGED")
        and wf["updated_at"] >= _iso(_now - timedelta(days=1))
    )
    avoidable = [wf["avoidable_days"] for wf in WORKFLOWS if wf["avoidable_days"] > 0]
    avg_delay = round(sum(avoidable) / len(avoidable), 1) if avoidable else 0.0

    return {
        "auth_pending_count": auth_pending,
        "placed_today_count": placed_today,
        "avg_delay_days": avg_delay,
        "auth_pending_delta": -1,  # compared to yesterday
        "placed_delta": 2,
        "delay_delta": -0.3,
    }


def get_alerts() -> list:
    """Return all active alerts sorted by created_at desc."""
    return sorted(ALERTS, key=lambda a: a["created_at"], reverse=True)


def update_workflow_status(workflow_id: str, status: str) -> Optional[dict]:
    """Update a workflow's status."""
    for wf in WORKFLOWS:
        if wf["id"] == workflow_id:
            wf["status"] = status
            wf["updated_at"] = _iso(datetime.utcnow())
            # Add audit entry with hashed patient ID
            AUDIT_ENTRIES.append({
                "id": _uuid(),
                "workflow_id": workflow_id,
                "patient_id_hash": hash_identifier(wf["patient_id"]),
                "action": f"status_updated_to_{status}",
                "agent": "api",
                "details": {"new_status": status},
                "model_version": None,
                "status": "success",
                "user_id": "api_user",
                "session_id": _uuid(),
                "created_at": _iso(datetime.utcnow()),
            })
            return _enrich_workflow(wf)
    return None


def create_workflow(patient_id: str, trigger_event: str) -> Optional[dict]:
    """Create a new workflow for a patient."""
    patient = get_patient(patient_id)
    if not patient:
        return None

    new_wf = {
        "id": _uuid(),
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "patient_mrn": patient["mrn"],
        "payer_name": patient.get("coverage_payer_name", "Unknown"),
        "status": "INITIATED",
        "trigger_event": trigger_event,
        "prior_auth_id": None,
        "selected_facility_id": None,
        "avoidable_days": 0,
        "created_at": _iso(datetime.utcnow()),
        "updated_at": _iso(datetime.utcnow()),
    }
    WORKFLOWS.append(new_wf)

    # Audit entry with hashed patient ID
    AUDIT_ENTRIES.append({
        "id": _uuid(),
        "workflow_id": new_wf["id"],
        "patient_id_hash": hash_identifier(patient_id),
        "action": "workflow_created",
        "agent": "supervisor_agent",
        "details": {"trigger": trigger_event, "payer": patient.get("coverage_payer_name")},
        "model_version": None,
        "status": "success",
        "user_id": "api_user",
        "session_id": _uuid(),
        "created_at": _iso(datetime.utcnow()),
    })

    return _enrich_workflow(new_wf)
