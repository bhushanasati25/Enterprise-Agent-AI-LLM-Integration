"""
Enterprise Agent AI — Document Q&A Agent

LangGraph workflow for document-grounded question answering with citations.
Implements: retrieval → reasoning → answer generation with source attribution.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models.schemas import AgentResponse, AgentStatus, AgentStep, AgentType


class DocumentQAAgent(BaseAgent):
    """
    Document Q&A agent using a RAG pipeline.

    Workflow:
    1. Parse and understand the query
    2. Retrieve relevant document chunks (simulated for now)
    3. Reason over retrieved context
    4. Generate answer with citations
    """

    agent_type = AgentType.DOCUMENT_QA

    def _build_system_prompt(self) -> str:
        return (
            "You are an enterprise document Q&A assistant. Your role is to answer "
            "questions accurately based on the provided document context.\n\n"
            "Guidelines:\n"
            "- Only answer based on the provided context. If the context doesn't "
            "contain the answer, say so clearly.\n"
            "- Always cite your sources with [Source: document_name, section] format.\n"
            "- Provide structured, professional responses.\n"
            "- Highlight key findings with bullet points.\n"
            "- If multiple documents are relevant, synthesize across them."
        )

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Execute the document Q&A workflow."""
        start_time = self._timer()
        steps: list[AgentStep] = []
        context = context or {}

        # Step 1: Query Analysis
        step_start = self._timer()
        analysis_prompt = (
            f"Analyze this enterprise query and identify key topics to search for:\n"
            f"Query: {query}\n"
            f"Context: {context}\n\n"
            f"Respond with the key search terms and the type of information needed."
        )

        messages = [
            SystemMessage(content="You are a query analysis expert. Identify search terms."),
            HumanMessage(content=analysis_prompt),
        ]
        analysis_response = self.llm.invoke(messages)

        steps.append(AgentStep(
            step_number=1,
            action="query_analysis",
            input=query,
            output=str(analysis_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Step 2: Document Retrieval (simulated)
        step_start = self._timer()
        retrieved_docs = self._simulate_retrieval(query)

        steps.append(AgentStep(
            step_number=2,
            action="document_retrieval",
            input=f"Searching for: {query[:100]}",
            output=f"Retrieved {len(retrieved_docs)} relevant chunks",
            duration_ms=self._timer() - step_start,
        ))

        # Step 3: Answer Generation with Context
        step_start = self._timer()
        context_text = "\n\n".join(
            f"[Source: {doc['source']}]\n{doc['content']}" for doc in retrieved_docs
        )

        answer_messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=(
                f"Based on the following document context, answer the question.\n\n"
                f"Context:\n{context_text}\n\n"
                f"Question: {query}\n\n"
                f"Provide a comprehensive answer with citations."
            )),
        ]

        answer_response = self.llm.invoke(answer_messages)

        steps.append(AgentStep(
            step_number=3,
            action="answer_generation",
            input=f"Generating answer from {len(retrieved_docs)} sources",
            output=str(answer_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Build response
        tokens = self._extract_token_usage(answer_response)
        latency = self._timer() - start_time
        sources = [doc["source"] for doc in retrieved_docs]

        return self._create_response(
            result=str(answer_response.content),
            status=AgentStatus.COMPLETED,
            steps=steps,
            tokens=tokens,
            latency_ms=latency,
            sources=sources,
        )

    def _simulate_retrieval(self, query: str) -> list[dict[str, Any]]:
        """
        Simulate document retrieval for demonstration.
        In production, this would query pgvector.
        """
        return [
            {
                "source": "Enterprise Policy Manual v3.2, Section 4.1",
                "content": (
                    "All customer service requests must be acknowledged within 2 business "
                    "hours and resolved within 48 business hours. Escalation procedures "
                    "must be followed for requests exceeding the SLA threshold."
                ),
                "score": 0.92,
            },
            {
                "source": "Compliance Handbook 2025, Chapter 7",
                "content": (
                    "Data handling procedures must comply with SOC 2 Type II standards. "
                    "All personally identifiable information (PII) must be encrypted at "
                    "rest using AES-256 and in transit using TLS 1.3."
                ),
                "score": 0.87,
            },
            {
                "source": "Operations Runbook, Section 12.3",
                "content": (
                    "Production services maintain a 99.9% uptime SLA. Incident response "
                    "teams must be notified within 15 minutes of any P1 incident. "
                    "Post-mortems are required for all severity 1 and 2 incidents."
                ),
                "score": 0.81,
            },
        ]
