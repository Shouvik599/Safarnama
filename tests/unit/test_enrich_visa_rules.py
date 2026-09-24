"""Unit tests for scripts/enrich_visa_rules.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from scripts.enrich_visa_rules import (
    enrich_destination,
    fetch_tavily_search,
    find_destination,
    select_best_option,
    upsert_enriched,
)
from src.models.visa import EnrichedVisaRecord, VisaOption


def test_select_best_option_prioritizes_free_over_paid():
    opt_free = VisaOption(
        visa_type="Visa-Free 15 Days",
        duration_days=15,
        cost_inr=0.0,
        entry_type="VISA_FREE",
        requires_loi=False,
        source=["https://example.com/free"],
    )
    opt_paid = VisaOption(
        visa_type="Tourist e-Visa 30 Days",
        duration_days=30,
        cost_inr=2500.0,
        entry_type="E_VISA",
        requires_loi=False,
        source=["https://example.com/evisa"],
    )
    best = select_best_option([opt_paid, opt_free])
    assert best.visa_type == "Visa-Free 15 Days"


def test_select_best_option_prioritizes_longer_stay_when_same_cost():
    opt_30 = VisaOption(
        visa_type="Visa-Free 30 Days",
        duration_days=30,
        cost_inr=0.0,
        entry_type="VISA_FREE",
        requires_loi=False,
        source=["https://example.com/30"],
    )
    opt_90 = VisaOption(
        visa_type="Visa-Free 90 Days",
        duration_days=90,
        cost_inr=0.0,
        entry_type="VISA_FREE",
        requires_loi=False,
        source=["https://example.com/90"],
    )
    best = select_best_option([opt_30, opt_90])
    assert best.visa_type == "Visa-Free 90 Days"


def test_find_destination_case_insensitive():
    rules = [
        {"destination": "Japan", "country_code": "JP", "requirement": "E_VISA"},
        {"destination": "Uzbekistan", "country_code": "UZ", "requirement": "E_VISA"},
    ]
    res = find_destination(rules, "japan")
    assert res is not None
    assert res["country_code"] == "JP"

    none_res = find_destination(rules, "NonExistent")
    assert none_res is None


def test_upsert_enriched():
    existing = [
        {"destination": "Japan", "country_code": "JP", "status": "old"},
        {"destination": "Thailand", "country_code": "TH", "status": "active"},
    ]
    updated_japan = {"destination": "Japan", "country_code": "JP", "status": "updated"}
    result = upsert_enriched(existing, updated_japan)
    assert len(result) == 2
    assert result[0]["status"] == "updated"

    new_country = {"destination": "Vietnam", "country_code": "VN"}
    result2 = upsert_enriched(existing, new_country)
    assert len(result2) == 3


def test_fetch_tavily_search_returns_empty_on_network_error():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        results = fetch_tavily_search("test query", "dummy_key")
        assert results == []


def test_enrich_destination_succeeds_with_mocked_gemini():
    mock_record_dict = {
        "destination": "Testland",
        "country_code": "TL",
        "options": [
            {
                "visa_type": "Visa Free",
                "duration_days": 30,
                "cost_inr": 0.0,
                "entry_type": "VISA_FREE",
                "requires_loi": False,
                "source": ["https://example.com"],
            }
        ],
        "selected_option": {
            "visa_type": "Visa Free",
            "duration_days": 30,
            "cost_inr": 0.0,
            "entry_type": "VISA_FREE",
            "requires_loi": False,
            "source": ["https://example.com"],
        },
        "last_updated": "2026-09-24",
    }

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_record_dict)
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        with patch("scripts.enrich_visa_rules.fetch_tavily_search", return_value=[]):
            enriched = enrich_destination(
                destination="Testland",
                baseline={"destination": "Testland", "country_code": "TL"},
                gemini_api_key="fake-key",
            )
            assert isinstance(enriched, EnrichedVisaRecord)
            assert enriched.destination == "Testland"
            assert enriched.selected_option.visa_type == "Visa Free"
