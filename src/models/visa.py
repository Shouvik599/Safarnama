"""Pydantic domain models for visa rule data.

Two model families live here:

``VisaOption`` / ``EnrichedVisaRecord``
    Used by ``scripts/enrich_visa_rules.py`` for the Gemini-enriched,
    multi-option visa records written to ``data/static/visa_rules_enriched.json``.

These are the canonical, importable contracts shared between the enrichment
script and Phase 2 runtime tools (``src/tools/static_data.py``, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VisaOption(BaseModel):
    """A single legal entry pathway for Indian passport holders."""

    visa_type: str = Field(
        description=(
            "Short, human-readable label for this pathway, e.g. "
            "'Visa-Free Entry (30 Days)', 'Tourist e-Visa (Single Entry)'."
        )
    )
    duration_days: int | None = Field(
        default=None,
        description="Maximum permitted stay in days. Null if unlimited or unclear.",
    )
    cost_inr: float = Field(
        description=(
            "Approximate visa/processing fee in Indian Rupees (INR). "
            "Use 0.0 for free options. Convert from USD/EUR at a reasonable "
            "current rate if the official fee is in foreign currency."
        )
    )
    entry_type: str = Field(
        description=(
            "Entry classification. One of: VISA_FREE, CONDITIONAL_FREE, "
            "VISA_ON_ARRIVAL, E_VISA, STICKER_VISA_REQUIRED, UNKNOWN."
        )
    )
    entry_port_restriction: str | None = Field(
        default=None,
        description=(
            "If entry is only permitted through specific ports/airports, "
            "describe the restriction here. Null if no restriction."
        ),
    )
    requires_loi: bool = Field(
        description="True if a Letter of Invitation (LOI) is mandatory for this pathway."
    )
    notes: str | None = Field(
        default=None,
        description=(
            "Brief factual note about special conditions, recent policy changes, "
            "temporary pilots, or important caveats. Null if no note is needed."
        ),
    )
    source: list[str] = Field(
        description=(
            "List of URL strings for the official or credible sources that "
            "confirm this pathway. Must be non-empty."
        )
    )


class EnrichedVisaRecord(BaseModel):
    """Fully enriched visa record for a single destination country.

    Captures all currently valid legal entry pathways in ``options`` and
    designates the most favourable active pathway in ``selected_option``.
    Written to ``data/static/visa_rules_enriched.json`` by
    ``scripts/enrich_visa_rules.py``.
    """

    destination: str = Field(description="Full English country name.")
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code (uppercase).")
    last_updated: str = Field(description="ISO-8601 date of this enrichment run (YYYY-MM-DD).")
    options: list[VisaOption] = Field(
        description=(
            "All currently valid legal entry pathways for Indian passport holders. "
            "Must contain at least one option. Include ALL overlapping or "
            "alternative routes (e.g. a new visa-free regime that coexists with "
            "a legacy e-visa option)."
        )
    )
    selected_option: VisaOption = Field(
        description=(
            "The single most optimal, currently active pathway. "
            "Must be one of the entries in the options array. "
            "Prefer lowest cost, longest duration, fewest restrictions."
        )
    )


class BaseVisaRule(BaseModel):
    """Baseline entry rule for Indian passport holders from static Passport Index data."""

    destination: str = Field(description="Full country or destination name.")
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code (uppercase).")
    requirement: str = Field(
        description=(
            "Normalised requirement enum (e.g. VISA_FREE, VISA_ON_ARRIVAL, "
            "E_VISA, STICKER_VISA_REQUIRED, UNKNOWN)."
        )
    )
    last_updated: str = Field(description="ISO-8601 date of the ingestion run (YYYY-MM-DD).")
    allowed_stay_days: int | None = Field(
        default=None, description="Permitted stay in days if visa-free, else None."
    )
