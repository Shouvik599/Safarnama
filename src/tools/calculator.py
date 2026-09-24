"""Deterministic financial and travel budget calculation engine.

Strictly enforces the architectural invariant: LLM-based arithmetic is forbidden.
All trip cost additions, splits, averages, contingency buffers, and variances
must be computed deterministically through this module using exact decimal arithmetic.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class CalculatorError(Exception):
    """Base exception for all calculator tool errors."""


class InvalidAmountError(CalculatorError, ValueError):
    """Raised when an expense amount is negative, infinite, NaN, or non-numeric."""


class InvalidTravelerCountError(CalculatorError, ValueError):
    """Raised when traveler count is not a positive integer (>= 1)."""


class InvalidDaysError(CalculatorError, ValueError):
    """Raised when trip duration is not a positive integer (>= 1)."""


class InvalidPercentageError(CalculatorError, ValueError):
    """Raised when a buffer or discount percentage is negative or invalid."""


# ---------------------------------------------------------------------------
# Structured Result Models
# ---------------------------------------------------------------------------


class BudgetVariance(BaseModel):
    """Deterministic comparison between total trip cost and user-allocated budget."""

    user_budget: float = Field(description="User allocated budget ceiling in INR.")
    total_cost: float = Field(description="Total actual or planned expense in INR.")
    variance: float = Field(
        description="Cost minus budget (positive = over budget, negative = under budget)."
    )
    percentage_variance: float = Field(
        description="Percentage deviation from user budget (e.g. +12.5% or -8.0%)."
    )
    status: str = Field(
        description="Budget health classification: 'UNDER_BUDGET', 'EXACT', or 'OVER_BUDGET'."
    )
    is_over_budget: bool = Field(description="True if total_cost strictly exceeds user_budget.")


class BudgetBreakdown(BaseModel):
    """Comprehensive structured breakdown of expenses across travel categories."""

    categories: dict[str, float] = Field(
        description="Rounded costs per category (flights, hotels, activities, food, visa, etc.)."
    )
    category_shares: dict[str, float] = Field(
        description="Percentage share of each category relative to subtotal (0.0 to 100.0)."
    )
    subtotal: float = Field(description="Sum of all base category costs before buffer.")
    buffer_percentage: float = Field(description="Contingency buffer percentage applied.")
    contingency_buffer: float = Field(description="Contingency buffer amount in INR.")
    grand_total: float = Field(description="Final total including contingency buffer.")
    per_person: float | None = Field(
        default=None, description="Cost per traveler if traveler count was supplied."
    )
    per_day: float | None = Field(
        default=None, description="Average cost per day if duration was supplied."
    )


# ---------------------------------------------------------------------------
# Pure Deterministic Arithmetic Helpers
# ---------------------------------------------------------------------------


def round_currency(amount: float | int | Decimal | str) -> float:
    """Safely round an amount to 2 decimal places using bankers-safe half-up rounding.

    Args:
        amount: Numeric amount to format.

    Returns:
        Rounded float representation.

    Raises:
        InvalidAmountError: If amount is non-numeric, NaN, infinite, or negative.
    """
    if isinstance(amount, float) and (math.isnan(amount) or math.isinf(amount)):
        raise InvalidAmountError(f"Amount cannot be NaN or infinite: {amount!r}")

    try:
        dec = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InvalidAmountError(f"Invalid numeric amount: {amount!r}") from exc

    if dec.is_nan() or dec.is_infinite():
        raise InvalidAmountError(f"Amount cannot be NaN or infinite: {amount!r}")

    return float(dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_total_expenses(
    expenses: Sequence[float | int | Decimal | str] | Mapping[str, float | int | Decimal | str],
) -> float:
    """Sum a sequence or dictionary of expenses deterministically.

    Args:
        expenses: Sequence of numbers or mapping of item names to amounts.

    Returns:
        Total expense rounded to 2 decimal places.

    Raises:
        InvalidAmountError: If any expense item is negative, NaN, or non-numeric.
    """
    items = expenses.values() if isinstance(expenses, Mapping) else expenses

    total = Decimal("0.00")
    for item in items:
        if isinstance(item, float) and (math.isnan(item) or math.isinf(item)):
            raise InvalidAmountError(f"Expense item cannot be NaN or infinite: {item!r}")
        try:
            d = Decimal(str(item))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise InvalidAmountError(f"Invalid expense value {item!r}") from exc

        if d < 0:
            raise InvalidAmountError(f"Expense cannot be negative: {item!r}")

        total += d

    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_per_person_cost(
    total_cost: float | int | Decimal | str,
    travelers: int,
) -> float:
    """Calculate expense share per traveler.

    Args:
        total_cost: Total trip or component expense.
        travelers: Count of travelers (must be >= 1).

    Returns:
        Per-person cost rounded to 2 decimal places.

    Raises:
        InvalidTravelerCountError: If travelers < 1 or not an integer.
        InvalidAmountError: If total_cost is negative or invalid.
    """
    if not isinstance(travelers, int) or travelers < 1:
        raise InvalidTravelerCountError(
            f"Traveler count must be an integer >= 1, received {travelers!r}"
        )

    rounded_total = round_currency(total_cost)
    if rounded_total < 0:
        raise InvalidAmountError(f"Total cost cannot be negative: {total_cost!r}")

    dec_total = Decimal(str(rounded_total))
    per_person = dec_total / Decimal(travelers)
    return float(per_person.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_daily_average(
    total_cost: float | int | Decimal | str,
    days: int,
) -> float:
    """Calculate average expense per day.

    Args:
        total_cost: Total trip or category expense.
        days: Trip duration in days (must be >= 1).

    Returns:
        Average daily cost rounded to 2 decimal places.

    Raises:
        InvalidDaysError: If days < 1 or not an integer.
        InvalidAmountError: If total_cost is negative or invalid.
    """
    if not isinstance(days, int) or days < 1:
        raise InvalidDaysError(f"Trip days must be an integer >= 1, received {days!r}")

    rounded_total = round_currency(total_cost)
    if rounded_total < 0:
        raise InvalidAmountError(f"Total cost cannot be negative: {total_cost!r}")

    dec_total = Decimal(str(rounded_total))
    daily = dec_total / Decimal(days)
    return float(daily.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_contingency_buffer(
    base_cost: float | int | Decimal | str,
    buffer_percentage: float | int | Decimal | str = 10.0,
) -> float:
    """Calculate safety contingency buffer amount.

    Args:
        base_cost: Base cost before buffer (must be >= 0).
        buffer_percentage: Percentage buffer to reserve (default 10.0%).

    Returns:
        Buffer amount rounded to 2 decimal places.

    Raises:
        InvalidPercentageError: If buffer_percentage is negative or non-numeric.
        InvalidAmountError: If base_cost is negative or invalid.
    """
    rounded_base = round_currency(base_cost)
    if rounded_base < 0:
        raise InvalidAmountError(f"Base cost cannot be negative: {base_cost!r}")

    try:
        pct = Decimal(str(buffer_percentage))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InvalidPercentageError(f"Invalid buffer percentage: {buffer_percentage!r}") from exc

    if pct < 0:
        raise InvalidPercentageError(f"Buffer percentage cannot be negative: {buffer_percentage!r}")

    buffer_amount = Decimal(str(rounded_base)) * (pct / Decimal("100"))
    return float(buffer_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_total_with_buffer(
    base_cost: float | int | Decimal | str,
    buffer_percentage: float | int | Decimal | str = 10.0,
) -> float:
    """Calculate grand total including safety contingency buffer.

    Args:
        base_cost: Base cost before buffer.
        buffer_percentage: Contingency percentage (default 10.0%).

    Returns:
        Base cost + buffer amount, rounded to 2 decimal places.
    """
    base = round_currency(base_cost)
    buffer = calculate_contingency_buffer(base, buffer_percentage)
    total_dec = Decimal(str(base)) + Decimal(str(buffer))
    return float(total_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_budget_variance(
    total_cost: float | int | Decimal | str,
    user_budget: float | int | Decimal | str,
) -> BudgetVariance:
    """Calculate deviation between total plan cost and user's allocated budget ceiling.

    Args:
        total_cost: Total calculated cost in INR.
        user_budget: User's allocated budget in INR.

    Returns:
        BudgetVariance model with difference, percentage, and health status.

    Raises:
        InvalidAmountError: If either amount is negative, NaN, or non-numeric.
    """
    rounded_cost = round_currency(total_cost)
    rounded_budget = round_currency(user_budget)

    if rounded_cost < 0:
        raise InvalidAmountError(f"Total cost cannot be negative: {total_cost!r}")
    if rounded_budget < 0:
        raise InvalidAmountError(f"User budget cannot be negative: {user_budget!r}")

    dec_cost = Decimal(str(rounded_cost))
    dec_budget = Decimal(str(rounded_budget))

    diff = dec_cost - dec_budget

    if dec_budget > Decimal("0.00"):
        pct_diff = (diff / dec_budget) * Decimal("100")
    else:
        pct_diff = Decimal("100.00") if dec_cost > 0 else Decimal("0.00")

    if diff > Decimal("0.00"):
        status = "OVER_BUDGET"
        is_over = True
    elif diff < Decimal("0.00"):
        status = "UNDER_BUDGET"
        is_over = False
    else:
        status = "EXACT"
        is_over = False

    return BudgetVariance(
        user_budget=rounded_budget,
        total_cost=rounded_cost,
        variance=float(diff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        percentage_variance=float(pct_diff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        status=status,
        is_over_budget=is_over,
    )


def calculate_rooms_needed(
    travelers: int,
    standard_occupancy: int = 2,
) -> int:
    """Calculate minimum hotel rooms required for a travel party.

    Args:
        travelers: Number of travelers (>= 1).
        standard_occupancy: Max adults/guests per standard room (default 2).

    Returns:
        Ceiling of travelers divided by standard_occupancy.

    Raises:
        InvalidTravelerCountError: If travelers < 1 or occupancy < 1.
    """
    if not isinstance(travelers, int) or travelers < 1:
        raise InvalidTravelerCountError(f"Traveler count must be an integer >= 1: {travelers!r}")
    if not isinstance(standard_occupancy, int) or standard_occupancy < 1:
        raise InvalidTravelerCountError(
            f"Standard room occupancy must be an integer >= 1: {standard_occupancy!r}"
        )

    return math.ceil(travelers / standard_occupancy)


def calculate_budget_breakdown(
    category_costs: Mapping[str, float | int | Decimal | str],
    buffer_percentage: float | int | Decimal | str = 10.0,
    travelers: int | None = None,
    days: int | None = None,
) -> BudgetBreakdown:
    """Generate a comprehensive multi-category budget breakdown.

    Args:
        category_costs: Mapping of category names to amounts.
        buffer_percentage: Contingency percentage (default 10.0%).
        travelers: Optional traveler count for per-person calculation.
        days: Optional duration in days for daily average calculation.

    Returns:
        BudgetBreakdown model containing categories, shares, buffer, and totals.
    """
    rounded_categories: dict[str, float] = {}
    for cat, cost in category_costs.items():
        rounded = round_currency(cost)
        if rounded < 0:
            raise InvalidAmountError(f"Cost for category {cat!r} cannot be negative: {cost!r}")
        rounded_categories[cat] = rounded

    subtotal = calculate_total_expenses(rounded_categories)
    dec_subtotal = Decimal(str(subtotal))

    shares: dict[str, float] = {}
    for cat, cost in rounded_categories.items():
        if dec_subtotal > Decimal("0.00"):
            share = (Decimal(str(cost)) / dec_subtotal) * Decimal("100")
            shares[cat] = float(share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            shares[cat] = 0.0

    buffer_amt = calculate_contingency_buffer(subtotal, buffer_percentage)
    grand_total = float(
        (dec_subtotal + Decimal(str(buffer_amt))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )

    per_person = (
        calculate_per_person_cost(grand_total, travelers) if travelers is not None else None
    )
    per_day = calculate_daily_average(grand_total, days) if days is not None else None

    return BudgetBreakdown(
        categories=rounded_categories,
        category_shares=shares,
        subtotal=subtotal,
        buffer_percentage=float(Decimal(str(buffer_percentage)).quantize(Decimal("0.01"))),
        contingency_buffer=buffer_amt,
        grand_total=grand_total,
        per_person=per_person,
        per_day=per_day,
    )
