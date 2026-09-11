"""
Enterprise Agent AI — Pydantic Schemas

Request/response models for all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentType(str, Enum):
    """Available agent types."""
    DOCUMENT_QA = "document_qa"
    DATA_EXTRACTION = "data_extraction"
    TASK_AUTOMATION = "task_automation"


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


# ---------------------------------------------------------------------------
# Agent Schemas
# ---------------------------------------------------------------------------

class AgentInvokeRequest(BaseModel):
    """Request to invoke an AI agent."""
    agent_type: AgentType = Field(..., description="Type of agent to invoke")
    query: str = Field(..., min_length=1, max_length=10000, description="User query or instruction")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    provider: str | None = Field(None, description="LLM provider override")
    model_name: str | None = Field(None, description="Model name override")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(4096, ge=1, le=128000, description="Maximum response tokens")
    stream: bool = Field(False, description="Enable streaming response")

    model_config = {"json_schema_extra": {
        "examples": [{
            "agent_type": "document_qa",
            "query": "What is our company refund policy?",
            "context": {"department": "customer_support"},
        }]
    }}


class AgentResponse(BaseModel):
    """Response from an AI agent invocation."""
    id: str = Field(..., description="Unique invocation ID")
    agent_type: AgentType
    status: AgentStatus
    result: str = Field(..., description="Agent response content")
    metadata: AgentMetadata
    created_at: datetime


class AgentMetadata(BaseModel):
    """Metadata about an agent execution."""
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="LLM provider")
    tokens_used: TokenUsage
    latency_ms: float = Field(..., description="Total execution time in milliseconds")
    steps: list[AgentStep] = Field(default_factory=list, description="Execution steps")
    sources: list[str] = Field(default_factory=list, description="Retrieved source documents")


class TokenUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class AgentStep(BaseModel):
    """Single step in agent execution."""
    step_number: int
    action: str
    input: str = ""
    output: str = ""
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Document Schemas
# ---------------------------------------------------------------------------

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: str
    filename: str
    chunks_created: int
    status: str = "processed"
    created_at: datetime


class DocumentSearchRequest(BaseModel):
    """Request to search documents."""
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(5, ge=1, le=50)
    filters: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResult(BaseModel):
    """Single search result."""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResponse(BaseModel):
    """Response from document search."""
    query: str
    results: list[DocumentSearchResult]
    total_results: int


# ---------------------------------------------------------------------------
# Health Schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "agent-api"
    version: str = "1.0.0"
    environment: str = "development"
    checks: dict[str, str] = Field(default_factory=dict)


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    ready: bool = True
    database: str = "connected"
    llm_provider: str = "available"


# ---------------------------------------------------------------------------
# Error Schemas
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str = ""
    status_code: int = 500
    timestamp: datetime = Field(default_factory=datetime.utcnow)
