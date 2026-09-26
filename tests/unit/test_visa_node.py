"""Unit tests for Phase 7 — Visa Functionality (Visa Planning Node).

Tests:
1. Domestic bypass (no visa processing, cost 0, empty countries).
2. International single destination invocation (e.g. Thailand, Japan, UK).
3. Static enriched rules and baseline retrieval.
4. Live policy override behavior.
5. Live search verification and graceful fallback on search failure.
6. Multiple international non-Schengen destinations (sum of fees).
7. Multiple Schengen destinations (single uniform Schengen visa optimization).
8. Traveler party size scaling on total visa costs.
9. Advance application requirement flag detection.
10. Unknown destination handling without fabrication or crashes.
11. LangGraph node interface contract.
"""

from __future__ import annotations

from unittest.mock import patch

from src.models.trip import (
    BudgetMode,
    DateMode,
    Pace,
    ResolvedLocation,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.models.visa import (
    LiveVisaPolicyAnalysis,
    VisaRequirementStatus,
    VisaVerdict,
)
from src.models.web_search import SearchResultItem, WebSearchResult
from src.nodes.intake_node import process_intake
from src.nodes.visa_node import (
    evaluate_country_visa,
    map_entry_type_to_status,
    process_visa,
    visa_node,
)

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


def make_context(
    origin: str,
    destinations: list[str],
    scope: TravelScope = TravelScope.INTERNATIONAL,
    adults: int = 1,
    children: int = 0,
) -> TripContext:
    """Create a minimal valid TripContext."""
    return TripContext(
        origin=origin,
        destinations=destinations,
        scope=scope,
        dates=TripDates(mode=DateMode.EXACT, start_date="2026-10-01", end_date="2026-10-10"),
        party=TripParty(adults=adults, children=children),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=200000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
    )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


def test_map_entry_type_to_status() -> None:
    """Verify entry type strings correctly map to VisaRequirementStatus enum."""
    assert map_entry_type_to_status("VISA_FREE") == VisaRequirementStatus.VISA_FREE
    assert map_entry_type_to_status("visa-free") == VisaRequirementStatus.VISA_FREE
    assert map_entry_type_to_status("FREE") == VisaRequirementStatus.VISA_FREE
    assert map_entry_type_to_status("VISA_ON_ARRIVAL") == VisaRequirementStatus.VISA_ON_ARRIVAL
    assert map_entry_type_to_status("voa") == VisaRequirementStatus.VISA_ON_ARRIVAL
    assert map_entry_type_to_status("E_VISA") == VisaRequirementStatus.E_VISA
    assert map_entry_type_to_status("evisa") == VisaRequirementStatus.E_VISA
    assert (
        map_entry_type_to_status("STICKER_VISA_REQUIRED")
        == VisaRequirementStatus.STICKER_VISA_REQUIRED
    )
    assert map_entry_type_to_status("sticker visa") == VisaRequirementStatus.STICKER_VISA_REQUIRED
    assert map_entry_type_to_status("CONDITIONAL_FREE") == VisaRequirementStatus.CONDITIONAL_FREE
    assert map_entry_type_to_status("RESTRICTED") == VisaRequirementStatus.RESTRICTED
    assert map_entry_type_to_status("DOMESTIC_BYPASS") == VisaRequirementStatus.DOMESTIC_BYPASS
    assert map_entry_type_to_status("UNKNOWN_VALUE") == VisaRequirementStatus.UNKNOWN


def test_domestic_trip_bypass_via_trip_context() -> None:
    """Domestic trip context immediately bypasses visa processing with 0 cost."""
    ctx = make_context(origin="DEL", destinations=["BOM", "GOA"], scope=TravelScope.DOMESTIC)
    verdict = process_visa(ctx)

    assert isinstance(verdict, VisaVerdict)
    assert verdict.is_domestic_bypass is True
    assert verdict.countries == []
    assert verdict.total_visa_cost_inr == 0.0
    assert verdict.requires_advance_application is False
    assert verdict.schengen_single_visa_applicable is False
    assert verdict.warnings == []


def test_domestic_trip_bypass_via_planning_state() -> None:
    """Domestic InitialPlanningState immediately bypasses visa processing."""
    ctx = make_context(origin="DEL", destinations=["Jaipur"], scope=TravelScope.DOMESTIC)
    state = process_intake(ctx)

    verdict = process_visa(state)

    assert verdict.is_domestic_bypass is True
    assert len(verdict.countries) == 0
    assert verdict.total_visa_cost_inr == 0.0


def test_domestic_trip_all_indian_destinations_bypasses() -> None:
    """Itinerary where all destinations are in India bypasses even if scope missing."""
    state_dict = {
        "travel_scope": TravelScope.DOMESTIC,
        "destinations": [
            {
                "query": "DEL",
                "name": "Delhi",
                "country_code": "IN",
                "latitude": 28.5,
                "longitude": 77.1,
            },
        ],
    }
    verdict = process_visa(state_dict)
    assert verdict.is_domestic_bypass is True


def test_international_single_country_japan() -> None:
    """Japan requires e-Visa or sticker visa for Indian travelers."""
    ctx = make_context(origin="DEL", destinations=["Japan"], scope=TravelScope.INTERNATIONAL)
    state = process_intake(ctx)

    verdict = process_visa(state)

    assert verdict.is_domestic_bypass is False
    assert len(verdict.countries) == 1
    jp = verdict.countries[0]

    assert jp.country_code == "JP"
    assert jp.status in (
        VisaRequirementStatus.E_VISA,
        VisaRequirementStatus.STICKER_VISA_REQUIRED,
    )
    assert jp.data_source == "STATIC_DATASET"
    assert jp.is_live_verified is False
    assert jp.confidence in ("HIGH", "MEDIUM")
    assert len(jp.required_documents) > 0
    assert jp.application_process is not None
    assert verdict.requires_advance_application is True


def test_international_visa_free_destination() -> None:
    """Evaluating a visa-free destination (e.g. Nepal or Thailand)."""
    verdict = evaluate_country_visa("NP")

    assert verdict.country_code == "NP"
    assert verdict.status == VisaRequirementStatus.VISA_FREE
    assert verdict.visa_fee_inr == 0.0
    assert len(verdict.required_documents) > 0
    assert "Indian passport" in verdict.required_documents[0]


def test_live_policy_override() -> None:
    """Manual or simulated live intelligence can override static baseline."""
    override = {
        "status": VisaRequirementStatus.VISA_FREE,
        "visa_fee_inr": 0.0,
        "visa_type_label": "Temporary Visa Waiver 2026",
        "permitted_stay_days": 30,
        "entry_conditions": ["Direct flights only"],
        "sources": ["https://immigration.gov.example/waiver"],
    }

    verdict = evaluate_country_visa("TH", live_policy_override=override)

    assert verdict.status == VisaRequirementStatus.VISA_FREE
    assert verdict.visa_fee_inr == 0.0
    assert verdict.visa_type_label == "Temporary Visa Waiver 2026"
    assert verdict.permitted_stay_days == 30
    assert verdict.is_live_verified is True
    assert verdict.data_source == "LIVE_VERIFIED"
    assert "Direct flights only" in verdict.entry_conditions
    assert any("Live policy update" in w for w in verdict.warnings)


def test_live_search_verification_detected_waiver() -> None:
    """Live search returns snippets and LLM reconciler confirms an active visa-free exemption."""
    mock_search = WebSearchResult(
        query="test query",
        results=[
            SearchResultItem(
                title="Government announces visa-free entry for Indian citizens",
                url="https://mfa.gov.test/visa-free",
                snippet=(
                    "The Ministry announced a visa-free waiver for Indian passport "
                    "holders for 30 days."
                ),
                source_provider="tavily",
            ),
        ],
        provider_used="Tavily",
        timestamp="2026-10-01T00:00:00Z",
    )

    mock_analysis = LiveVisaPolicyAnalysis(
        applies_to_indian_passports=True,
        policy_change_confirmed=True,
        status=VisaRequirementStatus.VISA_FREE,
        visa_type_label="Visa-Free Entry (Live Policy Update)",
        permitted_stay_days=30,
        visa_fee_inr=0.0,
        waiver_end_date=None,
        official_source_url="https://mfa.gov.test/visa-free",
        confidence="HIGH",
        reasoning="Official ministry announced active 30-day visa-free waiver for Indian citizens.",
    )

    with (
        patch("src.nodes.visa_node.search_web", return_value=mock_search),
        patch("src.nodes.visa_node._reconcile_with_llm", return_value=mock_analysis),
    ):
        verdict = evaluate_country_visa("TH", live_search_enabled=True)

        assert verdict.is_live_verified is True
        assert verdict.data_source == "LIVE_VERIFIED"
        assert verdict.status == VisaRequirementStatus.VISA_FREE
        assert verdict.visa_fee_inr == 0.0
        assert any("Live policy update" in w for w in verdict.warnings)


def test_live_reconciliation_rejects_other_nationality_waiver() -> None:
    """Semantic analysis rejects rules that apply only to foreign citizens (e.g. EU/US)."""
    mock_search = WebSearchResult(
        query="test query",
        results=[
            SearchResultItem(
                title="Visa Free Entry Policy Announced",
                url="https://immigration.gov.example/rules",
                snippet=(
                    "Citizens of the European Union enjoy visa-free entry for 90 days. "
                    "Indian citizens require an approved tourist e-visa before travel."
                ),
                source_provider="tavily",
            ),
        ],
        provider_used="Tavily",
        timestamp="2026-10-01T00:00:00Z",
    )

    # LLM correctly recognizes the visa-free rule does NOT apply to Indian passports
    mock_analysis = LiveVisaPolicyAnalysis(
        applies_to_indian_passports=False,
        policy_change_confirmed=False,
        status=None,
        confidence="HIGH",
        reasoning=(
            "Visa-free entry applies exclusively to EU citizens; "
            "Indian passport holders still require e-visa."
        ),
    )

    with (
        patch("src.nodes.visa_node.search_web", return_value=mock_search),
        patch("src.nodes.visa_node._reconcile_with_llm", return_value=mock_analysis),
    ):
        verdict = evaluate_country_visa("TH", live_search_enabled=True)

        # Baseline must NOT be overridden to VISA_FREE!
        assert verdict.status != VisaRequirementStatus.VISA_FREE
        assert any("do not apply to Indian passport holders" in w for w in verdict.warnings)


def test_live_reconciliation_rejects_speculative_news() -> None:
    """Speculative or unconfirmed policy proposals do not override verified baseline."""
    mock_search = WebSearchResult(
        query="test query",
        results=[
            SearchResultItem(
                title="Cabinet considers visa-free travel for Indian tourists",
                url="https://news.example/travel",
                snippet=(
                    "The tourism ministry has proposed visa-free access, "
                    "but cabinet approval is pending."
                ),
                source_provider="tavily",
            ),
        ],
        provider_used="Tavily",
        timestamp="2026-10-01T00:00:00Z",
    )

    mock_analysis = LiveVisaPolicyAnalysis(
        applies_to_indian_passports=True,
        policy_change_confirmed=False,  # Still pending proposal
        status=None,
        confidence="LOW",
        reasoning="Policy is a pending proposal, not an enacted official decree.",
    )

    with (
        patch("src.nodes.visa_node.search_web", return_value=mock_search),
        patch("src.nodes.visa_node._reconcile_with_llm", return_value=mock_analysis),
    ):
        verdict = evaluate_country_visa("TH", live_search_enabled=True)

        # Must not change to VISA_FREE
        assert verdict.status != VisaRequirementStatus.VISA_FREE
        has_proposal_or_baseline = any(
            "pending proposal" in w.lower() or "baseline" in w.lower() for w in verdict.warnings
        )
        assert has_proposal_or_baseline


def test_live_reconciliation_rejects_expired_waiver() -> None:
    """Temporary waiver expiring before planned travel date is rejected."""
    mock_search = WebSearchResult(
        query="test query",
        results=[
            SearchResultItem(
                title="Temporary visa waiver 2026",
                url="https://mfa.gov.test/waiver",
                snippet="Temporary visa waiver in effect through May 1, 2026.",
                source_provider="tavily",
            ),
        ],
        provider_used="Tavily",
        timestamp="2026-10-01T00:00:00Z",
    )

    mock_analysis = LiveVisaPolicyAnalysis(
        applies_to_indian_passports=True,
        policy_change_confirmed=True,
        status=VisaRequirementStatus.VISA_FREE,
        waiver_end_date="2026-05-01",
        confidence="HIGH",
        reasoning="Temporary exemption valid until May 1, 2026.",
    )

    with (
        patch("src.nodes.visa_node.search_web", return_value=mock_search),
        patch("src.nodes.visa_node._reconcile_with_llm", return_value=mock_analysis),
    ):
        # User is traveling in October 2026 (after the waiver expires on 2026-05-01)
        verdict = evaluate_country_visa("TH", live_search_enabled=True, travel_date="2026-10-15")

        # Must reject the expired waiver and retain baseline
        assert verdict.status != VisaRequirementStatus.VISA_FREE
        assert any(
            "expires on 2026-05-01 before planned travel date" in w for w in verdict.warnings
        )


def test_live_search_fallback_when_llm_unavailable() -> None:
    """Live search succeeds, but LLM reconciliation is unavailable -> retains baseline safely."""
    mock_search = WebSearchResult(
        query="test query",
        results=[
            SearchResultItem(
                title="General rules",
                url="https://test.gov",
                snippet="General guidelines for foreign nationals.",
                source_provider="tavily",
            ),
        ],
        provider_used="Tavily",
        timestamp="2026-10-01T00:00:00Z",
    )

    with (
        patch("src.nodes.visa_node.search_web", return_value=mock_search),
        patch("src.nodes.visa_node._reconcile_with_llm", return_value=None),
    ):
        verdict = evaluate_country_visa("JP", live_search_enabled=True)

        assert verdict.country_code == "JP"
        assert verdict.status in (
            VisaRequirementStatus.E_VISA,
            VisaRequirementStatus.STICKER_VISA_REQUIRED,
        )
        assert any(
            "LLM structured policy reconciliation was unavailable" in w for w in verdict.warnings
        )


def test_live_search_fallback_on_network_error() -> None:
    """Network failure during live search gracefully falls back to static dataset."""
    with patch("src.nodes.visa_node.search_web", side_effect=Exception("Connection timed out")):
        verdict = evaluate_country_visa("JP", live_search_enabled=True)

        # Must not crash, should fall back to static dataset
        assert verdict.country_code == "JP"
        assert verdict.data_source == "STATIC_DATASET"
        assert verdict.is_live_verified is False
        assert any("retained verified static baseline" in w for w in verdict.warnings)


def test_multiple_international_non_schengen() -> None:
    """Multiple non-Schengen international countries sum their individual visa fees."""
    ctx = make_context(
        origin="DEL",
        destinations=["Thailand", "Vietnam"],
        scope=TravelScope.INTERNATIONAL,
        adults=1,
    )
    state = process_intake(ctx)

    verdict = process_visa(state)

    assert verdict.is_domestic_bypass is False
    assert len(verdict.countries) == 2
    country_codes = {c.country_code for c in verdict.countries}
    assert "TH" in country_codes
    assert "VN" in country_codes
    assert verdict.schengen_single_visa_applicable is False

    expected_total = sum(c.visa_fee_inr for c in verdict.countries)
    assert verdict.total_visa_cost_inr == expected_total


def test_multiple_schengen_countries_single_visa_optimization() -> None:
    """Visiting multiple Schengen countries triggers single Schengen visa optimization."""
    ctx = make_context(
        origin="DEL",
        destinations=["France", "Netherlands", "Germany"],
        scope=TravelScope.INTERNATIONAL,
        adults=1,
    )
    state = process_intake(ctx)

    verdict = process_visa(state)

    assert verdict.is_domestic_bypass is False
    assert len(verdict.countries) == 3
    assert verdict.schengen_single_visa_applicable is True
    assert any("Schengen Area" in w for w in verdict.warnings)

    # Fee should be charged ONCE per traveler (not 3 times)
    schengen_fees = [c.visa_fee_inr for c in verdict.countries]
    max_fee = max(schengen_fees)
    assert verdict.total_visa_cost_inr == max_fee
    assert verdict.total_visa_cost_inr < sum(schengen_fees)


def test_traveler_party_multiplier_on_total_cost() -> None:
    """Total visa cost accurately scales by traveler party count."""
    ctx = make_context(
        origin="DEL",
        destinations=["Vietnam"],
        scope=TravelScope.INTERNATIONAL,
        adults=2,
        children=2,  # Total 4 travelers
    )
    state = process_intake(ctx)

    verdict = process_visa(state)

    vn = verdict.countries[0]
    expected_party_total = round(vn.visa_fee_inr * 4, 2)
    assert verdict.total_visa_cost_inr == expected_party_total


def test_advance_application_flag_detection() -> None:
    """Trip requiring e-Visa or Sticker Visa triggers requires_advance_application."""
    # UK requires advance application
    ctx_uk = make_context(origin="DEL", destinations=["GB"], scope=TravelScope.INTERNATIONAL)
    state_uk = process_intake(ctx_uk)
    verdict_uk = process_visa(state_uk)
    assert verdict_uk.requires_advance_application is True

    # Nepal is visa-free (freedom of movement)
    ctx_np = make_context(origin="DEL", destinations=["NP"], scope=TravelScope.INTERNATIONAL)
    state_np = process_intake(ctx_np)
    verdict_np = process_visa(state_np)
    assert verdict_np.requires_advance_application is False


def test_unknown_destination_safety_rule() -> None:
    """Unrecognized country does NOT fabricate requirements and reports limitation."""
    verdict = evaluate_country_visa("ZZ", country_name="Unknownland")

    assert verdict.status == VisaRequirementStatus.UNKNOWN
    assert verdict.confidence == "LOW"
    assert verdict.visa_fee_inr == 0.0
    assert any("No verified static visa record found" in w for w in verdict.warnings)


def test_deduplication_of_multiple_destinations_same_country() -> None:
    """Visiting multiple cities in Italy (e.g. Rome and Milan) evaluates Italy once."""
    loc_rome = ResolvedLocation(
        query="Rome",
        name="Leonardo da Vinci–Fiumicino Airport",
        city="Rome",
        country_code="IT",
        country_name="Italy",
        iata_code="FCO",
        latitude=41.8,
        longitude=12.2,
        is_schengen=True,
    )
    loc_milan = ResolvedLocation(
        query="Milan",
        name="Milan Malpensa Airport",
        city="Milan",
        country_code="IT",
        country_name="Italy",
        iata_code="MXP",
        latitude=45.6,
        longitude=8.7,
        is_schengen=True,
    )

    state_dict = {
        "travel_scope": TravelScope.INTERNATIONAL,
        "destinations": [loc_rome, loc_milan],
    }

    verdict = process_visa(state_dict)

    assert len(verdict.countries) == 1
    assert verdict.countries[0].country_code == "IT"
    assert verdict.schengen_single_visa_applicable is False


def test_visa_node_langgraph_dict_interface() -> None:
    """visa_node accepts dictionary state and returns updated dict with 'visa_verdict'."""
    ctx = make_context(origin="DEL", destinations=["Thailand"], scope=TravelScope.INTERNATIONAL)
    state = process_intake(ctx)

    result = visa_node(state)

    assert isinstance(result, dict)
    assert "visa_verdict" in result
    assert isinstance(result["visa_verdict"], VisaVerdict)
    assert result["visa_verdict"].is_domestic_bypass is False
