"""Tests for the benchmark runner."""

from __future__ import annotations

import os

import pytest

os.environ["ENVIRONMENT"] = "testing"
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"

from app.evaluation.benchmark_runner import BenchmarkConfig, BenchmarkRunner
from app.evaluation.reports import generate_json_report


@pytest.mark.asyncio
async def test_benchmark_runner_single_model():
    """Test benchmark runner with a single mock model."""
    config = BenchmarkConfig(
        models=[{"provider": "mock", "model": "mock-gpt-4o"}],
        dataset="enterprise_qa",
        metrics=["accuracy", "latency", "cost", "safety"],
        max_samples=3,
    )

    runner = BenchmarkRunner()
    report = await runner.run(config)

    assert report.id
    assert report.dataset == "enterprise_qa"
    assert len(report.models) == 1
    assert report.models[0].model == "mock-gpt-4o"
    assert report.models[0].samples_evaluated == 3
    assert report.duration_seconds > 0


@pytest.mark.asyncio
async def test_benchmark_runner_multi_model():
    """Test benchmark runner comparing multiple models."""
    config = BenchmarkConfig(
        models=[
            {"provider": "mock", "model": "mock-gpt-4o"},
            {"provider": "mock", "model": "mock-claude-sonnet"},
        ],
        dataset="enterprise_qa",
        metrics=["accuracy", "safety"],
        max_samples=2,
    )

    runner = BenchmarkRunner()
    report = await runner.run(config)

    assert len(report.models) == 2
    assert report.best_model  # Should identify a best model
    assert report.summary["model_comparison"]


@pytest.mark.asyncio
async def test_benchmark_report_generation():
    """Test JSON report generation."""
    config = BenchmarkConfig(
        models=[{"provider": "mock", "model": "mock-gpt-4o"}],
        dataset="enterprise_qa",
        max_samples=2,
    )

    runner = BenchmarkRunner()
    report = await runner.run(config)
    json_report = generate_json_report(report)

    assert json_report["benchmark_id"]
    assert json_report["dataset"] == "enterprise_qa"
    assert len(json_report["models"]) == 1
    assert json_report["recommendations"]  # Should have recommendations


@pytest.mark.asyncio
async def test_benchmark_all_metrics_present():
    """Test all requested metrics are present in results."""
    config = BenchmarkConfig(
        models=[{"provider": "mock", "model": "mock-gpt-4o"}],
        dataset="enterprise_qa",
        metrics=["accuracy", "latency", "cost", "safety"],
        max_samples=2,
    )

    runner = BenchmarkRunner()
    report = await runner.run(config)

    model_result = report.models[0]
    assert "accuracy" in model_result.metric_results
    assert "latency" in model_result.metric_results
    assert "cost" in model_result.metric_results
    assert "safety" in model_result.metric_results


@pytest.mark.asyncio
async def test_benchmark_invalid_dataset():
    """Test benchmark with invalid dataset raises error."""
    config = BenchmarkConfig(
        models=[{"provider": "mock", "model": "mock-gpt-4o"}],
        dataset="nonexistent_dataset",
    )

    runner = BenchmarkRunner()
    with pytest.raises(ValueError, match="Unknown dataset"):
        await runner.run(config)
