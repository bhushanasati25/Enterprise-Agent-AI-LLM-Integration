"""
LLM Evaluator — Dataset Loader

Loads benchmark datasets for LLM evaluation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Dataset directory
DATASETS_DIR = Path(__file__).parent.parent.parent / "evaluation_datasets"


# Embedded datasets (fallback if files not found)
EMBEDDED_DATASETS: dict[str, list[dict[str, Any]]] = {
    "enterprise_qa": [
        {
            "query": "What is the company's data retention policy?",
            "reference": "Customer data must be retained for 7 years per regulatory requirements. After the retention period, data must be securely deleted using approved methods.",
            "context": "Enterprise compliance",
            "category": "compliance",
        },
        {
            "query": "What are the SLA requirements for production services?",
            "reference": "Production services must maintain 99.9% uptime with a maximum response time of 200ms for P95. Incident response must begin within 15 minutes for P1 issues.",
            "context": "Operations",
            "category": "operations",
        },
        {
            "query": "How should API authentication be implemented?",
            "reference": "All APIs must use OAuth 2.0 with JWT tokens. API keys are acceptable for service-to-service communication. All tokens must expire within 60 minutes.",
            "context": "Security standards",
            "category": "security",
        },
        {
            "query": "What is the change management process for production deployments?",
            "reference": "All production changes require a Change Advisory Board approval for standard changes. Emergency changes need VP-level approval and must be documented within 24 hours.",
            "context": "DevOps processes",
            "category": "process",
        },
        {
            "query": "What encryption standards are required for data at rest?",
            "reference": "All sensitive data must be encrypted at rest using AES-256. Key management must follow NIST SP 800-57 guidelines with automated key rotation every 90 days.",
            "context": "Security",
            "category": "security",
        },
        {
            "query": "What are the performance benchmarks for the ML inference pipeline?",
            "reference": "ML inference must complete within 500ms for 95th percentile. Batch processing should handle 10,000 requests per minute. Model serving must support A/B testing.",
            "context": "ML Engineering",
            "category": "engineering",
        },
        {
            "query": "How should microservices handle inter-service communication?",
            "reference": "Synchronous calls use gRPC with circuit breakers (5s timeout, 3 retries). Async communication uses Kafka with guaranteed delivery. Service mesh (Istio) handles mTLS.",
            "context": "Architecture",
            "category": "architecture",
        },
        {
            "query": "What is the disaster recovery procedure?",
            "reference": "RPO is 1 hour, RTO is 4 hours. Multi-region failover is automated. Database backups run every 6 hours with point-in-time recovery. DR drills quarterly.",
            "context": "Business continuity",
            "category": "operations",
        },
        {
            "query": "What are the code review requirements?",
            "reference": "All changes require at least 2 approving reviews. Security-sensitive changes need a security team review. Code coverage must not drop below 80%.",
            "context": "Engineering practices",
            "category": "process",
        },
        {
            "query": "How should PII data be handled in logs?",
            "reference": "PII must never appear in logs. Use tokenization or hashing for any identifier fields. Log aggregation systems must have access controls and 30-day retention.",
            "context": "Data privacy",
            "category": "compliance",
        },
    ],
    "data_extraction": [
        {
            "query": "Acme Corporation reported Q3 2025 revenue of $12.5 million, representing 15.2% year-over-year growth. The customer base expanded to 1,250 active accounts with a churn rate of 2.1%.",
            "reference": '{"company": "Acme Corporation", "quarter": "Q3 2025", "revenue": "$12.5M", "yoy_growth": "15.2%", "customers": 1250, "churn_rate": "2.1%"}',
            "context": "Financial report extraction",
            "category": "financial",
        },
        {
            "query": "Meeting notes from March 15, 2025: Attendees - Sarah Chen (VP Engineering), James Wilson (CTO). Action items: 1) Migrate to Kubernetes by Q2, 2) Hire 3 senior engineers, 3) Complete SOC 2 audit.",
            "reference": '{"date": "2025-03-15", "attendees": [{"name": "Sarah Chen", "role": "VP Engineering"}, {"name": "James Wilson", "role": "CTO"}], "action_items": ["Migrate to Kubernetes by Q2", "Hire 3 senior engineers", "Complete SOC 2 audit"]}',
            "context": "Meeting extraction",
            "category": "meetings",
        },
        {
            "query": "Invoice #INV-2025-0847 from CloudTech Solutions, dated April 1, 2025. Total: $45,000.00. Line items: Cloud hosting ($25,000), Support tier ($15,000), Professional services ($5,000). Payment terms: Net 30.",
            "reference": '{"invoice_number": "INV-2025-0847", "vendor": "CloudTech Solutions", "date": "2025-04-01", "total": 45000.00, "line_items": [{"item": "Cloud hosting", "amount": 25000}, {"item": "Support tier", "amount": 15000}, {"item": "Professional services", "amount": 5000}], "payment_terms": "Net 30"}',
            "context": "Invoice extraction",
            "category": "financial",
        },
    ],
    "summarization": [
        {
            "query": "The quarterly board meeting covered several critical topics. First, the CFO presented financial results showing 18% revenue growth to $45M. Second, the CTO outlined the technology roadmap including migration to a microservices architecture and adoption of AI-powered automation. Third, the CHRO discussed workforce expansion plans to hire 50 engineers across three global offices. Finally, the board approved a $10M capital expenditure budget for infrastructure upgrades.",
            "reference": "Q-board meeting: 18% revenue growth to $45M. Tech roadmap includes microservices migration and AI automation. Plans to hire 50 engineers globally. $10M capex approved for infrastructure.",
            "context": "Executive summary",
            "category": "summary",
        },
    ],
}


def load_dataset(name: str) -> list[dict[str, Any]]:
    """
    Load a benchmark dataset by name.

    Tries to load from JSON files first, falls back to embedded datasets.
    """
    # Try loading from file
    file_path = DATASETS_DIR / f"{name}.json"
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)

    # Fall back to embedded datasets
    if name in EMBEDDED_DATASETS:
        return EMBEDDED_DATASETS[name]

    raise ValueError(f"Unknown dataset: {name}. Available: {list(EMBEDDED_DATASETS.keys())}")


def list_datasets() -> list[dict[str, Any]]:
    """List all available datasets with metadata."""
    datasets = []
    for name, data in EMBEDDED_DATASETS.items():
        categories = list({item.get("category", "general") for item in data})
        datasets.append({
            "name": name,
            "size": len(data),
            "categories": categories,
            "description": f"Enterprise {name.replace('_', ' ')} benchmark dataset",
        })
    return datasets
