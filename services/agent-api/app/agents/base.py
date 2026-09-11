"""
Enterprise Agent AI — Base Agent

Abstract base class and shared utilities for all LangGraph agent workflows.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.messages import AIMessage

from app.core.config import get_settings
from app.core.llm_factory import create_llm
from app.models.schemas import (
    AgentMetadata,
    AgentResponse,
    AgentStatus,
    AgentStep,
    AgentType,
    TokenUsage,
)


class AgentState(TypedDict, total=False):
    """Shared state for all agent workflows."""
    messages: list[Any]
    query: str
    context: dict[str, Any]
    steps: list[dict[str, Any]]
    result: str
    status: str
    error: str | None
    metadata: dict[str, Any]


class BaseAgent(ABC):
    """
    Abstract base class for enterprise AI agents.

    Provides shared utilities for LLM invocation, state management,
    error handling, and response formatting.
    """

    agent_type: AgentType

    def __init__(
        self,
        provider: str | None = None,
        model_name: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        self.llm = create_llm(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.settings = get_settings()
        self._provider = provider or self.settings.default_llm_provider
        self._model_name = model_name or self.settings.default_model_name

    @abstractmethod
    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Execute the agent workflow and return a formatted response."""
        ...

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent type."""
        return (
            "You are an enterprise AI assistant. Provide accurate, professional, "
            "and well-structured responses. Always cite sources when available. "
            "If you're unsure about something, clearly state your uncertainty."
        )

    def _create_response(
        self,
        result: str,
        status: AgentStatus,
        steps: list[AgentStep],
        tokens: TokenUsage,
        latency_ms: float,
        sources: list[str] | None = None,
    ) -> AgentResponse:
        """Create a standardized agent response."""
        return AgentResponse(
            id=str(uuid.uuid4()),
            agent_type=self.agent_type,
            status=status,
            result=result,
            metadata=AgentMetadata(
                model=self._model_name,
                provider=self._provider,
                tokens_used=tokens,
                latency_ms=latency_ms,
                steps=steps,
                sources=sources or [],
            ),
            created_at=datetime.utcnow(),
        )

    def _extract_token_usage(self, response: AIMessage) -> TokenUsage:
        """Extract token usage from an LLM response."""
        usage = {}
        if hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("usage", {})

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Rough cost estimation
        cost = self._estimate_cost(prompt_tokens, completion_tokens)

        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
        )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on provider pricing."""
        if self._provider == "mock":
            return 0.0

        # Approximate pricing per 1K tokens (2025/2026 rates)
        pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        }

        # Find matching pricing
        model_pricing = {"input": 0.001, "output": 0.003}
        for key, rates in pricing.items():
            if key in self._model_name.lower():
                model_pricing = rates
                break

        return round(
            (prompt_tokens / 1000) * model_pricing["input"]
            + (completion_tokens / 1000) * model_pricing["output"],
            6,
        )

    @staticmethod
    def _timer() -> float:
        """Return current time in milliseconds for latency tracking."""
        return time.time() * 1000
