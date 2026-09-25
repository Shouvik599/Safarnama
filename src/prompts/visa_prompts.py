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
