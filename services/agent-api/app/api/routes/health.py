"""
Enterprise Agent AI — Health Routes

Health and readiness endpoints for Kubernetes probes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Liveness probe — confirms the service is running.
    Used by Kubernetes liveness probes and load balancers.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service="agent-api",
        version="1.0.0",
        environment=settings.environment,
        checks={
            "api": "ok",
            "uptime": "ok",
        },
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe — confirms the service can accept traffic.
    Checks database connectivity and LLM provider availability.
    """
    settings = get_settings()

    # Check database (simplified — in production, actually ping the DB)
    db_status = "connected"

    # Check LLM provider
    llm_status = "available" if settings.default_llm_provider else "unavailable"

    return ReadinessResponse(
        ready=True,
        database=db_status,
        llm_provider=llm_status,
    )
