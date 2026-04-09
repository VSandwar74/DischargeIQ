"""
DischargeIQ Placement Agent

Finds, ranks, and sends referrals to skilled nursing facilities.
Integrates with CarePort/WellSky for facility search and referral management.

HIPAA: Patient identifiers are hashed before audit logging. Raw PHI is never logged.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from src.security.hashing import hash_identifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utility classes
# ---------------------------------------------------------------------------

class DotDict(dict):
    """Dict that allows attribute access."""
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class PlacementAgent:
    """Agent responsible for SNF facility matching and referral workflows."""

    DEFAULT_MAX_DISTANCE_MILES = 25

    def __init__(self, careport=None, governance=None):
        """
        Initialize the Placement Agent with injected dependencies.

        Args:
            careport: CarePort/WellSky client for facility search and referrals.
            governance: watsonx.governance client for audit logging.
        """
        if careport is None:
            from src.integrations.careport import CarePortClient
            careport = CarePortClient()

        self.careport = careport
        self.governance = governance
        self.last_search_status = None

    # ------------------------------------------------------------------
    # Facility Search and Filtering
    # ------------------------------------------------------------------

    async def find_matches(self, patient_data: dict) -> list:
        """
        Find matching SNF facilities for a patient.

        Searches via CarePort, then filters by bed availability, insurance
        acceptance, behavioral capability, care capabilities, and distance.
        Results are sorted by distance ascending.

        Args:
            patient_data: Patient clinical and coverage information.

        Returns:
            List of facility match dicts, sorted by distance ascending.
        """
        patient_id = patient_data.get("id", patient_data.get("patient_id", ""))
        if patient_id:
            patient_id_hash = hash_identifier(patient_id)
            logger.info("Searching facilities for patient_hash=%s", patient_id_hash)

        # Build search criteria — extract payer_id from various shapes
        payer_id = patient_data.get("payer_id", "")
        if not payer_id:
            payer_id = patient_data.get("insurance", {}).get("payer_id", "")
        # Extract from FHIR Coverage resource if present
        coverage = patient_data.get("coverage", {})
        if not payer_id and isinstance(coverage, dict):
            payors = coverage.get("payor", [])
            if payors and isinstance(payors, list):
                identifier = payors[0].get("identifier", {})
                if isinstance(identifier, dict):
                    payer_id = identifier.get("value", "")
                if not payer_id:
                    payer_id = payors[0].get("display", "")

        criteria = {
            "service_type": "SNF",
            "payer_id": payer_id,
        }

        # Behavioral flags
        behavioral_flags = patient_data.get("behavioral_flags", [])
        if behavioral_flags:
            criteria["behavioral"] = True

        # Care capabilities needed
        care_needs = patient_data.get("care_needs", patient_data.get("care_capabilities", []))
        if care_needs:
            criteria["care_capabilities"] = care_needs

        # Distance preference — check nested family_preferences too
        family_prefs = patient_data.get("family_preferences", {})
        max_distance = patient_data.get(
            "max_distance_miles",
            family_prefs.get("max_distance_miles", self.DEFAULT_MAX_DISTANCE_MILES)
        )
        criteria["max_distance_miles"] = max_distance

        # Search via CarePort
        try:
            raw_results = await self.careport.search_facilities(criteria)
        except Exception as e:
            logger.error("CarePort facility search failed: %s", type(e).__name__)
            self.last_search_status = "NO_MATCHES_FOUND"
            return []

        if not raw_results:
            self.last_search_status = "NO_MATCHES_FOUND"
            return []

        # Filter results
        filtered = []
        for facility in raw_results:
            # Normalize facility to dict
            if not isinstance(facility, dict):
                facility = vars(facility) if hasattr(facility, "__dict__") else {"name": str(facility)}

            # Filter: beds available > 0
            beds = facility.get("beds_available", facility.get("bed_available", 0))
            if isinstance(beds, bool):
                if not beds:
                    continue
            elif isinstance(beds, (int, float)):
                if beds <= 0:
                    continue

            # Filter: accepts patient's insurance
            if payer_id:
                accepted_payers = facility.get("accepted_payers", [])
                accepts_insurance = facility.get("accepts_insurance", None)
                if accepted_payers and payer_id not in accepted_payers:
                    continue
                if accepts_insurance is not None and not accepts_insurance:
                    continue

            # Filter: behavioral support
            if behavioral_flags:
                accepts_behavioral = facility.get("accepts_behavioral", False)
                if not accepts_behavioral:
                    continue

            # Filter: care capabilities
            if care_needs:
                facility_capabilities = facility.get("care_capabilities", [])
                if not all(need in facility_capabilities for need in care_needs):
                    continue

            # Filter: distance
            distance = facility.get("distance_miles", facility.get("distance", 0))
            if max_distance and distance > max_distance:
                continue

            filtered.append(facility)

        # Sort by distance ascending
        filtered.sort(key=lambda f: f.get("distance_miles", f.get("distance", 0)))

        if filtered:
            self.last_search_status = "MATCHES_FOUND"
        else:
            self.last_search_status = "NO_MATCHES_FOUND"

        return filtered

    # ------------------------------------------------------------------
    # Referral Management
    # ------------------------------------------------------------------

    async def send_referral(self, patient_data: dict = None, facility_id: str = None) -> dict:
        """
        Send a referral to a specific facility via CarePort.

        Args:
            patient_data: Patient clinical and administrative data for the referral packet.
            facility_id: Target facility ID.

        Returns:
            Referral submission result dict.
        """
        referral_packet = {}
        if patient_data:
            # Build referral packet without raw PHI in logs
            referral_packet = {
                "patient_id_hash": hash_identifier(
                    patient_data.get("id", patient_data.get("patient_id", "unknown"))
                ),
                "service_type": "SNF",
                "submitted_at": datetime.utcnow().isoformat(),
            }

        result = await self.careport.send_referral(facility_id, referral_packet)

        if isinstance(result, dict):
            return result
        return {
            "referral_id": getattr(result, "referral_id", str(uuid.uuid4())),
            "facility_id": facility_id,
            "status": getattr(result, "status", "SENT"),
        }

    async def send_referral_with_fallback(self, patient_data: dict, facility_ids: list) -> DotDict:
        """
        Try sending referrals to facilities in order until one accepts.

        If all facilities decline, returns an escalation result.

        Args:
            patient_data: Patient clinical and administrative data.
            facility_ids: Ordered list of facility IDs to try.

        Returns:
            DotDict with referral result or escalation status.
        """
        for facility_id in facility_ids:
            try:
                result = await self.careport.send_referral(facility_id, patient_data)

                # Check if declined
                if isinstance(result, dict):
                    status = result.get("status", "")
                else:
                    status = getattr(result, "status", "")

                if status.upper() in ("DECLINED", "REJECTED"):
                    logger.info("Facility %s declined referral, trying next", facility_id)
                    continue

                # Accepted
                if isinstance(result, dict):
                    return DotDict(result)
                return DotDict({
                    "referral_id": getattr(result, "referral_id", str(uuid.uuid4())),
                    "facility_id": facility_id,
                    "status": status,
                })

            except Exception:
                logger.warning("Referral to facility %s failed, trying next", facility_id)
                continue

        # All declined or failed
        logger.warning("All %d facilities declined referral -- escalating", len(facility_ids))
        return DotDict({
            "status": "ALL_DECLINED",
            "escalated": True,
            "facilities_tried": len(facility_ids),
        })

    # ------------------------------------------------------------------
    # Facility Ranking
    # ------------------------------------------------------------------

    def rank_facilities(self, facilities: list, criteria: dict = None) -> list:
        """
        Rank facilities by match score in descending order.

        Args:
            facilities: List of facility dicts.
            criteria: Optional ranking criteria overrides.

        Returns:
            Sorted list of facilities (highest match score first).
        """
        return sorted(
            facilities,
            key=lambda f: f.get("match_score", 0) if isinstance(f, dict) else getattr(f, "match_score", 0),
            reverse=True,
        )

    # ------------------------------------------------------------------
    # Search Parameter Builder
    # ------------------------------------------------------------------

    def build_search_params(self, patient_data: dict, attempt_number: int = 1) -> DotDict:
        """
        Build search parameters, expanding radius on repeated attempts
        or when the patient has behavioral flags.

        Args:
            patient_data: Patient data dict.
            attempt_number: Which search attempt this is (1-based).

        Returns:
            DotDict with max_distance_miles, default_max_distance, and other params.
        """
        default_max = self.DEFAULT_MAX_DISTANCE_MILES
        max_distance = default_max

        behavioral_flags = patient_data.get("behavioral_flags", [])

        # Expand search radius on 3rd+ attempt or if behavioral
        if attempt_number >= 3 or behavioral_flags:
            max_distance = default_max * 2  # double the radius

        return DotDict({
            "max_distance_miles": max_distance,
            "default_max_distance": default_max,
            "attempt_number": attempt_number,
            "service_type": "SNF",
            "expanded": max_distance > default_max,
        })

    # ------------------------------------------------------------------
    # Placement Duration Monitoring
    # ------------------------------------------------------------------

    def check_placement_duration(self, patient_id: str, days_searching: int) -> Optional[DotDict]:
        """
        Check if placement search has exceeded acceptable duration.

        Critical alert at 12+ days of searching.

        Args:
            patient_id: Patient identifier (hashed for logging).
            days_searching: Number of days the placement search has been active.

        Returns:
            Alert DotDict if critical threshold exceeded, None or low-priority otherwise.
        """
        patient_id_hash = hash_identifier(patient_id)

        if days_searching >= 12:
            logger.warning(
                "Placement search critical: %d days for patient_hash=%s",
                days_searching,
                patient_id_hash,
            )
            return DotDict({
                "patient_id_hash": patient_id_hash,
                "days_searching": days_searching,
                "priority": "critical",
                "recommended_action": "Immediately escalate to discharge planning supervisor",
                "level": "CRITICAL",
            })
        elif days_searching >= 5:
            return DotDict({
                "patient_id_hash": patient_id_hash,
                "days_searching": days_searching,
                "priority": "low",
                "recommended_action": "Monitor placement search progress",
                "level": "INFO",
            })

        return None
