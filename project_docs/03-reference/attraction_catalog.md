# Source-backed Attraction Catalog

## Purpose

Must-visit values are named attractions, not route cities. The picker offers only attraction records whose city is on the current route and whose country is selected for the trip. Restaurants, generic city names, and unsourced free text are not selectable.

## Data Files

- `data/static/attractions.json` is canonical. It retains source title, URL, evidence snippet, retrieval date, city/country identity, and per-city completion status.
- `frontend/src/data/attractions.json` is a compact generated projection containing only fields needed by the picker. It excludes evidence snippets to limit the frontend bundle.
- `data/static/attraction_city_seeds.json` lists route cities missing from the generated country top-city records, including Kyoto, Kanazawa, and the curated Italy route cities.

The seed builder combines 94 unique popular Indian cities, up to three top cities for each generated international country record, and curated route overrides. The current deduplicated seed set contains 677 cities across 241 country codes. It does not include all 4,198 Indian settlements.

## Generation

The one-time generator uses search results (Tavily or keyless DuckDuckGo) as evidence and Gemini structured output to extract attraction candidates. A record is saved only when at least one cited result contains the attraction name and target city or country. Candidates without source support are discarded. A successful city search with no accepted candidates is recorded as `NO_RESULTS`; failed lookups are left retryable. The runner uses bounded concurrency, an RPM-based thread-safe rate limiter, exponential backoff retries on 429 quota errors, and progressively saves each result to both files.

Environment variables:
- `GEMINI_ENRICHMENT_API_KEY` or `GEMINI_API_KEY` (required).
- `TAVILY_VISA_ENRICHMENT_API_KEY` or `TAVILY_API_KEY` (optional if using `--search-engine ddg` or when auto-falling back).

```powershell
# Run with DuckDuckGo (no Tavily key needed, paced at 15 RPM for free tier):
uv run python scripts/enrich_attractions.py --all --skip-existing --search-engine ddg --rpm 15 --workers 2

# Run with Tavily primary and DuckDuckGo fallback:
uv run python scripts/enrich_attractions.py --all --skip-existing --search-engine auto --workers 4 --delay 0.15
```

After changing or restoring only the canonical file, refresh the compact frontend projection without API calls:

```powershell
uv run python scripts/enrich_attractions.py --sync-frontend
```

Useful scoped/test runs:

```powershell
uv run python scripts/enrich_attractions.py --city Kyoto --country Japan --country-code JP --region Kansai --search-engine ddg --dry-run
uv run python scripts/enrich_attractions.py --all --scope domestic --limit 5 --search-engine ddg --dry-run
uv run python scripts/enrich_attractions.py --all --scope international --limit 5 --search-engine ddg --dry-run
```

This is an offline catalog-build step; the frontend does not call Tavily or Gemini. Ratings, hours, and prices are intentionally excluded because they change frequently.

## Frontend Contract

`getMustVisitOptions` reads the compact catalog and filters by route city, country code, and `ATTRACTION`. Route city names themselves are excluded. Selected values remain attraction-name strings to preserve the existing `PlanRequest.must_visits` contract. Preferences and Review validate the choices against the current route, flagging saved values that become out of scope after trip edits.

If no source-backed attraction exists for a route city, the picker shows no matches rather than inventing a fallback. Add seeds or rerun the resumable batch to expand coverage.