"""
LLM Evaluator — FastAPI Application

Benchmarking service for evaluating commercial LLMs.
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.routes import benchmarks, models
from app.core.config import get_evaluator_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("llm-evaluator")

# Prometheus metrics
REQUEST_COUNT = Counter("evaluator_requests_total", "Total requests", ["method", "endpoint", "status"])
BENCHMARK_RUNS = Counter("benchmark_runs_total", "Total benchmark runs", ["dataset"])
BENCHMARK_DURATION = Histogram("benchmark_duration_seconds", "Benchmark duration", ["dataset"])


def create_app() -> FastAPI:
    settings = get_evaluator_settings()

    app = FastAPI(
        title="Enterprise LLM Evaluator",
        description="Custom benchmarking framework for evaluating commercial LLMs with accuracy, latency, cost, and safety metrics.",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        if request.url.path not in ("/health", "/ready", "/metrics"):
            logger.info(f"{request.method} {request.url.path} → {response.status_code} ({time.time()-start:.3f}s)")
        return response

    @app.get("/health", tags=["Health"])
    async def health():
        return {
            "status": "healthy",
            "service": "llm-evaluator",
            "version": "1.0.0",
            "environment": settings.environment,
        }

    @app.get("/ready", tags=["Health"])
    async def ready():
        return {"ready": True, "llm_provider": "available"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type="text/plain")

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})

    app.include_router(benchmarks.router, prefix="/api")
    app.include_router(models.router, prefix="/api")

    return app


app = create_app()
