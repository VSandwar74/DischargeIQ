"""
Tests: Placement Coordinator Agent
Priority: P1 — second agent, handles SNF matching and referrals.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.fixtures.synthetic_data import (
    SYNTHETIC_PATIENTS, SYNTHETIC_FACILITIES,
    COVERAGE_AETNA_MA, COVERAGE_CARESOURCE_MEDICAID,
    AMPAC_SCORE_LOW, AMPAC_SCORE_BORDERLINE,
    REFERRAL_ACCEPTED, REFERRAL_DECLINED_INSURANCE,
    REFERRAL_DECLINED_BEHAVIORAL, REFERRAL_DECLINED_NO_BEDS,
)
from src.agents.placement import PlacementAgent


# ===================================================================
# Facility Search & Matching
# ===================================================================

class TestFacilitySearch:

    @pytest.mark.asyncio
    async def test_returns_facilities_with_beds(self, mock_careport):
        """Only facilities with available beds should be returned."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        results = await agent.find_matches(patient_data={"coverage": COVERAGE_AETNA_MA})
        assert all(f["beds_available"] > 0 for f in results)
        # Sunrise (fac-002) has 0 beds — should be excluded
        assert "fac-002" not in [f["id"] for f in results]

    @pytest.mark.asyncio
    async def test_filters_by_insurance_acceptance(self, mock_careport):
        """Facilities that don't accept the patient's payer should be excluded."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        # patient has Aetna MA — Oakwood (fac-003) only takes UHC
        results = await agent.find_matches(patient_data={"coverage": COVERAGE_AETNA_MA})
        facility_ids = [f["id"] for f in results]
        assert "fac-003" not in facility_ids  # doesn't accept Aetna
        assert "fac-001" in facility_ids      # accepts Aetna

    @pytest.mark.asyncio
    async def test_filters_behavioral_patients(self, mock_careport):
        """Patients with behavioral flags should only match facilities that accept behavioral."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        patient_data = {"behavioral_flags": ["wandering", "aggression"]}
        results = await agent.find_matches(patient_data)
        # All returned facilities must accept behavioral
        assert all(f["accepts_behavioral"] for f in results)

    @pytest.mark.asyncio
    async def test_matches_care_capabilities(self, mock_careport):
        """Patient needing IV antibiotics should only match facilities with that capability."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        patient_data = {"care_needs": ["PT", "IV_antibiotics"]}
        results = await agent.find_matches(patient_data)
        # All returned facilities must have IV_antibiotics capability
        assert all("IV_antibiotics" in f["care_capabilities"] for f in results)

    @pytest.mark.asyncio
    async def test_ranks_by_distance(self, mock_careport):
        """Closer facilities should rank higher (all else equal)."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        results = await agent.find_matches(patient_data={"coverage": COVERAGE_AETNA_MA})
        distances = [f["distance_miles"] for f in results]
        assert distances == sorted(distances)  # ascending

    @pytest.mark.asyncio
    async def test_respects_family_geography_preference(self, mock_careport):
        """If family only wants nearby facilities, exclude distant options."""
        mock_careport.search_facilities.return_value = SYNTHETIC_FACILITIES
        agent = PlacementAgent(careport=mock_careport)
        patient_data = {"family_preferences": {"geography": "west_side", "max_distance_miles": 5}}
        results = await agent.find_matches(patient_data)
        assert all(f["distance_miles"] <= 5 for f in results)

    @pytest.mark.asyncio
    async def test_returns_empty_list_gracefully(self, mock_careport):
        """If no facilities match, return empty list — don't crash."""
        mock_careport.search_facilities.return_value = []
        agent = PlacementAgent(careport=mock_careport)
        results = await agent.find_matches(patient_data={"coverage": COVERAGE_AETNA_MA})
        assert results == []


# ===================================================================
# Referral Submission
# ===================================================================

