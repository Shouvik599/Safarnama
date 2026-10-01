"""Tests for the static attraction catalog contracts and enrichment filters."""

from __future__ import annotations

import json
from datetime import date

import pytest
import scripts.enrich_attractions as enrichment
from pydantic import ValidationError
from scripts.enrich_attractions import (
    build_source_backed_attractions,
    collect_city_seeds,
    upsert_city_entries,
)
from src.models.attractions import (
    AttractionCandidate,
    AttractionCandidateBatch,
    AttractionCatalog,
    AttractionSource,
    CuratedAttraction,
)


def test_curated_attraction_requires_city_scope_and_source_evidence():
    attraction = CuratedAttraction(
        attraction_id="IN-jaipur-hawa-mahal",
        name="Hawa Mahal",
        city="Jaipur",
        region="Rajasthan",
        country="India",
        country_code="IN",
        description="A historic palace known for its distinctive facade.",
        sources=[
            AttractionSource(
                title="Hawa Mahal visitor information",
                url="https://tourism.example.org/hawa-mahal",
                snippet="Hawa Mahal is a palace in Jaipur, Rajasthan, India.",
            )
        ],
        retrieved_at=date(2026, 9, 29),
    )

    catalog = AttractionCatalog(entries=[attraction])

    assert catalog.entries[0].category == "ATTRACTION"
    assert catalog.entries[0].city == "Jaipur"
    assert str(catalog.entries[0].sources[0].url) == "https://tourism.example.org/hawa-mahal"


def test_curated_attraction_rejects_missing_sources_and_invalid_country_code():
    with pytest.raises(ValidationError):
        CuratedAttraction(
            attraction_id="JP-kyoto-kinkakuji",
            name="Kinkaku-ji",
            city="Kyoto",
            country="Japan",
            country_code="JPN",
            description="A Zen Buddhist temple in northern Kyoto.",
            sources=[],
            retrieved_at=date(2026, 9, 29),
        )


def test_seed_builder_covers_popular_indian_cities_and_curated_international_routes():
    seeds = collect_city_seeds()
    seed_keys = {(seed["country_code"], seed["city"].casefold()) for seed in seeds}

    assert ("IN", "jaipur") in seed_keys
    assert ("IN", "mysuru") in seed_keys
    assert ("JP", "kyoto") in seed_keys
    assert ("JP", "kanazawa") in seed_keys
    assert ("IT", "rome") in seed_keys
    assert ("KR", "seoul") in seed_keys
    assert len([seed for seed in seeds if seed["country_code"] == "IN"]) == 94


def test_candidate_filter_requires_cited_name_and_city_or_country_evidence():
    seed = {"city": "Kyoto", "region": "Kansai", "country": "Japan", "country_code": "JP"}
    results = [
        {
            "title": "Kinkaku-ji temple in Kyoto, Japan",
            "url": "https://example.org/kinkakuji",
            "content": "Kinkaku-ji, the Golden Pavilion, is a Zen temple in Kyoto, Japan.",
        }
    ]
    batch = AttractionCandidateBatch(
        attractions=[
            AttractionCandidate(
                name="Kinkaku-ji",
                description="A Zen temple known as the Golden Pavilion.",
                source_indexes=[0],
            ),
            AttractionCandidate(
                name="Invented Moon Palace",
                description="A famous historic palace in Kyoto.",
                source_indexes=[0],
            ),
            AttractionCandidate(
                name="Uncited Shrine",
                description="A historic shrine in Kyoto.",
                source_indexes=[5],
            ),
        ]
    )

    accepted = build_source_backed_attractions(seed, batch, results)

    assert [entry.name for entry in accepted] == ["Kinkaku-ji"]
    assert accepted[0].city == "Kyoto"
    assert str(accepted[0].sources[0].url) == "https://example.org/kinkakuji"


