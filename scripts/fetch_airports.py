"""Phase 1 — Airport ingestion.

Downloads ``airports.csv`` from the davidmegginson/ourairports-data GitHub
repository, filters for commercially-served airports that have an IATA code,
and writes the result to ``data/static/airports.json``.

Usage::

    uv run python scripts/fetch_airports.py

If the network request fails and a previous ``airports.json`` already exists,
the existing file is preserved and the error is logged.  No existing data is
ever silently deleted.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_URL = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "static" / "airports.json"

# Only retain airports that offer scheduled commercial passenger service and
# have an IATA code.  "large_airport" and "medium_airport" are the two OurAirports
# types that carry scheduled commercial traffic relevant to travel planning.
ALLOWED_TYPES = {"large_airport", "medium_airport"}

# Required CSV columns that must be present in the source file.
REQUIRED_COLUMNS = {
    "type",
    "name",
    "latitude_deg",
    "longitude_deg",
    "iso_country",
    "municipality",
    "scheduled_service",
    "iata_code",
}

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public helpers (importable by tests)
# ---------------------------------------------------------------------------


def parse_airports(csv_text: str) -> list[dict]:
    """Parse *csv_text* and return a list of airport dicts.

    Applies type, IATA, and scheduled-service filters.

    Args:
        csv_text: Raw CSV string as returned by the upstream source.

    Returns:
        List of airport dictionaries with the project-required fields.

    Raises:
        ValueError: If any required column is absent from the CSV header.
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    if reader.fieldnames is None:
        raise ValueError("CSV appears to be empty — no header row found.")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise ValueError(f"Source CSV is missing required columns: {sorted(missing)}")

    airports: list[dict] = []
    for row in reader:
        iata = row.get("iata_code", "").strip()
        airport_type = row.get("type", "").strip()
        scheduled = row.get("scheduled_service", "").strip().lower()

        # Apply all three filters: type, non-empty IATA, scheduled service.
        if airport_type not in ALLOWED_TYPES:
            continue
        if not iata:
            continue
        if scheduled != "yes":
            continue

        try:
            latitude = float(row["latitude_deg"])
            longitude = float(row["longitude_deg"])
        except (ValueError, KeyError):
            log.warning(
                "Skipping airport %s — invalid coordinates: lat=%r lon=%r",
                iata,
                row.get("latitude_deg"),
                row.get("longitude_deg"),
            )
            continue

        airports.append(
            {
                "iata_code": iata,
                "type": airport_type,
                "name": row["name"].strip(),
                "municipality": row.get("municipality", "").strip(),
                "iso_country": row.get("iso_country", "").strip().upper(),
                "latitude_deg": latitude,
                "longitude_deg": longitude,
            }
        )

    return airports


def fetch_csv(url: str) -> str:
    """Fetch *url* and return the body as a UTF-8 string.

    Raises:
        urllib.error.URLError: On network or HTTP failure.
    """
    log.info("Fetching %s", url)
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8")


def write_json(data: list[dict], path: Path) -> None:
    """Write *data* as pretty-printed JSON to *path*, creating directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    log.info("Wrote %d airports to %s", len(data), path)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the airport ingestion pipeline.

    Returns:
        0 on success, 1 on unrecoverable failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    try:
        csv_text = fetch_csv(SOURCE_URL)
    except (urllib.error.URLError, OSError) as exc:
        if OUTPUT_PATH.exists():
            log.warning(
                "Network fetch failed (%s). Existing %s preserved.",
                exc,
                OUTPUT_PATH,
            )
            return 0
        else:
            log.error(
                "Network fetch failed (%s) and no existing output found. Cannot continue.",
                exc,
            )
            return 1

    try:
        airports = parse_airports(csv_text)
    except ValueError as exc:
        log.error("CSV parsing failed: %s", exc)
        return 1

    if not airports:
        log.error("No airports matched the filter criteria. Output not written.")
        return 1

    write_json(airports, OUTPUT_PATH)
    log.info("Done. %d airports written.", len(airports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
