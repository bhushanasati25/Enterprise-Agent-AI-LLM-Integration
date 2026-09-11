"""
Enterprise Agent AI — LLM Factory

Unified factory for creating LLM instances across providers (OpenAI, Anthropic, Google, Mock).
Supports fallback chains for resilience.
"""

from __future__ import annotations

import random
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import get_settings


class MockChatModel(BaseChatModel):
    """
    Mock LLM for development and testing.
    Returns realistic-looking responses without requiring API keys.
    """

    model_name: str = "mock-gpt-4o"
    response_delay: float = 0.1

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Simulate latency
        time.sleep(self.response_delay)

        last_message = messages[-1].content if messages else ""

        # Generate contextual mock responses
        mock_responses = {
            "document_qa": (
                "Based on the documents provided, here is the answer to your query:\n\n"
                "The enterprise policy states that all requests must be processed within "
                "48 business hours. Key findings:\n\n"
                "1. **Compliance**: All data handling follows SOC 2 Type II standards\n"
                "2. **SLA**: 99.9% uptime guarantee for production services\n"
                "3. **Security**: End-to-end encryption with AES-256\n\n"
                "**Sources**: Policy Document v3.2, Section 4.1; Compliance Manual 2025, p.42"
            ),
            "extraction": (
                '{"company_name": "Acme Corp", "revenue": "$12.5M", '
                '"quarter": "Q3 2025", "growth_rate": "15.2%", '
                '"key_metrics": {"customer_count": 1250, "churn_rate": "2.1%", '
                '"nps_score": 72}}'
            ),
            "task": (
                "Task execution plan created:\n\n"
                "**Step 1**: Validate input parameters ✅\n"
                "**Step 2**: Query internal database for relevant records\n"
                "**Step 3**: Process and transform data\n"
                "**Step 4**: Generate report and send notifications\n\n"
                "Estimated completion time: 3 minutes\n"
                "Status: Awaiting approval for Step 2"
            ),
        }

        # Select response based on context
        response_text = mock_responses.get("document_qa", "")
        for key, response in mock_responses.items():
            if key in str(last_message).lower():
                response_text = response
                break

        if not response_text:
            response_text = (
                f"I've analyzed your request regarding: '{str(last_message)[:100]}...'\n\n"
                "Here are my findings based on the enterprise knowledge base:\n\n"
                "1. The requested information has been located and verified\n"
                "2. All compliance requirements are met\n"
                "3. Recommended next steps have been identified\n\n"
                "Please let me know if you need additional details."
            )

        message = AIMessage(
            content=response_text,
            response_metadata={
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": random.randint(100, 500),
                    "completion_tokens": random.randint(50, 300),
                    "total_tokens": random.randint(150, 800),
                },
                "finish_reason": "stop",
            },
        )

        return ChatResult(generations=[ChatGeneration(message=message)])


def create_llm(
    provider: str | None = None,
    model_name: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Create an LLM instance based on the specified provider.

    Args:
        provider: LLM provider name (openai, anthropic, google, mock)
        model_name: Specific model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        **kwargs: Additional provider-specific arguments

    Returns:
        A configured BaseChatModel instance
    """
    settings = get_settings()
    provider = provider or settings.default_llm_provider
    model_name = model_name or settings.default_model_name

    if provider == "openai" and settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openai_api_key,
            **kwargs,
        )

    elif provider == "anthropic" and settings.anthropic_api_key:
        from langchain_community.chat_models import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=settings.anthropic_api_key,
            **kwargs,
        )

    elif provider == "google" and settings.google_api_key:
        from langchain_community.chat_models import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=settings.google_api_key,
            **kwargs,
        )

    # Default: Mock provider
    return MockChatModel(model_name=model_name)


def get_available_providers() -> list[dict[str, Any]]:
    """Return list of configured LLM providers and their status."""
    settings = get_settings()

    providers = [
        {
            "provider": "openai",
            "configured": bool(settings.openai_api_key),
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        },
        {
            "provider": "anthropic",
            "configured": bool(settings.anthropic_api_key),
            "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
        },
        {
            "provider": "google",
            "configured": bool(settings.google_api_key),
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
        },
        {
            "provider": "mock",
            "configured": True,
            "models": ["mock-gpt-4o", "mock-claude-sonnet", "mock-gemini-pro"],
        },
    ]

    return providers
