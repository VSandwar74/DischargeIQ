"""
DischargeIQ CarePort/WellSky Client

Supports two modes:
  - DEV_MODE=true  → CarePortClient (mock, synthetic facilities)
  - DEV_MODE=false → CarePortLiveClient (real CarePort/WellSky API)

Facility search, referral submission, and status tracking for SNF placements.
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
# Production Client — Real CarePort/WellSky API
# ---------------------------------------------------------------------------

class CarePortLiveClient:
    """
    Production CarePort/WellSky client for facility search and referrals.

    Auth: API key in X-API-Key header + hospital ID for context.

    Requires env vars:
      CAREPORT_API_BASE, CAREPORT_API_KEY, CAREPORT_HOSPITAL_ID
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        hospital_id: Optional[str] = None,
    ):
        self.api_base = (api_base or os.getenv("CAREPORT_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("CAREPORT_API_KEY", "")
        self.hospital_id = hospital_id or os.getenv("CAREPORT_HOSPITAL_ID", "")

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            verify=True,
            headers={
                "X-API-Key": self.api_key,
                "X-Hospital-ID": self.hospital_id,
                "Content-Type": "application/json",
            },
        )

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Authenticated request to CarePort API."""
        url = f"{self.api_base}/{path.lstrip('/')}"
        resp = await self._http.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def search_facilities(self, criteria: dict) -> list:
        """
        Search for SNF facilities matching criteria.

        Maps to: POST /facilities/search
        Body includes: service_type, payer_id, location, distance, capabilities.
        """
        data = await self._request(
            "POST",
            "facilities/search",
            json={
                "service_type": criteria.get("service_type", "SNF"),
                "payer_id": criteria.get("payer_id", ""),
                "max_distance_miles": criteria.get("max_distance_miles", 25),
                "care_capabilities": criteria.get("care_capabilities", []),
                "behavioral": criteria.get("behavioral", False),
                "beds_required": True,
            },
        )
        return data.get("facilities", [])

    async def send_referral(self, facility_id: str, packet: dict) -> dict:
        """
        Send a referral packet to a facility.

        Maps to: POST /referrals
        """
        return await self._request(
            "POST",
            "referrals",
            json={
                "facility_id": facility_id,
                "hospital_id": self.hospital_id,
                "patient_data": packet,
            },
        )

    async def check_referral_status(self, referral_id: str) -> dict:
        """
        Check referral status.

        Maps to: GET /referrals/{referral_id}
        """
        return await self._request("GET", f"referrals/{referral_id}")

    async def close(self):
        await self._http.aclose()


# ---------------------------------------------------------------------------
# Mock Client — Synthetic data for dev/demo
# ---------------------------------------------------------------------------

class CarePortClient:
    """Mock CarePort/WellSky client with synthetic facility data."""

    FACILITIES = [
        {
            "id": "fac-001",
            "name": "Maple Grove Skilled Nursing",
            "address": "1200 Maple Ave, Dallas, TX 75201",
            "beds_total": 120,
            "beds_available": 8,
            "specialty": "Orthopedic Rehabilitation",
            "rating": 4.2,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "UnitedHealthcare", "Anthem", "Humana"],
        },
        {
            "id": "fac-002",
            "name": "Sunrise Senior Care",
            "address": "3450 Sunrise Blvd, Dallas, TX 75204",
            "beds_total": 95,
            "beds_available": 3,
            "specialty": "Cardiac Recovery",
            "rating": 4.5,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "UnitedHealthcare", "Cigna", "WellCare"],
        },
        {
            "id": "fac-003",
            "name": "Oak Hill Rehabilitation Center",
            "address": "780 Oak Hill Dr, Plano, TX 75023",
            "beds_total": 150,
            "beds_available": 12,
            "specialty": "General Skilled Nursing",
            "rating": 3.9,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "Anthem", "Humana", "WellCare"],
        },
        {
            "id": "fac-004",
            "name": "Brookdale Health & Rehab",
            "address": "2100 Brookdale Ln, Richardson, TX 75080",
            "beds_total": 110,
            "beds_available": 5,
            "specialty": "Neurological Rehabilitation",
            "rating": 4.1,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["UnitedHealthcare", "Anthem", "Cigna"],
        },
        {
            "id": "fac-005",
            "name": "Silver Lake SNF",
            "address": "550 Silver Lake Rd, Garland, TX 75040",
            "beds_total": 85,
            "beds_available": 0,
            "specialty": "Pulmonary Rehabilitation",
            "rating": 3.7,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "Humana", "WellCare"],
        },
        {
            "id": "fac-006",
            "name": "Heritage Park Nursing Center",
            "address": "4200 Heritage Park Dr, Irving, TX 75061",
            "beds_total": 130,
            "beds_available": 7,
            "specialty": "Wound Care",
            "rating": 4.3,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "UnitedHealthcare", "Anthem", "Cigna", "Humana"],
        },
        {
            "id": "fac-007",
            "name": "Lakewood Recovery Center",
            "address": "900 Lakewood Blvd, Mesquite, TX 75150",
            "beds_total": 100,
            "beds_available": 4,
            "specialty": "Post-Surgical Recovery",
            "rating": 4.0,
            "accepts_medicare_advantage": True,
            "accepted_payers": ["Aetna", "UnitedHealthcare", "WellCare"],
        },
    ]

    def search_facilities(self, criteria: dict) -> list:
        results = []
        payer_filter = criteria.get("payer_name", "").strip()
        for facility in self.FACILITIES:
            match = True
            if payer_filter and not any(payer_filter.lower() in p.lower() for p in facility["accepted_payers"]):
                match = False
            if criteria.get("beds_required", False) and facility["beds_available"] == 0:
                match = False
            if match:
                results.append({
                    **facility,
                    "distance_miles": round(random.uniform(2.0, 25.0), 1),
                })
        return results

    def send_referral(self, facility_id: str, packet: dict) -> dict:
        return {
            "referral_id": f"CP-{random.randint(100000, 999999)}",
            "facility_id": facility_id,
            "status": "SENT",
            "submitted_at": datetime.utcnow().isoformat(),
            "estimated_response_hours": random.randint(2, 24),
        }

    def check_referral_status(self, referral_id: str) -> str:
        return random.choices(["SENT", "ACCEPTED", "DECLINED", "NO_RESPONSE"], weights=[20, 50, 15, 15], k=1)[0]


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


def create_careport_client(**kwargs) -> CarePortClient | CarePortLiveClient:
    """Factory: returns mock or live CarePort client based on DEV_MODE / CAREPORT_MODE."""
    if _is_live("CAREPORT_MODE"):
        logger.info("Using live CarePort client")
        return CarePortLiveClient(**kwargs)
    logger.info("Using mock CarePort client")
    return CarePortClient()
