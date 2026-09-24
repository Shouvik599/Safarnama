"""Unit tests for Phase 3 Forex currency conversion tool (src/tools/forex.py).

Verifies fixture mode, offline baseline fallbacks, cache invalidation, precision rounding,
identity conversions, and error handling for unknown currencies.
"""

from __future__ import annotations

import math
import urllib.error
from unittest.mock import patch

import pytest
from src.tools.calculator import InvalidAmountError
from src.tools.forex import (
    ForexConversion,
    ForexError,
    ForexNetworkError,
    UnsupportedCurrencyError,
    clear_forex_cache,
    convert_currency,
    convert_to_inr,
    get_exchange_rate,
)


@pytest.fixture(autouse=True)
def _reset_forex_cache() -> None:
    """Ensure in-memory cache is clean before and after each test."""
    clear_forex_cache()
    yield
    clear_forex_cache()


# ===========================================================================
# 1. Fixture-backed Conversions
# ===========================================================================


def test_convert_to_inr_from_usd_fixture() -> None:
    """100 USD at 87.50 INR/USD should be exactly 8,750.00 INR."""
    conv = convert_to_inr(100.0, "USD", use_fixture=True)
    assert isinstance(conv, ForexConversion)
    assert conv.from_currency == "USD"
    assert conv.to_currency == "INR"
    assert conv.original_amount == 100.0
    assert conv.converted_amount == 8750.0
    assert conv.exchange_rate == 87.5
    assert conv.provider == "fixture"
    assert conv.is_estimated is False


def test_convert_to_inr_from_eur_fixture() -> None:
    """Verify EUR to INR cross-currency calculation from USD base rates."""
    # In mock fixture: USD->INR = 87.5, USD->EUR = 0.92
    # EUR->INR = 87.5 / 0.92 = 95.108696 -> 100 EUR = 9,510.87 INR
    conv = convert_to_inr(100.0, "EUR", use_fixture=True)
    assert conv.from_currency == "EUR"
    assert conv.converted_amount == 9510.87
    assert conv.provider == "fixture"


def test_convert_to_inr_identity_inr() -> None:
    """Converting INR to INR should immediately return 1:1 without network access."""
    conv = convert_to_inr(12500.50, "INR")
    assert conv.from_currency == "INR"
    assert conv.to_currency == "INR"
    assert conv.original_amount == 12500.50
    assert conv.converted_amount == 12500.50
    assert conv.exchange_rate == 1.0
    assert conv.provider == "identity"
    assert conv.is_estimated is False


def test_convert_cross_currency_non_inr() -> None:
    """Cross conversion between two foreign currencies (e.g. JPY to USD)."""
    # 15200 JPY in mock fixture (152 JPY per USD) = 100.0 USD
    conv = convert_currency(15200.0, "JPY", "USD", use_fixture=True)
    assert conv.from_currency == "JPY"
    assert conv.to_currency == "USD"
    assert conv.converted_amount == 100.0


# ===========================================================================
# 2. Direct Rate Queries
# ===========================================================================


def test_get_exchange_rate_usd_to_inr() -> None:
    rate = get_exchange_rate("USD", "INR", use_fixture=True)
    assert rate == 87.5


def test_get_exchange_rate_identity() -> None:
    assert get_exchange_rate("EUR", "EUR") == 1.0
    assert get_exchange_rate("INR", "INR") == 1.0


# ===========================================================================
# 3. Offline Baseline Fallback Resilience
# ===========================================================================


def test_fallback_to_fawazahmed_when_open_access_fails() -> None:
    """When ExchangeRate-API open access fails, tool falls back to FawazAhmed CDN."""
    with (
        patch("src.tools.forex._fetch_live_open_access", side_effect=RuntimeError("Rate limited")),
        patch(
            "src.tools.forex._fetch_live_fawazahmed",
            return_value=(
                {"USD": 1.0, "INR": 92.5},
                "fawazahmed-cdn",
                False,
                "2026-09-25T00:00:00Z",
            ),
        ),
    ):
        conv = convert_to_inr(100.0, "USD", use_fixture=False)
        assert conv.provider == "fawazahmed-cdn"
        assert conv.is_estimated is False
        assert conv.converted_amount == 9250.0