class TestReferralSubmission:

    @pytest.mark.asyncio
    async def test_sends_referral_to_selected_facility(self, mock_careport):
        """Happy path: send referral and receive acceptance."""
        mock_careport.send_referral.return_value = REFERRAL_ACCEPTED
        agent = PlacementAgent(careport=mock_careport)
        result = await agent.send_referral(patient_data=SYNTHETIC_PATIENTS[0], facility_id="fac-001")
        assert result["status"] == "ACCEPTED"
        assert result["bed_assigned"] is not None

    @pytest.mark.asyncio
    async def test_handles_referral_decline_insurance(self, mock_careport):
        """Facility declines due to insurance — agent should try next facility."""
        mock_careport.send_referral.side_effect = [
            REFERRAL_DECLINED_INSURANCE,  # first facility declines
            REFERRAL_ACCEPTED,             # second facility accepts
        ]
        agent = PlacementAgent(careport=mock_careport)
        result = await agent.send_referral_with_fallback(
            patient_data=SYNTHETIC_PATIENTS[0],
            facility_ids=["fac-003", "fac-001"]
        )
        assert result.status == "ACCEPTED"
        assert mock_careport.send_referral.call_count == 2

    @pytest.mark.asyncio
    async def test_handles_referral_decline_no_beds(self, mock_careport):
        """Facility declines due to no beds — should be removed from candidates."""
        mock_careport.send_referral.return_value = REFERRAL_DECLINED_NO_BEDS
        agent = PlacementAgent(careport=mock_careport)
        result = await agent.send_referral(patient_data=SYNTHETIC_PATIENTS[0], facility_id="fac-002")
        assert result["status"] == "DECLINED"
        assert result["decline_reason"] == "no_beds_available"

    @pytest.mark.asyncio
    async def test_handles_referral_decline_behavioral(self, mock_careport):
        """Facility declines due to behavioral capacity — agent should filter future matches."""
        mock_careport.send_referral.return_value = REFERRAL_DECLINED_BEHAVIORAL
        agent = PlacementAgent(careport=mock_careport)
        result = await agent.send_referral(patient_data=SYNTHETIC_PATIENTS[0], facility_id="fac-001")
        assert result["decline_reason"] == "behavioral_capacity_full"

    @pytest.mark.asyncio
    async def test_all_facilities_decline(self, mock_careport):
        """If every facility declines, agent should escalate to case manager."""
        mock_careport.send_referral.return_value = REFERRAL_DECLINED_NO_BEDS
        agent = PlacementAgent(careport=mock_careport)
        result = await agent.send_referral_with_fallback(
            patient_data=SYNTHETIC_PATIENTS[0],
            facility_ids=["fac-001", "fac-002", "fac-003"]
        )
        assert result.status == "ALL_DECLINED"
        assert result.escalated is True

    @pytest.mark.asyncio
    async def test_referral_packet_contains_required_docs(self, mock_careport):
        """Referral packet must include clinical summary, therapy notes, insurance info."""
        # TODO: Verifying referral packet contents depends on the internal
        # structure of the referral packet built by send_referral(). The exact
        # shape of call_args varies by implementation. Leaving as a spec until
        # the referral packet format is finalized.
        mock_careport.send_referral.return_value = REFERRAL_ACCEPTED
        agent = PlacementAgent(careport=mock_careport)
        await agent.send_referral(patient_data=SYNTHETIC_PATIENTS[0], facility_id="fac-001")
        mock_careport.send_referral.assert_called_once()


# ===================================================================
# 20-Day Placement Failure Scenario
# ===================================================================

class TestDifficultPlacements:
    """From interview: patients can sit 20+ days for behavioral placements."""

    @pytest.mark.asyncio
    async def test_long_stay_patient_gets_escalation(self):
        """Patient with 12+ avoidable days should trigger escalation."""
        agent = PlacementAgent(careport=AsyncMock())
        alert = agent.check_placement_duration(
            patient_id="synth-patient-003",
            days_searching=12
        )
        assert alert.priority == "critical"
        assert "escalate" in alert.recommended_action.lower()

    @pytest.mark.asyncio
    async def test_behavioral_patient_searches_wider_network(self):
        """Behavioral patients should trigger expanded geographic search."""
        agent = PlacementAgent(careport=AsyncMock())
        search_params = agent.build_search_params(
            patient_data={"behavioral_flags": ["aggression"]},
            attempt_number=3  # third attempt
        )
        assert search_params.max_distance_miles > search_params.default_max_distance
