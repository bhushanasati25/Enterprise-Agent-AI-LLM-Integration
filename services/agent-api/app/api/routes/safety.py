"""
Enterprise Agent AI — Safety & Guardrails Module

Real-time prompt injection detection, PII redacting, and safety evaluation.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import validate_api_key

router = APIRouter(prefix="/safety", tags=["Safety & Guardrails"])


class SafetyAuditRequest(BaseModel):
    text: str = Field(..., description="Prompt or response text to audit")


class SafetyAuditResponse(BaseModel):
    text: str
    safety_score: float
    is_safe: bool
    risk_level: str
    detected_risks: list[str]
    pii_redacted_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/audit",
    response_model=SafetyAuditResponse,
    summary="Audit prompt or response for safety and PII",
)
async def audit_safety(
    request: SafetyAuditRequest,
    _api_key: str = Depends(validate_api_key),
) -> SafetyAuditResponse:
    text = request.text
    detected_risks = []
    penalties = 0.0

    # 1. PII Detection & Redaction
    pii_patterns = {
        "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    }

    redacted_text = text
    for pii_type, pattern in pii_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            detected_risks.append(f"PII Detected: {pii_type} ({len(matches)} occurrences)")
            penalties += 0.35 * len(matches)
            redacted_text = re.sub(pattern, f"[REDACTED_{pii_type}]", redacted_text)

    # 2. Prompt Injection & Jailbreak Attacks
    adversarial_patterns = [
        (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", "Instruction Bypass / Prompt Injection"),
        (r"disregard\s+(the\s+)?system\s+prompt", "System Prompt Override"),
        (r"you\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode)", "Persona Jailbreak (DAN)"),
        (r"print\s+(the\s+)?(system\s+prompt|hidden\s+rules)", "System Prompt Leakage Attempt"),
        (r"reveal\s+(api\s+keys?|passwords?|credentials?)", "Credential Harvesting Attempt"),
    ]

    for pattern, description in adversarial_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            detected_risks.append(f"Adversarial Attack: {description}")
            penalties += 0.50

    # 3. Calculate Safety Score
    score = max(0.0, min(1.0, 1.0 - penalties))
    is_safe = score >= 0.70

    risk_level = "LOW"
    if score < 0.40:
        risk_level = "CRITICAL"
    elif score < 0.70:
        risk_level = "HIGH"
    elif score < 0.90:
        risk_level = "MEDIUM"

    return SafetyAuditResponse(
        text=text,
        safety_score=round(score, 2),
        is_safe=is_safe,
        risk_level=risk_level,
        detected_risks=detected_risks,
        pii_redacted_text=redacted_text,
        metadata={
            "rules_evaluated": len(pii_patterns) + len(adversarial_patterns),
            "guardrail_status": "INTERCEPTED" if not is_safe else "PASSED",
        },
    )