def test_fallback_to_frankfurter_when_fawaz_fails() -> None:
    """When both open access and FawazAhmed fail, tool falls back to Frankfurter."""
    with (
        patch("src.tools.forex._fetch_live_open_access", side_effect=RuntimeError("Failed")),
        patch("src.tools.forex._fetch_live_fawazahmed", side_effect=RuntimeError("CDN down")),
        patch(
            "src.tools.forex._fetch_live_frankfurter",
            return_value=({"USD": 1.0, "INR": 93.0}, "frankfurter", False, "2026-09-25T00:00:00Z"),
        ),
    ):
        conv = convert_to_inr(100.0, "USD", use_fixture=False)
        assert conv.provider == "frankfurter"
        assert conv.is_estimated is False
        assert conv.converted_amount == 9300.0


def test_fallback_to_offline_baseline_when_network_fails() -> None:
    """When all live endpoints fail, tool must fall back to built-in baseline rates."""
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("Network unreachable"),
    ):
        conv = convert_to_inr(100.0, "USD", use_fixture=False)
        assert conv.provider == "offline-baseline"
        assert conv.is_estimated is True
        assert conv.converted_amount == 8750.0  # baseline rate for USD is 87.50


def test_fallback_handles_major_travel_currencies_offline() -> None:
    """Verify key Safarnama destinations resolve offline."""
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("No connection"),
    ):
        currencies = ["EUR", "GBP", "JPY", "AED", "THB", "SGD", "UZS", "NOK"]
        for curr in currencies:
            conv = convert_to_inr(100.0, curr, use_fixture=False)
            assert conv.converted_amount > 0.0
            assert conv.provider == "offline-baseline"
            assert conv.is_estimated is True


# ===========================================================================
# 4. In-Memory Cache Behavior
# ===========================================================================


def test_rates_are_cached_in_memory() -> None:
    """Subsequent calls should use cached rates without making network calls."""
    with patch(
        "src.tools.forex._fetch_live_open_access",
        return_value=({"USD": 1.0, "INR": 90.0}, "open-access", False, "2026-09-25T00:00:00Z"),
    ) as mock_fetch:
        # First call fetches and caches
        conv1 = convert_to_inr(100.0, "USD", use_fixture=False)
        assert conv1.converted_amount == 9000.0
        assert mock_fetch.call_count == 1

        # Second call uses cache
        conv2 = convert_to_inr(200.0, "USD", use_fixture=False)
        assert conv2.converted_amount == 18000.0
        assert mock_fetch.call_count == 1


def test_clear_forex_cache_forces_refresh() -> None:
    """Clearing cache causes next call to re-fetch."""
    with patch(
        "src.tools.forex._fetch_live_open_access",
        return_value=({"USD": 1.0, "INR": 85.0}, "open-access", False, "2026-09-25T00:00:00Z"),
    ) as mock_fetch:
        convert_to_inr(100.0, "USD", use_fixture=False)
        assert mock_fetch.call_count == 1

        clear_forex_cache()
        convert_to_inr(100.0, "USD", use_fixture=False)
        assert mock_fetch.call_count == 2


# ===========================================================================
# 5. Error Handling & Validation
# ===========================================================================


def test_convert_negative_amount_raises() -> None:
    with pytest.raises(InvalidAmountError):
        convert_to_inr(-50.0, "USD", use_fixture=True)


@pytest.mark.parametrize("invalid_amt", [math.nan, math.inf, "non-numeric", None])
def test_convert_invalid_amount_raises(invalid_amt) -> None:
    with pytest.raises(InvalidAmountError):
        convert_to_inr(invalid_amt, "USD", use_fixture=True)


def test_convert_unsupported_currency_raises() -> None:
    with pytest.raises(UnsupportedCurrencyError, match="NONEXISTENT"):
        convert_to_inr(100.0, "NONEXISTENT", use_fixture=True)


def test_forex_exception_hierarchy() -> None:
    assert issubclass(UnsupportedCurrencyError, ForexError)
    assert issubclass(ForexNetworkError, ForexError)
    assert issubclass(UnsupportedCurrencyError, ValueError)
