"""Phase 1 tests — Visa rules ingestion (scripts/fetch_visa_rules.py).

All tests are offline and deterministic.  They use the fixture CSVs at
``data/fixtures/visa_rules_sample.csv`` (full country names) and
``data/fixtures/visa_rules_sample_iso2.csv`` (ISO-2 codes) rather than the
live GitHub source.

Network-dependent behaviour is tested by monkeypatching ``fetch_csv``.

The ingestion script now reads from:
  https://github.com/imorte/passport-index-data  (imorte/passport-index-data)
  - passport-index-tidy.csv      (full country names)
  - passport-index-tidy-iso2.csv (ISO-2 codes, parallel rows)

Output records include: destination, country_code, requirement,
last_updated, and optionally allowed_stay_days.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Locate project root
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURE_VISA_CSV = PROJECT_ROOT / "data" / "fixtures" / "visa_rules_sample.csv"
FIXTURE_VISA_ISO2_CSV = PROJECT_ROOT / "data" / "fixtures" / "visa_rules_sample_iso2.csv"

# ---------------------------------------------------------------------------
# Import helpers from the ingestion script.
# sys.path manipulation must happen before the import, so noqa is required.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from fetch_visa_rules import (  # noqa: E402, I001
    REQUIRED_COLUMNS,
    normalise_requirement,
    parse_visa_rules,
    write_json,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _fixture_tidy_csv() -> str:
    """Return the content of the full-names fixture CSV."""
    return FIXTURE_VISA_CSV.read_text(encoding="utf-8")


def _fixture_iso2_csv() -> str:
    """Return the content of the ISO-2 fixture CSV."""
    return FIXTURE_VISA_ISO2_CSV.read_text(encoding="utf-8")


def _parse_fixture() -> list[dict]:
    """Parse both fixtures and return the joined visa rules."""
    return parse_visa_rules(_fixture_tidy_csv(), _fixture_iso2_csv())


# ---------------------------------------------------------------------------
# 1. Fixture file existence
# ---------------------------------------------------------------------------


def test_fixture_csv_exists() -> None:
    """The visa rules fixture CSV must be present for offline tests."""
    assert FIXTURE_VISA_CSV.exists(), f"Fixture file missing: {FIXTURE_VISA_CSV}."


def test_fixture_iso2_csv_exists() -> None:
    """The ISO-2 visa rules fixture CSV must be present for offline tests."""
    assert FIXTURE_VISA_ISO2_CSV.exists(), f"ISO-2 fixture file missing: {FIXTURE_VISA_ISO2_CSV}."


# ---------------------------------------------------------------------------
# 2. Required source columns present in fixtures
# ---------------------------------------------------------------------------


def test_required_columns_present_in_tidy_fixture() -> None:
    """Every required column must exist in the tidy fixture CSV header."""
    import csv
    import io

    reader = csv.DictReader(io.StringIO(_fixture_tidy_csv()))
    header = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - header
    assert not missing, f"Tidy fixture CSV is missing required columns: {sorted(missing)}"


def test_required_columns_present_in_iso2_fixture() -> None:
    """Every required column must exist in the ISO-2 fixture CSV header."""
    import csv
    import io

    reader = csv.DictReader(io.StringIO(_fixture_iso2_csv()))
    header = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - header
    assert not missing, f"ISO-2 fixture CSV is missing required columns: {sorted(missing)}"


# ---------------------------------------------------------------------------
# 3. normalise_requirement — all value types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected_req,expected_days",
    [
        ("visa free", "VISA_FREE", None),
        ("Visa Free", "VISA_FREE", None),  # case-insensitive
        ("30", "VISA_FREE", 30),
        ("60", "VISA_FREE", 60),
        ("90", "VISA_FREE", 90),
        ("14", "VISA_FREE", 14),
        ("visa on arrival", "VISA_ON_ARRIVAL", None),
        ("Visa On Arrival", "VISA_ON_ARRIVAL", None),
        ("e-visa", "E_VISA", None),
        ("E-Visa", "E_VISA", None),
        ("eta", "E_VISA", None),
        ("ETA", "E_VISA", None),
        ("visa required", "STICKER_VISA_REQUIRED", None),
        ("Visa Required", "STICKER_VISA_REQUIRED", None),
    ],
)
def test_normalise_requirement_known_values(
    raw: str, expected_req: str, expected_days: int | None
) -> None:
    """normalise_requirement must return the correct (requirement, days) tuple."""
    req, days = normalise_requirement(raw)
    assert req == expected_req, f"raw={raw!r}: expected {expected_req}, got {req}"
    assert days == expected_days, f"raw={raw!r}: expected days={expected_days}, got {days}"


def test_normalise_requirement_unknown_returns_unknown() -> None:
    """An unrecognised requirement value should return UNKNOWN, not raise."""
    req, days = normalise_requirement("some_unknown_value")
    assert req == "UNKNOWN"
    assert days is None


def test_normalise_requirement_numeric_float_string() -> None:
    """Numeric strings that represent floats (e.g. '30.0') must also work."""
    req, days = normalise_requirement("30.0")
    assert req == "VISA_FREE"
    assert days == 30


# ---------------------------------------------------------------------------
# 4. Filtering — only India rows returned
# ---------------------------------------------------------------------------


def test_parse_returns_only_india_rows() -> None:
    """parse_visa_rules must only return rows where Passport == India."""
    rules = _parse_fixture()
    # Fixture has 20 India rows + 2 Afghanistan rows
    assert len(rules) == 20


def test_parse_non_india_passports_excluded() -> None:
    """Afghanistan rows (and any other non-India passport) must be excluded."""
    rules = _parse_fixture()
    # Every rule's destination should be one of the India fixture destinations,
    # never a non-India destination sneaking in.
    destinations = {r["destination"] for r in rules}
    # Afghanistan appears only as Passport in fixture, never as a destination for India.
    # This verifies count-based exclusion (verified by count test above).
    assert len(destinations) == 20


# ---------------------------------------------------------------------------
# 5. Specific rules from the fixture
# ---------------------------------------------------------------------------


def test_nepal_is_visa_free() -> None:
    """Nepal → India should be VISA_FREE (visa free string in fixture)."""
    rules = _parse_fixture()
    nepal = next((r for r in rules if r["destination"] == "Nepal"), None)
    assert nepal is not None
    assert nepal["requirement"] == "VISA_FREE"
    assert "allowed_stay_days" not in nepal  # "visa free" has no numeric days


def test_nepal_has_country_code() -> None:
    """Nepal rule must include the ISO-2 country code 'NP'."""
    rules = _parse_fixture()
    nepal = next((r for r in rules if r["destination"] == "Nepal"), None)
    assert nepal is not None
    assert nepal["country_code"] == "NP"


def test_maldives_visa_free_with_days() -> None:
    """Maldives → India should be VISA_FREE with allowed_stay_days == 90."""
    rules = _parse_fixture()
    maldives = next((r for r in rules if r["destination"] == "Maldives"), None)
    assert maldives is not None
    assert maldives["requirement"] == "VISA_FREE"
    assert maldives.get("allowed_stay_days") == 90
    assert maldives["country_code"] == "MV"


def test_thailand_is_visa_on_arrival() -> None:
    rules = _parse_fixture()
    thailand = next((r for r in rules if r["destination"] == "Thailand"), None)
    assert thailand is not None
    assert thailand["requirement"] == "VISA_ON_ARRIVAL"
    assert thailand["country_code"] == "TH"


def test_sri_lanka_is_e_visa() -> None:
    rules = _parse_fixture()
    sl = next((r for r in rules if r["destination"] == "Sri Lanka"), None)
    assert sl is not None
    assert sl["requirement"] == "E_VISA"
    assert sl["country_code"] == "LK"


def test_new_zealand_eta_mapped_to_e_visa() -> None:
    """ETA must be normalised to E_VISA."""
    rules = _parse_fixture()
    nz = next((r for r in rules if r["destination"] == "New Zealand"), None)
    assert nz is not None
    assert nz["requirement"] == "E_VISA"
    assert nz["country_code"] == "NZ"


def test_uk_is_sticker_visa_required() -> None:
    rules = _parse_fixture()
    uk = next((r for r in rules if r["destination"] == "United Kingdom"), None)
    assert uk is not None
    assert uk["requirement"] == "STICKER_VISA_REQUIRED"
    assert uk["country_code"] == "GB"


def test_malaysia_visa_free_with_days() -> None:
    """Malaysia → India should be VISA_FREE with allowed_stay_days == 30."""
    rules = _parse_fixture()
    my = next((r for r in rules if r["destination"] == "Malaysia"), None)
    assert my is not None
    assert my["requirement"] == "VISA_FREE"
    assert my.get("allowed_stay_days") == 30
    assert my["country_code"] == "MY"


# ---------------------------------------------------------------------------
# 6. Output field structure
# ---------------------------------------------------------------------------


def test_output_contains_required_fields() -> None:
    """Each rule dict must have 'destination', 'country_code', 'requirement', 'last_updated'."""
    rules = _parse_fixture()
    for rule in rules:
        assert "destination" in rule, f"Missing 'destination' in: {rule}"
        assert "country_code" in rule, f"Missing 'country_code' in: {rule}"
        assert "requirement" in rule, f"Missing 'requirement' in: {rule}"
        assert "last_updated" in rule, f"Missing 'last_updated' in: {rule}"


def test_country_code_is_two_letter_string() -> None:
    """country_code must be a 2-character uppercase string for all rules."""
    rules = _parse_fixture()
    for rule in rules:
        code = rule["country_code"]
        assert isinstance(code, str), f"country_code is not a string: {rule}"
        assert len(code) == 2, f"country_code not 2 chars: {code!r} in {rule}"
        assert code == code.upper(), f"country_code not uppercase: {code!r} in {rule}"


def test_last_updated_is_iso_date() -> None:
    """last_updated must be a valid ISO-8601 date (YYYY-MM-DD)."""
    import datetime

    rules = _parse_fixture()
    for rule in rules:
        date_str = rule["last_updated"]
        # Should parse without error
        parsed = datetime.date.fromisoformat(date_str)
        assert parsed is not None, f"Invalid last_updated date: {date_str!r}"


def test_allowed_stay_days_only_present_when_numeric() -> None:
    """allowed_stay_days must only appear when the source value was numeric."""
    rules = _parse_fixture()
    for rule in rules:
        if rule["requirement"] == "VISA_FREE":
            # allowed_stay_days may or may not be present
            if "allowed_stay_days" in rule:
                assert isinstance(rule["allowed_stay_days"], int)
        elif rule["requirement"] in {"VISA_ON_ARRIVAL", "E_VISA", "STICKER_VISA_REQUIRED"}:
            assert "allowed_stay_days" not in rule, (
                f"Unexpected allowed_stay_days for {rule['requirement']}: {rule}"
            )


def test_requirement_values_are_valid_enum() -> None:
    """All requirement values in output must be from the expected set."""
    valid_values = {"VISA_FREE", "VISA_ON_ARRIVAL", "E_VISA", "STICKER_VISA_REQUIRED", "UNKNOWN"}
    rules = _parse_fixture()
    for rule in rules:
        assert rule["requirement"] in valid_values, (
            f"Unexpected requirement: {rule['requirement']!r} in {rule}"
        )


# ---------------------------------------------------------------------------
# 7. Missing / invalid source data handling
# ---------------------------------------------------------------------------


def test_parse_raises_on_missing_required_column_in_tidy() -> None:
    """parse_visa_rules must raise ValueError when a required column is absent in tidy CSV."""
    bad_tidy = "Passport,Requirement\nIndia,visa on arrival\n"
    with pytest.raises(ValueError, match="missing required columns"):
        parse_visa_rules(bad_tidy, _fixture_iso2_csv())


def test_parse_raises_on_missing_required_column_in_iso2() -> None:
    """parse_visa_rules must raise ValueError when a required column is absent in iso2 CSV."""
    bad_iso2 = "Passport,Requirement\nIN,visa on arrival\n"
    with pytest.raises(ValueError, match="missing required columns"):
        parse_visa_rules(_fixture_tidy_csv(), bad_iso2)


def test_parse_raises_on_empty_tidy_csv() -> None:
    """parse_visa_rules must raise ValueError when the tidy CSV has no header."""
    with pytest.raises(ValueError, match="empty"):
        parse_visa_rules("", _fixture_iso2_csv())


def test_parse_raises_on_empty_iso2_csv() -> None:
    """parse_visa_rules must raise ValueError when the iso2 CSV has no header."""
    with pytest.raises(ValueError, match="empty"):
        parse_visa_rules(_fixture_tidy_csv(), "")


def test_parse_raises_on_row_count_mismatch() -> None:
    """parse_visa_rules must raise ValueError when the two CSVs have different India row counts."""
    # tidy has 20 India rows; this iso2 has only 1
    short_iso2 = "Passport,Destination,Requirement\nIN,NP,visa free\n"
    with pytest.raises(ValueError, match="Row count mismatch"):
        parse_visa_rules(_fixture_tidy_csv(), short_iso2)


def test_parse_returns_empty_for_no_india_rows() -> None:
    """If no rows match India in either CSV, return an empty list (not an error)."""
    no_india_tidy = "Passport,Destination,Requirement\nAfghanistan,Nepal,visa on arrival\n"
    no_india_iso2 = "Passport,Destination,Requirement\nAF,NP,visa on arrival\n"
    rules = parse_visa_rules(no_india_tidy, no_india_iso2)
    assert rules == []


def test_custom_run_date_reflected_in_output() -> None:
    """A custom run_date should appear in every record's last_updated field."""
    custom_date = "2026-01-15"
    tidy = "Passport,Destination,Requirement\nIndia,Nepal,visa free\n"
    iso2 = "Passport,Destination,Requirement\nIN,NP,visa free\n"
    rules = parse_visa_rules(tidy, iso2, run_date=custom_date)
    assert len(rules) == 1
    assert rules[0]["last_updated"] == custom_date


