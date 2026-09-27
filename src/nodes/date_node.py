"""Phase 15 — Flexible Dates (Date Optimization Planning Node).

Evaluates and optimizes travel date options for Safarnama itineraries:
1. Supports three distinct date modes (Architecture Section 14 & PRD Section 5.5):
   - EXACT: Confirms user-specified dates without modification.
   - FLEXIBLE: Evaluates candidate departure dates shifted within +/- flexibility_days.
   - FIND_BEST: Evaluates candidate duration windows across window_start to window_end.
2. Evaluates candidate travel windows balancing:
   - Live pricing & logistics costs (flights/transport and hotel accommodation).
   - Weather forecasts (rain probability, average temperatures, outdoor friendliness).
   - Route feasibility and seasonal demand.
   - Calendar convenience (maximizing weekend travel days to save leave days).
3. Selects the primary recommended travel window and provides 2–3 alternatives
   with explicit trade-offs and composite quality scores (0–100).
4. Updates TripContext with the recommended dates so downstream logistics,
   experience, and budget nodes execute against the optimal dates.
5. All operations support 100% offline fixture-first execution.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from src.models.trip import (
    DateCandidate,
    DateMode,
    DateOptimizationResult,
    InitialPlanningState,
    ResolvedLocation,
    TravelScope,
    TravelStyle,
    TripContext,
    TripDates,
    TripParty,
)
from src.nodes.intake_node import process_intake
from src.tools.hotels import search_hotels
from src.tools.transport import search_transport
from src.tools.weather import get_weather_forecast

log = logging.getLogger(__name__)

# Heuristic fallback pricing defaults (INR)
DEFAULT_HEURISTIC_FLIGHT_INR = 4500.0
DEFAULT_HEURISTIC_HOTEL_INR = 4500.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class DateOptimizationError(Exception):
    """Base exception for date optimization errors."""


# ---------------------------------------------------------------------------
# Candidate Range Generation
# ---------------------------------------------------------------------------


def generate_candidate_date_ranges(dates: TripDates) -> list[tuple[str, str, int]]:
    """Generate candidate (start_date, end_date, duration_days) ranges based on DateMode.

    Args:
        dates: Validated TripDates specification.

    Returns:
        List of candidate tuples: (start_date_str, end_date_str, duration_days).
    """
    candidates: list[tuple[str, str, int]] = []

    # 1. EXACT Mode: exactly 1 candidate matching user request
    if dates.mode == DateMode.EXACT:
        if dates.start_date and dates.end_date:
            try:
                d1 = datetime.strptime(dates.start_date, "%Y-%m-%d").date()
                d2 = datetime.strptime(dates.end_date, "%Y-%m-%d").date()
                dur = (d2 - d1).days + 1
            except ValueError:
                dur = dates.duration_days or 1
            candidates.append((dates.start_date, dates.end_date, dur))
        return candidates

    # 2. FLEXIBLE Mode: shift start_date within +/- flexibility_days
    if dates.mode == DateMode.FLEXIBLE:
        base_start_str = dates.start_date
        dur = dates.duration_days or 5
        flex = dates.flexibility_days if dates.flexibility_days > 0 else 3

        if not base_start_str:
            # Fallback to +14 days from today if missing
            today = datetime.now(UTC).date()
            base_date = today + timedelta(days=14)
        else:
            try:
                base_date = datetime.strptime(base_start_str, "%Y-%m-%d").date()
            except ValueError:
                today = datetime.now(UTC).date()
                base_date = today + timedelta(days=14)

        # Generate offset range
        offsets: list[int] = []
        if flex <= 3:
            offsets = list(range(-flex, flex + 1))
        else:
            # Sample up to 5 strategic offsets across the flexible window
            offsets = sorted(
                list(
                    {
                        0,
                        -flex,
                        -max(1, flex // 2),
                        max(1, flex // 2),
                        flex,
                    }
                )
            )

        seen_starts: set[str] = set()
        for offset in offsets:
            c_start = base_date + timedelta(days=offset)
            c_end = c_start + timedelta(days=dur - 1)
            c_start_str = c_start.strftime("%Y-%m-%d")
            c_end_str = c_end.strftime("%Y-%m-%d")
            if c_start_str not in seen_starts:
                seen_starts.add(c_start_str)
                candidates.append((c_start_str, c_end_str, dur))
        return candidates

    # 3. FIND_BEST Mode: sample windows of length duration_days between window_start & window_end
    if dates.mode == DateMode.FIND_BEST:
        dur = dates.duration_days or 5
        today = datetime.now(UTC).date()
        try:
            w_start = (
                datetime.strptime(dates.window_start, "%Y-%m-%d").date()
                if dates.window_start
                else today + timedelta(days=14)
            )
        except ValueError:
            w_start = today + timedelta(days=14)

        try:
            w_end = (
                datetime.strptime(dates.window_end, "%Y-%m-%d").date()
                if dates.window_end
                else w_start + timedelta(days=30)
            )
        except ValueError:
            w_end = w_start + timedelta(days=30)

        if w_end < w_start:
            raise DateOptimizationError("window_start must be before window_end.")

        total_window_days = (w_end - w_start).days + 1
        max_start_offset = total_window_days - dur

        if max_start_offset <= 0:
            # Window too small for duration; use single window from w_start
            c_end = w_start + timedelta(days=dur - 1)
            candidates.append((w_start.strftime("%Y-%m-%d"), c_end.strftime("%Y-%m-%d"), dur))
            return candidates

        # If 5 or fewer possible start dates, evaluate all
        if max_start_offset <= 4:
            offsets = list(range(max_start_offset + 1))
        else:
            # Sample 5 candidate windows evenly spread across the window
            offsets = sorted(
                list(
                    {
                        0,
                        max_start_offset // 4,
                        max_start_offset // 2,
                        (3 * max_start_offset) // 4,
                        max_start_offset,
                    }
                )
            )

        seen_starts = set()
        for offset in offsets:
            c_start = w_start + timedelta(days=offset)
            c_end = c_start + timedelta(days=dur - 1)
            c_start_str = c_start.strftime("%Y-%m-%d")
            c_end_str = c_end.strftime("%Y-%m-%d")
            if c_start_str not in seen_starts:
                seen_starts.add(c_start_str)
                candidates.append((c_start_str, c_end_str, dur))

        return candidates

    return candidates


# ---------------------------------------------------------------------------
# Candidate Evaluation
# ---------------------------------------------------------------------------


def evaluate_date_candidate(
    start_date: str,
    end_date: str,
    duration_days: int,
    origin: ResolvedLocation,
    destinations: list[ResolvedLocation],
    party: TripParty,
    travel_style: TravelStyle,
    travel_scope: TravelScope,
    budget_inr: float,
    use_fixture: bool = False,
) -> DateCandidate:
    """Evaluate pricing, weather, seasonality, and calendar convenience for a candidate window.

    Args:
        start_date: Candidate start date string (YYYY-MM-DD).
        end_date: Candidate end date string (YYYY-MM-DD).
        duration_days: Length of the trip in days.
        origin: Resolved departure hub in India.
        destinations: List of resolved destination gateways.
        party: Traveler party headcount composition.
        travel_style: User's travel comfort preference.
        travel_scope: DOMESTIC or INTERNATIONAL.
        budget_inr: Total budget ceiling in INR.
        use_fixture: Force offline mock fixture evaluation.

    Returns:
        Evaluated DateCandidate domain model with scores and trade-offs.
    """
    primary_dest = destinations[0] if destinations else origin
    nights = max(1, duration_days - 1)
    travelers_count = party.total_travelers if party else 2
    rooms_count = max(1, (party.adults + 1) // 2) if party else 1

    # 1. Transport Cost Estimation (Outbound + Return)
    orig_code = origin.iata_code or origin.city or origin.name
    dest_code = primary_dest.iata_code or primary_dest.city or primary_dest.name

    outbound_price_pp = DEFAULT_HEURISTIC_FLIGHT_INR
    try:
        t_out = search_transport(
            origin=orig_code,
            destination=dest_code,
            travel_date=start_date,
            use_fixture=use_fixture,
        )
        if t_out and t_out.options:
            outbound_price_pp = float(t_out.options[0].price_inr)
    except Exception as exc:
        log.debug("Date optimizer transport outbound lookup failed: %s", exc)

    return_price_pp = outbound_price_pp
    try:
        t_ret = search_transport(
            origin=dest_code,
            destination=orig_code,
            travel_date=end_date,
            use_fixture=use_fixture,
        )
        if t_ret and t_ret.options:
            return_price_pp = float(t_ret.options[0].price_inr)
    except Exception as exc:
        log.debug("Date optimizer transport return lookup failed: %s", exc)

    total_transport = round((outbound_price_pp + return_price_pp) * travelers_count, 2)

    # 2. Hotel Cost Estimation
    dest_query = primary_dest.city or primary_dest.name or dest_code
    hotel_nightly = DEFAULT_HEURISTIC_HOTEL_INR
    try:
        h_res = search_hotels(
            destination=dest_query,
            checkin_date=start_date,
            checkout_date=end_date,
            nights=nights,
            guests=travelers_count,
            use_fixture=use_fixture,
        )
        if h_res and h_res.options:
            hotel_nightly = float(h_res.options[0].price_per_night_inr)
    except Exception as exc:
        log.debug("Date optimizer hotel lookup failed: %s", exc)

    total_hotel = round(hotel_nightly * nights * rooms_count, 2)
    total_logistics = round(total_transport + total_hotel, 2)

    # 3. Weather Evaluation
    avg_temp: float | None = None
    rain_prob: float | None = None
    is_favorable = True
    weather_summary = "Pleasant travel conditions"

    try:
        w_res = get_weather_forecast(
            latitude=primary_dest.latitude,
            longitude=primary_dest.longitude,
            start_date=start_date,
            end_date=end_date,
            destination=dest_query,
            use_fixture=use_fixture,
        )
        if w_res and w_res.daily_forecasts:
            temps = [
                f.temperature_max_c
                for f in w_res.daily_forecasts
                if f.temperature_max_c is not None
            ]
            rains = [
                f.rain_probability_percent
                for f in w_res.daily_forecasts
                if f.rain_probability_percent is not None
            ]

            if temps:
                avg_temp = round(sum(temps) / len(temps), 1)
            if rains:
                rain_prob = round(sum(rains) / len(rains), 1)

            is_favorable = w_res.is_outdoor_friendly
            weather_summary = w_res.summary
    except Exception as exc:
        log.debug("Date optimizer weather lookup failed: %s", exc)

    # 4. Weekend Optimization (Spanning Friday, Saturday, Sunday)
    try:
        d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        cur = d_start
        weekend_days = 0
        while cur <= d_end:
            if cur.weekday() in (4, 5, 6):  # Fri, Sat, Sun
                weekend_days += 1
            cur += timedelta(days=1)
        is_weekend_heavy = weekend_days >= 2
    except Exception:
        is_weekend_heavy = False

    # 5. Deterministic Scoring
    # Price score (0-100): how well logistics fits into budget
    if budget_inr > 0:
        ratio = total_logistics / budget_inr
        if ratio <= 0.60:
            price_score = 95.0
        elif ratio <= 0.85:
            price_score = 85.0 + (0.85 - ratio) * 40.0
        elif ratio <= 1.0:
            price_score = 70.0 + (1.0 - ratio) * 100.0
        else:
            price_score = max(20.0, 70.0 - (ratio - 1.0) * 80.0)
    else:
        price_score = 75.0
    price_score = round(min(100.0, max(10.0, price_score)), 1)

    # Weather score (0-100): based on outdoor friendliness & precipitation
    weather_score = 85.0
    if rain_prob is not None:
        weather_score -= rain_prob * 0.5
    if is_favorable:
        weather_score += 10.0
    else:
        weather_score -= 20.0
    if avg_temp is not None:
        if 18.0 <= avg_temp <= 28.0:
            weather_score += 5.0
        elif avg_temp > 35.0 or avg_temp < 5.0:
            weather_score -= 10.0
    weather_score = round(min(100.0, max(10.0, weather_score)), 1)

    # Composite Score (0-100)
    # 45% price, 45% weather, 10% weekend bonus
    weekend_bonus = 10.0 if is_weekend_heavy else 0.0
    composite_score = round(0.45 * price_score + 0.45 * weather_score + weekend_bonus, 1)

    # 6. Structured Trade-Off Observations
    trade_offs: list[str] = [
        (
            f"Est. logistics cost: ₹{total_logistics:,.0f} "
            f"(Transport: ₹{total_transport:,.0f}, Lodging: ₹{total_hotel:,.0f})."
        ),
        f"Weather: {weather_summary}"
        + (
            f" (avg {avg_temp}°C, {rain_prob:.0f}% rain)"
            if avg_temp is not None and rain_prob is not None
            else "."
        ),
    ]
    if is_weekend_heavy:
        trade_offs.append(
            "Weekend-optimized: Spans weekend days to minimize working leave required."
        )
    else:
        trade_offs.append(
            "Mid-week schedule: Often benefits from lower attraction crowds and calmer travel."
        )

    return DateCandidate(
        start_date=start_date,
        end_date=end_date,
        duration_days=duration_days,
        estimated_transport_cost_inr=total_transport,
        estimated_hotel_cost_inr=total_hotel,
        total_logistics_cost_inr=total_logistics,
        weather_summary=weather_summary,
        avg_temperature_c=avg_temp,
        rain_probability_pct=rain_prob,
        is_weather_favorable=is_favorable,
        price_score=price_score,
        weather_score=weather_score,
        composite_score=composite_score,
        trade_offs=trade_offs,
        is_weekend_heavy=is_weekend_heavy,
    )


# ---------------------------------------------------------------------------
# Core Date Optimization Processing
# ---------------------------------------------------------------------------


def process_date_optimization(
    state: InitialPlanningState | TripContext | dict[str, Any],
    use_fixture: bool = False,
) -> tuple[TripContext, DateOptimizationResult]:
    """Execute flexible travel date optimization across candidate windows.

    Accepts:
    1. An InitialPlanningState from the intake node.
    2. A TripContext domain model.
    3. A state dictionary from the LangGraph workflow.

    Args:
        state: Input planning state or context.
        use_fixture: Force offline mock fixtures.

    Returns:
        Tuple of (updated TripContext with recommended dates, DateOptimizationResult).

    Raises:
        DateOptimizationError: If state lacks required context.
    """
    use_fixture = use_fixture or os.environ.get("SAFARNAMA_USE_FIXTURES", "").lower() in (
        "true",
        "1",
    )

    # 1. Normalize input context
    if isinstance(state, InitialPlanningState):
        context = state.trip_context
        origin = state.origin
        destinations = state.destinations
        total_budget = state.total_budget_inr
        scope = state.travel_scope
    elif isinstance(state, TripContext):
        planning_state = process_intake(state)
        context = planning_state.trip_context
        origin = planning_state.origin
        destinations = planning_state.destinations
        total_budget = planning_state.total_budget_inr
        scope = planning_state.travel_scope
    elif isinstance(state, dict):
        if "trip_context" in state and isinstance(state["trip_context"], TripContext):
            context = state["trip_context"]
        elif "trip_context" in state and isinstance(state["trip_context"], dict):
            context = TripContext.model_validate(state["trip_context"])
        else:
            context = TripContext.model_validate(state)

        # Retrieve resolved locations if present
        if (
            "origin" in state
            and "destinations" in state
            and isinstance(state["destinations"], list)
        ):
            try:
                origin = (
                    state["origin"]
                    if isinstance(state["origin"], ResolvedLocation)
                    else ResolvedLocation.model_validate(state["origin"])
                )
                destinations = [
                    d if isinstance(d, ResolvedLocation) else ResolvedLocation.model_validate(d)
                    for d in state["destinations"]
                ]
                total_budget = float(state.get("total_budget_inr", context.budget.amount_inr))
                scope = TravelScope(state.get("travel_scope", context.scope))
            except Exception:
                planning_state = process_intake(context)
                origin = planning_state.origin
                destinations = planning_state.destinations
                total_budget = planning_state.total_budget_inr
                scope = planning_state.travel_scope
        else:
            planning_state = process_intake(context)
            origin = planning_state.origin
            destinations = planning_state.destinations
            total_budget = planning_state.total_budget_inr
            scope = planning_state.travel_scope
    else:
        raise DateOptimizationError(
            f"Unsupported input type for date optimization: {type(state).__name__}"
        )

    dates = context.dates
    mode = dates.mode

    # 2. Generate candidate date ranges
    candidate_ranges = generate_candidate_date_ranges(dates)

    if not candidate_ranges:
        # Fallback to a single candidate
        today = datetime.now(UTC).date()
        s_date = today + timedelta(days=14)
        e_date = s_date + timedelta(days=(dates.duration_days or 5) - 1)
        candidate_ranges = [
            (s_date.strftime("%Y-%m-%d"), e_date.strftime("%Y-%m-%d"), dates.duration_days or 5)
        ]

    # 3. Evaluate each candidate range
    evaluated_candidates: list[DateCandidate] = []
    party = context.party
    style = context.travel_style

    for c_start, c_end, c_dur in candidate_ranges:
        candidate = evaluate_date_candidate(
            start_date=c_start,
            end_date=c_end,
            duration_days=c_dur,
            origin=origin,
            destinations=destinations,
            party=party,
            travel_style=style,
            travel_scope=scope,
            budget_inr=total_budget,
            use_fixture=use_fixture,
        )
        evaluated_candidates.append(candidate)

    # 4. Sort candidates by composite_score descending
    evaluated_candidates.sort(key=lambda c: c.composite_score, reverse=True)

    recommended = evaluated_candidates[0]
    alternatives = evaluated_candidates[1:4]  # Up to 3 alternatives

    # 5. Formulate human-readable evaluation summary narrative
    if mode == DateMode.EXACT:
        summary_text = (
            f"Exact travel dates confirmed: {recommended.start_date} to {recommended.end_date} "
            f"({recommended.duration_days} days). "
            f"Overall date quality score: {recommended.composite_score:.1f}/100."
        )
    elif mode == DateMode.FLEXIBLE:
        summary_text = (
            f"Flexible date optimization selected {recommended.start_date} to "
            f"{recommended.end_date} as the top recommendation "
            f"(Score: {recommended.composite_score:.1f}/100, "
            f"Est. logistics ₹{recommended.total_logistics_cost_inr:,.0f}). "
            f"Evaluated {len(evaluated_candidates)} candidate windows across "
            f"+/-{dates.flexibility_days} days."
        )
    else:  # FIND_BEST
        summary_text = (
            f"Window search across {dates.window_start} to {dates.window_end} identified "
            f"{recommended.start_date} to {recommended.end_date} as the optimal "
            f"{recommended.duration_days}-day travel window "
            f"(Score: {recommended.composite_score:.1f}/100, "
            f"Est. logistics ₹{recommended.total_logistics_cost_inr:,.0f})."
        )

    optimization_result = DateOptimizationResult(
        mode=mode,
        recommended=recommended,
        alternatives=alternatives,
        total_candidates_evaluated=len(evaluated_candidates),
        evaluation_summary=summary_text,
    )

    # 6. Construct updated TripContext with recommended dates
    # Downstream nodes will plan against recommended.start_date and recommended.end_date
    updated_dates = TripDates(
        mode=mode,
        start_date=recommended.start_date,
        end_date=recommended.end_date,
        duration_days=recommended.duration_days,
        flexibility_days=dates.flexibility_days,
        window_start=dates.window_start,
        window_end=dates.window_end,
    )

    updated_context = TripContext(
        origin=context.origin,
        destinations=context.destinations,
        scope=context.scope,
        party=context.party,
        dates=updated_dates,
        budget=context.budget,
        travel_style=context.travel_style,
        pace=context.pace,
        activity_preferences=context.activity_preferences,
        must_visits=context.must_visits,
        food=context.food,
        previous_travel=context.previous_travel,
    )

    return updated_context, optimization_result


# ---------------------------------------------------------------------------
# LangGraph Node Entrypoint
# ---------------------------------------------------------------------------


def date_node(state: dict[str, Any] | InitialPlanningState) -> dict[str, Any]:
    """LangGraph node function for flexible date optimization.

    Evaluates candidate date windows and updates the planning state with the
    recommended dates and alternative options before logistics and experience fan-out.

    Args:
        state: Shared PlanGraphState or state dictionary.

    Returns:
        State update dictionary containing updated trip_context, date_options, and warnings.
    """
    if isinstance(state, dict) and state.get("errors"):
        return {}

    context = (
        state.trip_context if isinstance(state, InitialPlanningState) else state.get("trip_context")
    )
    if not context:
        return {}

    use_fixture = os.environ.get("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")

    try:
        updated_context, date_result = process_date_optimization(state, use_fixture=use_fixture)
    except Exception as exc:
        log.error("Date optimization node encountered an error: %s", exc, exc_info=True)
        return {
            "warnings": [f"Date optimization warning: {exc}. Retaining original requested dates."]
        }

    warnings: list[str] = []
    if date_result.mode != DateMode.EXACT:
        rec = date_result.recommended
        warnings.append(
            f"Date Optimization ({date_result.mode.value}): Recommended {rec.start_date} "
            f"to {rec.end_date} (Score: {rec.composite_score:.1f}/100). "
            f"{len(date_result.alternatives)} alternative date window(s) evaluated."
        )

    return {
        "trip_context": updated_context,
        "date_options": date_result,
        "effective_duration_days": date_result.recommended.duration_days,
        "warnings": warnings,
    }
