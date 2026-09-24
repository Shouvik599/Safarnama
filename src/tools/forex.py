"""Deterministic foreign exchange (Forex) tool for travel currency conversion.

Ensures all overseas travel costs (flights, hotels, activities, food, visas)
can be converted accurately and deterministically into Indian Rupee (INR).

Architecture & Fallback Chain:
1. In-Memory Cache: 24-hour TTL in-memory rate store to prevent redundant HTTP requests.
2. Fixture Mode: When requested or SAFARNAMA_USE_FIXTURES=true, loads data/fixtures/mock_forex.json.
3. Live Tier 1 (Open Access): Keyless endpoint at https://open.er-api.com/v6/latest/USD.
4. Live Tier 2 (Authenticated): Keyed endpoint at https://v6.exchangerate-api.com/v6/{KEY}/latest/USD.
5. Offline Baseline Table: Built-in exchange rates for ~40 global travel currencies against USD/INR.
   Guarantees Safarnama never crashes even with zero internet connectivity.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.tools.calculator import InvalidAmountError, round_currency

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_forex.json"
CACHE_TTL_SECONDS = 86400  # 24 hours

# ---------------------------------------------------------------------------
# Offline Baseline Rates (Base = USD)
# ---------------------------------------------------------------------------
# Used when network is completely unreachable or provider is rate-limited.
# Provides robust, predictable offline estimates for major destination currencies.
OFFLINE_BASELINE_RATES: dict[str, float] = {
    "USD": 1.0,
    "INR": 87.50,
    "EUR": 0.92,
    "GBP": 0.78,
    "JPY": 152.0,
    "AED": 3.6725,
    "THB": 35.0,
    "SGD": 1.34,
    "MYR": 4.45,
    "IDR": 15800.0,
    "VND": 25400.0,
    "UZS": 12800.0,
    "NOK": 10.8,
    "SEK": 10.5,
    "CHF": 0.89,
    "AUD": 1.55,
    "CAD": 1.38,
    "NZD": 1.68,
    "TRY": 34.2,
    "SAR": 3.75,
    "QAR": 3.64,
    "OMR": 0.385,
    "KWD": 0.307,
    "BHD": 0.376,
    "NPR": 140.0,
    "LKR": 300.0,
    "BTN": 87.50,
    "MVR": 15.4,
    "EGP": 48.5,
    "ZAR": 18.2,
    "KES": 129.0,
    "GEL": 2.75,
    "AZN": 1.70,
    "KZT": 490.0,
    "KRW": 1380.0,
    "HKD": 7.78,
    "TWD": 32.5,
    "CNY": 7.25,
}


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class ForexError(Exception):
    """Base exception for all forex conversion errors."""


class UnsupportedCurrencyError(ForexError, ValueError):
    """Raised when an unrecognised or unsupported ISO-4217 currency code is requested."""


class ForexNetworkError(ForexError):
    """Raised when all external live forex endpoints fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# Pydantic Output Contracts
# ---------------------------------------------------------------------------


class ForexConversion(BaseModel):
    """Structured, auditable result of a currency conversion."""

    from_currency: str = Field(
        description="Source ISO 4217 uppercase 3-letter currency code, e.g. 'USD', 'EUR'."
    )
    to_currency: str = Field(
        description="Target ISO 4217 uppercase 3-letter currency code, e.g. 'INR'."
    )
    original_amount: float = Field(description="Amount in the source currency.")
    converted_amount: float = Field(
        description="Deterministic converted amount in target currency rounded to 2 decimals."
    )
    exchange_rate: float = Field(
        description="Applied conversion rate (units of target currency per 1 unit of source)."
    )
    provider: str = Field(
        description=(
            "Provenance of the rate: 'fixture', 'open-access', "
            "'authenticated', or 'offline-baseline'."
        )
    )
    is_estimated: bool = Field(
        description="True if calculated using fallback offline baseline estimates."
    )
    timestamp: str = Field(description="ISO 8601 timestamp of rates data used for conversion.")


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class _ForexCache:
    def __init__(self) -> None:
        self.rates: dict[str, float] = {}
        self.provider: str = ""
        self.is_estimated: bool = False
        self.timestamp: str = ""
        self.fetched_at: float = 0.0

    def is_valid(self) -> bool:
        return bool(self.rates) and (time.time() - self.fetched_at < CACHE_TTL_SECONDS)

    def set(
        self,
        rates: dict[str, float],
        provider: str,
        is_estimated: bool,
        timestamp: str,
    ) -> None:
        self.rates = dict(rates)
        self.provider = provider
        self.is_estimated = is_estimated
        self.timestamp = timestamp
        self.fetched_at = time.time()

    def clear(self) -> None:
        self.rates = {}
        self.provider = ""
        self.is_estimated = False
        self.timestamp = ""
        self.fetched_at = 0.0


