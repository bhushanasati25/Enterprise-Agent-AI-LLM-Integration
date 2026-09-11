"""
Agent API — API Integration Tests

Tests for all API endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agent-api"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient):
    """Test readiness check returns ready status."""
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True


@pytest.mark.asyncio
async def test_list_agent_types(client: AsyncClient):
    """Test listing available agent types."""
    response = await client.get("/api/agents/types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    types = [item["type"] for item in data]
    assert "document_qa" in types
    assert "data_extraction" in types
    assert "task_automation" in types


@pytest.mark.asyncio
async def test_invoke_document_qa_agent(client: AsyncClient):
    """Test invoking the document Q&A agent."""
    response = await client.post(
        "/api/agents/invoke",
        json={
            "agent_type": "document_qa",
            "query": "What is the company refund policy?",
            "context": {"department": "support"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "document_qa"
    assert data["status"] == "completed"
    assert data["result"]  # Non-empty result
    assert data["metadata"]["model"]
    assert data["metadata"]["latency_ms"] > 0
    assert len(data["metadata"]["steps"]) >= 1


@pytest.mark.asyncio
async def test_invoke_data_extraction_agent(client: AsyncClient):
    """Test invoking the data extraction agent."""
    response = await client.post(
        "/api/agents/invoke",
        json={
            "agent_type": "data_extraction",
            "query": "Acme Corp reported Q3 2025 revenue of $12.5M with 15% growth.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "data_extraction"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_invoke_task_automation_agent(client: AsyncClient):
    """Test invoking the task automation agent."""
    response = await client.post(
        "/api/agents/invoke",
        json={
            "agent_type": "task_automation",
            "query": "Generate a monthly sales report and email to stakeholders",
            "context": {"department": "sales"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "task_automation"
    assert data["status"] in ["completed", "awaiting_approval"]


@pytest.mark.asyncio
async def test_invoke_invalid_agent_type(client: AsyncClient):
    """Test that invalid agent type returns 422."""
    response = await client.post(
        "/api/agents/invoke",
        json={
            "agent_type": "nonexistent",
            "query": "test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invoke_empty_query(client: AsyncClient):
    """Test that empty query returns 422."""
    response = await client.post(
        "/api/agents/invoke",
        json={
            "agent_type": "document_qa",
            "query": "",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_document_search(client: AsyncClient):
    """Test document search endpoint."""
    response = await client.post(
        "/api/documents/search",
        json={
            "query": "security policy",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "security policy"
    assert len(data["results"]) <= 3
    assert data["total_results"] > 0


@pytest.mark.asyncio
async def test_openapi_docs(client: AsyncClient):
    """Test OpenAPI docs are available in dev mode."""
    response = await client.get("/docs")
    assert response.status_code == 200
