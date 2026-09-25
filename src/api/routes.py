"""FastAPI Router definitions for Safarnama API Layer."""

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.models import (
    EstimateRequest,
    EstimateResponse,
    HealthResponse,
    PlanPreviewRequest,
    PlanPreviewResponse,
    ToolStatusItem,
    ToolStatusResponse,
)
from src.tools.calculator import (
    calculate_budget_breakdown,
    calculate_budget_variance,
)
from src.tools.fallback_estimator import (
    estimate_cost,
    get_fallback_estimator_status,
)
from src.tools.forex import get_rates_table
from src.tools.hotels import get_hotels_status
from src.tools.places import get_places_status
from src.tools.static_data import (
    AirportNotFoundError,
    find_airport,
    find_country,
    get_store,
    get_visa_rule,
)
from src.tools.transport import get_transport_status
from src.tools.web_search import get_web_search_status

router = APIRouter(prefix="/api/v1", tags=["Safarnama API"])


@router.get("/health", response_model=HealthResponse)
@router.get(
    "/healthcheck",
    response_model=HealthResponse,
    include_in_schema=False,
)
def health_check() -> HealthResponse:
    """Return health status of the API service."""
    return HealthResponse()


@router.get("/tools/status", response_model=ToolStatusResponse)
def get_tools_status() -> ToolStatusResponse:
    """Aggregate health and readiness status across all static and external tools."""
    store = get_store()
    airports_loaded = len(getattr(store, "_airports_by_iata", {}))
    countries_loaded = len(getattr(store, "_countries_by_code", {}))
    visa_rules_loaded = len(getattr(store, "_visa_base_by_dest", {}))
    enriched_visa_loaded = len(getattr(store, "_visa_enriched_by_dest", {}))

    static_status = ToolStatusItem(
        tool="static_data",
        status="available" if airports_loaded > 0 else "uninitialized",
        provider="In-Memory Static Store",
        details={
            "airports_loaded": airports_loaded,
            "countries_loaded": countries_loaded,
            "visa_rules_loaded": visa_rules_loaded,
            "enriched_visa_loaded": enriched_visa_loaded,
        },
    )

    rates = get_rates_table()
    forex_status = ToolStatusItem(
        tool="forex",
        status="available",
        provider="Multi-Tier Forex Engine",
        details={"currencies_available": len(rates)},
    )

    ws_status_raw = get_web_search_status()
    web_search_status = ToolStatusItem(
        tool="web_search",
        status=ws_status_raw.get("status", "available"),
        provider=ws_status_raw.get("provider", "Tavily/DDG/Firecrawl"),
        details=ws_status_raw,
    )

    trans_status_raw = get_transport_status()
    transport_status = ToolStatusItem(
        tool="transport",
        status=trans_status_raw.get("status", "available"),
        provider=trans_status_raw.get("provider", "SkyScraper/IRCTC/Physics"),
        details=trans_status_raw,
    )

    hotel_status_raw = get_hotels_status()
    hotel_status = ToolStatusItem(
        tool="hotels",
        status=hotel_status_raw.get("status", "available"),
        provider=hotel_status_raw.get("provider", "SerpApi/Booking/OSM"),
        details=hotel_status_raw,
    )

    place_status_raw = get_places_status()
    place_status = ToolStatusItem(
        tool="places",
        status=place_status_raw.get("status", "available"),
        provider=place_status_raw.get("provider", "SerpApi/OSM/Search"),
        details=place_status_raw,
    )

    est_status_raw = get_fallback_estimator_status()
    estimator_status = ToolStatusItem(
        tool="fallback_estimator",
        status=est_status_raw.get("status", "available"),
        provider=est_status_raw.get("active_provider", "Gemini/Groq/NVIDIA/Heuristic"),
        details=est_status_raw,
    )

    return ToolStatusResponse(
        status="ok",
        tools={
            "static_data": static_status,
            "forex": forex_status,
            "web_search": web_search_status,
            "transport": transport_status,
            "hotels": hotel_status,
            "places": place_status,
            "fallback_estimator": estimator_status,
        },
    )


@router.post("/estimate", response_model=EstimateResponse)
def estimate_category_cost(request: EstimateRequest) -> EstimateResponse:
    """Provide numerical cost bounds using multi-provider fallback estimation."""
    try:
        category_map = {
            "hotel": "HOTEL",
            "transport": "TRANSPORT",
            "food": "FOOD",
            "activity": "ACTIVITY",
            "misc": "MISC",
            "total_budget": "TOTAL_BUDGET",
        }
        tier_map = {
            "budget": "BUDGET",
            "moderate": "MID_RANGE",
            "mid_range": "MID_RANGE",
            "mid-range": "MID_RANGE",
            "luxury": "LUXURY",
        }

        cat_str = category_map.get(request.category.lower(), request.category.upper())
        tier_str = tier_map.get((request.budget_tier or "moderate").lower(), "MID_RANGE")

        res = estimate_cost(
            destination=request.destination,
            category=cat_str,
            tier=tier_str,
            duration_days=request.nights or 1,
            num_travelers=request.travelers or 1,
            use_fixture=True,
        )
        return EstimateResponse(
            destination=res.destination,
            category=res.category,
            estimated_cost_inr=res.estimated_cost_inr,
            is_estimated=res.is_estimated,
            confidence=res.confidence_score,
            explanation=res.reasoning,
            provider=res.provider_used,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estimation failed: {str(exc)}",
        ) from exc


