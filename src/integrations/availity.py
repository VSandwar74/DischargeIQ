"""
DischargeIQ Availity Client

Supports two modes:
  - DEV_MODE=true  → AvailityClient (mock, synthetic data)
  - DEV_MODE=false → AvailityLiveClient (real Availity OAuth + APIs)

Strategy pattern supports CMS-0057-F transition: X12 278 (legacy) → FHIR PAS (Da Vinci).
Submission method is configurable per-payer or globally.
"""

import os
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Production Client — Real Availity APIs
# ---------------------------------------------------------------------------

class AvailityLiveClient:
    """
    Production Availity client with OAuth 2.0 auth and dual submission support.

    Auth: client_credentials grant → Bearer token.

    Requires env vars:
      AVAILITY_API_BASE, AVAILITY_CLIENT_ID, AVAILITY_CLIENT_SECRET
    """

    TOKEN_EXPIRY_BUFFER = 60

    def __init__(
        self,
        api_base: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        submission_method: str = "X12_278",
    ):
        self.api_base = (api_base or os.getenv("AVAILITY_API_BASE", "")).rstrip("/")
        self.client_id = client_id or os.getenv("AVAILITY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AVAILITY_CLIENT_SECRET", "")
        self.submission_method = submission_method

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            verify=True,
        )

    async def _ensure_token(self):
        """Obtain or refresh OAuth access token."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        resp = await self._http.post(
            f"{self.api_base}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "hipaa",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        self._token_expires_at = (
            time.time() + body.get("expires_in", 3600) - self.TOKEN_EXPIRY_BUFFER
        )
        logger.info("Availity token obtained")

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Authenticated request to Availity API."""
        await self._ensure_token()
        url = f"{self.api_base}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            **kwargs.pop("headers", {}),
        }
        resp = await self._http.request(method, url, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # ----- CRD (Da Vinci Coverage Requirements Discovery) -----

    async def crd_check(self, payer_id: str, service_type: str = "SNF") -> "CRDResponse":
        """
        Check coverage requirements — is PA required for this payer + service?

        Maps to: POST /crd/coverage-requirements
        """
        data = await self._request(
            "POST",
            "crd/coverage-requirements",
            json={
                "payer_id": payer_id,
                "service_type": service_type,
                "context": "discharge_snf",
            },
        )
        return CRDResponse(
            pa_required=data.get("pa_required", True),
            documentation_required=data.get("documentation_required", []),
            response_sla_hours=data.get("response_sla_hours", 168),
        )

    # ----- DTR (Da Vinci Documentation Templates & Rules) -----

    async def dtr_populate(self, payer_id: str, clinical_summary: str, therapy_scores: dict) -> dict:
        """
        Auto-populate PA form from clinical data.

        Maps to: POST /dtr/populate-form
        """
        return await self._request(
            "POST",
            "dtr/populate-form",
            json={
                "payer_id": payer_id,
                "clinical_summary": clinical_summary,
                "therapy_scores": therapy_scores,
            },
        )

    # ----- PA Submission (FHIR PAS) -----

    async def pas_submit(self, form_data: dict) -> dict:
        """
        Submit PA via FHIR PAS (Da Vinci Prior Authorization Support IG).

        Maps to: POST /pas/submit
        """
        return await self._request("POST", "pas/submit", json=form_data)

    # ----- PA Submission (X12 278 legacy EDI) -----

    async def x12_278_submit(self, form_data: dict) -> dict:
        """
        Submit PA via X12 278 transaction.

        Maps to: POST /prior-authorizations
        """
        return await self._request("POST", "prior-authorizations", json=form_data)

    # ----- Unified submit (strategy pattern) -----

    async def submit_pa(self, form_data: dict) -> dict:
        """Submit PA using configured method."""
        if self.submission_method == "FHIR_PAS":
            return await self.pas_submit(form_data)
        return await self.x12_278_submit(form_data)

    # ----- Payer capability check -----

    async def payer_supports_fhir(self, payer_id: str) -> bool:
        """Check if a payer supports FHIR PAS submission."""
        try:
            data = await self._request(
                "GET", f"payers/{payer_id}/capabilities"
            )
            return "FHIR_PAS" in data.get("supported_methods", [])
        except Exception:
            return False

    # ----- Portal access check -----

    async def check_portal_access(self, payer_id: str) -> bool:
        """Check if hospital has portal access for a payer."""
        try:
            data = await self._request("GET", f"payers/{payer_id}/portal-access")
            return data.get("has_access", True)
        except Exception:
            return True  # default: assume access

    # ----- PA Status -----

    async def get_pa_status(self, tracking_number: str) -> dict:
        """
        Check PA request status.

        Maps to: GET /prior-authorizations/{tracking_number}
        """
        return await self._request("GET", f"prior-authorizations/{tracking_number}")

    async def close(self):
        await self._http.aclose()


class CRDResponse:
    """Structured CRD check response."""
    def __init__(self, pa_required: bool, documentation_required: list = None, response_sla_hours: int = 168):
        self.pa_required = pa_required
        self.documentation_required = documentation_required or []
        self.response_sla_hours = response_sla_hours


# ---------------------------------------------------------------------------
# Mock Client — Synthetic data for dev/demo
# ---------------------------------------------------------------------------

class AvailityClient:
    """Mock Availity client with strategy pattern for PA submission."""

    def __init__(self, submission_method: str = "X12_278"):
        if submission_method not in ("X12_278", "FHIR_PAS"):
            raise ValueError(f"Unsupported submission method: {submission_method}")
        self.submission_method = submission_method

    def crd_check(self, payer_id: str, service_type: str = "SNF") -> CRDResponse:
        pa_required = payer_id.lower() in ("aetna", "united", "anthem") or random.random() < 0.5
        return CRDResponse(
            pa_required=pa_required,
            documentation_required=["History & Physical", "AM-PAC", "Therapy Evaluation"] if pa_required else [],
            response_sla_hours=168 if pa_required else 0,
        )

    def dtr_populate(self, payer_id: str, clinical_summary: str, therapy_scores: dict) -> dict:
        return {
            "form_id": str(uuid.uuid4()),
            "payer_id": payer_id,
            "service_type": "SNF",
            "therapy_scores": therapy_scores,
            "populated_at": datetime.utcnow().isoformat(),
        }

    def pas_submit(self, form_data: dict) -> dict:
        tracking = f"AVL-2026-{random.randint(10000, 99999)}"
        return {
            "tracking_number": tracking,
            "status": "SUBMITTED",
            "submission_method": "FHIR_PAS",
            "submitted_at": datetime.utcnow().isoformat(),
        }

    def x12_278_submit(self, form_data: dict) -> dict:
        tracking = f"AVL-2026-{random.randint(10000, 99999)}"
        return {
            "tracking_number": tracking,
            "status": "SUBMITTED",
            "submission_method": "X12_278",
            "submitted_at": datetime.utcnow().isoformat(),
        }

    def submit_pa(self, form_data: dict) -> dict:
        """Unified submit — routes by configured method."""
        if self.submission_method == "FHIR_PAS":
            return self.pas_submit(form_data)
        return self.x12_278_submit(form_data)

    def submit(self, form_data: dict) -> dict:
        return self.submit_pa(form_data)

    def check_status(self, tracking_id: str) -> dict:
        statuses = ["SUBMITTED", "PENDING_REVIEW", "APPROVED", "DENIED"]
        weights = [10, 50, 30, 10]
        status = random.choices(statuses, weights=weights, k=1)[0]
        result = {"tracking_number": tracking_id, "status": status}
        if status == "APPROVED":
            result["approved_days"] = random.randint(14, 30)
        elif status == "DENIED":
            result["denial_reason"] = "Medical necessity not established"
        return result


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


def create_availity_client(**kwargs) -> AvailityClient | AvailityLiveClient:
    """Factory: returns mock or live Availity client based on DEV_MODE / AVAILITY_MODE."""
    if _is_live("AVAILITY_MODE"):
        logger.info("Using live Availity client")
        return AvailityLiveClient(**kwargs)
    logger.info("Using mock Availity client")
    return AvailityClient(**{k: v for k, v in kwargs.items() if k == "submission_method"})
