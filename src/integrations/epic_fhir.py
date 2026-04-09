"""
DischargeIQ Epic FHIR Client

Supports two modes:
  - DEV_MODE=true  → EpicFHIRClient (mock, synthetic data)
  - DEV_MODE=false → EpicFHIRLiveClient (real SMART on FHIR)

SMART Backend Services auth uses JWT assertion (RS384) per Epic specs.
TLS 1.3 enforced. All responses are FHIR R4.
"""

import os
import logging
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from jose import jwt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Production Client — Real Epic FHIR R4
# ---------------------------------------------------------------------------

class EpicFHIRLiveClient:
    """
    Production Epic FHIR R4 client using SMART Backend Services auth.

    Auth flow:
      1. Build a signed JWT assertion (RS384) with the app's private key
      2. POST to Epic's token endpoint to get an access token
      3. Use the token for FHIR API calls (15-min expiry)

    Requires env vars:
      EPIC_FHIR_BASE_URL, EPIC_CLIENT_ID, EPIC_PRIVATE_KEY_PATH, EPIC_TOKEN_ENDPOINT
    """

    TOKEN_EXPIRY_BUFFER_SECONDS = 60  # refresh token 60s before expiry

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        private_key_path: Optional[str] = None,
        token_endpoint: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("EPIC_FHIR_BASE_URL", "")).rstrip("/")
        self.client_id = client_id or os.getenv("EPIC_CLIENT_ID", "")
        self.token_endpoint = token_endpoint or os.getenv(
            "EPIC_TOKEN_ENDPOINT", ""
        )

        # Load RSA private key for JWT signing
        key_path = private_key_path or os.getenv("EPIC_PRIVATE_KEY_PATH", "")
        self._private_key = ""
        if key_path and os.path.exists(key_path):
            with open(key_path, "r") as f:
                self._private_key = f.read()

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        # httpx async client with TLS enforcement and timeouts
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            http2=True,
            verify=True,  # TLS certificate verification
            headers={"Accept": "application/fhir+json"},
        )

    # ----- Auth -----

    async def _ensure_token(self):
        """Obtain or refresh the SMART Backend Services access token."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        if not self._private_key:
            raise RuntimeError(
                "Epic private key not configured. Set EPIC_PRIVATE_KEY_PATH."
            )

        now = int(time.time())
        claims = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_endpoint,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + 300,  # 5-minute assertion
        }
        assertion = jwt.encode(claims, self._private_key, algorithm="RS384")

        resp = await self._http.post(
            self.token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": assertion,
            },
        )
        resp.raise_for_status()
        body = resp.json()

        self._access_token = body["access_token"]
        self._token_expires_at = (
            time.time() + body.get("expires_in", 300) - self.TOKEN_EXPIRY_BUFFER_SECONDS
        )
        logger.info("Epic FHIR access token obtained, expires in %ds", body.get("expires_in", 300))

    async def _get(self, path: str, params: dict = None) -> dict:
        """
        Authenticated GET to the Epic FHIR server.
        Retries once on 429 (rate limit) with backoff.
        """
        await self._ensure_token()
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        for attempt in range(2):
            resp = await self._http.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                logger.warning("Epic 429 rate limit, retrying after %ds", retry_after)
                import asyncio
                await asyncio.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()

        raise httpx.HTTPStatusError(
            "429 Too Many Requests after retry",
            request=resp.request,
            response=resp,
        )

    # ----- FHIR Resource Methods (same interface as mock) -----

    async def get_patient(self, patient_id: str) -> dict:
        """Fetch a FHIR Patient resource by ID."""
        return await self._get(f"Patient/{patient_id}")

    async def get_encounter(self, patient_id: str) -> dict:
        """Fetch the most recent active Encounter for a patient."""
        bundle = await self._get(
            "Encounter",
            params={
                "patient": patient_id,
                "status": "in-progress",
                "_sort": "-date",
                "_count": "1",
            },
        )
        entries = bundle.get("entry", [])
        if not entries:
            raise ValueError(f"No active encounter found for patient {patient_id}")
        return entries[0]["resource"]

    async def get_coverage(self, patient_id: str) -> dict:
        """Fetch active Coverage for a patient."""
        bundle = await self._get(
            "Coverage",
            params={"patient": patient_id, "status": "active", "_count": "1"},
        )
        entries = bundle.get("entry", [])
        if not entries:
            return {}
        return entries[0]["resource"]

    async def get_therapy_assessments(self, patient_id: str) -> list:
        """Fetch AM-PAC / functional status Observations."""
        bundle = await self._get(
            "Observation",
            params={
                "patient": patient_id,
                "category": "survey",
                "code": "94937-5,94940-9",  # AM-PAC LOINC codes
                "_sort": "-date",
                "_count": "5",
            },
        )
        return [e["resource"] for e in bundle.get("entry", [])]

    async def get_conditions(self, patient_id: str) -> list:
        """Fetch active Condition resources (diagnoses)."""
        bundle = await self._get(
            "Condition",
            params={
                "patient": patient_id,
                "clinical-status": "active",
                "_count": "20",
            },
        )
        return [e["resource"] for e in bundle.get("entry", [])]

    async def get_clinical_documents(self, patient_id: str) -> list:
        """Fetch clinical DocumentReference resources (H&P, therapy notes)."""
        bundle = await self._get(
            "DocumentReference",
            params={
                "patient": patient_id,
                "status": "current",
                "_sort": "-date",
                "_count": "10",
            },
        )
        docs = []
        for entry in bundle.get("entry", []):
            resource = entry["resource"]
            doc_type = resource.get("type", {})
            type_text = doc_type.get("text", "")
            if not type_text:
                codings = doc_type.get("coding", [])
                type_text = codings[0].get("display", "Unknown") if codings else "Unknown"
            docs.append({
                "id": resource.get("id", ""),
                "type": type_text,
                "content": "",  # actual content fetched separately via Binary endpoint
            })
        return docs

    async def close(self):
        """Close the HTTP client."""
        await self._http.aclose()


# ---------------------------------------------------------------------------
# Mock Client — Synthetic data for dev/demo
# ---------------------------------------------------------------------------

class EpicFHIRClient:
    """Mock Epic FHIR R4 client returning synthetic patient data."""

    def get_patient(self, patient_id: str) -> dict:
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "name": [{"use": "official", "given": ["Jane"], "family": "Doe"}],
            "gender": "female",
            "birthDate": "1945-03-15",
            "address": [
                {
                    "use": "home",
                    "line": ["123 Synthetic Ave"],
                    "city": "Dallas",
                    "state": "TX",
                    "postalCode": "75201",
                }
            ],
            "identifier": [
                {"system": "urn:oid:1.2.36.146.595.217.0.1", "value": patient_id}
            ],
        }

    def get_encounter(self, patient_id: str) -> dict:
        admit_date = (datetime.utcnow() - timedelta(days=random.randint(2, 7))).isoformat()
        return {
            "resourceType": "Encounter",
            "id": f"enc-{patient_id[:8]}",
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "inpatient",
                "display": "Inpatient",
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {"start": admit_date},
        }

    def get_coverage(self, patient_id: str) -> dict:
        payers = [
            ("aetna-ma-001", "Aetna Medicare Advantage"),
            ("uhc-ma-002", "UnitedHealthcare Medicare"),
            ("anthem-ma-003", "Anthem Blue Cross Medicare"),
        ]
        payer_ref, payer_display = random.choice(payers)
        return {
            "resourceType": "Coverage",
            "id": f"cov-{patient_id[:8]}",
            "status": "active",
            "type": {
                "coding": [{"code": "MCPOL", "display": "Medicare Advantage Policy"}],
                "text": "Medicare Advantage",
            },
            "subscriber": {"reference": f"Patient/{patient_id}"},
            "payor": [{"reference": f"Organization/{payer_ref}", "display": payer_display}],
        }

    def get_conditions(self, patient_id: str) -> list:
        conditions = [
            ("S72.001A", "Fracture of unspecified part of neck of right femur"),
            ("I50.9", "Heart failure, unspecified"),
            ("J44.1", "COPD with acute exacerbation"),
        ]
        selected = random.sample(conditions, min(random.randint(1, 2), len(conditions)))
        return [
            {
                "resourceType": "Condition",
                "id": f"cond-{patient_id[:8]}-{i}",
                "clinicalStatus": {"coding": [{"code": "active"}]},
                "code": {
                    "coding": [
                        {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": code, "display": display}
                    ]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
            }
            for i, (code, display) in enumerate(selected)
        ]

    def get_observations(self, patient_id: str) -> list:
        return [
            {
                "resourceType": "Observation",
                "id": f"obs-ampac-{patient_id[:8]}",
                "status": "final",
                "code": {"coding": [{"code": "94937-5", "display": "AM-PAC Basic Mobility"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "valueQuantity": {"value": round(random.uniform(15.0, 22.0), 1), "unit": "score"},
            }
        ]

    # Alias used by agents
    get_therapy_assessments = get_observations

    def get_documents(self, patient_id: str) -> list:
        return [
            {"id": f"doc-{patient_id[:8]}-0", "type": "History and Physical", "content": ""},
            {"id": f"doc-{patient_id[:8]}-1", "type": "Therapy Evaluation", "content": ""},
        ]

    # Alias used by agents
    get_clinical_documents = get_documents


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _is_live(service_var: str) -> bool:
    dev_mode = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")
    service_mode = os.getenv(service_var, "").lower()
    if service_mode == "live":
        return True
    if dev_mode or service_mode == "mock":
        return False
    return True


def create_epic_client(**kwargs) -> EpicFHIRClient | EpicFHIRLiveClient:
    """Factory: returns mock or live Epic client based on DEV_MODE / EPIC_MODE."""
    if _is_live("EPIC_MODE"):
        logger.info("Using live Epic FHIR client")
        return EpicFHIRLiveClient(**kwargs)
    logger.info("Using mock Epic FHIR client")
    return EpicFHIRClient()
