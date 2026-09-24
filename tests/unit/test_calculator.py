"""Unit tests for Phase 3 deterministic calculator tool (src/tools/calculator.py).

Verifies strict mathematical precision, rounding, budget variances, per-person splits,
contingency buffer computations, and input validation without LLM hallucination.
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest
from src.tools.calculator import (
    BudgetBreakdown,
    BudgetVariance,
    CalculatorError,
    InvalidAmountError,
    InvalidDaysError,
    InvalidPercentageError,
    InvalidTravelerCountError,
    calculate_budget_breakdown,
    calculate_budget_variance,
    calculate_contingency_buffer,
    calculate_daily_average,
    calculate_per_person_cost,
    calculate_rooms_needed,
    calculate_total_expenses,
    calculate_total_with_buffer,
    round_currency,
)

# ===========================================================================
# 1. Currency Rounding & Sanitization
# ===========================================================================


def test_round_currency_standard_values() -> None:
    assert round_currency(100) == 100.0
    assert round_currency(100.5) == 100.5
    assert round_currency(100.555) == 100.56
    assert round_currency(100.554) == 100.55
    assert round_currency(Decimal("1234.567")) == 1234.57
    assert round_currency("543.21") == 543.21


def test_round_currency_half_up() -> None:
    # 0.005 rounds up to 0.01
    assert round_currency(10.005) == 10.01
    assert round_currency(10.015) == 10.02


@pytest.mark.parametrize(
    "invalid_amount", [math.nan, math.inf, -math.inf, "invalid", None, object()]
)
def test_round_currency_invalid_inputs_raise(invalid_amount) -> None:
    with pytest.raises(InvalidAmountError):
        round_currency(invalid_amount)


# ===========================================================================
# 2. Total Expenses Aggregation
# ===========================================================================


def test_calculate_total_expenses_sequence() -> None:
    expenses = [35000.50, 18500.25, 4200.00, 1250.75]
    total = calculate_total_expenses(expenses)
    assert total == 58951.50


def test_calculate_total_expenses_mapping() -> None:
    category_map = {
        "flights": 42000.00,
        "hotels": 35000.50,
        "activities": 12000.25,
        "food": 9500.00,
        "visa": 3500.00,
    }
    total = calculate_total_expenses(category_map)
    assert total == 102000.75


def test_calculate_total_expenses_empty() -> None:
    assert calculate_total_expenses([]) == 0.0
    assert calculate_total_expenses({}) == 0.0


def test_calculate_total_expenses_negative_raises() -> None:
    with pytest.raises(InvalidAmountError, match="cannot be negative"):
        calculate_total_expenses([100.0, -50.0, 20.0])


@pytest.mark.parametrize("bad_val", [math.nan, "non-numeric", None])
def test_calculate_total_expenses_invalid_types_raise(bad_val) -> None:
    with pytest.raises(InvalidAmountError):
        calculate_total_expenses([100.0, bad_val])


# ===========================================================================
# 3. Per-Person Cost Splitting
# ===========================================================================


def test_calculate_per_person_cost_exact() -> None:
    assert calculate_per_person_cost(100000.00, 2) == 50000.00
    assert calculate_per_person_cost(100000.00, 4) == 25000.00
    assert calculate_per_person_cost(75000.00, 1) == 75000.00


def test_calculate_per_person_cost_rounding() -> None:
    # 100 / 3 = 33.3333... -> 33.33
    assert calculate_per_person_cost(100.00, 3) == 33.33
    # 200 / 3 = 66.6666... -> 66.67
    assert calculate_per_person_cost(200.00, 3) == 66.67


@pytest.mark.parametrize("bad_travelers", [0, -1, -5, 1.5, "two", None])
def test_calculate_per_person_cost_invalid_travelers_raise(bad_travelers) -> None:
    with pytest.raises(InvalidTravelerCountError):
        calculate_per_person_cost(50000.00, bad_travelers)


def test_calculate_per_person_cost_negative_total_raises() -> None:
    with pytest.raises(InvalidAmountError):
        calculate_per_person_cost(-500.00, 2)


# ===========================================================================
# 4. Daily Average Calculation
# ===========================================================================


def test_calculate_daily_average_exact() -> None:
    assert calculate_daily_average(70000.00, 7) == 10000.00
    assert calculate_daily_average(100000.00, 10) == 10000.00


def test_calculate_daily_average_rounding() -> None:
    # 500 / 3 = 166.666... -> 166.67
    assert calculate_daily_average(500.00, 3) == 166.67


@pytest.mark.parametrize("bad_days", [0, -1, -10, 3.5, "five", None])
def test_calculate_daily_average_invalid_days_raise(bad_days) -> None:
    with pytest.raises(InvalidDaysError):
        calculate_daily_average(25000.00, bad_days)


# ===========================================================================
# 5. Contingency Buffer & Totals
# ===========================================================================


def test_calculate_contingency_buffer_default_10_percent() -> None:
    buffer_amt = calculate_contingency_buffer(100000.00)
    assert buffer_amt == 10000.00


def test_calculate_contingency_buffer_custom_percentage() -> None:
    assert calculate_contingency_buffer(50000.00, 15.0) == 7500.00
    assert calculate_contingency_buffer(50000.00, 0.0) == 0.00
    assert calculate_contingency_buffer(12345.67, 7.5) == 925.93


def test_calculate_contingency_buffer_negative_percentage_raises() -> None:
    with pytest.raises(InvalidPercentageError):
        calculate_contingency_buffer(50000.00, -5.0)


def test_calculate_total_with_buffer() -> None:
    assert calculate_total_with_buffer(100000.00, 10.0) == 110000.00
    assert calculate_total_with_buffer(50000.00, 15.0) == 57500.00
    assert calculate_total_with_buffer(50000.00, 0.0) == 50000.00


# ===========================================================================
# 6. Budget Variance Analysis
# ===========================================================================


def test_calculate_budget_variance_under_budget() -> None:
    variance = calculate_budget_variance(total_cost=80000.00, user_budget=100000.00)
    assert isinstance(variance, BudgetVariance)
    assert variance.user_budget == 100000.00
    assert variance.total_cost == 80000.00
    assert variance.variance == -20000.00
    assert variance.percentage_variance == -20.00
    assert variance.status == "UNDER_BUDGET"
    assert variance.is_over_budget is False


def test_calculate_budget_variance_exact() -> None:
    variance = calculate_budget_variance(total_cost=100000.00, user_budget=100000.00)
    assert variance.variance == 0.00
    assert variance.percentage_variance == 0.00
    assert variance.status == "EXACT"
    assert variance.is_over_budget is False


def test_calculate_budget_variance_over_budget() -> None:
    variance = calculate_budget_variance(total_cost=125000.00, user_budget=100000.00)
    assert variance.variance == 25000.00
    assert variance.percentage_variance == 25.00
    assert variance.status == "OVER_BUDGET"
    assert variance.is_over_budget is True


def test_calculate_budget_variance_negative_amounts_raise() -> None:
    with pytest.raises(InvalidAmountError):
        calculate_budget_variance(total_cost=-1000.0, user_budget=5000.0)
    with pytest.raises(InvalidAmountError):
        calculate_budget_variance(total_cost=1000.0, user_budget=-5000.0)


# ===========================================================================
# 7. Room Allocation Requirements
# ===========================================================================


@pytest.mark.parametrize(
    "travelers,occupancy,expected_rooms",
    [
        (1, 2, 1),
        (2, 2, 1),
        (3, 2, 2),
        (4, 2, 2),
        (5, 2, 3),
        (6, 2, 3),
        (5, 3, 2),
        (10, 4, 3),
    ],
)
def test_calculate_rooms_needed(travelers: int, occupancy: int, expected_rooms: int) -> None:
    assert calculate_rooms_needed(travelers, standard_occupancy=occupancy) == expected_rooms


@pytest.mark.parametrize("bad_val", [0, -1, "two", None])
def test_calculate_rooms_needed_invalid_inputs_raise(bad_val) -> None:
    with pytest.raises(InvalidTravelerCountError):
        calculate_rooms_needed(bad_val)
    with pytest.raises(InvalidTravelerCountError):
        calculate_rooms_needed(2, standard_occupancy=bad_val)


# ===========================================================================
# 8. Comprehensive Multi-Category Budget Breakdown
# ===========================================================================


def test_calculate_budget_breakdown_comprehensive() -> None:
    categories = {
        "flights": 40000.00,
        "hotels": 30000.00,
        "activities": 15000.00,
        "food": 10000.00,
        "visa": 5000.00,
    }
    breakdown = calculate_budget_breakdown(
        categories,
        buffer_percentage=10.0,
        travelers=2,
        days=5,
    )
    assert isinstance(breakdown, BudgetBreakdown)
    assert breakdown.subtotal == 100000.00
    assert breakdown.contingency_buffer == 10000.00
    assert breakdown.grand_total == 110000.00

    # Shares: 40k/100k = 40%, 30k/100k = 30%, etc.
    assert breakdown.category_shares["flights"] == 40.0
    assert breakdown.category_shares["hotels"] == 30.0
    assert breakdown.category_shares["activities"] == 15.0
    assert breakdown.category_shares["food"] == 10.0
    assert breakdown.category_shares["visa"] == 5.0

    # Per person: 110,000 / 2 = 55,000
    assert breakdown.per_person == 55000.00
    # Per day: 110,000 / 5 = 22,000
    assert breakdown.per_day == 22000.00


def test_calculate_budget_breakdown_without_travelers_or_days() -> None:
    categories = {"flights": 20000.00, "hotels": 15000.00}
    breakdown = calculate_budget_breakdown(categories)
    assert breakdown.subtotal == 35000.00
    assert breakdown.contingency_buffer == 3500.00
    assert breakdown.grand_total == 38500.00
    assert breakdown.per_person is None
    assert breakdown.per_day is None


def test_calculate_budget_breakdown_negative_category_raises() -> None:
    with pytest.raises(InvalidAmountError):
        calculate_budget_breakdown({"flights": 20000.0, "hotels": -5000.0})


# ===========================================================================
# 9. Exception Hierarchy
# ===========================================================================


def test_calculator_exception_hierarchy() -> None:
    assert issubclass(InvalidAmountError, CalculatorError)
    assert issubclass(InvalidTravelerCountError, CalculatorError)
    assert issubclass(InvalidDaysError, CalculatorError)
    assert issubclass(InvalidPercentageError, CalculatorError)
    assert issubclass(InvalidAmountError, ValueError)
