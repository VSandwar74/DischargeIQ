"""
Synthetic test fixtures for DischargeIQ.
ALL data is fabricated. No real PHI.
"""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Synthetic Patients
# ---------------------------------------------------------------------------

SYNTHETIC_PATIENTS = [
    {
        "id": "synth-patient-001",
        "fhir_id": "eJzKv9QdRx2",
        "name": "Alice Testworth",
        "mrn": "T0000001",
        "dob": "1942-05-14",
        "gender": "female",
        "address": "100 Synthetic Ave, Faketown, OH 45000",
        "phone": "555-000-0001",
    },
    {
        "id": "synth-patient-002",
        "fhir_id": "eJzKv9QdRx3",
        "name": "Bob Mockson",
        "mrn": "T0000002",
        "dob": "1938-11-22",
        "gender": "male",
        "address": "200 Fabricated Blvd, Testville, NY 10000",
        "phone": "555-000-0002",
    },
    {
        "id": "synth-patient-003",
        "fhir_id": "eJzKv9QdRx4",
        "name": "Carol Demofield",
        "mrn": "T0000003",
        "dob": "1955-03-08",
        "gender": "female",
        "address": "300 Placeholder St, Mocksburg, FL 33000",
        "phone": "555-000-0003",
    },
]


# ---------------------------------------------------------------------------
# Encounters
# ---------------------------------------------------------------------------

def make_encounter(patient_id: str, status: str = "in-progress",
                   admit_days_ago: int = 3,
                   class_code: str = "IMP"):  # IMP = inpatient, OBSENC = observation
    return {
        "resourceType": "Encounter",
        "id": f"enc-{uuid.uuid4().hex[:8]}",
        "status": status,
        "class": {"code": class_code, "display": "inpatient" if class_code == "IMP" else "observation"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": (datetime.utcnow() - timedelta(days=admit_days_ago)).isoformat() + "Z",
        },
        "diagnosis": [
            {
                "condition": {"reference": "Condition/synth-cond-001"},
                "use": {"coding": [{"code": "AD", "display": "Admission diagnosis"}]},
            }
        ],
    }


ENCOUNTER_INPATIENT = make_encounter("synth-patient-001", class_code="IMP", admit_days_ago=3)
ENCOUNTER_OBSERVATION = make_encounter("synth-patient-002", class_code="OBSENC", admit_days_ago=2)
ENCOUNTER_LONG_STAY = make_encounter("synth-patient-003", class_code="IMP", admit_days_ago=12)


# ---------------------------------------------------------------------------
# Coverage / Insurance
# ---------------------------------------------------------------------------

COVERAGE_AETNA_MA = {
    "resourceType": "Coverage",
    "id": "cov-synth-001",
    "status": "active",
    "type": {"coding": [{"code": "MA", "display": "Medicare Advantage"}]},
    "subscriber": {"reference": "Patient/synth-patient-001"},
    "payor": [{"display": "Aetna Medicare", "identifier": {"value": "AETNA_MA"}}],
    "class": [{"type": {"coding": [{"code": "plan"}]}, "value": "HMO-Gold"}],
}

COVERAGE_UNITED_MA = {
    "resourceType": "Coverage",
    "id": "cov-synth-002",
    "status": "active",
    "type": {"coding": [{"code": "MA", "display": "Medicare Advantage"}]},
    "subscriber": {"reference": "Patient/synth-patient-002"},
    "payor": [{"display": "UnitedHealthcare Medicare", "identifier": {"value": "UHC_MA"}}],
    "class": [{"type": {"coding": [{"code": "plan"}]}, "value": "PPO-Standard"}],
}

COVERAGE_TRADITIONAL_MEDICARE = {
    "resourceType": "Coverage",
    "id": "cov-synth-003",
    "status": "active",
    "type": {"coding": [{"code": "MC", "display": "Medicare"}]},
    "subscriber": {"reference": "Patient/synth-patient-003"},
    "payor": [{"display": "Medicare FFS", "identifier": {"value": "MEDICARE_FFS"}}],
}

COVERAGE_CARESOURCE_MEDICAID = {
    "resourceType": "Coverage",
    "id": "cov-synth-004",
    "status": "active",
    "type": {"coding": [{"code": "MD", "display": "Medicaid"}]},
    "subscriber": {"reference": "Patient/synth-patient-001"},
    "payor": [{"display": "CareSource", "identifier": {"value": "CARESOURCE_MD"}}],
}


# ---------------------------------------------------------------------------
# Therapy Assessments (AMPAC scores)
# ---------------------------------------------------------------------------

AMPAC_SCORE_LOW = {
    "resourceType": "Observation",
    "id": "obs-ampac-001",
    "status": "final",
    "category": [{"coding": [{"code": "functional-status"}]}],
    "code": {"coding": [{"code": "AMPAC", "display": "AM-PAC Basic Mobility"}]},
    "subject": {"reference": "Patient/synth-patient-001"},
    "valueQuantity": {"value": 14, "unit": "score"},  # Below 17 — qualifies
}

