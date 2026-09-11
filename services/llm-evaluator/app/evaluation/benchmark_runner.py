"""
LLM Evaluator — Benchmark Runner

Orchestrates benchmark execution across multiple models and datasets.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.providers import create_provider
from app.evaluation.datasets import load_dataset
from app.evaluation.metrics import AccuracyMetric, CostMetric, LatencyMetric, SafetyMetric
from app.evaluation.metrics.base import BaseMetric, MetricResult
from app.evaluation.metrics.cost import CostMetric as CostMetricClass


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    models: list[dict[str, str]]  # [{"provider": "mock", "model": "mock-gpt-4o"}, ...]
    dataset: str = "enterprise_qa"
    metrics: list[str] = field(default_factory=lambda: ["accuracy", "latency", "cost", "safety"])
    max_samples: int | None = None
    temperature: float = 0.0


@dataclass
class ModelBenchmarkResult:
    """Results for a single model."""
    model: str
    provider: str
    metric_results: dict[str, MetricResult]
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    total_tokens: int = 0
    samples_evaluated: int = 0


@dataclass
class BenchmarkReport:
    """Complete benchmark report across all models."""
    id: str
    dataset: str
    models: list[ModelBenchmarkResult]
    best_model: str = ""
    summary: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    duration_seconds: float = 0.0


class BenchmarkRunner:
    """
    Orchestrates benchmark execution across multiple LLM models.

    Runs each model against a dataset, collects metrics,
    and produces a comparative report.
    """

    # Available metrics registry
    METRICS_REGISTRY: dict[str, type[BaseMetric]] = {
        "accuracy": AccuracyMetric,
        "latency": LatencyMetric,
        "cost": CostMetric,
        "safety": SafetyMetric,
    }

    async def run(self, config: BenchmarkConfig) -> BenchmarkReport:
        """Execute a full benchmark suite."""
        start_time = time.time()
        benchmark_id = str(uuid.uuid4())

        # Load dataset
        dataset = load_dataset(config.dataset)
        if config.max_samples:
            dataset = dataset[: config.max_samples]

        # Initialize metrics
        metrics = self._initialize_metrics(config.metrics)

        # Run benchmarks for each model
        model_results: list[ModelBenchmarkResult] = []
        for model_config in config.models:
            result = await self._benchmark_model(
                provider_name=model_config["provider"],
                model_name=model_config["model"],
                dataset=dataset,
                metrics=metrics,
                temperature=config.temperature,
            )
            model_results.append(result)

        # Determine best model (by accuracy score)
        best_model = ""
        best_accuracy = -1.0
        for result in model_results:
            acc = result.metric_results.get("accuracy")
            if acc and acc.score > best_accuracy:
                best_accuracy = acc.score
                best_model = result.model

        duration = time.time() - start_time

        return BenchmarkReport(
            id=benchmark_id,
            dataset=config.dataset,
            models=model_results,
            best_model=best_model,
            summary=self._build_summary(model_results),
            duration_seconds=round(duration, 2),
        )

    async def _benchmark_model(
        self,
        provider_name: str,
        model_name: str,
        dataset: list[dict[str, Any]],
        metrics: dict[str, BaseMetric],
        temperature: float = 0.0,
    ) -> ModelBenchmarkResult:
        """Run benchmark for a single model."""
        provider = create_provider(provider_name, model_name)

        # Collect scores per metric
        metric_scores: dict[str, list[float]] = {name: [] for name in metrics}
        total_cost = 0.0
        total_tokens = 0
        latencies: list[float] = []

        for sample in dataset:
            query = sample["query"]
            reference = sample.get("reference", "")
            context = sample.get("context", "")

            # Generate response
            response = await provider.generate(
                prompt=query,
                system_prompt=context,
                temperature=temperature,
            )

            # Calculate cost
            cost = CostMetricClass.calculate_cost(
                model_name, response.prompt_tokens, response.completion_tokens
            )
            total_cost += cost
            total_tokens += response.total_tokens
            latencies.append(response.latency_ms)

            # Evaluate each metric
            for name, metric in metrics.items():
                if name == "latency":
                    score = await metric.evaluate(
                        prediction=response.content,
                        context=str(response.latency_ms),
                    )
                elif name == "cost":
                    score = await metric.evaluate(
                        prediction=response.content,
                        context=str(cost),
                    )
                else:
                    score = await metric.evaluate(
                        prediction=response.content,
                        reference=reference,
                        query=query,
                        context=context,
                    )
                metric_scores[name].append(score)

        # Aggregate results
        metric_results = {}
        for name, metric in metrics.items():
            metric_results[name] = await metric.aggregate(metric_scores[name])

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return ModelBenchmarkResult(
            model=model_name,
            provider=provider_name,
            metric_results=metric_results,
            total_cost_usd=round(total_cost, 6),
            avg_latency_ms=round(avg_latency, 2),
            total_tokens=total_tokens,
            samples_evaluated=len(dataset),
        )

    def _initialize_metrics(self, metric_names: list[str]) -> dict[str, BaseMetric]:
        """Initialize requested metrics."""
        metrics = {}
        for name in metric_names:
            metric_class = self.METRICS_REGISTRY.get(name)
            if metric_class:
                metrics[name] = metric_class()
        return metrics

    def _build_summary(self, results: list[ModelBenchmarkResult]) -> dict[str, Any]:
        """Build comparative summary across all models."""
        summary: dict[str, Any] = {"model_comparison": {}}

        for result in results:
            model_summary: dict[str, Any] = {
                "avg_latency_ms": result.avg_latency_ms,
                "total_cost_usd": result.total_cost_usd,
                "total_tokens": result.total_tokens,
                "samples": result.samples_evaluated,
            }
            for metric_name, metric_result in result.metric_results.items():
                model_summary[f"{metric_name}_score"] = metric_result.score
                model_summary[f"{metric_name}_passed"] = metric_result.passed

            summary["model_comparison"][result.model] = model_summary

        return summary
