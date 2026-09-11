"""
LLM Evaluator — Base Metric

Abstract base class for all custom benchmarking metrics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricResult:
    """Result from a single metric evaluation."""
    metric_name: str
    score: float  # 0.0 to 1.0
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    raw_scores: list[float] = field(default_factory=list)


class BaseMetric(ABC):
    """
    Abstract base class for custom evaluation metrics.

    All metrics must implement:
    - name: Unique metric identifier
    - evaluate(): Score a single model response
    - aggregate(): Combine scores across a dataset
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique metric identifier."""
        ...

    @property
    def threshold(self) -> float:
        """Minimum score to pass (0.0 to 1.0)."""
        return 0.7

    @abstractmethod
    async def evaluate(
        self,
        prediction: str,
        reference: str = "",
        query: str = "",
        context: str = "",
    ) -> float:
        """
        Evaluate a single model response.

        Args:
            prediction: Model-generated response
            reference: Ground truth / expected answer
            query: Original input query
            context: Additional context

        Returns:
            Score between 0.0 and 1.0
        """
        ...

    async def aggregate(self, scores: list[float]) -> MetricResult:
        """Aggregate scores across a dataset into a MetricResult."""
        if not scores:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={"error": "No scores to aggregate"},
            )

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        return MetricResult(
            metric_name=self.name,
            score=round(avg_score, 4),
            passed=avg_score >= self.threshold,
            details={
                "mean": round(avg_score, 4),
                "min": round(min_score, 4),
                "max": round(max_score, 4),
                "std": round(self._std_dev(scores), 4),
                "count": len(scores),
                "threshold": self.threshold,
            },
            raw_scores=scores,
        )

    @staticmethod
    def _std_dev(values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
