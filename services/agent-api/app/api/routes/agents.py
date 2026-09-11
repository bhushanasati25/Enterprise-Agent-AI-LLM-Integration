"""
Enterprise Agent AI — Agent Routes

API endpoints for invoking AI agents.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.agents import DataExtractionAgent, DocumentQAAgent, TaskAutomationAgent
from app.core.security import validate_api_key
from app.models.schemas import AgentInvokeRequest, AgentResponse, AgentType, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])

# Agent registry
AGENT_REGISTRY = {
    AgentType.DOCUMENT_QA: DocumentQAAgent,
    AgentType.DATA_EXTRACTION: DataExtractionAgent,
    AgentType.TASK_AUTOMATION: TaskAutomationAgent,
}


@router.post(
    "/invoke",
    response_model=AgentResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Invoke an AI agent",
    description="Execute an AI agent workflow and return the result.",
)
async def invoke_agent(
    request: AgentInvokeRequest,
    _api_key: str = Depends(validate_api_key),
) -> AgentResponse:
    """
    Invoke an AI agent with the specified type and query.

    Available agent types:
    - **document_qa**: Document-grounded Q&A with citations
    - **data_extraction**: Structured data extraction from text
    - **task_automation**: Multi-step task planning and execution
    """
    agent_class = AGENT_REGISTRY.get(request.agent_type)
    if not agent_class:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent type: {request.agent_type}. "
            f"Available types: {[t.value for t in AgentType]}",
        )

    try:
        agent = agent_class(
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        logger.info(
            "Invoking agent",
            extra={
                "agent_type": request.agent_type,
                "provider": request.provider,
                "query_length": len(request.query),
            },
        )

        response = await agent.invoke(query=request.query, context=request.context)

        logger.info(
            "Agent completed",
            extra={
                "agent_type": request.agent_type,
                "status": response.status,
                "latency_ms": response.metadata.latency_ms,
                "tokens": response.metadata.tokens_used.total_tokens,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Agent invocation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get(
    "/types",
    summary="List available agent types",
    description="Return all available agent types and their descriptions.",
)
async def list_agent_types() -> list[dict[str, Any]]:
    """List all available agent types with descriptions."""
    return [
        {
            "type": AgentType.DOCUMENT_QA.value,
            "name": "Document Q&A",
            "description": "Answer questions based on enterprise documents with source citations",
            "capabilities": ["RAG retrieval", "Source citation", "Multi-document synthesis"],
        },
        {
            "type": AgentType.DATA_EXTRACTION.value,
            "name": "Data Extraction",
            "description": "Extract structured data from unstructured text",
            "capabilities": ["Schema-guided extraction", "Confidence scoring", "Data validation"],
        },
        {
            "type": AgentType.TASK_AUTOMATION.value,
            "name": "Task Automation",
            "description": "Plan and execute multi-step enterprise tasks",
            "capabilities": ["Task planning", "Step execution", "Approval gates", "Audit trail"],
        },
    ]
