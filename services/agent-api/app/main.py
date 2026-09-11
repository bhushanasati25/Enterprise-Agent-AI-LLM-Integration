"""
Enterprise Agent AI — FastAPI Application

Main application factory with middleware, CORS, and route registration.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.routes import agents, documents, health, safety
from app.core.config import get_settings
from app.core.security import RateLimitMiddleware

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent-api")

# ---------------------------------------------------------------------------
# Prometheus Metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "agent_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "agent_api_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)
AGENT_INVOCATIONS = Counter(
    "agent_invocations_total",
    "Total agent invocations",
    ["agent_type", "status"],
)


# ---------------------------------------------------------------------------
# Application Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting Agent API | env={settings.environment} | provider={settings.default_llm_provider}")

    # Initialize database (skip in testing to avoid PG dependency)
    if settings.environment != "testing":
        try:
            from app.core.database import init_db
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(f"Database init skipped: {e}")

    yield

    # Cleanup
    if settings.environment != "testing":
        try:
            from app.core.database import close_db
            await close_db()
            logger.info("Database connections closed")
        except Exception:
            pass

    logger.info("Agent API shutdown complete")


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Enterprise Agent AI API",
        description=(
            "Production-grade enterprise AI agent platform powered by LangChain/LangGraph. "
            "Supports document Q&A, data extraction, and task automation workflows."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate Limiting ---
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100, burst=20)

    # --- Request Logging & Metrics Middleware ---
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Record Prometheus metrics
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        # Structured logging for non-health requests
        if endpoint not in ("/health", "/ready", "/metrics"):
            logger.info(
                f"{request.method} {endpoint} → {response.status_code} "
                f"({duration:.3f}s)"
            )

        return response

    # --- Prometheus Metrics Endpoint ---
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type="text/plain")

    # --- Global Exception Handler ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.environment == "development" else "An error occurred",
            },
        )

    # --- Register Routes ---
    app.include_router(health.router)
    app.include_router(agents.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(safety.router, prefix="/api")

    # --- Static Files & Console UI ---
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_index():
            return FileResponse(static_dir / "index.html")

    return app


# Create the application instance
app = create_app()
