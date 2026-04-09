#!/usr/bin/env python3
"""
Synthetic Patient Data Generator for DischargeIQ
All patient data is synthetic. No real PHI.
"""
import json
import random
from datetime import datetime, timedelta
import uuid

random.seed(42)

# Lists for generation
FIRST_NAMES = ["Margaret", "Robert", "Dorothy", "James", "Helen", "William", "Patricia", "Thomas", "Barbara", "Richard", "Elizabeth", "Charles", "Susan", "Joseph", "Nancy", "George", "Karen", "Edward"]
LAST_NAMES = ["Chen", "Williams", "Johnson", "Patterson", "Garcia", "Thompson", "Davis", "Anderson", "Martinez", "Lee", "Wilson", "Brown", "Taylor", "Moore", "Jackson", "White"]
PAYERS = ["Aetna Medicare Advantage", "UnitedHealthcare Medicare", "Anthem Blue Cross Medicare", "Humana Gold Plus", "Cigna Medicare Advantage", "WellCare Medicare"]
DIAGNOSES = [
    {"code": "S72.001A", "display": "Fracture of unspecified intracapsular section of right femur"},
    {"code": "I63.9", "display": "Cerebral infarction, unspecified"},
    {"code": "M17.11", "display": "Primary osteoarthritis, right knee"},
    {"code": "S32.001A", "display": "Wedge compression fracture of unspecified lumbar vertebra"},
    {"code": "I50.9", "display": "Heart failure, unspecified"},
    {"code": "J18.9", "display": "Pneumonia, unspecified organism"},
    {"code": "S42.001A", "display": "Fracture of unspecified part of right clavicle"},
    {"code": "M48.06", "display": "Spinal stenosis, lumbar region"}
]
ENCOUNTER_TYPES = ["inpatient", "inpatient", "inpatient", "observation"]  # weighted toward inpatient

def generate_patient():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    age = random.randint(65, 90)
    dob = datetime(2026, 4, 9) - timedelta(days=age * 365 + random.randint(0, 364))
    diagnosis = random.choice(DIAGNOSES)
    return {
        "id": str(uuid.uuid4()),
        "name": f"{first} {last}",
        "first_name": first,
        "last_name": last,
        "mrn": f"{random.randint(10000000, 99999999)}",
        "dob": dob.strftime("%Y-%m-%d"),
        "age": age,
        "gender": random.choice(["female", "male"]),
        "payer": random.choice(PAYERS),
        "diagnosis": diagnosis,
        "ampac_score": round(random.uniform(6, 24), 1),
        "encounter_type": random.choice(ENCOUNTER_TYPES),
        "length_of_stay_days": random.randint(2, 14),
        "admission_date": (datetime(2026, 4, 9) - timedelta(days=random.randint(2, 14))).strftime("%Y-%m-%d"),
    }

def main():
    patients = [generate_patient() for _ in range(18)]
    print(json.dumps(patients, indent=2))

if __name__ == "__main__":
    main()
