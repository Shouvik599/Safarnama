"""Phase 1 — Country profile metadata ingestion.

Fetches normalized country metadata from the REST Countries v5 API
(https://restcountries.com), transforms raw country objects into canonical
``CountryProfile`` structures, and writes the output to:

    ``data/static/countries.json``

The enriched dataset provides foundational geographic, currency, language,
timezone, driving, and regional bloc (e.g. Schengen) metadata consumed by
Phase 2 static data tools (``src/tools/static_data.py``) and downstream
planning agents.

Usage::

    uv run python scripts/fetch_country_profiles.py
    uv run python scripts/fetch_country_profiles.py --dry-run
    uv run python scripts/fetch_country_profiles.py --api-key "YOUR_KEY"

Environment::

    REST_COUNTRIES_API_KEY — REST Countries v5 Bearer API key from .env
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Allow importing from src.* when run directly
sys.path.insert(0, str(PROJECT_ROOT))
from src.models.country import CountryProfile  # noqa: E402

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = "https://api.restcountries.com/countries/v5"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "static" / "countries.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safarnama/1.0"
PAGE_LIMIT = 100


# ---------------------------------------------------------------------------
# Transformation logic
# ---------------------------------------------------------------------------


def parse_country_record(raw: dict[str, Any], today_str: str) -> dict[str, Any]:
    """Transform a raw REST Countries v5 object into a canonical CountryProfile dict.

    Handles optional/missing fields gracefully for dependent territories
    and special regions.
    """
    names = raw.get("names") or {}
    codes = raw.get("codes") or {}
    flag = raw.get("flag") or {}
    cars = raw.get("cars") or {}
    memberships = raw.get("memberships") or {}

    # Country codes
    country_code = str(codes.get("alpha_2") or "").strip().upper()
    country_code_alpha3 = str(codes.get("alpha_3") or "").strip().upper()

    # Country names
    name = str(names.get("common") or "").strip()
    official_name = str(names.get("official") or name).strip()

    # Capital and coordinates
    capital_name: str | None = None
    capital_coords: dict[str, float] | None = None
    raw_capitals = raw.get("capitals") or []
    if raw_capitals and isinstance(raw_capitals, list):
        # Prefer capital marked primary, else first capital
        chosen_cap = next(
            (
                c
                for c in raw_capitals
                if isinstance(c, dict) and c.get("attributes", {}).get("primary")
            ),
            raw_capitals[0] if isinstance(raw_capitals[0], dict) else {},
        )
        if isinstance(chosen_cap, dict):
            cap_name = chosen_cap.get("name")
            if cap_name:
                capital_name = str(cap_name).strip()
            coords = chosen_cap.get("coordinates")
            if (
                isinstance(coords, dict)
                and coords.get("lat") is not None
                and coords.get("lng") is not None
            ):
                capital_coords = {"lat": float(coords["lat"]), "lng": float(coords["lng"])}

    # Currencies
    currencies: list[dict[str, str]] = []
    for cur in raw.get("currencies") or []:
        if isinstance(cur, dict) and cur.get("code"):
            currencies.append(
                {
                    "code": str(cur["code"]).strip().upper(),
                    "name": str(cur.get("name") or cur["code"]).strip(),
                    "symbol": str(cur.get("symbol") or "").strip(),
                }
            )

    # Languages
    languages: list[dict[str, str]] = []
    for lang in raw.get("languages") or []:
        if isinstance(lang, dict) and lang.get("name"):
            code = lang.get("bcp47") or lang.get("iso639_1") or lang.get("iso639_2b") or ""
            languages.append(
                {
                    "code": str(code).strip(),
                    "name": str(lang["name"]).strip(),
                }
            )

    # Timezones
    raw_tzs = raw.get("timezones") or []
    timezones = [str(tz).strip() for tz in raw_tzs if str(tz).strip()]

    # Driving side
    driving_side: str | None = cars.get("side")
    if driving_side:
        driving_side = str(driving_side).strip().lower()

    # Calling codes
    calling_code: str | None = None
    calling_codes_list = raw.get("calling_codes") or []
    if calling_codes_list and str(calling_codes_list[0]).strip():
        cc_val = str(calling_codes_list[0]).strip().lstrip("+")
        calling_code = f"+{cc_val}"

    # Borders
    raw_borders = raw.get("borders") or []
    borders = [str(b).strip().upper() for b in raw_borders if str(b).strip()]

    # Region / Subregion
    region = str(raw.get("region") or "Unknown").strip()
    subregion = raw.get("subregion")
    if subregion:
        subregion = str(subregion).strip()

    # Flag emoji
    flag_emoji = flag.get("emoji")
    if flag_emoji:
        flag_emoji = str(flag_emoji).strip()

    # Regional memberships
    is_schengen = bool(memberships.get("schengen", False))
    is_eu = bool(memberships.get("eu", False))

    profile_dict = {
        "country_code": country_code,
        "country_code_alpha3": country_code_alpha3,
        "name": name,
        "official_name": official_name,
        "capital": capital_name,
        "capital_coordinates": capital_coords,
        "region": region,
        "subregion": subregion,
        "currencies": currencies,
        "languages": languages,
        "timezones": timezones,
        "driving_side": driving_side,
        "calling_code": calling_code,
        "flag_emoji": flag_emoji,
        "is_schengen": is_schengen,
        "is_eu": is_eu,
        "borders": borders,
        "last_updated": today_str,
    }

    # Validate against CountryProfile contract
    validated = CountryProfile.model_validate(profile_dict)
    return validated.model_dump()


# ---------------------------------------------------------------------------
# Network & Ingestion
# ---------------------------------------------------------------------------


def fetch_all_countries(api_key: str, limit: int = PAGE_LIMIT) -> list[dict[str, Any]]:
    """Fetch all country objects from REST Countries v5 across paginated batches."""
    all_raw_objects: list[dict[str, Any]] = []
    offset = 0

    while True:
        url = f"{API_BASE_URL}?limit={limit}&offset={offset}"
        log.info("Fetching page: offset=%d limit=%d", offset, limit)

        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"REST Countries API request failed (HTTP {exc.code}): {err_body}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Network error querying REST Countries API: {exc}") from exc

        objects = data.get("data", {}).get("objects", [])
        if not objects:
            break

        all_raw_objects.extend(objects)
        log.info("Received %d countries (total so far: %d)", len(objects), len(all_raw_objects))

        if len(objects) < limit:
            break
        offset += limit

    return all_raw_objects


def save_countries_json(path: Path, data: list[dict[str, Any]]) -> None:
    """Save the country profiles to disk in sorted, indented JSON format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_data = sorted(data, key=lambda c: c["name"].lower())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Fetch country profiles from REST Countries and save to static JSON."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    parser = argparse.ArgumentParser(
        description="Ingest country metadata profiles from REST Countries v5 API.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="REST Countries API key override (defaults to REST_COUNTRIES_API_KEY in .env).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Target output file path (default: {DEFAULT_OUTPUT_PATH}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate records without writing to the output JSON file.",
    )
    args = parser.parse_args()

    # Resolve API Key
    raw_key = args.api_key or os.environ.get("REST_COUNTRIES_API_KEY", "")
    api_key = raw_key.strip().strip('"').strip("'")
    if not api_key:
        log.error(
            "REST_COUNTRIES_API_KEY environment variable is not set. "
            "Please add it to your .env file or pass via --api-key."
        )
        return 1

    out_path = Path(args.output)
    today_str = datetime.date.today().isoformat()

    log.info("Starting REST Countries v5 ingestion...")
    try:
        raw_objects = fetch_all_countries(api_key=api_key)
    except RuntimeError as exc:
        log.error("Ingestion failed: %s", exc)
        if out_path.exists():
            log.info("Existing %s is preserved and unchanged.", out_path.name)
        return 1

    if not raw_objects:
        log.error("API returned 0 country objects. Aborting without modifying disk.")
        return 1

    # Transform and validate
    transformed: list[dict[str, Any]] = []
    errors = 0
    for obj in raw_objects:
        try:
            profile = parse_country_record(obj, today_str)
            # Skip records without valid alpha-2 code (e.g. unknown territories)
            if profile["country_code"] and len(profile["country_code"]) == 2:
                transformed.append(profile)
        except Exception as exc:
            errors += 1
            log.warning("Validation failed for record: %s", exc)

    log.info(
        "Successfully transformed and validated %d country profiles (%d errors).",
        len(transformed),
        errors,
    )

    if args.dry_run:
        log.info("--dry-run specified: skipping write to %s", out_path)
        return 0

    save_countries_json(out_path, transformed)
    log.info("Saved %d country profiles to %s", len(transformed), out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
