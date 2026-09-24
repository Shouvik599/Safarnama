"""Phase 1 tests — Airport ingestion (scripts/fetch_airports.py).

All tests are offline and deterministic.  They use the fixture CSV at
``data/fixtures/airports_sample.csv`` rather than the live GitHub source.
Network-dependent behaviour is tested by monkeypatching ``fetch_csv``.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Locate project root so tests work regardless of CWD
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURE_AIRPORTS_CSV = PROJECT_ROOT / "data" / "fixtures" / "airports_sample.csv"

# ---------------------------------------------------------------------------
# Import the helpers from the ingestion script.
# sys.path manipulation must happen before the import, so noqa is required.
# ---------------------------------------------------------------------------

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from fetch_airports import REQUIRED_COLUMNS, parse_airports, write_json  # noqa: E402, I001


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _fixture_csv() -> str:
    """Return the content of the airports fixture CSV."""
    return FIXTURE_AIRPORTS_CSV.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Fixture file existence
# ---------------------------------------------------------------------------


def test_fixture_csv_exists() -> None:
    """The airports fixture CSV must be present for offline tests."""
    assert FIXTURE_AIRPORTS_CSV.exists(), (
        f"Fixture file missing: {FIXTURE_AIRPORTS_CSV}. "
        "Run the ingestion script at least once or recreate the fixture."
    )


# ---------------------------------------------------------------------------
# 2. Required source columns are present in the fixture
# ---------------------------------------------------------------------------


def test_required_columns_present_in_fixture() -> None:
    """Every required column must exist in the fixture CSV header."""
    import csv
    import io

    reader = csv.DictReader(io.StringIO(_fixture_csv()))
    header = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - header
    assert not missing, f"Fixture CSV is missing required columns: {sorted(missing)}"


# ---------------------------------------------------------------------------
# 3. Basic parse — correct number of valid airports returned
# ---------------------------------------------------------------------------


def test_parse_returns_only_valid_airports() -> None:
    """parse_airports should return only the filtered valid airports."""
    airports = parse_airports(_fixture_csv())
    # Fixture has 6 valid rows (3 large_airport IN + OSL + TAS + FRU)
    # Rows excluded: small_airport/no-IATA, heliport, no-IATA large, not-scheduled
    assert len(airports) == 6


def test_parse_returns_expected_iata_codes() -> None:
    """Specific IATA codes expected from the fixture must be present."""
    airports = parse_airports(_fixture_csv())
    codes = {a["iata_code"] for a in airports}
    assert "DEL" in codes
    assert "CCU" in codes
    assert "BLR" in codes
    assert "OSL" in codes
    assert "TAS" in codes
    assert "FRU" in codes


# ---------------------------------------------------------------------------
# 4. Filtering: excluded types / missing IATA / no scheduled service
# ---------------------------------------------------------------------------


def test_small_airport_excluded() -> None:
    """Airports with type == small_airport must be excluded."""
    airports = parse_airports(_fixture_csv())
    codes = {a["iata_code"] for a in airports}
    # The fixture small_airport has an empty IATA anyway, but the type filter
    # should also reject it.
    assert "" not in codes


def test_heliport_excluded() -> None:
    """Airports with type == heliport must be excluded."""
    airports = parse_airports(_fixture_csv())
    types = {a["type"] for a in airports}
    assert "heliport" not in types


def test_airport_without_iata_excluded() -> None:
    """Airports with no IATA code must be excluded."""
    airports = parse_airports(_fixture_csv())
    for a in airports:
        assert a["iata_code"], f"Empty IATA code found in: {a}"


def test_non_scheduled_airport_excluded() -> None:
    """Airports with scheduled_service != yes must be excluded."""
    # COK_NO_SCHED has scheduled_service = no in the fixture
    airports = parse_airports(_fixture_csv())
    codes = {a["iata_code"] for a in airports}
    assert "COK_NO_SCHED" not in codes


# ---------------------------------------------------------------------------
# 5. Output field structure
# ---------------------------------------------------------------------------


def test_output_contains_required_fields() -> None:
    """Each airport dict must have all required output fields."""
    required_output_fields = {
        "iata_code",
        "type",
        "name",
        "municipality",
        "iso_country",
        "latitude_deg",
        "longitude_deg",
    }
    airports = parse_airports(_fixture_csv())
    assert airports, "No airports parsed — cannot check fields."
    for airport in airports:
        missing = required_output_fields - set(airport.keys())
        assert not missing, f"Airport {airport.get('iata_code')} missing fields: {missing}"


def test_coordinates_are_floats() -> None:
    """Latitude and longitude must be Python floats."""
    airports = parse_airports(_fixture_csv())
    for a in airports:
        assert isinstance(a["latitude_deg"], float), (
            f"{a['iata_code']}: latitude_deg is {type(a['latitude_deg'])}"
        )
        assert isinstance(a["longitude_deg"], float), (
            f"{a['iata_code']}: longitude_deg is {type(a['longitude_deg'])}"
        )


def test_iso_country_is_uppercase() -> None:
    """iso_country must be stored as uppercase."""
    airports = parse_airports(_fixture_csv())
    for a in airports:
        assert a["iso_country"] == a["iso_country"].upper(), (
            f"{a['iata_code']}: iso_country not uppercase: {a['iso_country']}"
        )


def test_del_coordinates() -> None:
    """DEL should have the expected approximate coordinates."""
    airports = parse_airports(_fixture_csv())
    del_airports = [a for a in airports if a["iata_code"] == "DEL"]
    assert len(del_airports) == 1
    a = del_airports[0]
    assert abs(a["latitude_deg"] - 28.5665) < 0.01
    assert abs(a["longitude_deg"] - 77.1031) < 0.01
    assert a["iso_country"] == "IN"
    assert a["municipality"] == "New Delhi"


# ---------------------------------------------------------------------------
# 6. JSON output — write_json / re-run safety
# ---------------------------------------------------------------------------


def test_write_json_creates_valid_json(tmp_path: Path) -> None:
    """write_json must produce a file that round-trips through json.load."""
    airports = parse_airports(_fixture_csv())
    out = tmp_path / "airports.json"
    write_json(airports, out)
    assert out.exists()
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert isinstance(loaded, list)
    assert len(loaded) == len(airports)


def test_write_json_creates_parent_dirs(tmp_path: Path) -> None:
    """write_json must create any missing parent directories."""
    airports = parse_airports(_fixture_csv())
    out = tmp_path / "nested" / "deep" / "airports.json"
    write_json(airports, out)
    assert out.exists()


def test_write_json_safe_rerun(tmp_path: Path) -> None:
    """Running write_json twice must overwrite cleanly without error."""
    airports = parse_airports(_fixture_csv())
    out = tmp_path / "airports.json"
    write_json(airports, out)
    write_json(airports, out)  # second run — must not raise
    with open(out, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert len(loaded) == len(airports)


def test_json_output_ends_with_newline(tmp_path: Path) -> None:
    """The JSON file must end with a newline (UNIX convention)."""
    airports = parse_airports(_fixture_csv())
    out = tmp_path / "airports.json"
    write_json(airports, out)
    content = out.read_text(encoding="utf-8")
    assert content.endswith("\n"), "JSON output must end with a newline."


# ---------------------------------------------------------------------------
# 7. Missing / invalid source data handling
# ---------------------------------------------------------------------------


def test_parse_raises_on_missing_required_column() -> None:
    """parse_airports must raise ValueError when a required column is absent."""
    bad_csv = "type,name,latitude_deg\nlarge_airport,Foo,10.0\n"
    with pytest.raises(ValueError, match="missing required columns"):
        parse_airports(bad_csv)


def test_parse_raises_on_empty_csv() -> None:
    """parse_airports must raise ValueError when the CSV has no header."""
    with pytest.raises(ValueError, match="empty"):
        parse_airports("")


def test_parse_skips_row_with_invalid_coordinates() -> None:
    """Rows with non-numeric coordinates should be skipped, not crash."""
    bad_csv = textwrap.dedent("""\
        id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,\
