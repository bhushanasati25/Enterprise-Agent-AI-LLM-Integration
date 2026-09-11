"""
Agent API — Agent Unit Tests

Tests for individual agent workflows using mock LLMs.
"""

from __future__ import annotations

import os

import pytest

os.environ["ENVIRONMENT"] = "testing"
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"

from app.agents import DataExtractionAgent, DocumentQAAgent, TaskAutomationAgent
from app.models.schemas import AgentStatus


@pytest.mark.asyncio
async def test_document_qa_agent_invoke():
    """Test DocumentQAAgent produces valid response."""
    agent = DocumentQAAgent(provider="mock")
    response = await agent.invoke(
        query="What is the SLA for production services?",
        context={"department": "engineering"},
    )

    assert response.status == AgentStatus.COMPLETED
    assert response.result  # Non-empty
    assert response.metadata.model
    assert response.metadata.latency_ms > 0
    assert len(response.metadata.steps) == 3  # analysis, retrieval, generation
    assert len(response.metadata.sources) > 0


@pytest.mark.asyncio
async def test_document_qa_agent_steps():
    """Test DocumentQAAgent executes all workflow steps."""
    agent = DocumentQAAgent(provider="mock")
    response = await agent.invoke(query="Tell me about data security.")

    step_actions = [s.action for s in response.metadata.steps]
    assert "query_analysis" in step_actions
    assert "document_retrieval" in step_actions
    assert "answer_generation" in step_actions


@pytest.mark.asyncio
async def test_data_extraction_agent_invoke():
    """Test DataExtractionAgent produces valid response."""
    agent = DataExtractionAgent(provider="mock")
    response = await agent.invoke(
        query="Acme Corp reported Q3 2025 revenue of $12.5 million with 15.2% growth.",
    )

    assert response.status == AgentStatus.COMPLETED
    assert response.result
    assert response.metadata.latency_ms > 0
    assert len(response.metadata.steps) == 3  # analysis, extraction, validation


@pytest.mark.asyncio
async def test_data_extraction_with_custom_schema():
    """Test DataExtractionAgent with custom schema."""
    agent = DataExtractionAgent(provider="mock")
    custom_schema = {
        "revenue": {"type": "currency", "required": True},
        "company": {"type": "string", "required": True},
    }
    response = await agent.invoke(
        query="Revenue was $5M for Beta Inc.",
        context={"schema": custom_schema},
    )

    assert response.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_task_automation_agent_invoke():
    """Test TaskAutomationAgent produces valid response."""
    agent = TaskAutomationAgent(provider="mock")
    response = await agent.invoke(
        query="Set up a new development environment for the data team",
        context={"department": "engineering"},
    )

    assert response.status == AgentStatus.COMPLETED
    assert response.result
    assert len(response.metadata.steps) == 3  # planning, execution, report


@pytest.mark.asyncio
async def test_task_automation_with_approval():
    """Test TaskAutomationAgent returns awaiting_approval when required."""
    agent = TaskAutomationAgent(provider="mock")
    response = await agent.invoke(
        query="Deploy new version to production",
        context={"require_approval": True},
    )

    assert response.status == AgentStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_agent_token_tracking():
    """Test that all agents track token usage."""
    agent = DocumentQAAgent(provider="mock")
    response = await agent.invoke(query="Test query")

    tokens = response.metadata.tokens_used
    assert tokens.total_tokens > 0
    assert tokens.prompt_tokens >= 0
    assert tokens.completion_tokens >= 0


@pytest.mark.asyncio
async def test_agent_cost_estimation():
    """Test that mock provider returns zero cost."""
    agent = DocumentQAAgent(provider="mock", model_name="mock-gpt-4o")
    response = await agent.invoke(query="Test query")

    assert response.metadata.tokens_used.estimated_cost_usd == 0.0
