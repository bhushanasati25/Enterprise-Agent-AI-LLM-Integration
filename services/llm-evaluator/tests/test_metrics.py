"""Tests for evaluation metrics."""

from __future__ import annotations

import os

import pytest

os.environ["ENVIRONMENT"] = "testing"
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"

from app.evaluation.metrics.accuracy import AccuracyMetric
from app.evaluation.metrics.cost import CostMetric
from app.evaluation.metrics.latency import LatencyMetric
from app.evaluation.metrics.safety import SafetyMetric


@pytest.mark.asyncio
async def test_accuracy_exact_match():
    """Test accuracy metric with exact match."""
    metric = AccuracyMetric()
    score = await metric.evaluate(
        prediction="The answer is 42.",
        reference="The answer is 42.",
    )
    assert score > 0.8


@pytest.mark.asyncio
async def test_accuracy_partial_match():
    """Test accuracy metric with partial match."""
    metric = AccuracyMetric()
    score = await metric.evaluate(
        prediction="Revenue was $12.5 million with 15% growth.",
        reference="Revenue of $12.5M, growing at 15%.",
    )
    assert score > 0.3  # Should have some overlap


@pytest.mark.asyncio
async def test_accuracy_no_match():
    """Test accuracy metric with completely different texts."""
    metric = AccuracyMetric()
    score = await metric.evaluate(
        prediction="The sky is blue today.",
        reference="Machine learning models require training data.",
    )
    assert score < 0.5


@pytest.mark.asyncio
async def test_accuracy_no_reference():
    """Test accuracy with no reference returns neutral score."""
    metric = AccuracyMetric()
    score = await metric.evaluate(prediction="Some answer")
    assert score == 0.5


@pytest.mark.asyncio
async def test_latency_fast_response():
    """Test latency metric scores fast responses highly."""
    metric = LatencyMetric(max_acceptable_ms=5000)
    score = await metric.evaluate(prediction="", context="100")  # 100ms
    assert score > 0.9


@pytest.mark.asyncio
async def test_latency_slow_response():
    """Test latency metric penalizes slow responses."""
    metric = LatencyMetric(max_acceptable_ms=5000)
    score = await metric.evaluate(prediction="", context="4500")  # 4500ms
    assert score < 0.2


@pytest.mark.asyncio
async def test_latency_zero():
    """Test latency metric with zero latency."""
    metric = LatencyMetric()
    score = await metric.evaluate(prediction="", context="0")
    assert score == 1.0


@pytest.mark.asyncio
async def test_cost_free():
    """Test cost metric with free (mock) provider."""
    metric = CostMetric(max_cost_per_query=0.10)
    score = await metric.evaluate(prediction="", context="0")
    assert score == 1.0


@pytest.mark.asyncio
async def test_cost_expensive():
    """Test cost metric with expensive query."""
    metric = CostMetric(max_cost_per_query=0.10)
    score = await metric.evaluate(prediction="", context="0.08")
    assert score < 0.3


@pytest.mark.asyncio
async def test_cost_calculation():
    """Test cost calculation for known model."""
    cost = CostMetric.calculate_cost("mock-gpt-4o", 1000, 500)
    assert cost == 0.0  # Mock models are free


@pytest.mark.asyncio
async def test_safety_clean_response():
    """Test safety metric with a clean response."""
    metric = SafetyMetric()
    score = await metric.evaluate(
        prediction="Based on our analysis, the recommended approach involves three key steps."
    )
    assert score > 0.9


@pytest.mark.asyncio
async def test_safety_pii_detection():
    """Test safety metric detects PII."""
    metric = SafetyMetric()
    score = await metric.evaluate(
        prediction="Contact john@example.com or call 555-123-4567 for SSN 123-45-6789."
    )
    assert score < 0.8  # Should penalize PII


@pytest.mark.asyncio
async def test_safety_hallucination_markers():
    """Test safety metric detects hallucination markers."""
    metric = SafetyMetric()
    score = await metric.evaluate(
        prediction="As of my last knowledge cutoff, I'm not sure if this is accurate."
    )
    assert score < 1.0  # Should penalize hedging


@pytest.mark.asyncio
async def test_metric_aggregation():
    """Test metric result aggregation."""
    metric = AccuracyMetric()
    scores = [0.9, 0.85, 0.78, 0.92, 0.88]
    result = await metric.aggregate(scores)

    assert result.metric_name == "accuracy"
    assert 0.85 < result.score < 0.90
    assert result.passed  # Above threshold
    assert result.details["count"] == 5
    assert result.details["min"] == 0.78
    assert result.details["max"] == 0.92


@pytest.mark.asyncio
async def test_metric_aggregation_empty():
    """Test aggregation with empty scores."""
    metric = AccuracyMetric()
    result = await metric.aggregate([])
    assert result.score == 0.0
    assert result.passed is False
