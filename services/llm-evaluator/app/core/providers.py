"""
LLM Evaluator — Unified LLM Provider Interface

Provides a consistent interface for calling different LLM providers
during benchmarking, including mock providers for testing.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any

from app.core.config import get_evaluator_settings


@dataclass
class LLMResponse:
    """Standardized LLM response across all providers."""
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider:
    """Unified interface for calling LLM providers."""

    def __init__(self, provider: str, model: str, api_key: str = ""):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        start_time = time.time()

        if self.provider == "mock":
            response = self._mock_generate(prompt, system_prompt)
        elif self.provider == "openai":
            response = await self._openai_generate(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            response = await self._anthropic_generate(prompt, system_prompt, temperature, max_tokens)
        else:
            response = self._mock_generate(prompt, system_prompt)

        response.latency_ms = (time.time() - start_time) * 1000
        return response

    def _mock_generate(self, prompt: str, system_prompt: str) -> LLMResponse:
        """Generate a mock response for benchmarking without real API keys."""
        # Simulate variable latency
        time.sleep(random.uniform(0.05, 0.3))

        # Generate model-specific mock responses
        mock_data = {
            "mock-gpt-4o": {
                "quality": 0.90,
                "style": "detailed and structured",
            },
            "mock-claude-sonnet": {
                "quality": 0.88,
                "style": "analytical and precise",
            },
            "mock-gemini-pro": {
                "quality": 0.85,
                "style": "comprehensive and broad",
            },
        }

        model_info = mock_data.get(self.model, {"quality": 0.80, "style": "generic"})

        content = (
            f"Based on my analysis, here is a {model_info['style']} response:\n\n"
            f"The key findings regarding your query about '{prompt[:80]}...' are:\n\n"
            f"1. Primary analysis indicates the core issue relates to enterprise process optimization\n"
            f"2. Secondary factors include compliance requirements and operational efficiency\n"
            f"3. Recommended actions have been identified based on best practices\n\n"
            f"Confidence: {model_info['quality'] * 100:.0f}%"
        )

        prompt_tokens = random.randint(100, 500)
        completion_tokens = random.randint(80, 400)

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    async def _openai_generate(
        self, prompt: str, system_prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Generate using OpenAI API."""
        import openai

        client = openai.AsyncOpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=self.model,
            provider="openai",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    async def _anthropic_generate(
        self, prompt: str, system_prompt: str, temperature: float, max_tokens: int
    ) -> LLMResponse:
        """Generate using Anthropic API."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=self.model,
            provider="anthropic",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )


def create_provider(provider: str, model: str) -> LLMProvider:
    """Factory function to create an LLM provider with the right API key."""
    settings = get_evaluator_settings()

    api_keys = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "google": settings.google_api_key,
        "mock": "",
    }

    return LLMProvider(
        provider=provider,
        model=model,
        api_key=api_keys.get(provider, ""),
    )