# ---------------------------------------------------------------------------
# 8. JSON output — write_json / re-run safety
# ---------------------------------------------------------------------------


def test_write_json_creates_valid_json(tmp_path: Path) -> None:
    """write_json must produce a file that round-trips through json.load."""
    rules = _parse_fixture()
    out = tmp_path / "visa_rules.json"
    write_json(rules, out)
    assert out.exists()
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert isinstance(loaded, list)
    assert len(loaded) == len(rules)


def test_write_json_creates_parent_dirs(tmp_path: Path) -> None:
    """write_json must create any missing parent directories."""
    rules = _parse_fixture()
    out = tmp_path / "nested" / "visa_rules.json"
    write_json(rules, out)
    assert out.exists()


def test_write_json_safe_rerun(tmp_path: Path) -> None:
    """Running write_json twice must overwrite cleanly without error."""
    rules = _parse_fixture()
    out = tmp_path / "visa_rules.json"
    write_json(rules, out)
    write_json(rules, out)  # second run
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert len(loaded) == len(rules)


def test_json_output_ends_with_newline(tmp_path: Path) -> None:
    """The JSON file must end with a newline (UNIX convention)."""
    rules = _parse_fixture()
    out = tmp_path / "visa_rules.json"
    write_json(rules, out)
    content = out.read_text(encoding="utf-8")
    assert content.endswith("\n"), "JSON output must end with a newline."


