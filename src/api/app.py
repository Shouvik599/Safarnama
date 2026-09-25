"""FastAPI Application Entry Point for Safarnama Travel Planner."""

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.models import APIErrorResponse
from src.api.routes import router
from src.tools.calculator import CalculatorError
from src.tools.fallback_estimator import EstimatorError
from src.tools.forex import ForexError
from src.tools.hotels import HotelError
from src.tools.places import PlaceError
from src.tools.static_data import StaticDataError
from src.tools.transport import TransportError
from src.tools.weather import WeatherError
from src.tools.web_search import WebSearchError


def create_app() -> FastAPI:
    """Factory creating and configuring the Safarnama FastAPI application."""
    app = FastAPI(
        title="Safarnama API",
        version="0.1.0",
        description=(
            "Autonomous Multi-Agent Travel Planner API for Indian travelers. "
            "Exposes constraint validation, tool status, cost estimation, and plan previews."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Middleware Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_resp = APIErrorResponse(
            detail=str(exc.detail),
            error_type="HTTPException",
            status_code=exc.status_code,
            timestamp=datetime.now(UTC).isoformat(),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        detail_msg = "; ".join(
            [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors]
        )
        error_resp = APIErrorResponse(
            detail=f"Validation Error: {detail_msg}",
            error_type="RequestValidationError",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            timestamp=datetime.now(UTC).isoformat(),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(StaticDataError)
    @app.exception_handler(CalculatorError)
    @app.exception_handler(ForexError)
    @app.exception_handler(WeatherError)
    @app.exception_handler(WebSearchError)
    @app.exception_handler(TransportError)
    @app.exception_handler(HotelError)
    @app.exception_handler(PlaceError)
    @app.exception_handler(EstimatorError)
    async def domain_tool_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_resp = APIErrorResponse(
            detail=str(exc),
            error_type=exc.__class__.__name__,
            status_code=status.HTTP_400_BAD_REQUEST,
            timestamp=datetime.now(UTC).isoformat(),
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_resp = APIErrorResponse(
            detail=f"Internal Server Error: {str(exc)}",
            error_type="UnhandledException",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            timestamp=datetime.now(UTC).isoformat(),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump(),
        )

    # Root endpoint redirecting or welcoming
    @app.get("/", include_in_schema=False)
    def root_welcome() -> dict[str, Any]:
        return {
            "message": "Welcome to Safarnama API Service",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    # Register Routers
    app.include_router(router)

    return app


app = create_app()
