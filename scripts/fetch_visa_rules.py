"""Phase 1 — Visa rules ingestion (updated source).

Downloads two parallel CSV files from the imorte/passport-index-data GitHub
repository:

  * ``passport-index-tidy.csv``       — full country names
    (Passport, Destination, Requirement)
  * ``passport-index-tidy-iso2.csv``  — ISO 3166-1 alpha-2 codes
    (Passport, Destination, Requirement)

Both files have **identical row ordering** (one row per passport×destination
pair). We join them positionally, filter for Indian passport rows, normalise
the Requirement field, and write the result to ``data/static/visa_rules.json``.

The enriched base record now includes:

  ``destination``   — full country name from the tidy CSV
  ``country_code``  — ISO-2 destination code from the iso2 CSV
  ``requirement``   — normalised requirement enum
  ``last_updated``  — ISO-8601 date of the ingestion run

This is a **static baseline only** — not authoritative current visa truth.
Live verification (e.g. via ``enrich_visa_rules.py``) will override this when
a destination is queried at runtime.

Usage::

    uv run python scripts/fetch_visa_rules.py

If the network request fails and a previous ``visa_rules.json`` already exists,
the existing file is preserved and the error is logged.  No existing data is
ever silently deleted.

Requirement taxonomy
--------------------
Source value                 → Normalised value
-------------------------------------------------
numeric string (e.g. "30")   → VISA_FREE  (allowed_stay_days set)
"visa free"                  → VISA_FREE
"visa on arrival"            → VISA_ON_ARRIVAL
"e-visa"                     → E_VISA
"eta"                        → E_VISA  (Electronic Travel Authority)
"visa required"              → STICKER_VISA_REQUIRED
any other / unknown          → UNKNOWN  (preserved, flagged)
"""

from __future__ import annotations

import csv
import datetime
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

# New source: imorte/passport-index-data (updated regularly, includes ISO codes)
_BASE_URL = "https://raw.githubusercontent.com/imorte/passport-index-data/main"

SOURCE_URL_TIDY = f"{_BASE_URL}/passport-index-tidy.csv"
SOURCE_URL_ISO2 = f"{_BASE_URL}/passport-index-tidy-iso2.csv"

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "static" / "visa_rules.json"

# The passport country name as it appears in the full-name tidy CSV.
INDIA_PASSPORT_NAME = "India"

# The ISO-2 code for India as it appears in the iso2 tidy CSV.
INDIA_PASSPORT_ISO2 = "IN"

# Required CSV columns that must be present in the source files.
REQUIRED_COLUMNS = {"Passport", "Destination", "Requirement"}

# ---------------------------------------------------------------------------
# Normalisation map for the Requirement field.
# Numeric values (str that parse as int/float) represent visa-free days.
# ---------------------------------------------------------------------------

_REQUIREMENT_MAP: dict[str, str] = {
    "visa free": "VISA_FREE",
    "visa on arrival": "VISA_ON_ARRIVAL",
    "e-visa": "E_VISA",
    "eta": "E_VISA",  # Electronic Travel Authority is functionally e-visa
    "visa required": "STICKER_VISA_REQUIRED",
}

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public helpers (importable by tests)
# ---------------------------------------------------------------------------


def normalise_requirement(raw: str) -> tuple[str, int | None]:
    """Normalise a raw ``Requirement`` value.

    Args:
        raw: The raw string from the CSV (e.g. ``"30"``, ``"visa on arrival"``).

    Returns:
        A ``(requirement, allowed_stay_days)`` tuple where:

        - ``requirement`` is one of ``VISA_FREE``, ``VISA_ON_ARRIVAL``,
          ``E_VISA``, ``STICKER_VISA_REQUIRED``, or ``UNKNOWN``.
        - ``allowed_stay_days`` is an integer when *raw* is numeric, otherwise
          ``None``.
    """
    stripped = raw.strip()

    # Numeric → visa-free with a known stay duration.
    try:
        days = int(float(stripped))
        return "VISA_FREE", days
    except ValueError:
        pass

    normalised = _REQUIREMENT_MAP.get(stripped.lower())
    if normalised is not None:
        return normalised, None

    log.warning("Unrecognised requirement value: %r — storing as UNKNOWN", stripped)
    return "UNKNOWN", None


