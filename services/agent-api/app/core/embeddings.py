"""
Enterprise Agent AI — Embeddings Configuration

Embedding model factory for vector search / RAG.
"""

from __future__ import annotations

import random
from typing import Any

from langchain_core.embeddings import Embeddings

from app.core.config import get_settings


class MockEmbeddings(Embeddings):
    """Mock embedding model for development and testing."""

    dimension: int = 1536

    def __init__(self, dimension: int = 1536, **kwargs: Any):
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate mock embeddings for a list of texts."""
        return [self._generate_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Generate a mock embedding for a single query."""
        return self._generate_embedding(text)

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate a deterministic-ish mock embedding based on text hash."""
        random.seed(hash(text) % (2**32))
        return [random.gauss(0, 0.1) for _ in range(self.dimension)]


def create_embeddings(
    provider: str | None = None,
    model_name: str | None = None,
) -> Embeddings:
    """
    Create an embeddings model instance.

    Args:
        provider: Provider name (openai, mock)
        model_name: Specific model to use

    Returns:
        A configured Embeddings instance
    """
    settings = get_settings()
    provider = provider or settings.default_llm_provider

    if provider == "openai" and settings.openai_api_key:
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=model_name or settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    # Default: Mock embeddings
    return MockEmbeddings(dimension=settings.embedding_dimension)
