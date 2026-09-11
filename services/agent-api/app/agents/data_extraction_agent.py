"""
Enterprise Agent AI — Data Extraction Agent

LangGraph workflow for structured data extraction from unstructured text.
Implements: text analysis → schema mapping → extraction → validation.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models.schemas import AgentResponse, AgentStatus, AgentStep, AgentType


class DataExtractionAgent(BaseAgent):
    """
    Structured data extraction agent.

    Workflow:
    1. Analyze input text and identify extractable entities
    2. Map entities to target schema
    3. Extract structured data with confidence scores
    4. Validate extracted data
    """

    agent_type = AgentType.DATA_EXTRACTION

    def _build_system_prompt(self) -> str:
        return (
            "You are an enterprise data extraction specialist. Your role is to extract "
            "structured data from unstructured text with high accuracy.\n\n"
            "Guidelines:\n"
            "- Extract all relevant fields from the provided text.\n"
            "- Return data in valid JSON format.\n"
            "- Include confidence scores for each extracted field (0.0 to 1.0).\n"
            "- Flag any ambiguous or uncertain extractions.\n"
            "- Normalize dates, currencies, and numeric values to standard formats.\n"
            "- If a field cannot be determined, set it to null with confidence 0.0."
        )

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Execute the data extraction workflow."""
        start_time = self._timer()
        steps: list[AgentStep] = []
        context = context or {}

        # Get target schema from context, or use default
        target_schema = context.get("schema", self._default_schema())

        # Step 1: Text Analysis
        step_start = self._timer()
        analysis_messages = [
            SystemMessage(content=(
                "Analyze the following text and identify all extractable entities, "
                "data points, and structured information. List them categorically."
            )),
            HumanMessage(content=f"Text to analyze:\n\n{query}"),
        ]
        analysis_response = self.llm.invoke(analysis_messages)

        steps.append(AgentStep(
            step_number=1,
            action="text_analysis",
            input=query[:200],
            output=str(analysis_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Step 2: Schema-Guided Extraction
        step_start = self._timer()
        extraction_messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=(
                f"Extract structured data from the following text according to this schema:\n\n"
                f"Target Schema:\n```json\n{json.dumps(target_schema, indent=2)}\n```\n\n"
                f"Text:\n{query}\n\n"
                f"Previous Analysis:\n{analysis_response.content}\n\n"
                f"Return a JSON object with the extracted data and confidence scores."
            )),
        ]
        extraction_response = self.llm.invoke(extraction_messages)

        steps.append(AgentStep(
            step_number=2,
            action="schema_extraction",
            input=f"Extracting against {len(target_schema)} schema fields",
            output=str(extraction_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Step 3: Validation
        step_start = self._timer()
        validation_messages = [
            SystemMessage(content=(
                "Validate the extracted data for correctness, completeness, and consistency. "
                "Check for logical errors, missing required fields, and data type mismatches. "
                "Return a validation report."
            )),
            HumanMessage(content=(
                f"Extracted Data:\n{extraction_response.content}\n\n"
                f"Original Text:\n{query[:500]}\n\n"
                f"Validate and report any issues."
            )),
        ]
        validation_response = self.llm.invoke(validation_messages)

        steps.append(AgentStep(
            step_number=3,
            action="validation",
            input="Validating extracted data",
            output=str(validation_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Build final result
        result = (
            f"## Extracted Data\n\n{extraction_response.content}\n\n"
            f"## Validation Report\n\n{validation_response.content}"
        )

        tokens = self._extract_token_usage(extraction_response)
        latency = self._timer() - start_time

        return self._create_response(
            result=result,
            status=AgentStatus.COMPLETED,
            steps=steps,
            tokens=tokens,
            latency_ms=latency,
        )

    def _default_schema(self) -> dict[str, Any]:
        """Default extraction schema for general business documents."""
        return {
            "company_name": {"type": "string", "required": True},
            "date": {"type": "date", "required": False},
            "revenue": {"type": "currency", "required": False},
            "key_metrics": {"type": "object", "required": False},
            "contacts": {
                "type": "array",
                "items": {
                    "name": "string",
                    "role": "string",
                    "email": "string",
                },
                "required": False,
            },
            "action_items": {"type": "array", "items": "string", "required": False},
        }
