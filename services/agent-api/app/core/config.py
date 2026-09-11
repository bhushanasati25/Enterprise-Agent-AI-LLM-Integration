"""
Enterprise Agent AI — Core Configuration

Pydantic Settings-based configuration loaded from environment variables.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # General
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # Server
    agent_api_host: str = "0.0.0.0"
    agent_api_port: int = 8000
    agent_api_workers: int = 4

    # Database
    database_url: str = "postgresql+asyncpg://enterprise:enterprise_secret_password@localhost:5432/enterprise_ai"

    # LLM Providers
    default_llm_provider: str = "mock"
    default_model_name: str = "mock-gpt-4o"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Embeddings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    # Security
    jwt_secret_key: str = "your-256-bit-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Monitoring
    prometheus_enabled: bool = True
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "agent-api"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
