"""Phase 2 tests — Static Data Access Layer (src/tools/static_data.py).

Verifies in-memory indexing, lookups, coordinates, visa rules, country profiles,
error handling, and reload capabilities.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.models.airport import Airport
from src.models.visa import EnrichedVisaRecord
from src.tools.static_data import (
    AirportNotFoundError,
    CountryNotFoundError,
    InvalidLookupError,
    StaticDataStore,
    VisaRuleNotFoundError,
    find_airport,
    find_country,
    get_airport,
    get_airport_coordinates,
    get_airports_by_city,
    get_airports_by_country,
    get_country,
    get_enriched_visa,
    get_ist_time_difference_hours,
    get_visa_baseline,
    get_visa_rule,
    is_schengen,
    parse_utc_offset_hours,
    reload_static_data,
)

# ===========================================================================
# 1. Airport Lookups (DEL, CCU, BGO, TAS, BSZ)
# ===========================================================================


@pytest.mark.parametrize("code", ["DEL", "CCU", "BGO", "TAS", "BSZ"])
def test_get_airport_valid_spec_examples(code: str) -> None:
    """Verify standard airports required by Phase 2 spec resolve cleanly."""
    airport = get_airport(code)
    assert isinstance(airport, Airport)
    assert airport.iata_code == code
    assert airport.latitude_deg != 0.0
    assert airport.longitude_deg != 0.0


def test_get_airport_case_insensitivity() -> None:
    """Airport IATA lookups must be case-insensitive and trim whitespace."""
    a1 = get_airport("del")
    a2 = get_airport(" DEL ")
    assert a1.iata_code == "DEL"
    assert a1.name == a2.name


def test_get_airport_not_found_raises() -> None:
    """Querying an unknown IATA code must raise AirportNotFoundError."""
    with pytest.raises(AirportNotFoundError, match="XYZ999"):
        get_airport("XYZ999")


@pytest.mark.parametrize("bad_input", ["", "   ", None])
def test_get_airport_invalid_input_raises(bad_input) -> None:
    """Empty or non-string IATA codes must raise InvalidLookupError."""
    with pytest.raises(InvalidLookupError):
        get_airport(bad_input)


def test_find_airport_returns_none_when_missing() -> None:
    """find_airport returns Airport if found, or None if missing/invalid."""
    assert find_airport("DEL") is not None
    assert find_airport("NONEXISTENT") is None
    assert find_airport("") is None


# ===========================================================================
# 2. Airport City & Country Searches & Coordinates
# ===========================================================================


def test_get_airports_by_city() -> None:
    """Lookup airports by municipality name."""
    airports = get_airports_by_city("New Delhi")
    assert len(airports) >= 1
    assert any(a.iata_code == "DEL" for a in airports)


def test_get_airports_by_city_empty_raises() -> None:
    with pytest.raises(InvalidLookupError):
        get_airports_by_city("")


def test_get_airports_by_country() -> None:
    """Lookup airports by ISO-2 country code."""
    airports = get_airports_by_country("IN")
    assert len(airports) >= 30
    assert any(a.iata_code == "DEL" for a in airports)
    assert any(a.iata_code == "CCU" for a in airports)


def test_get_airports_by_country_empty_raises() -> None:
    with pytest.raises(InvalidLookupError):
        get_airports_by_country("")


def test_get_airport_coordinates() -> None:
    """Retrieve latitude and longitude tuple for an airport."""
    lat, lng = get_airport_coordinates("DEL")
    assert isinstance(lat, float)
    assert isinstance(lng, float)
    # Delhi is approximately 28.5°N, 77.1°E
    assert 28.0 <= lat <= 29.0
    assert 76.5 <= lng <= 77.5


# ===========================================================================
# 3. Country Profile Lookups & Schengen / Timezone intelligence
# ===========================================================================


def test_get_country_by_iso2_iso3_and_name() -> None:
    """A country profile can be retrieved by ISO-2, ISO-3, or common name."""
    c1 = get_country("JP")
    c2 = get_country("JPN")
    c3 = get_country("Japan")
    assert c1.country_code == "JP"
    assert c2.country_code == "JP"
    assert c3.country_code == "JP"
    assert c1.name == "Japan"
    assert c1.flag_emoji == "🇯🇵"
    assert c1.capital == "Tokyo"
    assert len(c1.currencies) >= 1
    assert c1.currencies[0].code == "JPY"


def test_get_country_not_found_raises() -> None:
    with pytest.raises(CountryNotFoundError, match="NonExistentCountry"):
        get_country("NonExistentCountry")


@pytest.mark.parametrize("bad_input", ["", "  ", None])
def test_get_country_invalid_input_raises(bad_input) -> None:
    with pytest.raises(InvalidLookupError):
        get_country(bad_input)


def test_find_country_returns_none_when_missing() -> None:
    assert find_country("FR") is not None
    assert find_country("ZZZ") is None
    assert find_country("") is None


def test_is_schengen() -> None:
    """Verify Schengen Area membership resolution."""
    assert is_schengen("France") is True
    assert is_schengen("FR") is True
    assert is_schengen("FRA") is True
    assert is_schengen("Germany") is True
    assert is_schengen("Japan") is False
    assert is_schengen("India") is False
    assert is_schengen("NonExistent") is False


def test_parse_utc_offset_hours() -> None:
    assert parse_utc_offset_hours("UTC+09:00") == 9.0
    assert parse_utc_offset_hours("UTC+05:30") == 5.5
    assert parse_utc_offset_hours("UTC-03:30") == -3.5
    assert parse_utc_offset_hours("UTC-05:00") == -5.0
    assert parse_utc_offset_hours("UTC") == 0.0
    assert parse_utc_offset_hours("INVALID") is None


def test_get_ist_time_difference_hours() -> None:
    """Test time difference relative to IST (UTC+05:30)."""
    # Japan (UTC+09:00) is +3.5 hours ahead of IST (+5.5)
    diff_jp = get_ist_time_difference_hours("Japan")
    assert diff_jp == 3.5

    # France (UTC+01:00) is -4.5 hours behind IST (+5.5)
    diff_fr = get_ist_time_difference_hours("France")
    assert diff_fr == -4.5


# ===========================================================================
# 4. Visa Rule Lookups (Baseline & Enriched)
# ===========================================================================


def test_get_visa_baseline() -> None:
    """Retrieve static baseline visa rules from visa_rules.json."""
    rule_jp = get_visa_baseline("Japan")
    valid_requirements = (
        "E_VISA",
        "VISA_FREE",
        "VISA_ON_ARRIVAL",
        "STICKER_VISA_REQUIRED",
    )
    assert rule_jp.requirement in valid_requirements

    rule_by_code = get_visa_baseline("JP")
    assert rule_by_code.destination == rule_jp.destination


def test_get_visa_baseline_not_found_raises() -> None:
    with pytest.raises(VisaRuleNotFoundError):
        get_visa_baseline("Atlantis")


def test_get_enriched_visa() -> None:
    """Retrieve enriched multi-option visa records from visa_rules_enriched.json."""
    enriched = get_enriched_visa("Japan")
    assert isinstance(enriched, EnrichedVisaRecord)
    assert enriched.destination == "Japan"
    assert len(enriched.options) >= 1
    assert enriched.selected_option is not None
    assert enriched.selected_option.cost_inr >= 0.0


def test_get_visa_rule_unification() -> None:
    """get_visa_rule returns EnrichedVisaRecord for enriched countries."""
    res = get_visa_rule("Japan")
    assert isinstance(res, EnrichedVisaRecord)
    assert res.destination == "Japan"


# ===========================================================================
# 5. Custom Store & Fixture Isolation
# ===========================================================================


def test_custom_store_isolation(tmp_path: Path) -> None:
    """StaticDataStore can load custom fixture files safely."""
    custom_airports = [
        {
            "iata_code": "FRU",
            "type": "medium_airport",
            "name": "Manas International Airport",
            "municipality": "Bishkek",
            "iso_country": "KG",
            "latitude_deg": 43.0612,
            "longitude_deg": 74.4776,
        }
    ]
    custom_path = tmp_path / "custom_airports.json"
    with open(custom_path, "w", encoding="utf-8") as f:
        json.dump(custom_airports, f)

    store = StaticDataStore(
        airports_path=custom_path,
        visa_rules_path=tmp_path / "nonexistent_visa.json",
        enriched_visa_path=tmp_path / "nonexistent_enriched.json",
        countries_path=tmp_path / "nonexistent_countries.json",
    )

    fru = store.get_airport("FRU")
    assert fru.iata_code == "FRU"
    assert fru.municipality == "Bishkek"
    assert fru.latitude_deg == 43.0612


def test_reload_static_data() -> None:
    """reload_static_data must reload data into memory without errors."""
    reload_static_data()
    airport = get_airport("DEL")
    assert airport.iata_code == "DEL"