AMPAC_SCORE_BORDERLINE = {
    "resourceType": "Observation",
    "id": "obs-ampac-002",
    "status": "final",
    "category": [{"coding": [{"code": "functional-status"}]}],
    "code": {"coding": [{"code": "AMPAC", "display": "AM-PAC Basic Mobility"}]},
    "subject": {"reference": "Patient/synth-patient-002"},
    "valueQuantity": {"value": 18, "unit": "score"},  # Above 17 — borderline
}

AMPAC_SCORE_HIGH = {
    "resourceType": "Observation",
    "id": "obs-ampac-003",
    "status": "final",
    "category": [{"coding": [{"code": "functional-status"}]}],
    "code": {"coding": [{"code": "AMPAC", "display": "AM-PAC Basic Mobility"}]},
    "subject": {"reference": "Patient/synth-patient-003"},
    "valueQuantity": {"value": 23, "unit": "score"},  # Well above — likely home discharge
}


# ---------------------------------------------------------------------------
# Conditions (Diagnoses)
# ---------------------------------------------------------------------------

CONDITION_HIP_FRACTURE = {
    "resourceType": "Condition",
    "id": "synth-cond-001",
    "clinicalStatus": {"coding": [{"code": "active"}]},
    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "S72.001A", "display": "Fracture of unspecified intracapsular section of right femur, initial"}]},
    "subject": {"reference": "Patient/synth-patient-001"},
}

CONDITION_KNEE_REPLACEMENT = {
    "resourceType": "Condition",
    "id": "synth-cond-002",
    "clinicalStatus": {"coding": [{"code": "active"}]},
    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "Z96.651", "display": "Presence of right artificial knee joint"}]},
    "subject": {"reference": "Patient/synth-patient-002"},
}


# ---------------------------------------------------------------------------
# SNF Facilities
# ---------------------------------------------------------------------------

SYNTHETIC_FACILITIES = [
    {
        "id": "fac-001",
        "name": "Maple Grove Skilled Nursing",
        "npi": "1234567890",
        "beds_available": 3,
        "accepted_payers": ["AETNA_MA", "UHC_MA", "MEDICARE_FFS"],
        "accepts_behavioral": False,
        "distance_miles": 4.2,
        "care_capabilities": ["PT", "OT", "wound_care"],
    },
    {
        "id": "fac-002",
        "name": "Sunrise Rehabilitation Center",
        "npi": "0987654321",
        "beds_available": 0,  # No beds
        "accepted_payers": ["AETNA_MA", "UHC_MA", "CARESOURCE_MD"],
        "accepts_behavioral": True,
        "distance_miles": 8.7,
        "care_capabilities": ["PT", "OT", "IV_antibiotics", "behavioral"],
    },
    {
        "id": "fac-003",
        "name": "Oakwood Transitional Care",
        "npi": "1122334455",
        "beds_available": 1,
        "accepted_payers": ["UHC_MA"],  # Limited payer acceptance
        "accepts_behavioral": False,
        "distance_miles": 12.1,
        "care_capabilities": ["PT"],
    },
]


# ---------------------------------------------------------------------------
# Prior Auth Responses (mock Availity)
# ---------------------------------------------------------------------------

PA_RESPONSE_APPROVED = {
    "tracking_number": "AET-2026-SYNTH-001",
    "status": "APPROVED",
    "payer": "AETNA_MA",
    "decision_date": datetime.utcnow().isoformat() + "Z",
    "valid_through": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
    "approved_days": 20,
    "denial_reason": None,
}

PA_RESPONSE_DENIED = {
    "tracking_number": "AET-2026-SYNTH-002",
    "status": "DENIED",
    "payer": "AETNA_MA",
    "decision_date": datetime.utcnow().isoformat() + "Z",
    "denial_reason": "Medical necessity criteria not met. AMPAC score 18 does not meet threshold for SNF placement.",
    "appeal_deadline": (datetime.utcnow() + timedelta(days=60)).isoformat() + "Z",
}

PA_RESPONSE_PENDING = {
    "tracking_number": "UHC-2026-SYNTH-003",
    "status": "PENDING",
    "payer": "UHC_MA",
    "submitted_at": datetime.utcnow().isoformat() + "Z",
    "estimated_response_hours": 72,
    "denial_reason": None,
}


# ---------------------------------------------------------------------------
# CarePort Referral Responses
# ---------------------------------------------------------------------------

REFERRAL_ACCEPTED = {
    "referral_id": "ref-synth-001",
    "facility_id": "fac-001",
    "status": "ACCEPTED",
    "bed_assigned": "Room 204B",
    "response_time_minutes": 12,
}

REFERRAL_DECLINED_INSURANCE = {
    "referral_id": "ref-synth-002",
    "facility_id": "fac-003",
    "status": "DECLINED",
    "decline_reason": "insurance_not_accepted",
    "response_time_minutes": 8,
}

REFERRAL_DECLINED_BEHAVIORAL = {
    "referral_id": "ref-synth-003",
    "facility_id": "fac-001",
    "status": "DECLINED",
    "decline_reason": "behavioral_capacity_full",
    "response_time_minutes": 22,
}

REFERRAL_DECLINED_NO_BEDS = {
    "referral_id": "ref-synth-004",
    "facility_id": "fac-002",
    "status": "DECLINED",
    "decline_reason": "no_beds_available",
    "response_time_minutes": 5,
}
