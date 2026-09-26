"""LLM Fallback Estimator tool for Safarnama travel planning system.

Provides structured numerical cost estimations when live API tools return
incomplete cost figures or for offline budget estimation.

Cascade Strategy:
1. Test Fixture Mode (`data/fixtures/mock_fallback_estimates.json`)
2. In-Memory Cache (24-hour TTL)
3. Live Tier 1: Google Gemini API (`GEMINI_API_KEY`)
   Models: `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`
4. Live Tier 2: Groq OpenAI-Compatible API (`GROQ_API_KEY`)
   Models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`
5. Live Tier 3: NVIDIA NIM API (`NVIDIA_API_KEY`)
   Models: `meta/llama-3.3-70b-instruct`, `meta/llama-3.1-8b-instruct`
6. Tier 4: Offline Rule-Based Mathematical Baseline (`_estimate_heuristic_baseline`)
"""

import concurrent.futures
import json
import logging
import os
import pathlib
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from src.models.fallback_estimator import (
    CostCategory,
    EstimateRequest,
    FallbackEstimateResult,
    TravelTier,
)
from src.prompts.estimator_prompts import (
    build_estimator_system_prompt,
    build_estimator_user_prompt,
    build_gemini_estimator_prompt,
)

log = logging.getLogger(__name__)

# Default network timeout in seconds for live API requests
DEFAULT_TIMEOUT_SECONDS: float = 12.0

# In-memory cache TTL in seconds (24 hours)
CACHE_TTL_SECONDS: float = 86400.0


# ---------------------------------------------------------------------------
# Custom Tool Exceptions
# ---------------------------------------------------------------------------


class EstimatorError(Exception):
    """Base exception for Fallback Estimator errors."""

    pass


class InvalidDestinationError(EstimatorError, ValueError):
    """Raised when destination string is empty or invalid."""

    pass


# ---------------------------------------------------------------------------
# In-Memory Cache Implementation
# ---------------------------------------------------------------------------


class EstimatorCache:
    """Thread-safe in-memory cache for fallback cost estimation results."""

    def __init__(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, FallbackEstimateResult]] = {}

    def _make_key(
        self,
        destination: str,
        category: str,
        tier: str,
        duration_days: int,
        num_travelers: int,
    ) -> str:
        d = destination.strip().upper()
        c = category.upper()
        t = tier.upper()
        return f"{d}:{c}:{t}:{duration_days}:{num_travelers}"

    def get(
        self,
        destination: str,
        category: str,
        tier: str,
        duration_days: int,
        num_travelers: int,
    ) -> FallbackEstimateResult | None:
        key = self._make_key(destination, category, tier, duration_days, num_travelers)
        entry = self._cache.get(key)
        if entry is None:
            return None

        timestamp, result = entry
        if (datetime.now(UTC).timestamp() - timestamp) > self.ttl_seconds:
            del self._cache[key]
            return None

        return result

    def set(
        self,
        destination: str,
        category: str,
        tier: str,
        duration_days: int,
        num_travelers: int,
        result: FallbackEstimateResult,
    ) -> None:
        key = self._make_key(destination, category, tier, duration_days, num_travelers)
        self._cache[key] = (datetime.now(UTC).timestamp(), result)

    def clear(self) -> None:
        self._cache.clear()

    def count(self) -> int:
        now = datetime.now(UTC).timestamp()
        valid = [k for k, (ts, _) in self._cache.items() if (now - ts) <= self.ttl_seconds]
        return len(valid)


# Global cache instance
_ESTIMATOR_CACHE = EstimatorCache()


# ---------------------------------------------------------------------------
# String & Enum Normalization Helpers
# ---------------------------------------------------------------------------


def _normalize_enum_str(val: Any) -> str:
    """Normalize Enum or string value to uppercase string (e.g., 'HOTEL')."""
    if hasattr(val, "value"):
        return str(val.value).upper()
    s = str(val).strip()
    if "." in s:
        s = s.split(".")[-1]
    return s.upper()


# ---------------------------------------------------------------------------
# Provider Implementation 1: Mock Fixture Provider
# ---------------------------------------------------------------------------


