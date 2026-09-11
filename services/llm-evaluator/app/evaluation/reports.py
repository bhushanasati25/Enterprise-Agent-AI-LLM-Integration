"""
LLM Evaluator — Report Generation

Generates JSON and summary reports from benchmark results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.evaluation.benchmark_runner import BenchmarkReport, ModelBenchmarkResult


def generate_json_report(report: BenchmarkReport) -> dict[str, Any]:
    """Generate a structured JSON report from benchmark results."""
    return {
        "benchmark_id": report.id,
        "dataset": report.dataset,
        "timestamp": datetime.fromtimestamp(report.created_at).isoformat(),
        "duration_seconds": report.duration_seconds,
        "best_model": report.best_model,
        "models": [
            _format_model_result(result) for result in report.models
        ],
        "comparative_summary": report.summary,
        "recommendations": _generate_recommendations(report),
    }


def _format_model_result(result: ModelBenchmarkResult) -> dict[str, Any]:
    """Format a single model's results."""
    metrics = {}
    for name, metric_result in result.metric_results.items():
        metrics[name] = {
            "score": metric_result.score,
            "passed": metric_result.passed,
            "details": metric_result.details,
        }

    return {
        "model": result.model,
        "provider": result.provider,
        "metrics": metrics,
        "total_cost_usd": result.total_cost_usd,
        "avg_latency_ms": result.avg_latency_ms,
        "total_tokens": result.total_tokens,
        "samples_evaluated": result.samples_evaluated,
    }


def _generate_recommendations(report: BenchmarkReport) -> list[str]:
    """Generate actionable recommendations from benchmark results."""
    recommendations = []

    if not report.models:
        return ["No models were evaluated. Check configuration."]

    # Find best model per metric
    metric_leaders: dict[str, tuple[str, float]] = {}
    for result in report.models:
        for metric_name, metric_result in result.metric_results.items():
            current_best = metric_leaders.get(metric_name, ("", -1.0))
            if metric_result.score > current_best[1]:
                metric_leaders[metric_name] = (result.model, metric_result.score)

    # Generate recommendations
    for metric, (model, score) in metric_leaders.items():
        if score >= 0.9:
            recommendations.append(
                f"✅ {model} excels at {metric} (score: {score:.2f})"
            )
        elif score >= 0.7:
            recommendations.append(
                f"⚠️ {model} is adequate for {metric} (score: {score:.2f}) — consider alternatives"
            )
        else:
            recommendations.append(
                f"❌ All models underperform on {metric} (best: {score:.2f}) — review evaluation criteria"
            )

    # Cost vs. quality tradeoff
    if len(report.models) > 1:
        cheapest = min(report.models, key=lambda r: r.total_cost_usd)
        most_accurate = max(
            report.models,
            key=lambda r: r.metric_results.get("accuracy", type("", (), {"score": 0})).score,
        )
        if cheapest.model != most_accurate.model:
            recommendations.append(
                f"💡 Cost-quality tradeoff: {cheapest.model} is cheapest "
                f"(${cheapest.total_cost_usd:.4f}), but {most_accurate.model} is most accurate"
            )

    return recommendations
