"""Prompt definitions for Fallback Cost Estimator (src/tools/fallback_estimator.py)."""


def build_estimator_system_prompt() -> str:
    """Build system instructions prompt for OpenAI-compatible fallback estimation calls."""
    return (
        "You are an expert travel budget estimator. Output ONLY valid JSON matching schema.\n"
        "DO NOT include markdown wrappers or extra text outside JSON.\n"
        "DO NOT invent named entities (no specific hotel names, restaurant names, etc)."
    )


def build_estimator_user_prompt(
    destination: str,
    category: str,
    tier: str,
    duration_days: int,
    num_travelers: int,
    context_notes: str | None = None,
) -> str:
    """Build user prompt for OpenAI-compatible fallback cost estimation calls."""
    return (
        f"Estimate travel cost in INR for:\n"
        f"Destination: {destination}\n"
        f"Category: {category}\n"
        f"Tier: {tier}\n"
        f"Duration: {duration_days} day(s)\n"
        f"Travelers: {num_travelers}\n"
        f"Context: {context_notes or 'None'}\n\n"
        f"JSON Schema:\n"
        f"{{\n"
        f'  "estimated_cost_inr": 8500.0,\n'
        f'  "min_cost_inr": 6000.0,\n'
        f'  "max_cost_inr": 12000.0,\n'
        f'  "confidence_score": 0.85,\n'
        f'  "reasoning": "Detail assumptions in INR"\n'
        f"}}\n"
    )


def build_gemini_estimator_prompt(
    destination: str,
    category: str,
    tier: str,
    duration_days: int,
    num_travelers: int,
    context_notes: str | None = None,
) -> str:
    """Build prompt for Google Gemini API fallback cost estimation calls."""
    return (
        f"You are a travel cost estimation engine. Estimate travel cost in INR for:\n"
        f"- Destination: {destination}\n"
        f"- Cost Category: {category}\n"
        f"- Travel Tier: {tier}\n"
        f"- Duration: {duration_days} day(s)\n"
        f"- Number of Travelers: {num_travelers}\n"
        f"- Context Notes: {context_notes or 'None'}\n\n"
        f"CRITICAL RULE: DO NOT invent specific entity names (hotels, airlines, etc).\n"
        f"Return ONLY a valid JSON object matching this schema:\n"
        f"{{\n"
        f'  "estimated_cost_inr": 8500.0,\n'
        f'  "min_cost_inr": 6000.0,\n'
        f'  "max_cost_inr": 12000.0,\n'
        f'  "confidence_score": 0.85,\n'
        f'  "reasoning": "Explanation of daily rates and assumptions in INR"\n'
        f"}}\n"
    )
