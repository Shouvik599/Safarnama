"""Unit tests for scripts/fetch_country_profiles.py."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scripts.fetch_country_profiles import (
    fetch_all_countries,
    main,
    parse_country_record,
    save_countries_json,
)
from src.models.country import CountryProfile


@pytest.fixture
def sample_raw_country():
    return {
        "names": {
            "common": "Japan",
            "official": "Japan",
        },
        "codes": {
            "alpha_2": "JP",
            "alpha_3": "JPN",
        },
        "capitals": [
            {
                "name": "Tokyo",
                "attributes": {"primary": True},
                "coordinates": {"lat": 35.68, "lng": 139.75},
            }
        ],
        "region": "Asia",
        "subregion": "Eastern Asia",
        "currencies": [
            {
                "code": "JPY",
                "name": "Japanese yen",
                "symbol": "¥",
            }
        ],
        "languages": [
            {
                "bcp47": "ja",
                "name": "Japanese",
            }
        ],
        "timezones": ["UTC+09:00"],
        "cars": {"side": "left"},
        "calling_codes": ["81"],
        "flag": {"emoji": "🇯🇵"},
        "memberships": {
            "schengen": False,
            "eu": False,
        },
        "borders": [],
    }


def test_parse_country_record_full(sample_raw_country):
    parsed = parse_country_record(sample_raw_country, "2026-09-25")
    assert parsed["country_code"] == "JP"
    assert parsed["country_code_alpha3"] == "JPN"
    assert parsed["name"] == "Japan"
    assert parsed["capital"] == "Tokyo"
    assert parsed["capital_coordinates"] == {"lat": 35.68, "lng": 139.75}
    assert parsed["region"] == "Asia"
    assert parsed["subregion"] == "Eastern Asia"
    assert len(parsed["currencies"]) == 1
    assert parsed["currencies"][0]["code"] == "JPY"
    assert parsed["currencies"][0]["symbol"] == "¥"
    assert len(parsed["languages"]) == 1
    assert parsed["languages"][0]["name"] == "Japanese"
    assert parsed["timezones"] == ["UTC+09:00"]
    assert parsed["driving_side"] == "left"
    assert parsed["calling_code"] == "+81"
    assert parsed["flag_emoji"] == "🇯🇵"
    assert parsed["is_schengen"] is False
    assert parsed["is_eu"] is False
    assert parsed["last_updated"] == "2026-09-25"

    # Verify Pydantic validation passes
    model = CountryProfile.model_validate(parsed)
    assert model.name == "Japan"


def test_parse_country_record_sparse():
    raw_sparse = {
        "names": {"common": "Antarctica"},
        "codes": {"alpha_2": "AQ", "alpha_3": "ATA"},
        "region": "Antarctic",
    }
    parsed = parse_country_record(raw_sparse, "2026-09-25")
    assert parsed["country_code"] == "AQ"
    assert parsed["country_code_alpha3"] == "ATA"
    assert parsed["name"] == "Antarctica"
    assert parsed["capital"] is None
    assert parsed["capital_coordinates"] is None
    assert parsed["currencies"] == []
    assert parsed["languages"] == []
    assert parsed["calling_code"] is None
    assert parsed["is_schengen"] is False


def test_parse_country_record_schengen_and_borders():
    raw_france = {
        "names": {"common": "France", "official": "French Republic"},
        "codes": {"alpha_2": "FR", "alpha_3": "FRA"},
        "region": "Europe",
        "memberships": {"schengen": True, "eu": True},
        "borders": ["DEU", "ITA", "ESP"],
        "calling_codes": ["+33"],
    }
    parsed = parse_country_record(raw_france, "2026-09-25")
    assert parsed["is_schengen"] is True
    assert parsed["is_eu"] is True
    assert parsed["borders"] == ["DEU", "ITA", "ESP"]
    assert parsed["calling_code"] == "+33"


def test_fetch_all_countries_pagination():
    page1 = {"data": {"objects": [{"codes": {"alpha_2": f"C{i}"}} for i in range(100)]}}
    page2 = {"data": {"objects": [{"codes": {"alpha_2": "C101"}}, {"codes": {"alpha_2": "C102"}}]}}

    mock_resp1 = MagicMock()
    mock_resp1.read.return_value = json.dumps(page1).encode("utf-8")
    mock_resp1.__enter__.return_value = mock_resp1

    mock_resp2 = MagicMock()
    mock_resp2.read.return_value = json.dumps(page2).encode("utf-8")
    mock_resp2.__enter__.return_value = mock_resp2

    with patch("urllib.request.urlopen", side_effect=[mock_resp1, mock_resp2]) as mock_open:
        results = fetch_all_countries(api_key="dummy_key", limit=100)
        assert len(results) == 102
        assert mock_open.call_count == 2


def test_fetch_all_countries_handles_http_error():
    err_body = b'{"errors":[{"message":"Forbidden"}]}'
    http_err = urllib.error.HTTPError(
        url="https://api.restcountries.com",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=io.BytesIO(err_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError, match="HTTP 403"):
            fetch_all_countries(api_key="bad_key")


def test_save_countries_json(tmp_path: Path):
    target = tmp_path / "subdir" / "countries.json"
    data = [
        {"name": "Zimbabwe", "country_code": "ZW"},
        {"name": "Australia", "country_code": "AU"},
    ]
    save_countries_json(target, data)
    assert target.exists()

    with open(target, encoding="utf-8") as f:
        loaded = json.load(f)
    # Check that entries are sorted alphabetically by name
    assert loaded[0]["name"] == "Australia"
    assert loaded[1]["name"] == "Zimbabwe"


def test_main_fails_without_api_key(monkeypatch):
    monkeypatch.delenv("REST_COUNTRIES_API_KEY", raising=False)
    with patch("sys.argv", ["fetch_country_profiles.py", "--api-key", ""]):
        exit_code = main()
        assert exit_code == 1


def test_main_dry_run_does_not_write_file(tmp_path: Path, sample_raw_country):
    target = tmp_path / "countries.json"
    mock_page = {"data": {"objects": [sample_raw_country]}}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_page).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch(
            "sys.argv",
            [
                "fetch_country_profiles.py",
                "--api-key",
                "test-key",
                "--output",
                str(target),
                "--dry-run",
            ],
        ):
            exit_code = main()
            assert exit_code == 0
            assert not target.exists()