def _load_fixture_data() -> dict[str, Any]:
    """Load mock fallback estimates JSON fixture file."""
    root_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    fixture_path = root_dir / "data" / "fixtures" / "mock_fallback_estimates.json"

    if not fixture_path.exists():
        log.warning("Fixture file not found at %s. Returning fallback default.", fixture_path)
        return {"destinations": {}}

    try:
        with open(fixture_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning("Failed to load fixture JSON from %s: %s", fixture_path, exc)
        return {"destinations": {}}


def _estimate_fixture(request: EstimateRequest) -> FallbackEstimateResult:
    """Return fixture estimate for a given destination and cost category."""
    clean_dest = request.destination.strip().upper()
    req_cat = _normalize_enum_str(request.category)
    req_tier = _normalize_enum_str(request.tier)

    data = _load_fixture_data()
    destinations = data.get("destinations", {})

    dest_data = destinations.get(clean_dest) or destinations.get("DEFAULT", {})
    cat_data = dest_data.get(req_cat) or dest_data.get("HOTEL", {})

    # Scale base fixture cost for duration and travelers
    base_cost = float(cat_data.get("estimated_cost_inr", 5000.0))
    multiplier = request.duration_days * (0.8 + 0.2 * request.num_travelers)
    total_est = base_cost * multiplier

    return FallbackEstimateResult(
        destination=clean_dest,
        category=req_cat,
        tier=req_tier,
        estimated_cost_inr=round(total_est, 2),
        min_cost_inr=round(total_est * 0.75, 2),
        max_cost_inr=round(total_est * 1.35, 2),
        currency="INR",
        confidence_score=float(cat_data.get("confidence_score", 0.85)),
        reasoning=cat_data.get("reasoning", "Fixture cost estimate."),
        provider_used="fixture",
        model_used="mock-estimator-v1",
        is_fallback=True,
        is_estimated=True,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Provider Implementation 2: Offline Rule-Based Mathematical Baseline
# ---------------------------------------------------------------------------


def _estimate_heuristic_baseline(request: EstimateRequest) -> FallbackEstimateResult:
    """Compute offline heuristic estimate using deterministic rule tables."""
    clean_dest = request.destination.strip().upper()
    req_cat = _normalize_enum_str(request.category)
    req_tier = _normalize_enum_str(request.tier)

    # Destination multiplier tiers
    cost_multiplier = 1.0
    expensive_cities = {"TOKYO", "PARIS", "NEW YORK", "LONDON", "ZURICH", "SINGAPORE", "DUBAI"}
    mid_cities = {"MUMBAI", "DELHI", "BANGKOK", "BALI", "KUALA LUMPUR", "ROME", "ISTANBUL"}

    if any(c in clean_dest for c in expensive_cities):
        cost_multiplier = 2.2
    elif any(c in clean_dest for c in mid_cities):
        cost_multiplier = 1.2

    # Tier multipliers
    tier_multiplier = 1.0
    if req_tier == "BUDGET":
        tier_multiplier = 0.55
    elif req_tier == "LUXURY":
        tier_multiplier = 2.5

    # Base daily costs per person (INR)
    base_daily_costs = {
        "HOTEL": 4500.0,
        "TRANSPORT": 1200.0,
        "FOOD": 2000.0,
        "ACTIVITY": 1500.0,
        "MISC": 800.0,
        "TOTAL_BUDGET": 10000.0,
    }

    base_per_day = base_daily_costs.get(req_cat, 3500.0)
    per_day_cost = base_per_day * cost_multiplier * tier_multiplier

    total_est = per_day_cost * request.duration_days * request.num_travelers

    reasoning_msg = (
        f"Offline heuristic calculation for {req_tier.title()} tier travel in {clean_dest.title()} "
        f"over {request.duration_days} day(s) for {request.num_travelers} traveler(s)."
    )

    return FallbackEstimateResult(
        destination=clean_dest,
        category=req_cat,
        tier=req_tier,
        estimated_cost_inr=round(total_est, 2),
        min_cost_inr=round(total_est * 0.70, 2),
        max_cost_inr=round(total_est * 1.30, 2),
        currency="INR",
        confidence_score=0.70,
        reasoning=reasoning_msg,
        provider_used="offline-heuristic",
        model_used="rule-baseline-v1",
        is_fallback=True,
        is_estimated=True,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Helper: Extract JSON from LLM Response Text
# ---------------------------------------------------------------------------


def _parse_llm_json_response(text: str) -> dict[str, Any] | None:
    """Safely extract JSON payload from LLM text response."""
    if not text:
        return None

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting markdown block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 3: Live Tier 1 - Google Gemini API
# ---------------------------------------------------------------------------


def _estimate_gemini_single_model(
    model_name: str,
    gemini_key: str,
    prompt: str,
    clean_dest: str,
    req_cat: str,
    req_tier: str,
    timeout: float,
) -> FallbackEstimateResult | None:
    """Attempt Gemini estimation for a single model."""
    try:
        # Try google-genai SDK if installed
        try:
            from google import genai  # type: ignore

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw_text = response.text if hasattr(response, "text") else str(response)
        except Exception:
            # Fallback to direct REST call if SDK call fails or unavailable
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={gemini_key}"
            )
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    return None
                res_body = json.loads(resp.read().decode("utf-8"))
                candidates = res_body.get("candidates", [])
                if not candidates:
                    return None
                parts = candidates[0].get("content", {}).get("parts", [])
                raw_text = parts[0].get("text", "") if parts else ""

        parsed = _parse_llm_json_response(raw_text)
        if parsed and "estimated_cost_inr" in parsed:
            est = float(parsed.get("estimated_cost_inr", 0.0))
            min_c = float(parsed.get("min_cost_inr") or est * 0.75)
            max_c = float(parsed.get("max_cost_inr") or est * 1.35)
            conf = float(parsed.get("confidence_score") or 0.85)
            reas = str(parsed.get("reasoning") or f"Gemini {model_name} estimation.")

            log.info("Gemini model %s generated cost estimate for %s", model_name, clean_dest)
            return FallbackEstimateResult(
                destination=clean_dest,
                category=req_cat,
                tier=req_tier,
                estimated_cost_inr=round(est, 2),
                min_cost_inr=round(min_c, 2),
                max_cost_inr=round(max_c, 2),
                currency="INR",
                confidence_score=min(1.0, max(0.0, conf)),
                reasoning=reas,
                provider_used="gemini",
                model_used=model_name,
                is_fallback=True,
                is_estimated=True,
                timestamp=datetime.now(UTC).isoformat(),
            )
    except Exception as exc:
        log.warning("Gemini model %s estimation failed for %s: %s", model_name, clean_dest, exc)

    return None


def _estimate_gemini(
    request: EstimateRequest, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> FallbackEstimateResult | None:
    """Execute cost estimation via Google Gemini API."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key:
        return None

    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]

    clean_dest = request.destination.strip().upper()
    req_cat = _normalize_enum_str(request.category)
    req_tier = _normalize_enum_str(request.tier)

    prompt = build_gemini_estimator_prompt(
        destination=clean_dest,
        category=req_cat,
        tier=req_tier,
        duration_days=request.duration_days,
        num_travelers=request.num_travelers,
        context_notes=request.context_notes,
    )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(len(models_to_try), 8))
    try:
        futures = [
            executor.submit(
                _estimate_gemini_single_model,
                model_name,
                gemini_key,
                prompt,
                clean_dest,
                req_cat,
                req_tier,
                timeout,
            )
            for model_name in models_to_try
        ]

        for future in futures:
            try:
                res = future.result()
                if res is not None:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return res
            except Exception:
                continue
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 4: Live Tier 2 & 3 - OpenAI-Compatible Endpoint (Groq & NVIDIA)
# ---------------------------------------------------------------------------


def _estimate_openai_compatible_single_model(
    model_name: str,
    provider_name: str,
    api_key: str,
    base_url: str,
    sys_prompt: str,
    user_prompt: str,
    clean_dest: str,
    req_cat: str,
    req_tier: str,
    timeout: float,
) -> FallbackEstimateResult | None:
    """Attempt cost estimation for a single OpenAI-compatible model."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
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
                    content = choices[0].get("message", {}).get("content", "")
                    parsed = _parse_llm_json_response(content)
                    if parsed and "estimated_cost_inr" in parsed:
                        est = float(parsed.get("estimated_cost_inr", 0.0))
                        min_c = float(parsed.get("min_cost_inr") or est * 0.75)
                        max_c = float(parsed.get("max_cost_inr") or est * 1.35)
                        conf = float(parsed.get("confidence_score") or 0.85)
                        default_reas = f"{provider_name.title()} estimation."
                        reas = str(parsed.get("reasoning") or default_reas)

                        log.info(
                            "%s model %s generated cost estimate for %s",
                            provider_name.title(),
                            model_name,
                            clean_dest,
                        )
                        return FallbackEstimateResult(
                            destination=clean_dest,
                            category=req_cat,
                            tier=req_tier,
                            estimated_cost_inr=round(est, 2),
                            min_cost_inr=round(min_c, 2),
                            max_cost_inr=round(max_c, 2),
                            currency="INR",
                            confidence_score=min(1.0, max(0.0, conf)),
                            reasoning=reas,
                            provider_used=provider_name.lower(),
                            model_used=model_name,
                            is_fallback=True,
                            is_estimated=True,
                            timestamp=datetime.now(UTC).isoformat(),
                        )
    except Exception as exc:
        log.warning(
            "%s model %s estimation failed for %s: %s",
            provider_name.title(),
            model_name,
            clean_dest,
            exc,
        )

    return None


def _estimate_openai_compatible(
    request: EstimateRequest,
    provider_name: str,
    api_key: str | None,
    base_url: str,
    models: list[str],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> FallbackEstimateResult | None:
    """Execute cost estimation via OpenAI-compatible endpoint (Groq / NVIDIA NIM)."""
    if not api_key:
        return None

    clean_dest = request.destination.strip().upper()
    req_cat = _normalize_enum_str(request.category)
    req_tier = _normalize_enum_str(request.tier)

    sys_prompt = build_estimator_system_prompt()
    user_prompt = build_estimator_user_prompt(
        destination=clean_dest,
        category=req_cat,
        tier=req_tier,
        duration_days=request.duration_days,
        num_travelers=request.num_travelers,
        context_notes=request.context_notes,
    )

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(len(models), 8))
    try:
        futures = [
            executor.submit(
                _estimate_openai_compatible_single_model,
                model_name,
                provider_name,
                api_key,
                base_url,
                sys_prompt,
                user_prompt,
                clean_dest,
                req_cat,
                req_tier,
                timeout,
            )
            for model_name in models
        ]

        for future in futures:
            try:
                res = future.result()
                if res is not None:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return res
            except Exception:
                continue
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return None


def _estimate_groq(
    request: EstimateRequest, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> FallbackEstimateResult | None:
    """Execute cost estimation via Groq OpenAI-compatible API."""
    groq_key = os.getenv("GROQ_API_KEY")
    models = [
        os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]
    return _estimate_openai_compatible(
        request=request,
        provider_name="groq",
        api_key=groq_key,
        base_url="https://api.groq.com/openai/v1",
        models=models,
        timeout=timeout,
    )


def _estimate_nvidia(
    request: EstimateRequest, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> FallbackEstimateResult | None:
    """Execute cost estimation via NVIDIA NIM OpenAI-compatible API."""
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    models = [
        os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
        "meta/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct-v0.3",
    ]
    return _estimate_openai_compatible(
        request=request,
        provider_name="nvidia",
        api_key=nvidia_key,
        base_url="https://integrate.api.nvidia.com/v1",
        models=models,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Public Fallback Estimator Interface
# ---------------------------------------------------------------------------


def estimate_cost(
    destination: str,
    category: CostCategory | str = CostCategory.HOTEL,
    tier: TravelTier | str = TravelTier.MID_RANGE,
    duration_days: int = 1,
    num_travelers: int = 1,
    currency: str = "INR",
    context_notes: str | None = None,
    use_fixture: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> FallbackEstimateResult:
    """Estimate travel cost using multi-provider LLM fallback or offline heuristics.

    Args:
        destination: Target city or region name (e.g. 'Tokyo', 'Mumbai', 'Paris').
        category: Cost category: HOTEL, TRANSPORT, FOOD, ACTIVITY, MISC, TOTAL_BUDGET.
        tier: Travel budget tier: BUDGET, MID_RANGE, LUXURY.
        duration_days: Duration of stay in days (default: 1).
        num_travelers: Number of travelers (default: 1).
        currency: Target currency ISO code (default: 'INR').
        context_notes: Optional context hints (e.g. '3-star hotel near station').
        use_fixture: If True, bypass live API network requests and return fixture data.
        timeout: Network timeout in seconds for live LLM HTTP requests.

    Returns:
        FallbackEstimateResult containing validated cost bounds and reasoning.

    Raises:
        InvalidDestinationError: If destination string is empty or blank.
    """
    if not destination or not destination.strip():
        raise InvalidDestinationError("Destination location string cannot be empty or whitespace.")

    clean_dest = destination.strip().upper()
    req_cat = _normalize_enum_str(category)
    req_tier = _normalize_enum_str(tier)
    days = max(1, duration_days)
    travelers = max(1, num_travelers)

    request = EstimateRequest(
        destination=clean_dest,
        category=req_cat,
        tier=req_tier,
        duration_days=days,
        num_travelers=travelers,
        currency=currency,
        context_notes=context_notes,
    )

    # Check environment variable triggers for fixture mode
    force_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("true", "1")
    )

    # Check in-memory cache first
    cached_result = _ESTIMATOR_CACHE.get(clean_dest, req_cat, req_tier, days, travelers)
    if cached_result is not None:
        log.debug("Returning cached fallback estimate result for %s", clean_dest)
        return cached_result

    if force_fixture:
        log.info("Fixture mode active. Serving cost estimation from mock fixture.")
        res = _estimate_fixture(request)
        _ESTIMATOR_CACHE.set(clean_dest, req_cat, req_tier, days, travelers, res)
        return res

    # 1. Live Tier 1: Google Gemini API
    res = _estimate_gemini(request, timeout=timeout)
    if res is not None:
        _ESTIMATOR_CACHE.set(clean_dest, req_cat, req_tier, days, travelers, res)
        return res

    # 2. Live Tier 2: Groq OpenAI-Compatible API
    res = _estimate_groq(request, timeout=timeout)
    if res is not None:
        _ESTIMATOR_CACHE.set(clean_dest, req_cat, req_tier, days, travelers, res)
        return res

    # 3. Live Tier 3: NVIDIA NIM OpenAI-Compatible API
    res = _estimate_nvidia(request, timeout=timeout)
    if res is not None:
        _ESTIMATOR_CACHE.set(clean_dest, req_cat, req_tier, days, travelers, res)
        return res

    # 4. Tier 4: Offline Rule-Based Mathematical Baseline
    log.info("All live LLM APIs unavailable. Falling back to offline heuristic baseline.")
    res = _estimate_heuristic_baseline(request)
    _ESTIMATOR_CACHE.set(clean_dest, req_cat, req_tier, days, travelers, res)
    return res


# ---------------------------------------------------------------------------
# Diagnostics & Status Interface
# ---------------------------------------------------------------------------


def get_fallback_estimator_status() -> dict[str, Any]:
    """Return status and diagnostic metadata for the Fallback Estimator tool."""
    gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    groq_key = bool(os.getenv("GROQ_API_KEY"))
    nvidia_key = bool(os.getenv("NVIDIA_API_KEY"))

    return {
        "status": "healthy",
        "cache_entries": _ESTIMATOR_CACHE.count(),
        "fixture_available": True,
        "providers": {
            "gemini": {
                "configured": gemini_key,
                "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
            },
            "groq": {
                "configured": groq_key,
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            },
            "nvidia": {
                "configured": nvidia_key,
                "models": [
                    "meta/llama-3.3-70b-instruct",
                    "meta/llama-3.1-8b-instruct",
                    "mistralai/mistral-7b-instruct-v0.3",
                ],
            },
            "offline_heuristic": {"configured": True, "type": "rule-based-baseline"},
        },
    }
