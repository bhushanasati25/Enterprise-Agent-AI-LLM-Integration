"""
LLM Evaluator — Benchmark API Routes
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.evaluation.benchmark_runner import BenchmarkConfig, BenchmarkRunner
from app.evaluation.reports import generate_json_report

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

# In-memory results store (production would use a database)
_benchmark_results: dict[str, dict] = {}


class BenchmarkRequest(BaseModel):
    """Request to run a benchmark suite."""
    models: list[str] = Field(
        default=["mock-gpt-4o", "mock-claude-sonnet", "mock-gemini-pro"],
        description="Model names to benchmark",
    )
    dataset: str = Field(default="enterprise_qa", description="Dataset name")
    metrics: list[str] = Field(
        default=["accuracy", "latency", "cost", "safety"],
        description="Metrics to evaluate",
    )
    max_samples: int | None = Field(None, description="Max samples to evaluate")


# Model name → provider mapping
MODEL_PROVIDER_MAP = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "claude-3-5-sonnet": "anthropic",
    "claude-3-haiku": "anthropic",
    "gemini-1.5-pro": "google",
    "gemini-1.5-flash": "google",
    "mock-gpt-4o": "mock",
    "mock-claude-sonnet": "mock",
    "mock-gemini-pro": "mock",
}


@router.post("/run", summary="Run a benchmark suite")
async def run_benchmark(request: BenchmarkRequest) -> dict[str, Any]:
    """
    Execute LLM benchmarks across specified models and return comparative results.
    """
    # Map model names to provider configs
    model_configs = []
    for model_name in request.models:
        provider = MODEL_PROVIDER_MAP.get(model_name, "mock")
        model_configs.append({"provider": provider, "model": model_name})

    config = BenchmarkConfig(
        models=model_configs,
        dataset=request.dataset,
        metrics=request.metrics,
        max_samples=request.max_samples,
    )

    runner = BenchmarkRunner()

    try:
        report = await runner.run(config)
        result = generate_json_report(report)

        # Store results
        _benchmark_results[report.id] = result

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@router.get("/results/{benchmark_id}", summary="Get benchmark results")
async def get_benchmark_results(benchmark_id: str) -> dict[str, Any]:
    """Retrieve results of a previous benchmark run."""
    if benchmark_id not in _benchmark_results:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return _benchmark_results[benchmark_id]


@router.get("/results", summary="List all benchmark results")
async def list_benchmark_results() -> list[dict[str, Any]]:
    """List all stored benchmark results."""
    return [
        {"id": bid, "dataset": data.get("dataset"), "timestamp": data.get("timestamp")}
        for bid, data in _benchmark_results.items()
    ]
