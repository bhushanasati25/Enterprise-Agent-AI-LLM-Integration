# Enterprise Agent AI & LLM Integration

Production-grade enterprise platform for deploying AI agents, evaluating LLMs, and automating business processes — built with Python, C#, Kubernetes, and GitHub Actions CI/CD.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions CI/CD                       │
│  (lint → test → build → push images → deploy to K8s)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Kubernetes / OpenShift Cluster                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  C# Gateway  │→ │  Agent API   │→ │  LLM Evaluator     │    │
│  │  (ASP.NET)   │  │  (FastAPI)   │  │  (FastAPI)         │    │
│  │  Port 8080   │  │  Port 8000   │  │  Port 8001         │    │
│  └──────────────┘  └──────┬───────┘  └────────────────────┘    │
│                           │                                     │
│                    ┌──────▼───────┐                              │
│                    │  PostgreSQL  │                              │
│                    │  + pgvector  │                              │
│                    └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Tech Stack | Port | Description |
|---------|-----------|------|-------------|
| **API Gateway** | C# / ASP.NET Core 8 | 8080 | Reverse proxy with JWT auth, rate limiting, request logging |
| **Agent API** | Python / FastAPI / LangGraph | 8000 | Enterprise AI agents: document Q&A, data extraction, task automation |
| **LLM Evaluator** | Python / FastAPI | 8001 | Custom LLM benchmarking with accuracy, latency, cost & safety metrics |
| **PostgreSQL** | PostgreSQL 16 + pgvector | 5432 | Vector store for RAG, conversation history, audit logs |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- .NET 8 SDK
- (Optional) kubectl + a Kubernetes cluster

### Local Development

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys (optional — mock providers work by default)

# 2. Start all services
docker-compose up --build

# 3. Verify
curl http://localhost:8080/health    # Gateway
curl http://localhost:8000/health    # Agent API
curl http://localhost:8001/health    # LLM Evaluator
```

### Using Make

```bash
make build          # Build all Docker images
make up             # Start all services
make test           # Run all tests
make lint           # Lint all code
make down           # Stop all services
```

### Run Tests

```bash
# Python services
cd services/agent-api && pip install -r requirements.txt && pytest tests/ -v
cd services/llm-evaluator && pip install -r requirements.txt && pytest tests/ -v

# C# gateway
cd services/gateway && dotnet test
```

## API Examples

### Invoke an Agent
```bash
curl -X POST http://localhost:8080/api/agents/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "agent_type": "document_qa",
    "query": "What is our refund policy?",
    "context": {"department": "customer_support"}
  }'
```

### Run LLM Benchmark
```bash
curl -X POST http://localhost:8080/api/benchmarks/run \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["gpt-4o", "claude-3-sonnet", "gemini-pro"],
    "dataset": "enterprise_qa",
    "metrics": ["accuracy", "latency", "cost"]
  }'
```

## Kubernetes Deployment

```bash
# Dev environment
kubectl apply -k k8s/overlays/dev/

# Production (with resource quotas & network policies)
kubectl apply -k k8s/overlays/prod/
```

## CI/CD Pipelines

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `ci.yml` | Push/PR to main | Lint, test, build images, deploy |
| `ml-pipeline.yml` | Weekly / manual | Run LLM benchmarks, update model configs |
| `security-scan.yml` | Push/PR | Trivy scan, dependency audit, SAST |

## Project Structure

```
├── .github/workflows/          # CI/CD pipelines
├── services/
│   ├── agent-api/              # Python FastAPI + LangGraph agents
│   ├── llm-evaluator/          # Python LLM benchmarking service
│   └── gateway/                # C# ASP.NET Core API gateway
├── k8s/
│   ├── base/                   # Base Kubernetes manifests
│   └── overlays/               # Kustomize overlays (dev/prod)
├── monitoring/
│   ├── prometheus/             # Prometheus scrape configs
│   └── grafana/                # Grafana dashboards
├── docker-compose.yml          # Local development orchestration
├── Makefile                    # Common commands
└── .env.example                # Environment variable template
```

## License

Proprietary — Enterprise Internal Use Only