def parse_visa_rules(
    tidy_csv_text: str,
    iso2_csv_text: str,
    run_date: str | None = None,
) -> list[dict]:
    """Parse the two parallel CSV texts and return visa rules for the Indian passport.

    Args:
        tidy_csv_text: Raw CSV string from passport-index-tidy.csv (full names).
        iso2_csv_text: Raw CSV string from passport-index-tidy-iso2.csv (ISO-2 codes).
        run_date: ISO-8601 date string for the ``last_updated`` field.
                  Defaults to today's date (``YYYY-MM-DD``).

    Returns:
        List of visa-rule dictionaries with ``destination``, ``country_code``,
        ``requirement``, and optionally ``allowed_stay_days`` / ``last_updated``.

    Raises:
        ValueError: If any required column is absent from either CSV header,
                    or if the two CSVs have different row counts for India.
    """
    if run_date is None:
        run_date = datetime.date.today().isoformat()

    tidy_rows = _read_india_rows(tidy_csv_text, passport_col_value=INDIA_PASSPORT_NAME)
    iso2_rows = _read_india_rows(iso2_csv_text, passport_col_value=INDIA_PASSPORT_ISO2)

    if len(tidy_rows) != len(iso2_rows):
        raise ValueError(
            f"Row count mismatch between tidy ({len(tidy_rows)}) and "
            f"iso2 ({len(iso2_rows)}) CSV files. Cannot safely join."
        )

    rules: list[dict] = []
    for tidy_row, iso2_row in zip(tidy_rows, iso2_rows):
        destination = tidy_row["Destination"].strip()
        country_code = iso2_row["Destination"].strip()
        raw_req = tidy_row["Requirement"].strip()

        if not destination or not raw_req or not country_code:
            log.warning(
                "Skipping row with empty destination, country_code, or requirement: %r",
                tidy_row,
            )
            continue

        requirement, allowed_stay_days = normalise_requirement(raw_req)

        record: dict = {
            "destination": destination,
            "country_code": country_code,
            "requirement": requirement,
            "last_updated": run_date,
        }
        if allowed_stay_days is not None:
            record["allowed_stay_days"] = allowed_stay_days

        rules.append(record)

    return rules


def _read_india_rows(csv_text: str, passport_col_value: str) -> list[dict]:
    """Parse a CSV text and return only rows matching *passport_col_value*.

    Args:
        csv_text: Raw CSV string.
        passport_col_value: The value to filter on in the ``Passport`` column.

    Returns:
        List of raw row dicts (unprocessed).

    Raises:
        ValueError: If required columns are missing or CSV is empty.
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    if reader.fieldnames is None:
        raise ValueError("CSV appears to be empty — no header row found.")

    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise ValueError(f"Source CSV is missing required columns: {sorted(missing)}")

    rows = []
    for row in reader:
        passport = row.get("Passport", "").strip()
        if passport != passport_col_value:
            continue
        rows.append(row)

    return rows


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
    log.info("Wrote %d visa rules to %s", len(data), path)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the visa-rules ingestion pipeline.

    Returns:
        0 on success, 1 on unrecoverable failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Fetch both CSVs; preserve existing file if either fetch fails.
    try:
        tidy_text = fetch_csv(SOURCE_URL_TIDY)
    except (urllib.error.URLError, OSError) as exc:
        if OUTPUT_PATH.exists():
            log.warning(
                "Network fetch failed for tidy CSV (%s). Existing %s preserved.",
                exc,
                OUTPUT_PATH,
            )
            return 0
        else:
            log.error(
                "Network fetch failed for tidy CSV (%s) and no existing output found. "
                "Cannot continue.",
                exc,
            )
            return 1

    try:
        iso2_text = fetch_csv(SOURCE_URL_ISO2)
    except (urllib.error.URLError, OSError) as exc:
        if OUTPUT_PATH.exists():
            log.warning(
                "Network fetch failed for iso2 CSV (%s). Existing %s preserved.",
                exc,
                OUTPUT_PATH,
            )
            return 0
        else:
            log.error(
                "Network fetch failed for iso2 CSV (%s) and no existing output found. "
                "Cannot continue.",
                exc,
            )
            return 1

    try:
        rules = parse_visa_rules(tidy_text, iso2_text)
    except ValueError as exc:
        log.error("CSV parsing failed: %s", exc)
        return 1

    if not rules:
        log.error(
            "No visa rules found for passport %r. Output not written.",
            INDIA_PASSPORT_NAME,
        )
        return 1

    write_json(rules, OUTPUT_PATH)
    log.info("Done. %d visa rules written.", len(rules))
    return 0


if __name__ == "__main__":
    sys.exit(main())
