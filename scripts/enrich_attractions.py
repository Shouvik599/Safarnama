"""Generate a source-backed, static attraction catalog for planner Must-visits.

Examples::

    uv run python scripts/enrich_attractions.py --city Kyoto --country Japan \
        --country-code JP --region Kansai
    uv run python scripts/enrich_attractions.py --all --scope domestic --limit 10 --dry-run
    uv run python scripts/enrich_attractions.py --all --skip-existing --delay 1.0

The full batch uses popular Indian destinations and top cities from the generated
country directory, plus explicit overrides for curated circuit cities. Every saved
entry retains Tavily source snippets; unsupported candidates are discarded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import logging
import os
import random
import re
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.attractions import (  # noqa: E402
    AttractionCandidateBatch,
    AttractionCatalog,
    AttractionCityCoverage,
    AttractionSource,
    CuratedAttraction,
)
from src.prompts.attraction_prompts import build_attraction_enrichment_prompt  # noqa: E402

log = logging.getLogger("enrich_attractions")

COUNTRIES_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "generated_countries.json"
INDIA_PLACES_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "india_places.json"
ROUTE_SEEDS_PATH = PROJECT_ROOT / "data" / "static" / "attraction_city_seeds.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "static" / "attractions.json"
FRONTEND_CATALOG_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "attractions.json"

DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

DDG_TITLE_PATTERN = re.compile(
    r'<h2 class="result__title">.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL
)
DDG_SNIPPET_PATTERN = re.compile(
    r'<a class="result__snippet".*?>\s*(.*?)\s*</a>', re.DOTALL
)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class RateLimiter:
    """Thread-safe rate limiter enforcing requests-per-minute (RPM)."""

    def __init__(self, rpm: float = 15.0) -> None:
        self.rpm = rpm
        self.interval = 60.0 / max(0.1, rpm)
        self._lock = threading.Lock()
        self._last_call = 0.0

    def acquire(self) -> None:
        if self.rpm <= 0:
            return
        with self._lock:
            now = time.time()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self._last_call = time.time()


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value).casefold()
    text = "".join(
        character if character.isalnum() else " "
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(text.split())


def _slug(value: str) -> str:
    return "-".join(_normalized(value).split())


def collect_city_seeds(
    scope: str = "all",
    max_cities_per_country: int = 3,
) -> list[dict[str, str | None]]:
    """Collect popular India cities, international top cities, and route overrides."""
    seeds: dict[tuple[str, str], dict[str, str | None]] = {}

    def add(city: str, country: str, country_code: str, region: str | None) -> None:
        city = city.strip()
        country = country.strip()
        country_code = country_code.strip().upper()
        if not city or not country or not re.fullmatch(r"[A-Z]{2}", country_code):
            return
        if scope == "domestic" and country_code != "IN":
            return
        if scope == "international" and country_code == "IN":
            return
        key = (country_code, _normalized(city))
        seeds[key] = {
            "city": city,
            "country": country,
            "country_code": country_code,
            "region": region.strip() if region and region.strip() else None,
        }

    if scope != "international":
        india_data = _load_json(INDIA_PLACES_PATH)
        for place in india_data.get("cities", []):
            if place.get("is_popular"):
                add(place.get("name", ""), "India", "IN", place.get("state_name"))

    if scope != "domestic":
        for country in _load_json(COUNTRIES_PATH):
            if country.get("code", "").upper() == "IN":
                continue
            cities = country.get("top_cities", [])[:max_cities_per_country]
            for city in cities:
                add(city, country.get("name", ""), country.get("code", ""), None)

    if scope != "domestic" and ROUTE_SEEDS_PATH.exists():
        for route_seed in _load_json(ROUTE_SEEDS_PATH).get("seeds", []):
            add(
                route_seed.get("city", ""),
                route_seed.get("country", ""),
                route_seed.get("country_code", ""),
                route_seed.get("region"),
            )

    return sorted(
        seeds.values(),
        key=lambda seed: (str(seed["country"]), str(seed["city"])),
    )


def search_city_attractions_duckduckgo(
    city: str,
    region: str | None,
    country: str,
    max_results: int = 8,
    timeout: float = 15.0,
) -> list[dict[str, str]]:
    """Fetch DuckDuckGo HTML search results for one city without needing an API key."""
    query = f"named attractions landmarks museums temples parks in {city}, {country}"
    if region:
        query += f", {region}"
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status in (202, 403, 429):
                log.warning("DuckDuckGo returned %d (bot challenge / rate limit) for %s, %s", response.status, city, country)
                return []
            html_text = response.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        log.warning("DuckDuckGo HTTP %d for %s, %s", exc.code, city, country)
        return []
    except Exception as exc:
        log.warning("DuckDuckGo search failed for %s, %s: %s", city, country, exc)
        return []

    titles = DDG_TITLE_PATTERN.findall(html_text)
    snippets = DDG_SNIPPET_PATTERN.findall(html_text)
    results: list[dict[str, str]] = []

    for idx in range(min(len(titles), len(snippets), max_results)):
        raw_url, raw_title = titles[idx]
        clean_title = html.unescape(HTML_TAG_PATTERN.sub("", raw_title)).strip()
        clean_snippet = html.unescape(HTML_TAG_PATTERN.sub("", snippets[idx])).strip()

        actual_url = raw_url
        if "uddg=" in raw_url:
            parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
            if "uddg" in parsed_qs:
                actual_url = parsed_qs["uddg"][0]

        if actual_url.startswith("//"):
            actual_url = "https:" + actual_url

        if clean_title and clean_snippet:
            results.append(
                {
                    "title": clean_title,
                    "url": actual_url,
                    "content": clean_snippet,
                }
            )

    return results


def search_city_attractions_wikipedia(
    city: str,
    region: str | None,
    country: str,
    max_results: int = 8,
    timeout: float = 15.0,
) -> list[dict[str, str]]:
    """Fetch Wikipedia search results for a city; keyless, free, and bot-resilient."""
    query = f"tourist attractions landmarks monuments museums in {city} {country}"
    if region:
        query += f" {region}"
    encoded = urllib.parse.quote(query)
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit={max_results}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SafarnamaTravelPlanner/1.0 (contact@safarnama.local)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        search_items = data.get("query", {}).get("search", [])
        results: list[dict[str, str]] = []
        for item in search_items:
            title = str(item.get("title", "")).strip()
            raw_snippet = str(item.get("snippet", ""))
            clean_snippet = html.unescape(HTML_TAG_PATTERN.sub("", raw_snippet)).strip()
            if not title:
                continue
            wiki_slug = urllib.parse.quote(title.replace(" ", "_"))
            article_url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
            results.append(
                {
                    "title": title,
                    "url": article_url,
                    "content": f"{title} ({city}, {country}): {clean_snippet}",
                }
            )
        return results
    except Exception as exc:
        log.warning("Wikipedia search failed for %s, %s: %s", city, country, exc)
        return []


def search_city_attractions_tavily(
    city: str,
    region: str | None,
    country: str,
    api_key: str,
    max_results: int = 8,
    timeout: float = 30.0,
) -> list[dict[str, str]]:
    """Fetch Tavily result snippets for one city."""
    query = f"named attractions landmarks museums temples parks in {city}, {country}"
    if region:
        query += f", {region}"
    payload = json.dumps(
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return [
        {
            "title": str(result.get("title", "")),
            "url": str(result.get("url", "")),
            "content": str(result.get("content", "")),
        }
        for result in data.get("results", [])
        if result.get("url") and result.get("content")
    ]


def search_city_attractions(
    city: str,
    region: str | None,
    country: str,
    api_key: str | None = None,
    engine: str = "auto",
    max_results: int = 8,
) -> list[dict[str, str]]:
    """Search city attractions using Tavily, DuckDuckGo, Wikipedia, or auto fallback."""
    if engine == "wikipedia":
        return search_city_attractions_wikipedia(
            city=city, region=region, country=country, max_results=max_results
        )

    if engine == "ddg":
        ddg_results = search_city_attractions_duckduckgo(
            city=city, region=region, country=country, max_results=max_results
        )
        if ddg_results:
            return ddg_results
        log.info("DuckDuckGo returned 0 results for %s, %s; falling back to Wikipedia", city, country)
        return search_city_attractions_wikipedia(
            city=city, region=region, country=country, max_results=max_results
        )

    if engine == "tavily":
        if not api_key:
            raise ValueError("Tavily API key is required when engine is 'tavily'")
        return search_city_attractions_tavily(
            city=city, region=region, country=country, api_key=api_key, max_results=max_results
        )

    # engine == "auto"
    if api_key:
        try:
            results = search_city_attractions_tavily(
                city=city, region=region, country=country, api_key=api_key, max_results=max_results
            )
            if results:
                return results
            log.info("Tavily returned 0 results for %s, %s; trying DuckDuckGo", city, country)
        except Exception as exc:
            log.warning("Tavily search failed for %s, %s (%s); trying DuckDuckGo", city, country, exc)

    ddg_results = search_city_attractions_duckduckgo(
        city=city, region=region, country=country, max_results=max_results
    )
    if ddg_results:
        return ddg_results

    log.info("DuckDuckGo returned 0 results for %s, %s; falling back to Wikipedia", city, country)
    return search_city_attractions_wikipedia(
        city=city, region=region, country=country, max_results=max_results
    )


def build_source_backed_attractions(
    seed: dict[str, str | None],
    candidate_batch: AttractionCandidateBatch,
    search_results: list[dict[str, str]],
    retrieved_at: dt.date | None = None,
    max_attractions: int = 4,
) -> list[CuratedAttraction]:
    """Keep only candidates with an in-range citation containing name and location."""
    city = str(seed["city"])
    country = str(seed["country"])
    country_code = str(seed["country_code"])
    required_location = _normalized(city)
    country_location = _normalized(country)
    seen: set[str] = set()
    accepted: list[CuratedAttraction] = []
    date_value = retrieved_at or dt.date.today()

    for candidate in candidate_batch.attractions:
        if len(accepted) >= max_attractions:
            break
        name_key = _normalized(candidate.name)
        if not name_key or name_key in seen:
            continue

        evidence_sources: list[AttractionSource] = []
        cited_texts: list[str] = []
        for source_index in candidate.source_indexes:
            if source_index < 0 or source_index >= len(search_results):
                continue
            result = search_results[source_index]
            url = result.get("url", "")
            parsed_url = urlparse(url)
            title = result.get("title", "")
            snippet = result.get("content", "")
            source_text = _normalized(f"{title} {snippet}")
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                continue
            if name_key not in source_text:
                continue
            if required_location not in source_text and country_location not in source_text:
                continue
            evidence_sources.append(AttractionSource(title=title, url=url, snippet=snippet[:1600]))
            cited_texts.append(source_text)

        if not evidence_sources:
            continue

        attraction_id = f"{country_code}-{_slug(city)}-{_slug(candidate.name)}"
        accepted.append(
            CuratedAttraction(
                attraction_id=attraction_id,
                name=candidate.name.strip(),
                city=city,
                region=seed.get("region"),
                country=country,
                country_code=country_code,
                description=candidate.description.strip(),
                sources=evidence_sources,
                retrieved_at=date_value,
            )
        )
        seen.add(name_key)

    return accepted


def synthesize_city_attractions(
    seed: dict[str, str | None],
    search_results: list[dict[str, str]],
    gemini_api_key: str,
    preferred_model: str | None = None,
    rate_limiter: RateLimiter | None = None,
    max_retries: int = 4,
) -> AttractionCandidateBatch:
    """Use Gemini structured output over search snippets; no search means no candidates."""
    if not search_results:
        return AttractionCandidateBatch(attractions=[])

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed; run uv sync first") from exc

    prompt = build_attraction_enrichment_prompt(
        city=str(seed["city"]),
        region=seed.get("region"),
        country=str(seed["country"]),
        search_results=search_results,
    )
    models: list[str] = []
    if preferred_model:
        models.append(preferred_model)
    models.extend(model for model in DEFAULT_MODELS if model not in models)
    client = genai.Client(api_key=gemini_api_key)
    last_error: Exception | None = None

    for model in models:
        for attempt in range(max_retries):
            try:
                if rate_limiter:
                    rate_limiter.acquire()
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AttractionCandidateBatch.model_json_schema(),
                        temperature=0.1,
                    ),
                )
                if not response.text:
                    raise ValueError("Gemini returned an empty attraction response")
                return AttractionCandidateBatch.model_validate_json(response.text)
            except Exception as exc:
                last_error = exc
                err_str = str(exc).lower()
                is_rate_limit = (
                    "429" in err_str
                    or "resource_exhausted" in err_str
                    or "quota" in err_str
                    or "rate limit" in err_str
                )
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_sec = (2.0 ** attempt) * 2.0 + random.uniform(0.1, 1.0)
                    log.warning(
                        "Rate limit hit for %s on %s. Backing off for %.1fs (attempt %d/%d)...",
                        seed["city"],
                        model,
                        sleep_sec,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(sleep_sec)
                    continue
                log.warning(
                    "Gemini model %s failed for %s (attempt %d/%d): %s",
                    model,
                    seed["city"],
                    attempt + 1,
                    max_retries,
                    exc,
                )
                if not is_rate_limit:
                    break

    raise RuntimeError(f"All Gemini models failed for {seed['city']}: {last_error}")


def load_catalog(path: Path = CATALOG_PATH) -> AttractionCatalog:
    if not path.exists():
        return AttractionCatalog()
    return AttractionCatalog.model_validate(_load_json(path))


def save_catalog(catalog: AttractionCatalog) -> None:
    data = catalog.model_dump(mode="json")
    frontend_data = {
        "schema_version": data["schema_version"],
        "entries": [
            {
                key: entry[key]
                for key in (
                    "attraction_id",
                    "name",
                    "city",
                    "region",
                    "country",
                    "country_code",
                    "category",
                    "description",
                )
            }
            for entry in data["entries"]
        ],
    }
    for path, output in (
        (CATALOG_PATH, data),
        (FRONTEND_CATALOG_PATH, frontend_data),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)


def upsert_city_entries(
    catalog: AttractionCatalog,
    seed: dict[str, str | None],
    attractions: list[CuratedAttraction],
) -> AttractionCatalog:
    by_id = {entry.attraction_id: entry for entry in catalog.entries}
    by_id.update({entry.attraction_id: entry for entry in attractions})
    entries = sorted(by_id.values(), key=lambda entry: (entry.country, entry.city, entry.name))
    coverage_by_city = {
        (item.country_code, _normalized(item.city)): item for item in catalog.coverage
    }
    coverage = AttractionCityCoverage(
        city=str(seed["city"]),
        country=str(seed["country"]),
        country_code=str(seed["country_code"]),
        status="SOURCE_BACKED" if attractions else "NO_RESULTS",
        checked_at=dt.date.today(),
    )
    coverage_by_city[(coverage.country_code, _normalized(coverage.city))] = coverage
    ordered_coverage = sorted(coverage_by_city.values(), key=lambda item: (item.country, item.city))
    return AttractionCatalog(entries=entries, coverage=ordered_coverage)


def enrich_city_seed(
    seed: dict[str, str | None],
    tavily_key: str | None,
    gemini_key: str,
    model: str,
    engine: str = "auto",
    rate_limiter: RateLimiter | None = None,
) -> list[CuratedAttraction]:
    """Run search engine and Gemini for one seed and return only cited candidates."""
    results = search_city_attractions(
        city=str(seed["city"]),
        region=seed.get("region"),
        country=str(seed["country"]),
        api_key=tavily_key,
        engine=engine,
    )
    candidates = synthesize_city_attractions(
        seed=seed,
        search_results=results,
        gemini_api_key=gemini_key,
        preferred_model=model,
        rate_limiter=rate_limiter,
    )
    return build_source_backed_attractions(seed, candidates, results)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a static attraction catalog using search (Tavily/DuckDuckGo) and Gemini structured output."
        )
    )
    target = parser.add_mutually_exclusive_group(required=False)
    target.add_argument("--all", action="store_true", help="Process source-backed city seeds.")
    target.add_argument("--city", help="Process one city (requires --country and --country-code).")
    parser.add_argument(
        "--sync-frontend",
        action="store_true",
        help="Regenerate the compact frontend JSON from the canonical catalog without API calls.",
    )
    parser.add_argument("--country", help="Country for a single-city target.")
    parser.add_argument("--country-code", help="Two-letter ISO country code for --city.")
    parser.add_argument("--region", help="Optional state/province/region for --city.")
    parser.add_argument("--scope", choices=("all", "domestic", "international"), default="all")
    parser.add_argument("--max-cities-per-country", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.0, help="Pause between cities in seconds (default: 1.0).")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent lookups (default: 1 for sequential one-by-one).")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--search-engine",
        choices=("auto", "tavily", "ddg", "wikipedia"),
        default="auto",
        help="Search provider: 'auto' (Tavily -> DDG -> Wikipedia), 'tavily', 'ddg', or 'wikipedia'.",
    )
    parser.add_argument(
        "--rpm",
        type=float,
        default=15.0,
        help="Maximum requests per minute for Gemini API calls (default: 15.0 for free tier).",
    )
    parser.add_argument("--model", default=os.getenv("GEMINI_ENRICHMENT_MODEL", DEFAULT_MODELS[0]))
    parser.add_argument("--gemini-key", default=None)
    parser.add_argument("--tavily-key", default=None)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    args = _parse_args()
    if args.sync_frontend:
        if args.all or args.city:
            log.error("Use --sync-frontend separately from --all or --city.")
            return 2
        catalog = load_catalog()
        save_catalog(catalog)
        log.info(
            "Synchronized %d attraction record(s) to the frontend mirror.",
            len(catalog.entries),
        )
        return 0
    if not args.all and not args.city:
        log.error("Choose --all, --city, or --sync-frontend.")
        return 2
    gemini_key = (
        (
            args.gemini_key
            or os.getenv("GEMINI_ENRICHMENT_API_KEY", "")
            or os.getenv("GEMINI_API_KEY", "")
        )
        .strip()
        .strip("\"'")
    )
    tavily_key = (
        (
            args.tavily_key
            or os.getenv("TAVILY_VISA_ENRICHMENT_API_KEY", "")
            or os.getenv("TAVILY_API_KEY", "")
        )
        .strip()
        .strip("\"'")
    )
    if not gemini_key:
        log.error(
            "Gemini API key is required (pass --gemini-key or set GEMINI_ENRICHMENT_API_KEY / GEMINI_API_KEY)."
        )
        return 1

    if args.search_engine == "tavily" and not tavily_key:
        log.error("Tavily API key is required when using --search-engine tavily.")
        return 1

    if not tavily_key and args.search_engine == "auto":
        log.info("No Tavily key found; defaulting search engine to DuckDuckGo/Wikipedia.")

    if args.city:
        if not args.country or not args.country_code:
            log.error("--city requires --country and --country-code.")
            return 2
        seeds = [
            {
                "city": args.city,
                "country": args.country,
                "country_code": args.country_code.upper(),
                "region": args.region,
            }
        ]
    else:
        seeds = collect_city_seeds(args.scope, max(1, args.max_cities_per_country))
    catalog = load_catalog()
    if args.skip_existing:
        existing_cities = {(item.country_code, _normalized(item.city)) for item in catalog.coverage}
        existing_cities.update(
            (entry.country_code, _normalized(entry.city)) for entry in catalog.entries
        )
        seeds = [
            seed
            for seed in seeds
            if (str(seed["country_code"]), _normalized(str(seed["city"]))) not in existing_cities
        ]

    if args.limit is not None:
        seeds = seeds[: max(0, args.limit)]

    log.info(
        "Processing %d city seed(s); existing catalog has %d attractions. Search engine: %s, RPM limit: %.1f, Workers: %d",
        len(seeds),
        len(catalog.entries),
        args.search_engine,
        args.rpm,
        args.workers,
    )
    failures = 0
    worker_count = max(1, args.workers)
    rate_limiter = RateLimiter(rpm=args.rpm)

    if worker_count <= 1:
        # Sequential one-by-one execution: process, generate, and save immediately
        for index, seed in enumerate(seeds, start=1):
            city = str(seed["city"])
            country = str(seed["country"])
            log.info("[%d/%d] Processing %s, %s...", index, len(seeds), city, country)
            try:
                entries = enrich_city_seed(
                    seed=seed,
                    tavily_key=tavily_key,
                    gemini_key=gemini_key,
                    model=args.model,
                    engine=args.search_engine,
                    rate_limiter=rate_limiter,
                )
                log.info(
                    "[%d/%d] %s, %s: %d source-backed attraction(s) found.",
                    index,
                    len(seeds),
                    city,
                    country,
                    len(entries),
                )
                for entry in entries:
                    log.info("  -> %s", entry.name)

                if not args.dry_run:
                    catalog = upsert_city_entries(catalog, seed, entries)
                    save_catalog(catalog)
                    log.info("  [Saved] Catalog now has %d attractions.", len(catalog.entries))
            except Exception as exc:
                failures += 1
                log.error("[%d/%d] Failed for %s, %s: %s", index, len(seeds), city, country, exc)

            if index < len(seeds) and args.delay > 0:
                time.sleep(args.delay)
    else:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {}
            for index, seed in enumerate(seeds, start=1):
                log.info(
                    "[%d/%d] Queuing attractions in %s, %s",
                    index,
                    len(seeds),
                    seed["city"],
                    seed["country"],
                )
                future = executor.submit(
                    enrich_city_seed,
                    seed,
                    tavily_key,
                    gemini_key,
                    args.model,
                    args.search_engine,
                    rate_limiter,
                )
                futures[future] = (index, seed)
                if index < len(seeds) and args.delay > 0:
                    time.sleep(args.delay)

            for future in as_completed(futures):
                index, seed = futures[future]
                try:
                    entries = future.result()
                    log.info(
                        "[%d/%d] %s, %s: %d source-backed attraction(s).",
                        index,
                        len(seeds),
                        seed["city"],
                        seed["country"],
                        len(entries),
                    )
                    for entry in entries:
                        log.info("  %s", entry.name)
                    if not args.dry_run:
                        catalog = upsert_city_entries(catalog, seed, entries)
                        save_catalog(catalog)
                except Exception as exc:
                    failures += 1
                    log.error(
                        "[%d/%d] Failed for %s, %s: %s",
                        index,
                        len(seeds),
                        seed["city"],
                        seed["country"],
                        exc,
                    )

    log.info(
        "Finished: %d city seed(s), %d failure(s), %d catalog entries.",
        len(seeds),
        failures,
        len(catalog.entries),
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
