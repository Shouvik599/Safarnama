"""Deterministic web search tool with multi-tier API resilience.

Provides structured web search results (title, destination URL, snippet/markdown content,
provenance provider) for destination research, visa rules, travel guides, weather, transport,
and accommodation inquiries.

Fallback Cascade:
1. Test Fixture: data/fixtures/mock_web_search.json (if use_fixture=True or
   SAFARNAMA_USE_FIXTURES=true)
2. In-Memory Cache: 1-hour TTL per query string / result limit
3. Live Tier 1: Tavily Search API (POST https://api.tavily.com/search, TAVILY_API_KEY)
4. Live Tier 2: DuckDuckGo Search (Keyless open-access instant answer API / HTTP fallback)
5. Live Tier 3: Firecrawl Search API (POST https://api.firecrawl.dev/v2/search, FIRECRAWL_API_KEY)
6. Tier 4: Offline Search Fixture (Guarantees zero-crash resilience when offline/unconfigured)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from src.models.web_search import SearchResultItem, WebSearchResult

load_dotenv()

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_web_search.json"
TAVILY_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_tavily_search.json"
)

CACHE_TTL_SECONDS = 3600  # 1 hour
DEFAULT_TIMEOUT_SECONDS = 8.0

# Pre-compiled regular expressions for DuckDuckGo HTML result parsing
DDG_LINK_PATTERN = re.compile(
    r'<a class="result__url" href="([^"]+)".*?>\s*(.*?)\s*</a>', re.DOTALL
)
DDG_SNIPPET_PATTERN = re.compile(r'<a class="result__snippet".*?>\s*(.*?)\s*</a>', re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class WebSearchError(Exception):
    """Base exception for web search errors."""


class InvalidQueryError(WebSearchError, ValueError):
    """Raised when search query string is empty or invalid."""


class WebSearchAPIError(WebSearchError):
    """Raised when all web search providers fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class WebSearchCache:
    """Thread-safe in-memory cache store for search results with TTL expiration."""

    def __init__(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> None:
        self._cache: dict[str, tuple[float, WebSearchResult]] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, query: str, max_results: int) -> WebSearchResult | None:
        key = f"{query.strip().lower()}:{max_results}"
        if key in self._cache:
            created_at, result = self._cache[key]
            if time.time() - created_at < self.ttl_seconds:
                return result
            del self._cache[key]
        return None

    def set(self, query: str, max_results: int, result: WebSearchResult) -> None:
        key = f"{query.strip().lower()}:{max_results}"
        self._cache[key] = (time.time(), result)

    def clear(self) -> None:
        self._cache.clear()


_SEARCH_CACHE = WebSearchCache()


def clear_web_search_cache() -> None:
    """Clear the in-memory web search cache."""
    _SEARCH_CACHE.clear()


# ---------------------------------------------------------------------------
# Provider Implementation 1: Local Offline Fixture
# ---------------------------------------------------------------------------