@router.post("/plan/preview", response_model=PlanPreviewResponse)
def preview_trip_plan(request: PlanPreviewRequest) -> PlanPreviewResponse:
    """Generate a lightweight validated preview of trip constraints and baseline breakdown."""
    # 1. Resolve Origin Airport
    origin_airport_dict = None
    try:
        airport = find_airport(request.origin)
        if airport is not None:
            origin_airport_dict = {
                "iata": airport.iata_code,
                "name": airport.name,
                "municipality": airport.municipality,
                "iso_country": airport.iso_country,
            }
        else:
            origin_airport_dict = {"query": request.origin, "resolved": False}
    except AirportNotFoundError:
        origin_airport_dict = {"query": request.origin, "resolved": False}

    # 2. Resolve Destination Country & Travel Scope
    dest_country_dict = None
    travel_scope = "INTERNATIONAL"
    country = find_country(request.destination)
    if country is not None:
        dest_country_dict = {
            "iso2": country.country_code,
            "iso3": country.country_code_alpha3,
            "name": country.name,
            "capital": country.capital,
            "currencies": [c.code for c in country.currencies],
            "is_schengen": country.is_schengen,
        }
        if country.country_code == "IN":
            travel_scope = "DOMESTIC"
    else:
        # Check if destination is an Indian state/city
        if request.destination.lower() in [
            "goa",
            "kerala",
            "rajasthan",
            "jaipur",
            "mumbai",
            "delhi",
            "manali",
            "shimla",
            "ladakh",
            "kashmir",
            "agra",
            "karnataka",
        ]:
            travel_scope = "DOMESTIC"
            dest_country_dict = {
                "iso2": "IN",
                "name": "India",
                "region": request.destination.title(),
            }
        else:
            dest_country_dict = {"query": request.destination, "resolved": False}

    # 3. Visa Requirement Summary
    visa_summary = None
    if travel_scope == "INTERNATIONAL":
        try:
            visa_rec = get_visa_rule(request.destination)
            if hasattr(visa_rec, "selected_option") and visa_rec.selected_option:
                opt = visa_rec.selected_option
                visa_summary = {
                    "destination": visa_rec.destination,
                    "visa_type": opt.visa_type,
                    "cost_inr": opt.cost_inr,
                    "entry_type": opt.entry_type,
                    "notes": opt.notes,
                }
            elif hasattr(visa_rec, "requirement"):
                visa_summary = {
                    "destination": visa_rec.destination,
                    "requirement": visa_rec.requirement,
                    "notes": "Baseline visa rule record.",
                }
        except Exception:
            visa_summary = {
                "destination": request.destination,
                "requirement": "UNKNOWN",
                "notes": "Visa rule lookup unavailable.",
            }

    # 4. Calculate Baseline Costs
    daily_per_person = 4000.0 if travel_scope == "DOMESTIC" else 8000.0
    est_total_expenses = daily_per_person * request.duration_days * request.num_travelers
    if visa_summary and visa_summary.get("cost_inr"):
        est_total_expenses += visa_summary["cost_inr"] * request.num_travelers

    expenses_dict = {
        "transport": round(est_total_expenses * 0.35, 2),
        "accommodation": round(est_total_expenses * 0.35, 2),
        "food": round(est_total_expenses * 0.15, 2),
        "activities": round(est_total_expenses * 0.10, 2),
        "miscellaneous": round(est_total_expenses * 0.05, 2),
    }

    breakdown = calculate_budget_breakdown(
        category_costs=expenses_dict,
        buffer_percentage=10.0,
        travelers=request.num_travelers,
        days=request.duration_days,
    )

    variance = calculate_budget_variance(
        total_cost=breakdown.grand_total,
        user_budget=request.budget_inr,
    )

    return PlanPreviewResponse(
        status="preview",
        origin_airport=origin_airport_dict,
        destination_country=dest_country_dict,
        travel_scope=travel_scope,
        visa_summary=visa_summary,
        estimated_baseline_cost_inr=breakdown.grand_total,
        budget_variance=variance.model_dump(),
        weather_preview={
            "destination": request.destination,
            "status": "Forecast available upon date selection",
        },
    )


@router.get("/stream/events")
async def stream_planning_events() -> StreamingResponse:
    """Stream real-time planning workflow event notifications via Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        events = [
            {"event": "start", "message": "Initiating Safarnama planning engine"},
            {"event": "intake", "message": "Validated trip constraints and scope"},
            {"event": "logistics", "message": "Researched transport options and hotel tiers"},
            {"event": "experience", "message": "Aggregated points of interest and dining spots"},
            {"event": "budget", "message": "Performed deterministic budget calculation"},
            {"event": "complete", "message": "Plan preview generated successfully"},
        ]
        for ev in events:
            data_str = json.dumps(ev)
            yield f"data: {data_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
