"""
LLM Evaluator — Accuracy Metric

Measures response accuracy using exact match, fuzzy match, and semantic similarity.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.evaluation.metrics.base import BaseMetric


class AccuracyMetric(BaseMetric):
    """
    Multi-signal accuracy metric combining:
    - Exact match (normalized)
    - Fuzzy string similarity
    - Key fact extraction match
    """

    @property
    def name(self) -> str:
        return "accuracy"

    @property
    def threshold(self) -> float:
        return 0.70

    async def evaluate(
        self,
        prediction: str,
        reference: str = "",
        query: str = "",
        context: str = "",
    ) -> float:
        if not reference:
            return 0.5  # No reference — neutral score

        # Normalize texts
        pred_norm = self._normalize(prediction)
        ref_norm = self._normalize(reference)

        # Signal 1: Exact match (binary)
        exact_match = 1.0 if pred_norm == ref_norm else 0.0

        # Signal 2: Fuzzy similarity
        fuzzy_score = SequenceMatcher(None, pred_norm, ref_norm).ratio()

        # Signal 3: Key fact overlap
        fact_score = self._key_fact_overlap(prediction, reference)

        # Weighted combination
        score = (
            exact_match * 0.2
            + fuzzy_score * 0.3
            + fact_score * 0.5
        )

        return min(1.0, max(0.0, score))

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def _key_fact_overlap(self, prediction: str, reference: str) -> float:
        """
        Calculate overlap of key facts between prediction and reference.
        Extracts numbers, proper nouns, and key phrases.
        """
        ref_facts = self._extract_facts(reference)

        if not ref_facts:
            return 0.5

        matched = sum(1 for fact in ref_facts if fact in prediction.lower())
        return matched / len(ref_facts)

    def _extract_facts(self, text: str) -> list[str]:
        """Extract key facts (numbers, percentages, key terms)."""
        facts = []

        # Extract numbers and percentages
        numbers = re.findall(r"\d+\.?\d*%?", text)
        facts.extend(numbers)

        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', text)
        facts.extend(q.lower() for q in quoted)

        # Extract capitalized multi-word terms (potential proper nouns)
        proper = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", text)
        facts.extend(p.lower() for p in proper)

        return facts
