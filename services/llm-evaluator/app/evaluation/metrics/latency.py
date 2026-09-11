"""
LLM Evaluator — Latency Metric

Measures response latency with percentile analysis.
"""

from __future__ import annotations

from app.evaluation.metrics.base import BaseMetric, MetricResult


class LatencyMetric(BaseMetric):
    """
    Latency metric measuring response time in milliseconds.
    Lower is better — score is inverse of latency relative to threshold.
    """

    def __init__(self, max_acceptable_ms: float = 5000.0):
        self.max_acceptable_ms = max_acceptable_ms

    @property
    def name(self) -> str:
        return "latency"

    @property
    def threshold(self) -> float:
        return 0.5  # At least 50% of max acceptable time

    async def evaluate(
        self,
        prediction: str,
        reference: str = "",
        query: str = "",
        context: str = "",
    ) -> float:
        """
        Score is based on latency stored in context.
        Score = 1.0 - (latency / max_acceptable), clamped to [0, 1].
        """
        # Extract latency from context (passed as string for interface compat)
        try:
            latency_ms = float(context) if context else 0.0
        except (ValueError, TypeError):
            latency_ms = 0.0

        if latency_ms <= 0:
            return 1.0

        score = 1.0 - (latency_ms / self.max_acceptable_ms)
        return max(0.0, min(1.0, score))

    async def aggregate(self, scores: list[float]) -> MetricResult:
        """Aggregate with percentile analysis."""
        result = await super().aggregate(scores)

        if scores:
            sorted_scores = sorted(scores)
            n = len(sorted_scores)
            result.details["p50"] = sorted_scores[int(n * 0.50)]
            result.details["p95"] = sorted_scores[int(min(n * 0.95, n - 1))]
            result.details["p99"] = sorted_scores[int(min(n * 0.99, n - 1))]

        return result
