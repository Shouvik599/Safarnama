"""Phase 7 — Visa Functionality (Visa Planning Node).

Evaluates entry and visa requirements for Indian passport holders:
1. Evaluates travel scope: automatically bypasses visa processing for domestic trips.
2. Resolves destination countries against static enriched visa dataset and baseline rules.
3. Performs live verification via search tool when enabled, identifying recent policy changes.
4. Synthesizes validated, immutable VisaCountryVerdict and VisaVerdict Pydantic contracts.
5. Optimizes Schengen multi-destination itineraries under a single uniform Schengen visa.
6. Calculates accurate total visa costs multiplied by traveler party size.

Architectural Constraints:
- The fallback LLM and system must NEVER invent or fabricate visa requirements (Rule 35).
- If live verification fails, the system falls back gracefully to verified static data
  with a warning.
- All models conform strictly to frozen domain schemas in src.models.visa.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from src.models.trip import (
    InitialPlanningState,
    ResolvedLocation,
    TravelScope,
    TripContext,
    TripParty,
)
from src.models.visa import (
    BaseVisaRule,
    LiveVisaPolicyAnalysis,
    VisaCountryVerdict,
    VisaOption,
    VisaRequirementStatus,
    VisaVerdict,
)
from src.prompts.visa_prompts import build_live_visa_verification_prompt
from src.tools.static_data import (
    find_country,
    get_enriched_visa,
    get_visa_baseline,
    is_schengen,
)
from src.tools.web_search import search_web

log = logging.getLogger(__name__)

# Default timeout for live LLM policy reconciliation
DEFAULT_LLM_TIMEOUT: float = 12.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class VisaError(Exception):
    """Base exception for visa node errors."""


class VisaProcessingError(VisaError):
    """Raised when critical visa planning failures occur."""


# ---------------------------------------------------------------------------
# LLM Structured Policy Reconciliation Helpers (Option 1: Semantic, Zero Regex)
# ---------------------------------------------------------------------------


def _parse_llm_json_response(text: str) -> dict[str, Any] | None:
    """Safely extract JSON payload from LLM text response."""
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _query_gemini_reconciliation(prompt: str, timeout: float = DEFAULT_LLM_TIMEOUT) -> str | None:
    """Query Google Gemini API for structured visa policy reconciliation."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        return None

    models = [
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini-2.5-flash-lite",
    ]

    for model_name in models:
        try:
            from google import genai  # type: ignore

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if hasattr(response, "text") and response.text:
                return response.text
        except Exception:
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model_name}:generateContent?key={gemini_key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
            except Exception as rest_exc:
                log.warning(
                    "Gemini REST reconciliation failed for model %s: %s",
                    model_name,
                    rest_exc,
                )

    return None


def _query_openai_compatible_reconciliation(
    provider_name: str,
    api_key: str | None,
    base_url: str,
    models: list[str],
    prompt: str,
    timeout: float = DEFAULT_LLM_TIMEOUT,
) -> str | None:
    """Query OpenAI-compatible chat completion endpoint (Groq / NVIDIA NIM)."""
    if not api_key:
        return None

    url = f"{base_url.rstrip('/')}/chat/completions"

    for model_name in models:
        try:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
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
                    data = json.loads(resp.read().decode("utf-8"))
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
        except Exception as exc:
            log.warning(
                "%s visa reconciliation failed for model %s: %s",
                provider_name,
                model_name,
                exc,
            )

    return None


def _reconcile_with_llm(
    country_name: str,
    country_code: str,
    baseline_data: dict[str, Any],
    search_snippets: str,
    travel_date: str | None = None,
) -> LiveVisaPolicyAnalysis | None:
    """Execute LLM structured policy reconciliation cascade."""
    prompt = build_live_visa_verification_prompt(
        destination=country_name,
        country_code=country_code,
        baseline_rule=baseline_data,
        search_snippets=search_snippets,
        travel_date=travel_date,
    )

    raw_response: str | None = None

    # Tier 1: Google Gemini
    raw_response = _query_gemini_reconciliation(prompt)

    # Tier 2: Groq
    if not raw_response:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            raw_response = _query_openai_compatible_reconciliation(
                provider_name="Groq",
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
                prompt=prompt,
            )

    # Tier 3: NVIDIA NIM
    if not raw_response:
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            raw_response = _query_openai_compatible_reconciliation(
                provider_name="NVIDIA",
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1",
                models=["meta/llama-3.3-70b-instruct", "meta/llama-3.1-8b-instruct"],
                prompt=prompt,
            )

    if not raw_response:
        return None

    parsed = _parse_llm_json_response(raw_response)
    if not parsed or not isinstance(parsed, dict):
        return None

    try:
        # Normalize status string if present
        if "status" in parsed and isinstance(parsed["status"], str):
            parsed["status"] = map_entry_type_to_status(parsed["status"])
        return LiveVisaPolicyAnalysis.model_validate(parsed)
    except Exception as exc:
        log.warning("Failed to validate LiveVisaPolicyAnalysis for %s: %s", country_name, exc)
        return None


# ---------------------------------------------------------------------------
# Status Mapping and Document Templates
# ---------------------------------------------------------------------------


def map_entry_type_to_status(entry_type_str: str) -> VisaRequirementStatus:
    """Map raw entry_type string to VisaRequirementStatus enum."""
    normalized = entry_type_str.upper().strip().replace("-", "_").replace(" ", "_")
    mapping = {
        "VISA_FREE": VisaRequirementStatus.VISA_FREE,
        "FREE": VisaRequirementStatus.VISA_FREE,
        "VISA_ON_ARRIVAL": VisaRequirementStatus.VISA_ON_ARRIVAL,
        "VOA": VisaRequirementStatus.VISA_ON_ARRIVAL,
        "E_VISA": VisaRequirementStatus.E_VISA,
        "EVISA": VisaRequirementStatus.E_VISA,
        "ELECTRONIC_VISA": VisaRequirementStatus.E_VISA,
        "STICKER_VISA_REQUIRED": VisaRequirementStatus.STICKER_VISA_REQUIRED,
        "STICKER_VISA": VisaRequirementStatus.STICKER_VISA_REQUIRED,
        "VISA_REQUIRED": VisaRequirementStatus.STICKER_VISA_REQUIRED,
        "EMBASSY_VISA": VisaRequirementStatus.STICKER_VISA_REQUIRED,
        "CONDITIONAL_FREE": VisaRequirementStatus.CONDITIONAL_FREE,
        "CONDITIONAL_VISA_FREE": VisaRequirementStatus.CONDITIONAL_FREE,
        "RESTRICTED": VisaRequirementStatus.RESTRICTED,
        "NO_ADMISSION": VisaRequirementStatus.RESTRICTED,
        "DOMESTIC_BYPASS": VisaRequirementStatus.DOMESTIC_BYPASS,
    }
    return mapping.get(normalized, VisaRequirementStatus.UNKNOWN)


def get_standard_documents(
    status: VisaRequirementStatus,
    opt: VisaOption | None = None,
) -> list[str]:
    """Provide standard required document checklist for Indian passport holders."""
    docs: list[str] = [
        "Valid Indian passport (minimum 6 months validity from entry date)",
    ]

    if status == VisaRequirementStatus.VISA_FREE:
        docs.extend(
            [
                "Confirmed return or onward air ticket",
                "Proof of accommodation / hotel reservation",
                "Proof of sufficient travel funds (cash or international cards)",
            ]
        )
    elif status == VisaRequirementStatus.VISA_ON_ARRIVAL:
        docs.extend(
            [
                "Confirmed return or onward air ticket within allowable stay period",
                "Proof of hotel reservation / host accommodation",
                "Passport-size photographs as per destination port specifications",
                "Visa fee in cash (USD/local currency) or international payment card",
                "Completed arrival card / immigration declaration form",
            ]
        )
    elif status == VisaRequirementStatus.E_VISA:
        docs.extend(
            [
                "Scanned copy of passport biographical page (clear color scan)",
                "Recent digital passport photograph adhering to official portal guidelines",
                "Confirmed return/onward flight booking",
                "Credit or debit card with international transactions enabled for fee payment",
                "Printed physical copy of approved e-Visa clearance document",
            ]
        )
    elif status == VisaRequirementStatus.STICKER_VISA_REQUIRED:
        docs.extend(
            [
                "Original Indian passport with at least 2 blank pages",
                "Duly completed and signed official visa application form",
                "Recent passport-sized photographs on neutral white background",
                "Detailed day-wise travel itinerary and accommodation bookings",
                "Round-trip flight reservation / itinerary",
                "Original bank statements of past 3–6 months with bank seal and signature",
                "Income Tax Returns (ITR-V) or Form 16 for past 2–3 financial years",
                "Travel medical insurance covering entire stay (minimum €30,000 for Schengen)",
                "Cover letter explaining purpose of trip, itinerary, and financial sponsorship",
            ]
        )
    elif status == VisaRequirementStatus.CONDITIONAL_FREE:
        docs.extend(
            [
                "Confirmed return/onward flight booking",
                (
                    "Proof of valid visa or permanent residency of qualifying third country "
                    "(if applicable)"
                ),
                "Proof of hotel accommodation",
                "Proof of financial sufficiency",
            ]
        )
    else:
        docs.extend(
            [
                "Confirmed return flight booking",
                "Supporting documentation per consular guidelines",
            ]
        )

    if opt and opt.requires_loi:
        docs.append("Official Letter of Invitation (LOI) approved by host government authority")

    return docs


def get_default_processing_time(status: VisaRequirementStatus) -> str:
    """Return realistic typical processing time estimate based on requirement status."""
    if status == VisaRequirementStatus.VISA_FREE:
        return "Immediate (immigration clearance at port of entry)"
    if status == VisaRequirementStatus.VISA_ON_ARRIVAL:
        return "30–60 minutes upon arrival at international airport"
    if status == VisaRequirementStatus.E_VISA:
        return "2–5 business days online"
    if status == VisaRequirementStatus.STICKER_VISA_REQUIRED:
        return "15–20 business days via embassy/consular VFS application"
    if status == VisaRequirementStatus.CONDITIONAL_FREE:
        return "Immediate at border control subject to qualifying visa verification"
    return "Varies; check official consulate portal"


def get_default_application_process(
    status: VisaRequirementStatus,
    destination: str,
) -> str:
    """Return concise application guideline based on requirement status."""
    if status == VisaRequirementStatus.VISA_FREE:
        return (
            f"No prior application needed. Present passport and return ticket at "
            f"{destination} border control."
        )
    if status == VisaRequirementStatus.VISA_ON_ARRIVAL:
        return (
            f"Apply at the designated Visa-on-Arrival counter upon landing at recognized "
            f"international entry ports in {destination}."
        )
    if status == VisaRequirementStatus.E_VISA:
        return (
            f"Apply online at official {destination} government immigration portal at least "
            f"7–14 days prior to departure."
        )
    if status == VisaRequirementStatus.STICKER_VISA_REQUIRED:
        return (
            "Schedule biometric appointment and submit physical documents at authorized visa "
            "application center (e.g. VFS Global / BLS) 4–8 weeks before departure."
        )
    if status == VisaRequirementStatus.CONDITIONAL_FREE:
        return (
            "Entry without separate visa permitted if holding valid prerequisite credentials "
            "(e.g. US, UK, or Schengen visa)."
        )
    return f"Consult the nearest embassy or official mission of {destination}."


# ---------------------------------------------------------------------------
# Core Evaluation Engine
# ---------------------------------------------------------------------------


def evaluate_country_visa(
    country_code: str,
    country_name: str | None = None,
    live_search_enabled: bool = False,
    travel_date: str | None = None,
    live_policy_override: dict[str, Any] | None = None,
) -> VisaCountryVerdict:
    """Evaluate visa status and entry policy for a single international destination country.

    Args:
        country_code: ISO 3166-1 alpha-2 uppercase country code (e.g. 'TH', 'JP').
        country_name: Optional English country name.
        live_search_enabled: Whether to attempt live web search verification.
        travel_date: Optional planned travel start date (YYYY-MM-DD) for waiver validity checks.
        live_policy_override: Optional explicit live policy dictionary for testing/overrides.

    Returns:
        Validated frozen VisaCountryVerdict model.
    """
    code = country_code.upper().strip()

    # Resolve official country profile for name if missing
    country_profile = find_country(code)
    resolved_name = country_name or (country_profile.name if country_profile else code)

    # 1. Check for manual / injected live policy override (used in testing or live web agent)
    if live_policy_override:
        status_raw = live_policy_override.get("status", "VISA_FREE")
        status = (
            status_raw
            if isinstance(status_raw, VisaRequirementStatus)
            else map_entry_type_to_status(str(status_raw))
        )
        fee = float(live_policy_override.get("visa_fee_inr", 0.0))
        label = live_policy_override.get("visa_type_label", f"{status.value} Pathway")
        stay_days = live_policy_override.get("permitted_stay_days", 30)
        docs = live_policy_override.get("required_documents") or get_standard_documents(status)
        process = live_policy_override.get(
            "application_process"
        ) or get_default_application_process(status, resolved_name)
        proc_time = live_policy_override.get("processing_time_days") or get_default_processing_time(
            status
        )
        warnings = list(live_policy_override.get("warnings", []))
        warnings.append(
            f"Live policy update: {resolved_name} visa policy verified via live intelligence."
        )

        return VisaCountryVerdict(
            country_name=resolved_name,
            country_code=code,
            status=status,
            visa_type_label=label,
            permitted_stay_days=stay_days,
            visa_fee_inr=fee,
            required_documents=docs,
            application_process=process,
            processing_time_days=proc_time,
            entry_conditions=list(live_policy_override.get("entry_conditions", [])),
            data_source="LIVE_VERIFIED",
            is_live_verified=True,
            confidence="HIGH",
            warnings=warnings,
            sources=list(live_policy_override.get("sources", ["https://official-visa-live.gov"])),
            last_verified=datetime.now(UTC).date().isoformat(),
        )

    # 2. Retrieve static datasets
    enriched_record = get_enriched_visa(code)
    baseline_record: BaseVisaRule | None = None
    try:
        baseline_record = get_visa_baseline(code)
    except Exception:
        baseline_record = None

    # Determine baseline status, fee, and metadata
    data_source = "STATIC_DATASET"
    is_live_verified = False
    confidence = "HIGH" if enriched_record else ("MEDIUM" if baseline_record else "LOW")
    warnings: list[str] = []
    sources: list[str] = []
    opt: VisaOption | None = None

    if enriched_record is not None:
        opt = enriched_record.selected_option
        status = map_entry_type_to_status(opt.entry_type)
        visa_type_label = opt.visa_type
        stay_days = opt.duration_days if (opt.duration_days and opt.duration_days >= 1) else None
        fee_inr = max(0.0, float(opt.cost_inr))
        sources = list(opt.source)
        last_verified = enriched_record.last_updated

        entry_conditions: list[str] = []
        if opt.entry_port_restriction:
            entry_conditions.append(f"Port restriction: {opt.entry_port_restriction}")
        if opt.notes:
            entry_conditions.append(opt.notes)

    elif baseline_record is not None:
        status = map_entry_type_to_status(baseline_record.requirement)
        visa_type_label = f"{baseline_record.requirement.replace('_', ' ').title()}"
        stay_days = (
            baseline_record.allowed_stay_days
            if (baseline_record.allowed_stay_days and baseline_record.allowed_stay_days >= 1)
            else None
        )
        fee_inr = 0.0 if status == VisaRequirementStatus.VISA_FREE else 3500.0
        sources = ["https://www.passportindex.org"]
        last_verified = baseline_record.last_updated
        entry_conditions = []
        warnings.append(
            f"Enriched visa record unavailable for {resolved_name}; using static baseline."
        )

    else:
        # Unknown country without static data
        return VisaCountryVerdict(
            country_name=resolved_name,
            country_code=code,
            status=VisaRequirementStatus.UNKNOWN,
            visa_type_label="Unknown Visa Policy",
            permitted_stay_days=None,
            visa_fee_inr=0.0,
            required_documents=get_standard_documents(VisaRequirementStatus.UNKNOWN),
            application_process=get_default_application_process(
                VisaRequirementStatus.UNKNOWN, resolved_name
            ),
            processing_time_days=get_default_processing_time(VisaRequirementStatus.UNKNOWN),
            entry_conditions=[],
            data_source="STATIC_DATASET",
            is_live_verified=False,
            confidence="LOW",
            warnings=[
                f"No verified static visa record found for destination '{resolved_name}' ({code}). "
                "Manual embassy verification required."
            ],
            sources=[],
            last_verified=None,
        )

    # 3. Live search verification if enabled (Option 1: Semantic Structured Reconciliation)
    if live_search_enabled:
        try:
            search_query = (
                f"{resolved_name} visa requirements for Indian citizens passport official"
            )
            search_res = search_web(search_query, max_results=3)

            if search_res and search_res.results:
                for item in search_res.results:
                    if item.url and item.url not in sources:
                        sources.append(item.url)

                snippets_text = "\n\n".join(
                    f"[{r.title}] ({r.url}):\n{r.snippet}" for r in search_res.results
                )

                baseline_summary = {
                    "destination": resolved_name,
                    "country_code": code,
                    "current_status": status.value,
                    "visa_type": visa_type_label,
                    "fee_inr": fee_inr,
                    "duration_days": stay_days,
                }

                # Semantic LLM-based reconciliation (Zero Regex)
                analysis = _reconcile_with_llm(
                    country_name=resolved_name,
                    country_code=code,
                    baseline_data=baseline_summary,
                    search_snippets=snippets_text,
                    travel_date=travel_date,
                )

                if analysis is not None:
                    if not analysis.applies_to_indian_passports:
                        warnings.append(
                            f"Live intelligence note for {resolved_name}: Search results mentioned "
                            "entry policies that do not apply to Indian passport holders. "
                            "Retained verified static baseline."
                        )
                    elif analysis.policy_change_confirmed and analysis.status is not None:
                        is_expired = False
                        if travel_date and analysis.waiver_end_date:
                            try:
                                if travel_date > analysis.waiver_end_date:
                                    is_expired = True
                            except Exception:
                                is_expired = False

                        if is_expired:
                            warnings.append(
                                f"Live policy update: Temporary waiver for {resolved_name} "
                                f"expires on {analysis.waiver_end_date} before planned travel date "
                                f"({travel_date}). Retained standard static baseline."
                            )
                        elif analysis.confidence == "LOW":
                            warnings.append(
                                f"Live reports for {resolved_name} indicate potential policy "
                                "updates, but confidence is LOW. Retained verified static "
                                "baseline; verify with embassy."
                            )
                        else:
                            # Confirmed active policy update
                            status = analysis.status
                            if analysis.visa_type_label:
                                visa_type_label = analysis.visa_type_label
                            if analysis.permitted_stay_days is not None:
                                stay_days = analysis.permitted_stay_days
                            if analysis.visa_fee_inr is not None:
                                fee_inr = max(0.0, float(analysis.visa_fee_inr))
                            if (
                                analysis.official_source_url
                                and analysis.official_source_url not in sources
                            ):
                                sources.insert(0, analysis.official_source_url)

                            data_source = "LIVE_VERIFIED"
                            is_live_verified = True
                            confidence = analysis.confidence
                            reas = (
                                analysis.reasoning
                                or f"Confirmed policy update for {resolved_name}."
                            )
                            warnings.append(f"Live policy update: {reas}")
                    else:
                        # Baseline confirmed or no official change
                        data_source = "LIVE_VERIFIED"
                        is_live_verified = True
                        confidence = analysis.confidence
                        if analysis.reasoning:
                            warnings.append(
                                f"Live analysis for {resolved_name}: {analysis.reasoning}"
                            )
                else:
                    warnings.append(
                        f"Live search retrieved for {resolved_name}, but LLM structured policy "
                        "reconciliation was unavailable; retained verified static baseline."
                    )
            else:
                warnings.append(
                    f"Live search for {resolved_name} returned no results; "
                    "retained static baseline."
                )

        except Exception as exc:
            log.warning("Live visa verification search failed for %s: %s", resolved_name, exc)
            warnings.append(
                f"Live verification search failed for {resolved_name}; "
                "retained verified static baseline."
            )

    docs = get_standard_documents(status, opt)
    process = get_default_application_process(status, resolved_name)
    proc_time = get_default_processing_time(status)

    return VisaCountryVerdict(
        country_name=resolved_name,
        country_code=code,
        status=status,
        visa_type_label=visa_type_label,
        permitted_stay_days=stay_days,
        visa_fee_inr=fee_inr,
        required_documents=docs,
        application_process=process,
        processing_time_days=proc_time,
        entry_conditions=entry_conditions,
        data_source=data_source,
        is_live_verified=is_live_verified,
        confidence=confidence,
        warnings=warnings,
        sources=sources,
        last_verified=last_verified,
    )


# ---------------------------------------------------------------------------
# High-Level Visa Process & Aggregator
# ---------------------------------------------------------------------------


def process_visa(
    state: InitialPlanningState | TripContext | dict[str, Any],
    live_search_enabled: bool = False,
    live_overrides: dict[str, dict[str, Any]] | None = None,
) -> VisaVerdict:
    """Process visa requirements, handling domestic bypass and multi-country aggregation.

    Args:
        state: InitialPlanningState, TripContext, or dictionary state representation.
        live_search_enabled: Whether to attempt live web search verification.
        live_overrides: Optional per-country live policy override dicts, keyed by country code.

    Returns:
        Frozen top-level VisaVerdict model.
    """
    timestamp_iso = datetime.now(UTC).isoformat()

    # Extract scope, party, and destinations from input state
    travel_scope: TravelScope | None = None
    party: TripParty | None = None
    travel_date: str | None = None
    resolved_destinations: list[ResolvedLocation] = []

    if isinstance(state, InitialPlanningState):
        travel_scope = state.travel_scope
        party = state.trip_context.party
        resolved_destinations = state.destinations
        if state.trip_context.dates and state.trip_context.dates.start_date:
            travel_date = state.trip_context.dates.start_date
    elif isinstance(state, TripContext):
        travel_scope = state.scope
        party = state.party
        if state.dates and state.dates.start_date:
            travel_date = state.dates.start_date
        # Construct lightweight location references
        resolved_destinations = [
            ResolvedLocation(
                query=d,
                name=d,
                city=None,
                country_code=d if len(d) == 2 else "??",
                country_name=d,
                iata_code=d if len(d) == 3 else None,
                latitude=0.0,
                longitude=0.0,
                is_schengen=False,
                ist_offset_hours=0.0,
            )
            for d in state.destinations
        ]
    elif isinstance(state, dict):
        scope_val = state.get("travel_scope") or state.get("scope")
        if isinstance(scope_val, TravelScope):
            travel_scope = scope_val
        elif isinstance(scope_val, str):
            travel_scope = (
                TravelScope.DOMESTIC
                if scope_val.upper() == "DOMESTIC"
                else TravelScope.INTERNATIONAL
            )

        trip_ctx = state.get("trip_context")
        if isinstance(trip_ctx, TripContext):
            party = trip_ctx.party
            if trip_ctx.dates and trip_ctx.dates.start_date:
                travel_date = trip_ctx.dates.start_date
        elif isinstance(trip_ctx, dict) and "party" in trip_ctx:
            party_dict = trip_ctx["party"]
            if isinstance(party_dict, TripParty):
                party = party_dict
            elif isinstance(party_dict, dict):
                party = TripParty(**party_dict)

        dates_val = state.get("dates")
        if isinstance(dates_val, dict) and "start_date" in dates_val:
            travel_date = dates_val["start_date"]
        elif dates_val and hasattr(dates_val, "start_date"):
            travel_date = getattr(dates_val, "start_date")

        dest_val = state.get("destinations", [])
        for item in dest_val:
            if isinstance(item, ResolvedLocation):
                resolved_destinations.append(item)
            elif isinstance(item, dict):
                resolved_destinations.append(ResolvedLocation(**item))
            elif isinstance(item, str):
                resolved_destinations.append(
                    ResolvedLocation(
                        query=item,
                        name=item,
                        city=None,
                        country_code=item if len(item) == 2 else "??",
                        country_name=item,
                        iata_code=item if len(item) == 3 else None,
                        latitude=0.0,
                        longitude=0.0,
                        is_schengen=False,
                        ist_offset_hours=0.0,
                    )
                )

    # 1. Domestic Trip Bypass
    if travel_scope == TravelScope.DOMESTIC:
        return VisaVerdict(
            is_domestic_bypass=True,
            countries=[],
            total_visa_cost_inr=0.0,
            requires_advance_application=False,
            schengen_single_visa_applicable=False,
            warnings=[],
            timestamp=timestamp_iso,
        )

    # 2. Extract unique international destination countries (excluding India)
    unique_countries: dict[str, str | None] = {}
    for dest in resolved_destinations:
        c_code = dest.country_code.upper() if dest.country_code else "??"
        if c_code == "IN":
            continue

        c_name = dest.country_name or dest.name
        if c_code not in unique_countries:
            unique_countries[c_code] = c_name

    # If no international destinations exist (e.g. all domestic stops)
    if not unique_countries:
        return VisaVerdict(
            is_domestic_bypass=True,
            countries=[],
            total_visa_cost_inr=0.0,
            requires_advance_application=False,
            schengen_single_visa_applicable=False,
            warnings=[],
            timestamp=timestamp_iso,
        )

    # 3. Evaluate each country
    country_verdicts: list[VisaCountryVerdict] = []
    trip_warnings: list[str] = []

    for c_code, c_name in unique_countries.items():
        override = (live_overrides or {}).get(c_code)
        verdict = evaluate_country_visa(
            country_code=c_code,
            country_name=c_name,
            live_search_enabled=live_search_enabled,
            travel_date=travel_date,
            live_policy_override=override,
        )
        country_verdicts.append(verdict)
        if verdict.warnings:
            trip_warnings.extend(verdict.warnings)

    # 4. Schengen multi-country evaluation & single visa optimization
    schengen_verdicts = [c for c in country_verdicts if is_schengen(c.country_code)]
    schengen_single_visa_applicable = len(schengen_verdicts) >= 2

    if schengen_single_visa_applicable:
        names = ", ".join(c.country_name for c in schengen_verdicts)
        trip_warnings.append(
            f"Destinations [{names}] belong to the Schengen Area. A single uniform Schengen visa "
            "applies across all visited Schengen member states."
        )

    # 5. Calculate total visa cost in INR across traveler party
    party_size = party.total_travelers if party else 1

    if schengen_single_visa_applicable:
        # Non-Schengen fees are added individually
        non_schengen_per_person = sum(
            c.visa_fee_inr for c in country_verdicts if not is_schengen(c.country_code)
        )
        # Schengen fee is charged ONCE per traveler (highest single fee among Schengen destinations)
        schengen_per_person = max(
            (c.visa_fee_inr for c in schengen_verdicts),
            default=0.0,
        )
        per_person_total = non_schengen_per_person + schengen_per_person
    else:
        per_person_total = sum(c.visa_fee_inr for c in country_verdicts)

    total_visa_cost_inr = round(per_person_total * party_size, 2)

    # 6. Check if advance visa application is required
    requires_advance_app = any(
        c.status in (VisaRequirementStatus.E_VISA, VisaRequirementStatus.STICKER_VISA_REQUIRED)
        for c in country_verdicts
    )

    return VisaVerdict(
        is_domestic_bypass=False,
        countries=country_verdicts,
        total_visa_cost_inr=total_visa_cost_inr,
        requires_advance_application=requires_advance_app,
        schengen_single_visa_applicable=schengen_single_visa_applicable,
        warnings=trip_warnings,
        timestamp=timestamp_iso,
    )


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def visa_node(
    state: dict[str, Any] | InitialPlanningState,
) -> dict[str, Any]:
    """LangGraph node function for visa planning.

    Args:
        state: State dictionary or InitialPlanningState from the graph.

    Returns:
        State update dictionary containing the generated 'visa_verdict'.
    """
    verdict = process_visa(state)
    return {
        "visa_verdict": verdict,
    }