def test_json_records_contain_country_code(tmp_path: Path) -> None:
    """Written JSON records must include the country_code field."""
    rules = _parse_fixture()
    out = tmp_path / "visa_rules.json"
    write_json(rules, out)
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    for record in loaded:
        assert "country_code" in record, f"country_code missing from written record: {record}"


# ---------------------------------------------------------------------------
# 9. Network failure — existing data preserved
# ---------------------------------------------------------------------------


def test_main_preserves_existing_on_network_failure(tmp_path: Path, monkeypatch) -> None:
    """If the network fetch fails and visa_rules.json already exists, keep it."""
    import urllib.error

    from fetch_visa_rules import main

    sentinel = [
        {
            "destination": "Nepal",
            "country_code": "NP",
            "requirement": "VISA_FREE",
            "last_updated": "2026-01-01",
        }
    ]
    output_path = tmp_path / "visa_rules.json"
    with open(output_path, "w") as fh:
        json.dump(sentinel, fh)

    monkeypatch.setattr("fetch_visa_rules.OUTPUT_PATH", output_path)

    def _fail_fetch(url: str) -> str:
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("fetch_visa_rules.fetch_csv", _fail_fetch)

    result = main()

    assert result == 0
    with open(output_path, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert loaded == sentinel


def test_main_returns_error_when_no_existing_data_and_network_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """If the network fails and no visa_rules.json exists, main() must return 1."""
    import urllib.error

    from fetch_visa_rules import main

    output_path = tmp_path / "visa_rules.json"
    monkeypatch.setattr("fetch_visa_rules.OUTPUT_PATH", output_path)

    def _fail_fetch(url: str) -> str:
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("fetch_visa_rules.fetch_csv", _fail_fetch)

    result = main()
    assert result == 1
    assert not output_path.exists()


def test_main_success_path(tmp_path: Path, monkeypatch) -> None:
    """main() should return 0 and write visa_rules.json when fetch succeeds."""
    from fetch_visa_rules import main

    output_path = tmp_path / "visa_rules.json"
    monkeypatch.setattr("fetch_visa_rules.OUTPUT_PATH", output_path)

    call_count = {"n": 0}

    def _mock_fetch(url: str) -> str:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _fixture_tidy_csv()
        return _fixture_iso2_csv()

    monkeypatch.setattr("fetch_visa_rules.fetch_csv", _mock_fetch)

    result = main()

    assert result == 0
    assert output_path.exists()
    with open(output_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert len(data) >= 1
    # Verify new schema fields
    assert "country_code" in data[0]
    assert "last_updated" in data[0]
