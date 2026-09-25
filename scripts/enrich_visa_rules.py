"""On-demand visa-rule enrichment script.

Reads a destination's baseline record from ``data/static/visa_rules.json``
(populated by ``scripts/fetch_visa_rules.py``), performs live web research
via the Tavily API, and synthesizes a fully structured, multi-option enriched
visa record using Google Gemini with native JSON schema enforcement.

Includes automatic model fallback:
    If the primary Gemini model encounters rate limits (429) or transient
    ``gemini-3.5-flash-lite`` -> ``gemini-3.8-flash`` ->
    ``gemini-2.5-flash-lite`` -> ``gemini-2.5-flash``

Enriched records are written to a **separate file**:
  ``data/static/visa_rules_enriched.json``

This keeps the two files decoupled:
- ``visa_rules.json``          — overwritten freely by ``fetch_visa_rules.py``
- ``visa_rules_enriched.json`` — built up incrementally by this script

Usage::

    # Single destination:
    uv run python scripts/enrich_visa_rules.py --destination "Japan"
    uv run python scripts/enrich_visa_rules.py --destination "Japan" --dry-run

    # Batch execution for all countries:
    uv run python scripts/enrich_visa_rules.py --all --skip-existing
    uv run python scripts/enrich_visa_rules.py --all --limit 5
    uv run python scripts/enrich_visa_rules.py --all --skip-existing --delay 2.0

Environment::

    GEMINI_ENRICHMENT_API_KEY      — Google AI API key
    TAVILY_VISA_ENRICHMENT_API_KEY — Dedicated Tavily API key for visa enrichment
    TAVILY_API_KEY                 — Fallback general Tavily search API key
    GEMINI_ENRICHMENT_MODEL        — Optional model override (default: gemini-3.5-flash-lite)
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Allow importing from src.* when run directly
sys.path.insert(0, str(PROJECT_ROOT))
from src.models.visa import EnrichedVisaRecord, VisaOption  # noqa: E402
from src.prompts.visa_prompts import build_visa_enrichment_prompt  # noqa: E402

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------

VISA_RULES_PATH = PROJECT_ROOT / "data" / "static" / "visa_rules.json"
ENRICHED_PATH = PROJECT_ROOT / "data" / "static" / "visa_rules_enriched.json"

# ---------------------------------------------------------------------------
# Model fallback chain
# ---------------------------------------------------------------------------

DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

# ---------------------------------------------------------------------------
# Static data helpers
# ---------------------------------------------------------------------------


def load_json_list(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from *path*, returning an empty list if the file is absent."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def load_visa_rules(path: Path) -> list[dict[str, Any]]:
    """Load ``visa_rules.json`` and return it as a list of dicts.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a JSON array.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Visa rules file not found: {path}. Run scripts/fetch_visa_rules.py first."
        )
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def find_destination(rules: list[dict], destination: str) -> dict[str, Any] | None:
    """Find a baseline record for *destination* (case-insensitive)."""
    dest_lower = destination.strip().lower()
    for rule in rules:
        if rule.get("destination", "").lower() == dest_lower:
            return rule
    return None


def upsert_enriched(
    records: list[dict],
    enriched: dict[str, Any],
) -> list[dict]:
    """Replace or append the enriched record in *records* by destination name."""
    dest = enriched["destination"].lower()
    for i, rec in enumerate(records):
        if rec.get("destination", "").lower() == dest:
            records[i] = enriched
            return records
    records.append(enriched)
    return records


