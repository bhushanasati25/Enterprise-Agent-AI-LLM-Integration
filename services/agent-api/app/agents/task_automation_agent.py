"""
Enterprise Agent AI — Task Automation Agent

LangGraph workflow for multi-step task execution with human-in-the-loop approval.
Implements: planning → execution → review → approval gate.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.models.schemas import AgentResponse, AgentStatus, AgentStep, AgentType


class TaskAutomationAgent(BaseAgent):
    """
    Task automation agent for multi-step enterprise workflows.

    Workflow:
    1. Parse task and generate execution plan
    2. Execute each step sequentially
    3. Validate results at each checkpoint
    4. Generate summary report
    """

    agent_type = AgentType.TASK_AUTOMATION

    def _build_system_prompt(self) -> str:
        return (
            "You are an enterprise task automation specialist. Your role is to break down "
            "complex tasks into executable steps and manage their execution.\n\n"
            "Guidelines:\n"
            "- Create clear, numbered execution plans with estimated durations.\n"
            "- Identify dependencies between steps.\n"
            "- Flag any steps that require human approval.\n"
            "- Provide status updates after each step.\n"
            "- Include rollback procedures for critical operations.\n"
            "- Document all actions taken for audit compliance."
        )

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Execute the task automation workflow."""
        start_time = self._timer()
        steps: list[AgentStep] = []
        context = context or {}

        # Step 1: Task Planning
        step_start = self._timer()
        planning_messages = [
            SystemMessage(content=self._build_system_prompt()),
            HumanMessage(content=(
                f"Create a detailed execution plan for the following task:\n\n"
                f"Task: {query}\n\n"
                f"Context: {context}\n\n"
                f"Requirements:\n"
                f"1. Break into numbered steps\n"
                f"2. Estimate time for each step\n"
                f"3. Identify dependencies\n"
                f"4. Flag steps needing approval\n"
                f"5. Include success criteria for each step"
            )),
        ]
        plan_response = self.llm.invoke(planning_messages)

        steps.append(AgentStep(
            step_number=1,
            action="task_planning",
            input=query[:200],
            output=str(plan_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Step 2: Simulated Execution
        step_start = self._timer()
        execution_messages = [
            SystemMessage(content=(
                "Simulate executing the plan. For each step, report:\n"
                "- Status (completed/in_progress/blocked)\n"
                "- Output or result\n"
                "- Any warnings or issues\n"
                "- Next step recommendation"
            )),
            HumanMessage(content=(
                f"Execute this plan step by step:\n\n{plan_response.content}\n\n"
                f"Simulate realistic execution results for an enterprise environment."
            )),
        ]
        execution_response = self.llm.invoke(execution_messages)

        steps.append(AgentStep(
            step_number=2,
            action="task_execution",
            input="Executing planned steps",
            output=str(execution_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Step 3: Result Validation & Report
        step_start = self._timer()
        report_messages = [
            SystemMessage(content=(
                "Generate a comprehensive execution report including:\n"
                "- Overall status\n"
                "- Steps completed vs. planned\n"
                "- Key outcomes and deliverables\n"
                "- Any issues encountered\n"
                "- Recommendations for follow-up"
            )),
            HumanMessage(content=(
                f"Original Task: {query}\n\n"
                f"Execution Plan:\n{plan_response.content}\n\n"
                f"Execution Results:\n{execution_response.content}\n\n"
                f"Generate the final report."
            )),
        ]
        report_response = self.llm.invoke(report_messages)

        steps.append(AgentStep(
            step_number=3,
            action="report_generation",
            input="Generating execution report",
            output=str(report_response.content)[:200],
            duration_ms=self._timer() - step_start,
        ))

        # Determine final status
        requires_approval = context.get("require_approval", False)
        status = AgentStatus.AWAITING_APPROVAL if requires_approval else AgentStatus.COMPLETED

        result = (
            f"## Execution Plan\n\n{plan_response.content}\n\n"
            f"## Execution Results\n\n{execution_response.content}\n\n"
            f"## Summary Report\n\n{report_response.content}"
        )

        tokens = self._extract_token_usage(report_response)
        latency = self._timer() - start_time

        return self._create_response(
            result=result,
            status=status,
            steps=steps,
            tokens=tokens,
            latency_ms=latency,
        )
