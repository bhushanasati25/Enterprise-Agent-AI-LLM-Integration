"""
LLM Evaluator — Core Configuration
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class EvaluatorSettings(BaseSettings):
    """Evaluator service settings."""

    environment: str = "development"
    log_level: str = "INFO"

    evaluator_host: str = "0.0.0.0"
    evaluator_port: int = 8001
    evaluator_workers: int = 2

    default_llm_provider: str = "mock"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    max_concurrent_evaluations: int = 5
    benchmark_timeout_seconds: int = 300

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_evaluator_settings() -> EvaluatorSettings:
    return EvaluatorSettings()