def save_json(path: Path, data: list[dict[str, Any]]) -> None:
    """Save *data* as indented UTF-8 JSON to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    log.info("Saved %d records to %s", len(data), path)


# ---------------------------------------------------------------------------
# Tavily search helper
# ---------------------------------------------------------------------------


def fetch_tavily_search(query: str, api_key: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Fetch live web search results from Tavily Search API.

    Args:
        query: Search query string.
        api_key: Tavily API key.
        max_results: Max number of snippets to retrieve.

    Returns:
        List of result dicts with 'url', 'title', and 'content' keys.
    """
    if not api_key:
        log.warning("TAVILY_API_KEY is not set. Proceeding without live search context.")
        return []

    url = "https://api.tavily.com/search"
    payload = json.dumps(
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except Exception as exc:
        log.warning("Tavily search failed for query %r: %s", query, exc)
        return []


# ---------------------------------------------------------------------------
# Selection logic — choose the best option from the options array
# ---------------------------------------------------------------------------


def select_best_option(options: list[VisaOption]) -> VisaOption:
    """Return the most optimal entry pathway from *options*.

    Priority (ascending key = preferred):
      1. Lowest cost_inr (free is always best; None treated as high cost)
      2. Longest duration_days (None treated as 0 for sorting purposes)
      3. requires_loi=False preferred (False < True)
      4. First listed option wins ties.
    """

    def sort_key(opt: VisaOption) -> tuple:
        cost = opt.cost_inr if opt.cost_inr is not None else float("inf")
        duration = opt.duration_days if opt.duration_days is not None else 0
        return (cost, -duration, opt.requires_loi)

    return min(options, key=sort_key)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def build_enrichment_prompt(
    destination: str,
    baseline: dict[str, Any],
    search_context: str,
) -> str:
    """Build the multi-option enrichment prompt for Gemini."""
    return build_visa_enrichment_prompt(destination, baseline, search_context)


# ---------------------------------------------------------------------------
# Enrichment — Gemini synthesis with automatic fallback
# ---------------------------------------------------------------------------


def enrich_destination(
    destination: str,
    baseline: dict[str, Any],
    gemini_api_key: str,
    tavily_api_key: str = "",
    preferred_model: str | None = None,
) -> EnrichedVisaRecord:
    """Perform live web research via Tavily and synthesize via Gemini with model fallback.

    Args:
        destination: Full destination country name.
        baseline: Baseline record from visa_rules.json.
        gemini_api_key: Google AI API key.
        tavily_api_key: Tavily search API key.
        preferred_model: First Gemini model to try.

    Returns:
        An ``EnrichedVisaRecord`` with all valid pathways and optimal selected_option.

    Raises:
        RuntimeError: If all model attempts fail.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "google-genai package is not installed. Run: uv add google-genai"
        ) from exc

    # Step 1: Live web search via Tavily
    year = datetime.date.today().year
    query = f"{destination} visa requirements for Indian passport holders official {year}"
    log.info("Searching web via Tavily: %r", query)
    search_results = fetch_tavily_search(query, tavily_api_key, max_results=5)
    log.info("Retrieved %d search snippets from Tavily", len(search_results))

    if search_results:
        search_context = "\n\n".join(
            f"Source URL: {r.get('url')}\nTitle: {r.get('title')}\nSnippet: {r.get('content')}"
            for r in search_results
        )
    else:
        search_context = ""

    prompt = build_enrichment_prompt(destination, baseline, search_context)
    response_schema = EnrichedVisaRecord.model_json_schema()

    # Step 2: Build model fallback sequence
    models_to_try: list[str] = []
    if preferred_model and preferred_model.strip():
        models_to_try.append(preferred_model.strip())
    for m in DEFAULT_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    client = genai.Client(api_key=gemini_api_key)

    last_error: Exception | None = None

    for i, model_name in enumerate(models_to_try):
        log.info(
            "Calling Gemini (model %d/%d: %s) for %s...",
            i + 1,
            len(models_to_try),
            model_name,
            destination,
        )
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,
                ),
            )
            raw_text = response.text
            if not raw_text:
                raise RuntimeError("Gemini returned empty response")

            raw_dict = json.loads(raw_text)
            if not isinstance(raw_dict, dict):
                raise ValueError(f"Expected dict, got {type(raw_dict).__name__}")

            # Ensure required top-level attributes
            raw_dict.setdefault("destination", destination)
            raw_dict.setdefault("country_code", baseline.get("country_code", "??"))
            raw_dict.setdefault("last_updated", datetime.date.today().isoformat())

            enriched = EnrichedVisaRecord.model_validate(raw_dict)

            # Deterministic override of selected_option
            best = select_best_option(enriched.options)
            enriched = enriched.model_copy(update={"selected_option": best})
            log.info(
                "Enrichment succeeded via %s. selected_option -> %r "
                "(cost_inr=%s, duration_days=%s)",
                model_name,
                best.visa_type,
                best.cost_inr,
                best.duration_days,
            )
            return enriched

        except Exception as exc:
            last_error = exc
            is_last = i == len(models_to_try) - 1
            err_msg = str(exc)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                reason = "429 Rate Limit / Quota Exhausted"
            elif "503" in err_msg or "UNAVAILABLE" in err_msg:
                reason = "503 Service Temporarily Unavailable"
            elif "404" in err_msg or "NOT_FOUND" in err_msg:
                reason = "404 Model Not Found / Deprecated"
            else:
                reason = f"Error ({type(exc).__name__})"

            if not is_last:
                next_model = models_to_try[i + 1]
                log.warning(
                    "Model %s failed due to %s. Falling back to %s...",
                    model_name,
                    reason,
                    next_model,
                )
            else:
                log.error("All fallback models exhausted for %s.", destination)

    raise RuntimeError(f"All Gemini models failed for {destination!r}. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run on-demand multi-option visa rule enrichment (single destination or batch)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    parser = argparse.ArgumentParser(
        description="Enrich visa rules using Tavily web search and Gemini structured synthesis.",
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--destination",
        help="Full country name to enrich (e.g. 'Japan', 'Uzbekistan').",
    )
    target_group.add_argument(
        "--all",
        action="store_true",
        help="Enrich all destinations from data/static/visa_rules.json in batch mode.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip destinations that already exist in visa_rules_enriched.json.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of destinations to process (useful for testing batches).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay in seconds between destination requests (default: 1.5s).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"Primary Gemini model to try first (default: {DEFAULT_MODELS[0]}, "
            "or GEMINI_ENRICHMENT_MODEL env var). Falls back automatically if rate-limited."
        ),
    )
    parser.add_argument(
        "--tavily-key",
        default=None,
        help=(
            "Tavily API key override (defaults to "
            "TAVILY_VISA_ENRICHMENT_API_KEY or TAVILY_API_KEY)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the enriched record(s) but do not write to visa_rules_enriched.json.",
    )
    args = parser.parse_args()

    # Resolve API keys
    gemini_key = os.environ.get("GEMINI_ENRICHMENT_API_KEY", "").strip().strip('"').strip("'")
    if not gemini_key:
        log.error(
            "GEMINI_ENRICHMENT_API_KEY environment variable is not set. "
            "Add it to your .env file before running this script."
        )
        return 1

    raw_tavily = (
        args.tavily_key
        or os.environ.get("TAVILY_VISA_ENRICHMENT_API_KEY", "")
        or os.environ.get("TAVILY_API_KEY", "")
    )
    tavily_key = raw_tavily.strip().strip('"').strip("'")
    if not tavily_key:
        log.warning(
            "Neither TAVILY_VISA_ENRICHMENT_API_KEY nor TAVILY_API_KEY is set in .env. "
            "Web search results will not be available."
        )

    # Resolve preferred model
    raw_model = args.model or os.environ.get("GEMINI_ENRICHMENT_MODEL", DEFAULT_MODELS[0])
    preferred_model = raw_model.strip().strip('"').strip("'")

    # Load baseline from visa_rules.json
    try:
        base_rules = load_visa_rules(VISA_RULES_PATH)
    except (FileNotFoundError, ValueError) as exc:
        log.error("Failed to load visa rules: %s", exc)
        return 1

    # Load existing enriched records
    try:
        enriched_records = load_json_list(ENRICHED_PATH)
    except ValueError as exc:
        log.error("Failed to load existing enriched records: %s", exc)
        return 1

    existing_destinations = {
        r["destination"].strip().lower()
        for r in enriched_records
        if isinstance(r, dict) and "destination" in r
    }

    # Determine targets
    if args.destination:
        targets = [args.destination]
    else:
        # All destinations from base_rules
        targets = [
            rule["destination"]
            for rule in base_rules
            if isinstance(rule, dict) and "destination" in rule
        ]

    # Filter out already enriched if --skip-existing requested
    if args.skip_existing:
        original_count = len(targets)
        targets = [d for d in targets if d.strip().lower() not in existing_destinations]
        skipped_count = original_count - len(targets)
        if skipped_count > 0:
            log.info(
                "Skipping %d destinations already enriched in %s.",
                skipped_count,
                ENRICHED_PATH.name,
            )

    if args.limit is not None and args.limit > 0:
        targets = targets[: args.limit]

    if not targets:
        log.info("No destinations to process.")
        return 0

    log.info("Starting enrichment for %d destination(s)...", len(targets))

    success_count = 0
    fail_count = 0

    for idx, dest in enumerate(targets, start=1):
        log.info("[%d/%d] Enriching visa data for: %s", idx, len(targets), dest)
        baseline = find_destination(base_rules, dest)
        if baseline is None:
            baseline = {
                "destination": dest,
                "country_code": "??",
                "requirement": "UNKNOWN",
                "last_updated": datetime.date.today().isoformat(),
            }

        try:
            enriched = enrich_destination(
                destination=dest,
                baseline=baseline,
                gemini_api_key=gemini_key,
                tavily_api_key=tavily_key,
                preferred_model=preferred_model,
            )
            enriched_dict = enriched.model_dump()
            success_count += 1

            if len(targets) == 1:
                print(json.dumps(enriched_dict, indent=2, ensure_ascii=False))

            if not args.dry_run:
                # Progressive save immediately so progress is never lost
                current_records = load_json_list(ENRICHED_PATH)
                current_records = upsert_enriched(current_records, enriched_dict)
                save_json(ENRICHED_PATH, current_records)
                log.info("[%d/%d] Saved %s -> %s", idx, len(targets), dest, ENRICHED_PATH.name)
            else:
                log.info("[%d/%d] (dry-run) Enriched %s", idx, len(targets), dest)

        except Exception as exc:
            fail_count += 1
            log.error("[%d/%d] Failed to enrich %s: %s", idx, len(targets), dest, exc)

        # Delay before next request (if not last)
        if idx < len(targets) and args.delay > 0:
            time.sleep(args.delay)

    log.info(
        "Enrichment batch finished: %d succeeded, %d failed out of %d target(s).",
        success_count,
        fail_count,
        len(targets),
    )
    return 0 if fail_count == 0 else (1 if len(targets) == 1 else 0)


if __name__ == "__main__":
    sys.exit(main())