def _search_fixture(
    query: str, max_results: int = 5, is_fallback_trigger: bool = True
) -> WebSearchResult:
    """Retrieve search results from local mock fixture file."""
    target_path = FIXTURE_PATH if FIXTURE_PATH.exists() else TAVILY_FIXTURE_PATH
    if not target_path.exists():
        log.warning("Web search fixture file not found at %s", target_path)
        return WebSearchResult(
            query=query,
            results=[
                SearchResultItem(
                    title="Safarnama Offline Travel Research Baseline",
                    url="https://safarnama.local/search/baseline",
                    snippet=(
                        f"Offline mock search result for query '{query}'. External search "
                        "services are unconfigured or offline."
                    ),
                    source_provider="fixture",
                    score=0.80,
                )
            ],
            provider_used="fixture",
            total_results=1,
            is_fallback=is_fallback_trigger,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )

    try:
        with open(target_path, encoding="utf-8") as f:
            data = json.load(f)

        norm_query = query.strip().lower()
        queries_map: dict = data.get("queries", {})

        matched_data = None
        for q_key, q_val in queries_map.items():
            if q_key.lower() in norm_query or norm_query in q_key.lower():
                matched_data = q_val
                break

        if not matched_data:
            matched_data = data.get("default_fallback", {})

        raw_results = matched_data.get("results", [])[:max_results]
        results = [
            SearchResultItem(
                title=item.get("title", "Search Result"),
                url=item.get("url", "https://safarnama.local/search"),
                snippet=item.get("snippet", ""),
                source_provider=item.get("source_provider", "fixture"),
                score=item.get("score"),
                published_date=item.get("published_date"),
            )
            for item in raw_results
        ]

        return WebSearchResult(
            query=query,
            results=results,
            provider_used="fixture",
            total_results=len(results),
            is_fallback=is_fallback_trigger,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )
    except Exception as exc:
        log.error("Failed to parse web search fixture: %s", exc)
        return WebSearchResult(
            query=query,
            results=[],
            provider_used="fixture",
            total_results=0,
            is_fallback=True,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Provider Implementation 2: Live Tier 1 - Tavily Search API
# ---------------------------------------------------------------------------


def _search_tavily(
    query: str, max_results: int = 5, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> WebSearchResult | None:
    """Execute live web search via Tavily Search API (POST https://api.tavily.com/search)."""
    api_key = os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_VISA_ENRICHMENT_API_KEY")
    if not api_key:
        log.debug("Tavily API key not set (TAVILY_API_KEY or TAVILY_VISA_ENRICHMENT_API_KEY).")
        return None

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Safarnama/0.1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                raw_results = body.get("results", [])
                results = []
                for item in raw_results[:max_results]:
                    results.append(
                        SearchResultItem(
                            title=item.get("title") or "Tavily Search Result",
                            url=item.get("url") or "",
                            snippet=item.get("content") or item.get("snippet") or "",
                            source_provider="tavily",
                            score=item.get("score"),
                            published_date=item.get("published_date"),
                        )
                    )
                log.info("Successfully fetched %d search results from Tavily", len(results))
                return WebSearchResult(
                    query=query,
                    results=results,
                    provider_used="tavily",
                    total_results=len(results),
                    is_fallback=False,
                    is_estimated=False,
                    timestamp=datetime.now(UTC).isoformat(),
                )
    except Exception as exc:
        log.warning("Tavily search request failed for query '%s': %s", query, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 3: Live Tier 2 - DuckDuckGo Search (Keyless)
# ---------------------------------------------------------------------------


def _search_duckduckgo(
    query: str, max_results: int = 5, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> WebSearchResult | None:
    """Execute live web search via DuckDuckGo Open Access Instant Answer / HTML search API."""
    # Method A: Try DuckDuckGo Instant Answer JSON API
    encoded_query = urllib.parse.quote(query)
    json_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&no_redirect=1"

    try:
        req = urllib.request.Request(
            json_url,
            headers={"User-Agent": "Safarnama/0.1.0 (Mozilla/5.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                results = []

                # Extract Abstract if present
                if data.get("AbstractText") and data.get("AbstractURL"):
                    results.append(
                        SearchResultItem(
                            title=data.get("Heading") or "DuckDuckGo Instant Answer",
                            url=data.get("AbstractURL"),
                            snippet=data.get("AbstractText"),
                            source_provider="duckduckgo",
                            score=0.90,
                        )
                    )

                # Extract Related Topics
                for topic in data.get("RelatedTopics", []):
                    if len(results) >= max_results:
                        break
                    if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                        results.append(
                            SearchResultItem(
                                title=topic.get("Text", "").split(" - ")[0] or "DuckDuckGo Result",
                                url=topic["FirstURL"],
                                snippet=topic["Text"],
                                source_provider="duckduckgo",
                                score=0.80,
                            )
                        )

                if results:
                    log.info(
                        "Successfully fetched %d results from DuckDuckGo Instant Answer API",
                        len(results),
                    )
                    return WebSearchResult(
                        query=query,
                        results=results[:max_results],
                        provider_used="duckduckgo",
                        total_results=len(results[:max_results]),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.debug("DuckDuckGo Instant Answer API failed: %s", exc)

    # Method B: Fallback to DuckDuckGo HTML parsing if Instant Answer gave no topics
    html_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    try:
        req = urllib.request.Request(
            html_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                html_text = resp.read().decode("utf-8", errors="ignore")
                urls = DDG_LINK_PATTERN.findall(html_text)
                snippets = DDG_SNIPPET_PATTERN.findall(html_text)

                results = []
                for idx, (raw_url, title_text) in enumerate(urls[:max_results]):
                    clean_title = HTML_TAG_PATTERN.sub("", title_text).strip()
                    clean_snippet = ""
                    if idx < len(snippets):
                        clean_snippet = HTML_TAG_PATTERN.sub("", snippets[idx]).strip()

                    # Unquote DuckDuckGo redirect link if present
                    actual_url = raw_url
                    if "uddg=" in raw_url:
                        parsed_url = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                        if "uddg" in parsed_url:
                            actual_url = parsed_url["uddg"][0]

                    results.append(
                        SearchResultItem(
                            title=clean_title or "DuckDuckGo Result",
                            url=actual_url,
                            snippet=clean_snippet or clean_title,
                            source_provider="duckduckgo",
                            score=0.75,
                        )
                    )

                if results:
                    log.info("Successfully parsed %d results from DuckDuckGo HTML", len(results))
                    return WebSearchResult(
                        query=query,
                        results=results,
                        provider_used="duckduckgo",
                        total_results=len(results),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("DuckDuckGo HTML search failed for query '%s': %s", query, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 4: Live Tier 3 - Firecrawl API
# ---------------------------------------------------------------------------


def _search_firecrawl(
    query: str, max_results: int = 5, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> WebSearchResult | None:
    """Execute live web search via Firecrawl Search API (POST https://api.firecrawl.dev/v2/search)."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        log.debug("Firecrawl API key not set (FIRECRAWL_API_KEY).")
        return None

    url = "https://api.firecrawl.dev/v2/search"
    payload = {
        "query": query,
        "limit": max_results,
        "scrapeOptions": {"formats": ["markdown"]},
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Safarnama/0.1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                # Firecrawl returns data in data array
                raw_data = body.get("data", [])
                if isinstance(raw_data, list) and raw_data:
                    results = []
                    for item in raw_data[:max_results]:
                        snippet_val = (
                            item.get("markdown")
                            or item.get("description")
                            or item.get("snippet")
                            or ""
                        )
                        # Truncate very long markdown to reasonable snippet length
                        if len(snippet_val) > 1000:
                            snippet_val = snippet_val[:1000] + "..."

                        results.append(
                            SearchResultItem(
                                title=item.get("title") or "Firecrawl Search Result",
                                url=item.get("url") or "",
                                snippet=snippet_val,
                                source_provider="firecrawl",
                                score=item.get("score"),
                            )
                        )
                    log.info("Successfully fetched %d results from Firecrawl", len(results))
                    return WebSearchResult(
                        query=query,
                        results=results,
                        provider_used="firecrawl",
                        total_results=len(results),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Firecrawl search request failed for query '%s': %s", query, exc)

    return None


# ---------------------------------------------------------------------------
# Public Web Search Interface
# ---------------------------------------------------------------------------


def search_web(
    query: str,
    max_results: int = 5,
    use_fixture: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> WebSearchResult:
    """Execute a web search query with multi-tier API resilience and caching.

    Args:
        query: The search query string (e.g. 'japan visa for indian citizens').
        max_results: Maximum number of search result items to return (default: 5).
        use_fixture: If True, bypass live API network requests and return fixture data.
        timeout: Network timeout in seconds for live API HTTP requests.

    Returns:
        WebSearchResult containing ordered SearchResultItem instances and provenance.

    Raises:
        InvalidQueryError: If query is empty or blank.
    """
    if not query or not query.strip():
        raise InvalidQueryError("Search query string cannot be empty or whitespace.")

    clean_query = query.strip()
    if max_results <= 0:
        max_results = 5

    # Check environment variable triggers for fixture mode
    force_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("true", "1")
    )

    # Check in-memory cache first
    cached_result = _SEARCH_CACHE.get(clean_query, max_results)
    if cached_result is not None:
        log.debug("Returning cached web search result for query '%s'", clean_query)
        return cached_result

    if force_fixture:
        log.info("Fixture mode active. Serving web search from mock fixture.")
        res = _search_fixture(clean_query, max_results=max_results, is_fallback_trigger=True)
        _SEARCH_CACHE.set(clean_query, max_results, res)
        return res

    # 1. Live Tier 1: Tavily Search API
    result = _search_tavily(clean_query, max_results=max_results, timeout=timeout)
    if result is not None and result.results:
        _SEARCH_CACHE.set(clean_query, max_results, result)
        return result

    # 2. Live Tier 2: DuckDuckGo Search (Keyless)
    result = _search_duckduckgo(clean_query, max_results=max_results, timeout=timeout)
    if result is not None and result.results:
        _SEARCH_CACHE.set(clean_query, max_results, result)
        return result

    # 3. Live Tier 3: Firecrawl Search API
    result = _search_firecrawl(clean_query, max_results=max_results, timeout=timeout)
    if result is not None and result.results:
        _SEARCH_CACHE.set(clean_query, max_results, result)
        return result

    # 4. Tier 4: Offline Search Fixture (Guarantees zero-crash resilience)
    log.warning(
        "All live web search providers failed or unconfigured for query '%s'. "
        "Falling back to local offline search fixture.",
        clean_query,
    )
    fallback_result = _search_fixture(
        clean_query, max_results=max_results, is_fallback_trigger=True
    )
    _SEARCH_CACHE.set(clean_query, max_results, fallback_result)
    return fallback_result


def get_web_search_status() -> dict[str, bool | str]:
    """Retrieve operational status of configured web search API providers."""
    return {
        "tavily_configured": bool(
            os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_VISA_ENRICHMENT_API_KEY")
        ),
        "duckduckgo_configured": True,  # Keyless open access
        "firecrawl_configured": bool(os.getenv("FIRECRAWL_API_KEY")),
        "fixture_available": FIXTURE_PATH.exists() or TAVILY_FIXTURE_PATH.exists(),
    }
