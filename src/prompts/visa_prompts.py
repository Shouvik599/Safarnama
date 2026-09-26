"""Prompt definitions for Visa Rules Enrichment (scripts/enrich_visa_rules.py)."""

import datetime
import json
from typing import Any


def build_visa_enrichment_prompt(
    destination: str,
    baseline: dict[str, Any],
    search_context: str,
) -> str:
    """Build the multi-option enrichment prompt for Gemini visa research."""
    baseline_json = json.dumps(baseline, indent=2)
    today = datetime.date.today().isoformat()
    return f"""You are a travel visa information specialist researching entry requirements
for Indian passport holders.

Today's date: {today}
Destination: {destination}
Country code: {baseline.get("country_code", "??")}

Static baseline (may be outdated — use as context only):
{baseline_json}

Verified web search research results:
{search_context if search_context else "No external search data. Rely on official knowledge."}

Instructions:
1. Base your output on the verified search data above and official immigration policies
   for Indian passport holders entering {destination}.

2. **CRITICAL — Multi-option capture**: Look for ALL overlapping or alternative
   legal entry pathways that currently coexist. For example:
   - A new visa-free regime may still coexist with a legacy e-visa or
     visa-on-arrival option.
   - Some countries offer both a free short-stay AND a paid longer-stay option.
   - Include EVERY currently valid legal pathway in the `options` array.
   - Do NOT collapse multiple options into a single status string.

3. For each option, provide:
   - visa_type: short human-readable label
   - duration_days: maximum permitted stay in days (integer, or null)
   - cost_inr: fee in INR (0.0 for free; convert from foreign currency)
   - entry_type: VISA_FREE | CONDITIONAL_FREE | VISA_ON_ARRIVAL |
                 E_VISA | STICKER_VISA_REQUIRED | UNKNOWN
   - entry_port_restriction: airport/port restrictions (null if none)
   - requires_loi: true only if a Letter of Invitation is mandatory
   - notes: brief factual note on conditions/changes/pilots (null if none)
"""


def build_live_visa_verification_prompt(
    destination: str,
    country_code: str,
    baseline_rule: dict[str, Any],
    search_snippets: str,
    travel_date: str | None = None,
) -> str:
    """Build prompt for reconciling live search snippets against baseline visa rules with LLM."""
    baseline_json = json.dumps(baseline_rule, indent=2)
    today = datetime.date.today().isoformat()
    travel_date_line = (
        f"Planned travel start date: {travel_date}"
        if travel_date
        else "Planned travel start date: Not specified"
    )

    return f"""You are a specialized visa policy analyst verifying international entry requirements
for Indian passport holders traveling to {destination} ({country_code}).

Today's date: {today}
Destination: {destination} ({country_code})
{travel_date_line}

Static Baseline Record:
{baseline_json}

Recent Live Search Snippets:
{search_snippets if search_snippets else "No live search results available."}

Task:
Perform a rigorous semantic evaluation of the live search snippets against the baseline record.
Do NOT use keyword matching. Comprehend the context, subject nationality, and dates.

Rules & Anti-Hallucination Guardrails:
1. **Target Nationality**: You must verify that any mentioned policy applies specifically to
   INDIAN passport holders / Indian citizens. If a snippet states that other nationalities
   (e.g. EU, US, ASEAN) are visa-free but Indians require an e-visa or sticker visa, you must
   NOT flag visa-free for Indians.
2. **Confirmed vs. Proposed**: Distinguish between active, enacted official policies vs.
   proposals, considerations, or media speculations ("cabinet considers", "plans to ease").
   Only set `policy_change_confirmed: true` if the policy is already in effect or officially
   confirmed by immigration authorities.
3. **Validity & Expiry Dates**: If a temporary visa waiver or exemption is announced with an
   expiration date, extract `waiver_end_date` (YYYY-MM-DD). If the planned travel date falls
   after `waiver_end_date`, set `policy_change_confirmed: false` and explain that the waiver
   expires before travel.
4. **Ambiguity / Contradiction**: If search snippets contradict each other, lack official source
   backing, or are vague, set `confidence: "LOW"` and `policy_change_confirmed: false`.
5. **No Fabrication**: Never invent visa requirements, fees, or documents not corroborated
   by the snippets or baseline.

Respond ONLY with a valid JSON object conforming to this exact structure:
{{
  "applies_to_indian_passports": true,
  "policy_change_confirmed": true,
  "status": "VISA_FREE" | "VISA_ON_ARRIVAL" | "E_VISA" | "STICKER_VISA_REQUIRED",
  "visa_type_label": "Human-readable pathway title (e.g. 'Temporary Tourist Visa Exemption')",
  "permitted_stay_days": 30,
  "visa_fee_inr": 0.0,
  "waiver_end_date": "YYYY-MM-DD or null if permanent or unknown",
  "official_source_url": "URL of official immigration portal if present, else null",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "Factual explanation of what the search snippets confirm or reasons for doubt"
}}
"""