def test_evidence_matching_preserves_unicode_place_names():
    seed = {"city": "Kyoto", "region": "Kansai", "country": "Japan", "country_code": "JP"}
    results = [
        {
            "title": "清水寺 Kiyomizu-dera in Kyoto",
            "url": "https://example.org/kiyomizu",
            "content": "Kiyomizu-dera is a historic temple in Kyoto, Japan.",
        }
    ]
    batch = AttractionCandidateBatch(
        attractions=[
            AttractionCandidate(
                name="Kiyomizu-dera",
                description="A historic temple in Kyoto.",
                source_indexes=[0],
            )
        ]
    )

    assert len(build_source_backed_attractions(seed, batch, results)) == 1


def test_upsert_records_empty_search_coverage_for_resumable_batches():
    seed = {
        "city": "Rennes",
        "region": "Brittany",
        "country": "France",
        "country_code": "FR",
    }

    catalog = upsert_city_entries(AttractionCatalog(), seed, [])

    assert catalog.entries == []
    assert len(catalog.coverage) == 1
    assert catalog.coverage[0].status == "NO_RESULTS"
    assert catalog.coverage[0].city == "Rennes"


def test_catalog_save_keeps_evidence_canonical_and_frontend_projection_compact(
    tmp_path, monkeypatch
):
    backend_path = tmp_path / "backend-attractions.json"
    frontend_path = tmp_path / "frontend-attractions.json"
    monkeypatch.setattr(enrichment, "CATALOG_PATH", backend_path)
    monkeypatch.setattr(enrichment, "FRONTEND_CATALOG_PATH", frontend_path)
    attraction = CuratedAttraction(
        attraction_id="IN-jaipur-hawa-mahal",
        name="Hawa Mahal",
        city="Jaipur",
        region="Rajasthan",
        country="India",
        country_code="IN",
        description="A historic palace known for its distinctive facade.",
        sources=[
            AttractionSource(
                title="Hawa Mahal visitor information",
                url="https://tourism.example.org/hawa-mahal",
                snippet="Hawa Mahal is a palace in Jaipur, Rajasthan, India.",
            )
        ],
        retrieved_at=date(2026, 9, 29),
    )

    enrichment.save_catalog(AttractionCatalog(entries=[attraction]))

    backend_data = json.loads(backend_path.read_text(encoding="utf-8"))
    frontend_data = json.loads(frontend_path.read_text(encoding="utf-8"))
    assert backend_data["entries"][0]["sources"][0]["snippet"]
    assert "sources" not in frontend_data["entries"][0]
    assert frontend_data["entries"][0]["name"] == "Hawa Mahal"


def test_rate_limiter_paces_requests():
    import time
    limiter = enrichment.RateLimiter(rpm=300.0)  # 5 requests per second = 0.2s interval
    start = time.perf_counter()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.perf_counter() - start
    assert elapsed >= 0.18


def test_search_city_attractions_routes_to_ddg_when_requested(monkeypatch):
    mock_results = [{"title": "Mock Landmark", "url": "https://example.org", "content": "A mock snippet"}]
    monkeypatch.setattr(enrichment, "search_city_attractions_duckduckgo", lambda **kwargs: mock_results)

    results = enrichment.search_city_attractions(
        city="Kyoto",
        region="Kansai",
        country="Japan",
        api_key=None,
        engine="ddg",
    )
    assert results == mock_results


def test_search_city_attractions_auto_falls_back_to_ddg_on_tavily_error(monkeypatch):
    mock_results = [{"title": "DDG Fallback", "url": "https://example.org", "content": "Fallback snippet"}]

    def failing_tavily(**kwargs):
        raise RuntimeError("Tavily quota exceeded 429")

    monkeypatch.setattr(enrichment, "search_city_attractions_tavily", failing_tavily)
    monkeypatch.setattr(enrichment, "search_city_attractions_duckduckgo", lambda **kwargs: mock_results)

    results = enrichment.search_city_attractions(
        city="Jaipur",
        region="Rajasthan",
        country="India",
        api_key="mock-tavily-key",
        engine="auto",
    )
    assert results == mock_results
