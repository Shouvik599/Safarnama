"""Pydantic domain models for visa rule data.

Two model families live here:

**Data-ingestion models** — used by ingestion scripts and Phase 2 tools:

``VisaOption`` / ``EnrichedVisaRecord``
    Used by ``scripts/enrich_visa_rules.py`` for the Gemini-enriched,
    multi-option visa records written to ``data/static/visa_rules_enriched.json``.

``BaseVisaRule``
    Baseline entry rule from the static Passport Index dataset.

**Planning domain models** — used by the Visa Node and planning graph:

``VisaRequirementStatus``
    Enum capturing the final visa requirement classification for a destination.

``VisaCountryVerdict``
    Visa verdict for a single destination country.

``VisaVerdict``
    Top-level aggregate visa verdict for the full trip (covering all
    international destinations), produced by the Visa Node.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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


# ---------------------------------------------------------------------------
# Planning domain models — Visa Node output contracts
# ---------------------------------------------------------------------------


class VisaRequirementStatus(StrEnum):
    """Final visa requirement classification for a destination country.

    VISA_FREE
        Indian passport holders may enter without any visa formality.
    VISA_ON_ARRIVAL
        Visa can be obtained at the port of entry.
    E_VISA
        Electronic visa must be obtained online before departure.
    STICKER_VISA_REQUIRED
        A traditional sticker/paper visa must be obtained at the embassy/consulate.
    CONDITIONAL_FREE
        Entry is free under certain conditions (e.g. specific ports only, limited duration).
    RESTRICTED
        Entry is heavily restricted or not permitted for Indian passport holders.
    UNKNOWN
        Visa status could not be reliably determined; manual verification required.
    DOMESTIC_BYPASS
        Domestic trip — no visa processing required (set when scope is DOMESTIC).
    """

    VISA_FREE = "VISA_FREE"
    VISA_ON_ARRIVAL = "VISA_ON_ARRIVAL"
    E_VISA = "E_VISA"
    STICKER_VISA_REQUIRED = "STICKER_VISA_REQUIRED"
    CONDITIONAL_FREE = "CONDITIONAL_FREE"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"
    DOMESTIC_BYPASS = "DOMESTIC_BYPASS"


class VisaCountryVerdict(BaseModel):
    """Visa verdict for a single destination country.

    Produced by the Visa Node after reconciling the static baseline rule with
    live web search verification. The fallback LLM must NOT invent requirements;
    if live verification fails, the static baseline is used with a warning.
    """

    model_config = ConfigDict(frozen=True)

    country_name: str = Field(description="Full English destination country name.")
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code (uppercase).")
    status: VisaRequirementStatus = Field(description="Final visa requirement classification.")

    # Best available pathway details
    visa_type_label: str | None = Field(
        default=None,
        description=(
            "Human-readable label for the selected pathway, "
            "e.g. 'Visa-Free Entry (30 Days)', 'Tourist e-Visa'."
        ),
    )
    permitted_stay_days: int | None = Field(
        default=None,
        ge=1,
        description="Maximum permitted stay in days under the recommended pathway.",
    )
    visa_fee_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated visa/processing fee per person in INR (0.0 if free).",
    )

    # Documentation and application
    required_documents: list[str] = Field(
        default_factory=list,
        description=(
            "Key required documents (e.g. ['Valid passport', 'Return ticket', "
            "'Hotel booking proof', 'Travel insurance'])."
        ),
    )
    application_process: str | None = Field(
        default=None,
        description=(
            "Brief description of how/where to apply "
            "(e.g. 'Apply online at evisa.example.gov 7–30 days before travel')."
        ),
    )
    processing_time_days: str | None = Field(
        default=None,
        description="Typical processing time, e.g. '3–5 business days', 'Immediate on arrival'.",
    )
    entry_conditions: list[str] = Field(
        default_factory=list,
        description=(
            "Important entry requirements beyond the visa, "
            "e.g. ['Onward ticket required', 'Sufficient funds proof']."
        ),
    )

    # Data quality
    data_source: str = Field(
        default="STATIC_DATASET",
        description=(
            "Provenance of this verdict: 'STATIC_DATASET', 'LIVE_VERIFIED', "
            "'LIVE_UNVERIFIED', or 'FIXTURE'."
        ),
    )
    is_live_verified: bool = Field(
        default=False,
        description="True if this verdict was confirmed/updated via live web search.",
    )
    confidence: str = Field(
        default="MEDIUM",
        description="Confidence level in the verdict: 'HIGH', 'MEDIUM', or 'LOW'.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Specific warnings for this country, "
            "e.g. 'Policy changed recently — verify before travel', "
            "'Live verification failed; using static baseline'."
        ),
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Reference URLs for the visa policy information.",
    )
    last_verified: str | None = Field(
        default=None,
        description="ISO 8601 date when this verdict was last verified (YYYY-MM-DD).",
    )


class VisaVerdict(BaseModel):
    """Top-level aggregate visa verdict for the full trip.

    Covers all international destination countries. Produced by the Visa Node
    and carried in the LangGraph planning state.

    For domestic trips, ``is_domestic_bypass`` is True and ``countries`` is empty.
    """

    model_config = ConfigDict(frozen=True)

    is_domestic_bypass: bool = Field(
        default=False,
        description="True when the trip is domestic and visa processing was skipped.",
    )
    countries: list[VisaCountryVerdict] = Field(
        default_factory=list,
        description=(
            "Visa verdicts for each destination country in the trip. Empty for domestic trips."
        ),
    )

    # Aggregate totals
    total_visa_cost_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total estimated visa fees across all travelers and all countries in INR.",
    )
    requires_advance_application: bool = Field(
        default=False,
        description=(
            "True if any destination requires an advance visa application "
            "(i.e. not visa-free or on-arrival)."
        ),
    )

    # Schengen optimisation flag
    schengen_single_visa_applicable: bool = Field(
        default=False,
        description=(
            "True if all Schengen destinations can be covered under a single Schengen visa "
            "(i.e. traveler is visiting multiple Schengen countries and one visa suffices)."
        ),
    )

    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Trip-level visa warnings, "
            "e.g. 'Live verification failed for 1 destination; verify manually', "
            "'Visa required for UZ — apply at least 7 days before departure'."
        ),
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this visa verdict was generated.")