_global_cache = _ForexCache()


def clear_forex_cache() -> None:
    """Clear the in-memory exchange rates cache."""
    _global_cache.clear()


# ---------------------------------------------------------------------------
# Rate Ingestion and Resolution Pipeline
# ---------------------------------------------------------------------------


def _load_fixture_rates() -> tuple[dict[str, float], str, bool, str]:
    """Load rates from local fixture file."""
    if not FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Forex fixture file missing at {FIXTURE_PATH}")
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    rates: dict[str, float] = {k.upper(): float(v) for k, v in data.get("rates", {}).items()}
    ts = data.get("time_last_update_utc", datetime.now(UTC).isoformat())
    return rates, "fixture", False, ts


def _fetch_live_open_access() -> tuple[dict[str, float], str, bool, str]:
    """Fetch live rates from ExchangeRate-API open access endpoint."""
    url = "https://open.er-api.com/v6/latest/USD"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Safarnama/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("result") != "success" or "rates" not in data:
        raise RuntimeError(f"Open access response not successful: {data.get('result')}")

    rates = {k.upper(): float(v) for k, v in data["rates"].items()}
    ts = data.get("time_last_update_utc", datetime.now(UTC).isoformat())
    return rates, "open-access", False, ts


def _fetch_live_authenticated(api_key: str) -> tuple[dict[str, float], str, bool, str]:
    """Fetch live rates from ExchangeRate-API authenticated endpoint."""
    url = f"https://v6.exchangerate-api.com/v6/{api_key.strip()}/latest/USD"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Safarnama/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=8.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("result") != "success" or "conversion_rates" not in data:
        raise RuntimeError(f"Authenticated response not successful: {data.get('result')}")

    rates = {k.upper(): float(v) for k, v in data["conversion_rates"].items()}
    ts = data.get("time_last_update_utc", datetime.now(UTC).isoformat())
    return rates, "authenticated", False, ts


def get_rates_table(
    force_refresh: bool = False,
    use_fixture: bool | None = None,
) -> tuple[dict[str, float], str, bool, str]:
    """Retrieve the current exchange rate dictionary (relative to USD).

    Follows the multi-tier fallback architecture:
    Fixture -> In-Memory Cache -> Open Access -> Authenticated -> Offline Baseline.

    Returns:
        tuple of (rates_dict, provider_name, is_estimated, timestamp)
    """
    should_use_fixture = (
        use_fixture
        if use_fixture is not None
        else os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
    )

    if should_use_fixture:
        return _load_fixture_rates()

    if not force_refresh and _global_cache.is_valid():
        return (
            _global_cache.rates,
            _global_cache.provider,
            _global_cache.is_estimated,
            _global_cache.timestamp,
        )

    # Tier 1: Try Open Access
    try:
        rates, provider, is_estimated, ts = _fetch_live_open_access()
        _global_cache.set(rates, provider, is_estimated, ts)
        return rates, provider, is_estimated, ts
    except Exception as exc:
        log.warning("Open access forex endpoint failed (%s). Checking authenticated tier.", exc)

    # Tier 2: Try Authenticated if key configured
    api_key = os.getenv("EXCHANGERATE_API_KEY", "").strip()
    if api_key:
        try:
            rates, provider, is_estimated, ts = _fetch_live_authenticated(api_key)
            _global_cache.set(rates, provider, is_estimated, ts)
            return rates, provider, is_estimated, ts
        except Exception as exc:
            log.warning("Authenticated forex endpoint failed (%s). Falling back to baseline.", exc)

    # Tier 3: Fall back to Built-in Offline Baseline
    ts = datetime.now(UTC).isoformat()
    _global_cache.set(OFFLINE_BASELINE_RATES, "offline-baseline", True, ts)
    return dict(OFFLINE_BASELINE_RATES), "offline-baseline", True, ts


