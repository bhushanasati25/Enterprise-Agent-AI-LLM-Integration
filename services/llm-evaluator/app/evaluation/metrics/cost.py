"""
LLM Evaluator — Cost Metric

Measures cost-efficiency of LLM responses per token and per query.
"""

from __future__ import annotations

from app.evaluation.metrics.base import BaseMetric, MetricResult

# Pricing per 1K tokens (approximate 2025/2026 rates)
PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "mock-gpt-4o": {"input": 0.0, "output": 0.0},
    "mock-claude-sonnet": {"input": 0.0, "output": 0.0},
    "mock-gemini-pro": {"input": 0.0, "output": 0.0},
}


class CostMetric(BaseMetric):
    """
    Cost-efficiency metric.
    Scores based on cost per quality unit (cost-adjusted accuracy).
    """

    def __init__(self, max_cost_per_query: float = 0.10):
        self.max_cost_per_query = max_cost_per_query

    @property
    def name(self) -> str:
        return "cost"

    @property
    def threshold(self) -> float:
        return 0.3

    async def evaluate(
        self,
        prediction: str,
        reference: str = "",
        query: str = "",
        context: str = "",
    ) -> float:
        """Score based on cost relative to budget."""
        try:
            cost = float(context) if context else 0.0
        except (ValueError, TypeError):
            cost = 0.0

        if cost <= 0:
            return 1.0

        score = 1.0 - (cost / self.max_cost_per_query)
        return max(0.0, min(1.0, score))

    @staticmethod
    def calculate_cost(
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate cost for a specific model and token usage."""
        pricing = PRICING.get(model, {"input": 0.001, "output": 0.003})

        # Match partial model names
        if model not in PRICING:
            for key, price in PRICING.items():
                if key in model.lower():
                    pricing = price
                    break

        return (
            (prompt_tokens / 1000) * pricing["input"]
            + (completion_tokens / 1000) * pricing["output"]
        )

    async def aggregate(self, scores: list[float]) -> MetricResult:
        """Aggregate with total cost analysis."""
        result = await super().aggregate(scores)
        result.details["max_budget_per_query"] = self.max_cost_per_query
        return result
