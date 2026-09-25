"""Pydantic domain models for web search functionality.

Provides structured, validated contracts for individual search result items and
aggregated search query results consumed by Phase 3 tools, Visa research nodes,
Experience nodes, and general web inquiry utilities.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Structured result item from a web search query."""

    title: str = Field(description="Title of the search result webpage.")
    url: str = Field(description="Destination URL of the search result.")
    snippet: str = Field(description="Extracted summary, content snippet, or markdown text.")
    source_provider: str = Field(
        description="Provider name: 'tavily', 'duckduckgo', 'firecrawl', or 'fixture'."
    )
    score: float | None = Field(
        default=None, description="Relevance score if provided by the search engine."
    )
    published_date: str | None = Field(
        default=None, description="Publication date string if available."
    )


class WebSearchResult(BaseModel):
    """Aggregated web search result for a query across multi-tier search providers."""

    query: str = Field(description="Original search query string.")
    results: list[SearchResultItem] = Field(
        default_factory=list, description="Ordered list of search result items."
    )
    provider_used: str = Field(
        description=(
            "Provider that answered the query: 'tavily', 'duckduckgo', 'firecrawl', or 'fixture'."
        )
    )
    total_results: int = Field(default=0, description="Total number of result items returned.")
    is_fallback: bool = Field(
        default=False,
        description="True if a secondary provider or local fixture fallback was used.",
    )
    is_estimated: bool = Field(
        default=False,
        description="True if derived from offline fixture fallback dataset.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this search result was retrieved.")