# ---------------------------------------------------------------------------
# Public Currency Conversion API
# ---------------------------------------------------------------------------


def get_exchange_rate(
    from_currency: str,
    to_currency: str = "INR",
    use_fixture: bool | None = None,
) -> float:
    """Retrieve the direct conversion rate between two currencies.

    Args:
        from_currency: Source currency ISO code (e.g. 'EUR', 'USD').
        to_currency: Target currency ISO code (default 'INR').
        use_fixture: Force offline fixture if True.

    Returns:
        Conversion multiplier (units of to_currency per 1 unit of from_currency).

    Raises:
        UnsupportedCurrencyError: If either currency code is not supported.
    """
    from_curr = from_currency.strip().upper()
    to_curr = to_currency.strip().upper()

    if from_curr == to_curr:
        return 1.0

    rates, _, _, _ = get_rates_table(use_fixture=use_fixture)

    if from_curr not in rates:
        raise UnsupportedCurrencyError(
            f"Unsupported or unknown source currency code: {from_currency!r}"
        )
    if to_curr not in rates:
        raise UnsupportedCurrencyError(
            f"Unsupported or unknown target currency code: {to_currency!r}"
        )

    # rates table has USD as base: rates[C] = C per 1 USD
    # 1 from_curr = (1 / rates[from_curr]) USD
    # in to_curr = rates[to_curr] / rates[from_curr]
    rate = rates[to_curr] / rates[from_curr]
    return float(Decimal(str(rate)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def convert_currency(
    amount: float | int | Decimal | str,
    from_currency: str,
    to_currency: str = "INR",
    use_fixture: bool | None = None,
) -> ForexConversion:
    """Convert an amount from a source currency to a target currency.

    Args:
        amount: Numeric amount to convert.
        from_currency: Source currency code (e.g. 'EUR', 'USD', 'JPY').
        to_currency: Target currency code (default 'INR').
        use_fixture: Force offline fixture if True.

    Returns:
        ForexConversion Pydantic model with exact rounded amounts and provenance.

    Raises:
        InvalidAmountError: If amount is negative, NaN, or non-numeric.
        UnsupportedCurrencyError: If currency code is invalid.
    """
    rounded_amt = round_currency(amount)
    if rounded_amt < 0:
        raise InvalidAmountError(f"Conversion amount cannot be negative: {amount!r}")

    from_curr = from_currency.strip().upper()
    to_curr = to_currency.strip().upper()

    if from_curr == to_curr:
        return ForexConversion(
            from_currency=from_curr,
            to_currency=to_curr,
            original_amount=rounded_amt,
            converted_amount=rounded_amt,
            exchange_rate=1.0,
            provider="identity",
            is_estimated=False,
            timestamp=datetime.now(UTC).isoformat(),
        )

    rates, provider, is_estimated, ts = get_rates_table(use_fixture=use_fixture)

    if from_curr not in rates:
        raise UnsupportedCurrencyError(f"Unsupported source currency code: {from_currency!r}")
    if to_curr not in rates:
        raise UnsupportedCurrencyError(f"Unsupported target currency code: {to_currency!r}")

    raw_rate = rates[to_curr] / rates[from_curr]
    dec_rate = Decimal(str(raw_rate)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    dec_amt = Decimal(str(rounded_amt))
    dec_converted = dec_amt * dec_rate
    converted_rounded = float(dec_converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return ForexConversion(
        from_currency=from_curr,
        to_currency=to_curr,
        original_amount=rounded_amt,
        converted_amount=converted_rounded,
        exchange_rate=float(dec_rate),
        provider=provider,
        is_estimated=is_estimated,
        timestamp=ts,
    )


def convert_to_inr(
    amount: float | int | Decimal | str,
    from_currency: str,
    use_fixture: bool | None = None,
) -> ForexConversion:
    """Convenience helper to convert any foreign amount directly to Indian Rupee (INR).

    Args:
        amount: Price or expense in foreign currency.
        from_currency: Foreign currency code (e.g. 'USD', 'EUR', 'JPY').
        use_fixture: Force offline fixture if True.

    Returns:
        ForexConversion with target currency set to 'INR'.
    """
    return convert_currency(
        amount=amount,
        from_currency=from_currency,
        to_currency="INR",
        use_fixture=use_fixture,
    )
