"""Unit tests for web_search tool (src/tools/web_search.py).

Tests multi-tier web search cascade, provider fallbacks, fixture mode,
in-memory caching, exception handling, and Pydantic response models.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from src.models.web_search import SearchResultItem, WebSearchResult
from src.tools.web_search import (
    InvalidQueryError,
    clear_web_search_cache,
    get_web_search_status,
    search_web,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure clean cache before and after every test."""
    clear_web_search_cache()
    yield
    clear_web_search_cache()


def test_invalid_query_raises_exception():
    """Test that empty or blank queries raise InvalidQueryError."""
    with pytest.raises(InvalidQueryError, match="cannot be empty"):
        search_web("")

    with pytest.raises(InvalidQueryError, match="cannot be empty"):
        search_web("   ")


def test_fixture_mode_direct():
    """Test that setting use_fixture=True returns fixture results directly."""
    result = search_web("japan visa for indian citizens", use_fixture=True)

    assert isinstance(result, WebSearchResult)
    assert result.query == "japan visa for indian citizens"
    assert result.provider_used == "fixture"
    assert result.is_fallback is True
    assert result.is_estimated is True
    assert len(result.results) > 0

    first_item = result.results[0]
    assert isinstance(first_item, SearchResultItem)
    assert "Japan" in first_item.title or "Visa" in first_item.title
    assert first_item.url.startswith("http")


def test_fixture_unmatched_query_uses_default_fallback():
    """Test that an unrecognised query in fixture mode returns default fallback results."""
    result = search_web("some random non-existent travel topic 12345", use_fixture=True)

    assert isinstance(result, WebSearchResult)
    assert result.provider_used == "fixture"
    assert len(result.results) > 0
    assert "Safarnama Offline Travel Research Baseline" in result.results[0].title


def test_tavily_search_success(monkeypatch):
    """Test successful live Tier 1 Tavily Search API call via mock HTTP."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-mock-key-123")

    mock_response_data = {
        "results": [
            {
                "title": "Japan Tourist Visa Guidelines 2026",
                "url": "https://example.com/japan-visa",
                "content": "Indian citizens can apply online for Japan short-term visa.",
                "score": 0.98,
                "published_date": "2026-02-10",
            },
            {
                "title": "VFS Global Japan Application Guide",
                "url": "https://example.com/vfs-japan",
                "content": "Checklist of documents for applying through VFS India.",
                "score": 0.89,
            },
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_response_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = search_web("japan visa for indian citizens", max_results=2)

        assert result.provider_used == "tavily"
        assert result.is_fallback is False
        assert len(result.results) == 2
        assert result.results[0].title == "Japan Tourist Visa Guidelines 2026"
        assert result.results[0].source_provider == "tavily"
        assert result.results[0].url == "https://example.com/japan-visa"

        # Verify HTTP request method and payload
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.tavily.com/search"
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["api_key"] == "tvly-mock-key-123"
        assert payload["query"] == "japan visa for indian citizens"


def test_duckduckgo_instant_answer_fallback(monkeypatch):
    """Test fallback to Tier 2 DuckDuckGo when Tavily API key is missing."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_VISA_ENRICHMENT_API_KEY", raising=False)

    mock_ddg_data = {
        "Heading": "Tokyo",
        "AbstractText": (
            "Tokyo is the capital of Japan and the world's most populous metropolitan area."
        ),
        "AbstractURL": "https://en.wikipedia.org/wiki/Tokyo",
        "RelatedTopics": [
            {
                "Text": "Shinjuku - Major commercial and administrative centre in Tokyo",
                "FirstURL": "https://en.wikipedia.org/wiki/Shinjuku",
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_ddg_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_web("Tokyo travel guide", max_results=2)

        assert result.provider_used == "duckduckgo"
        assert result.is_fallback is True
        assert len(result.results) >= 1
        assert "Tokyo" in result.results[0].title
        assert result.results[0].url == "https://en.wikipedia.org/wiki/Tokyo"


def test_firecrawl_search_fallback(monkeypatch):
    """Test fallback to Tier 3 Firecrawl API when Tavily and DuckDuckGo fail."""
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-mock-key-456")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    # Tavily fails (no key), DuckDuckGo returns empty JSON
    mock_ddg_empty = MagicMock()
    mock_ddg_empty.status = 200
    mock_ddg_empty.read.return_value = json.dumps({}).encode("utf-8")
    mock_ddg_empty.__enter__.return_value = mock_ddg_empty

    mock_firecrawl_data = {
        "success": True,
        "data": [
            {
                "title": "Firecrawl Deep Scraped Itinerary",
                "url": "https://example.com/firecrawl-result",
                "markdown": (
                    "# Tokyo 5-Day Itinerary\nDetailed day-by-day travel breakdown for visitors."
                ),
            }
        ],
    }
    mock_firecrawl_resp = MagicMock()
    mock_firecrawl_resp.status = 200
    mock_firecrawl_resp.read.return_value = json.dumps(mock_firecrawl_data).encode("utf-8")
    mock_firecrawl_resp.__enter__.return_value = mock_firecrawl_resp

    def side_effect(req, timeout=8.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "duckduckgo" in url:
            return mock_ddg_empty
        if "firecrawl" in url:
            return mock_firecrawl_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("urllib.request.urlopen", side_effect=side_effect):
        result = search_web("tokyo 5-day itinerary", max_results=1)

        assert result.provider_used == "firecrawl"
        assert result.is_fallback is True
        assert len(result.results) == 1
        assert result.results[0].title == "Firecrawl Deep Scraped Itinerary"
        assert "Tokyo 5-Day Itinerary" in result.results[0].snippet


def test_all_live_providers_fail_falls_back_to_offline_fixture(monkeypatch):
    """Test that if all live providers fail/throw errors, tool falls back to local fixture."""
    monkeypatch.setenv("TAVILY_API_KEY", "invalid-key")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "invalid-key")

    with patch("urllib.request.urlopen", side_effect=OSError("Network Connection Refused")):
        result = search_web("japan visa for indian citizens")

        assert result.provider_used == "fixture"
        assert result.is_fallback is True
        assert result.is_estimated is True
        assert len(result.results) > 0


def test_in_memory_cache_behavior():
    """Test that identical queries hit the in-memory cache on subsequent calls."""
    res1 = search_web("japan visa for indian citizens", use_fixture=True)
    assert res1.provider_used == "fixture"

    # Second call should return cached object
    res2 = search_web("japan visa for indian citizens", use_fixture=True)
    assert res2 is res1

    # Clearing cache should force new fetch
    clear_web_search_cache()
    res3 = search_web("japan visa for indian citizens", use_fixture=True)
    assert res3 is not res1


def test_get_web_search_status(monkeypatch):
    """Test operational status reporting helper."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")

    status = get_web_search_status()

    assert status["tavily_configured"] is True
    assert status["duckduckgo_configured"] is True
    assert status["firecrawl_configured"] is True
    assert status["fixture_available"] is True
