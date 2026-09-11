"""
LLM Evaluator — Model Routes
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.evaluation.datasets import list_datasets

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/", summary="List available models")
async def list_models() -> list[dict[str, Any]]:
    """List all configured LLM models available for benchmarking."""
    return [
        {
            "provider": "openai",
            "models": [
                {"name": "gpt-4o", "type": "chat", "context_window": 128000},
                {"name": "gpt-4o-mini", "type": "chat", "context_window": 128000},
            ],
        },
        {
            "provider": "anthropic",
            "models": [
                {"name": "claude-3-5-sonnet", "type": "chat", "context_window": 200000},
                {"name": "claude-3-haiku", "type": "chat", "context_window": 200000},
            ],
        },
        {
            "provider": "google",
            "models": [
                {"name": "gemini-1.5-pro", "type": "chat", "context_window": 2000000},
                {"name": "gemini-1.5-flash", "type": "chat", "context_window": 1000000},
            ],
        },
        {
            "provider": "mock",
            "models": [
                {"name": "mock-gpt-4o", "type": "mock", "context_window": 128000},
                {"name": "mock-claude-sonnet", "type": "mock", "context_window": 200000},
                {"name": "mock-gemini-pro", "type": "mock", "context_window": 2000000},
            ],
        },
    ]


@router.get("/datasets", summary="List evaluation datasets")
async def list_evaluation_datasets() -> list[dict[str, Any]]:
    """List available benchmark datasets."""
    return list_datasets()