iso_country,iso_region,municipality,scheduled_service,icao_code,iata_code,\
gps_code,local_code,home_link,wikipedia_link,keywords
        1,VIDP,large_airport,Test Airport,NOT_A_FLOAT,77.0,0,AS,IN,IN-DL,Delhi,yes,VIDP,DEL,VIDP,,,
    """)
    airports = parse_airports(bad_csv)
    assert airports == []


def test_parse_empty_iata_excluded() -> None:
    """Rows without an IATA code must be excluded even if all other fields are valid."""
    no_iata_csv = textwrap.dedent("""\
        id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,\
iso_country,iso_region,municipality,scheduled_service,icao_code,iata_code,\
gps_code,local_code,home_link,wikipedia_link,keywords
        1,XXXX,large_airport,No IATA,10.0,20.0,0,AS,IN,IN-DL,City,yes,XXXX,,XXXX,,,
    """)
    airports = parse_airports(no_iata_csv)
    assert airports == []


# ---------------------------------------------------------------------------
# 8. Network failure — existing data preserved (integration-level unit test)
# ---------------------------------------------------------------------------


def test_main_preserves_existing_on_network_failure(tmp_path: Path, monkeypatch) -> None:
    """If the network fetch fails and airports.json already exists, it must be kept."""
    import urllib.error

    from fetch_airports import main

    # Plant a pre-existing airports.json with sentinel content.
    sentinel = [
        {
            "iata_code": "DEL",
            "type": "large_airport",
            "name": "Test",
            "municipality": "Delhi",
            "iso_country": "IN",
            "latitude_deg": 28.5,
            "longitude_deg": 77.1,
        }
    ]
    output_path = tmp_path / "airports.json"
    with open(output_path, "w") as fh:
        json.dump(sentinel, fh)

    # Monkeypatch OUTPUT_PATH and fetch_csv so no network call is made.
    monkeypatch.setattr("fetch_airports.OUTPUT_PATH", output_path)

    def _fail_fetch(url: str) -> str:
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("fetch_airports.fetch_csv", _fail_fetch)

    result = main()

    # main() should return 0 (graceful degradation) and not destroy the file.
    assert result == 0
    with open(output_path, encoding="utf-8") as fh:
        loaded = json.load(fh)
    assert loaded == sentinel


def test_main_returns_error_when_no_existing_data_and_network_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """If the network fails and no airports.json exists, main() must return 1."""
    import urllib.error

    from fetch_airports import main

    output_path = tmp_path / "airports.json"
    monkeypatch.setattr("fetch_airports.OUTPUT_PATH", output_path)

    def _fail_fetch(url: str) -> str:
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("fetch_airports.fetch_csv", _fail_fetch)

    result = main()
    assert result == 1
    assert not output_path.exists()


def test_main_success_path(tmp_path: Path, monkeypatch) -> None:
    """main() should return 0 and write airports.json when fetch succeeds."""
    from fetch_airports import main

    output_path = tmp_path / "airports.json"
    monkeypatch.setattr("fetch_airports.OUTPUT_PATH", output_path)
    monkeypatch.setattr("fetch_airports.fetch_csv", lambda _url: _fixture_csv())

    result = main()

    assert result == 0
    assert output_path.exists()
    with open(output_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert len(data) >= 1
