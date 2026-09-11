# Enterprise Agent AI & LLM Integration

Production-grade enterprise platform for deploying autonomous AI agents, benchmarking commercial LLMs, and automating business processes — built with Python, C#, Kubernetes, OpenShift, and GitHub Actions CI/CD.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions CI/CD                               │
│        (lint → 39 tests → build images → security scan → deploy to K8s)         │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                     Kubernetes / OpenShift Enterprise Cluster                   │
│                                                                                 │
│  ┌────────────────────┐   ┌────────────────────────┐   ┌─────────────────────┐  │
│  │   C# API Gateway   │──►│   Agent AI Service     │──►│    LLM Evaluator    │  │
│  │    (ASP.NET /      │   │    (FastAPI /          │   │  (Custom Multi-     │  │
│  │     YARP Proxy)    │   │     LangGraph)         │   │   Factor Metrics)   │  │
│  │     Port 8080      │   │     Port 8000          │   │     Port 8001       │  │
│  └────────────────────┘   └───────────┬────────────┘   └─────────────────────┘  │
│                                       │                                         │
│                                ┌──────▼───────┐                                 │
│                                │  PostgreSQL  │                                 │
│                                │  + pgvector  │                                 │
│                                └──────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Resume Alignment & Key Metrics

- **Process Automation (+30%)**: Deployed 3 stateful LangGraph agents (`DocumentQAAgent`, `DataExtractionAgent`, `TaskAutomationAgent`) on FastAPI with human-in-the-loop approvals, vector retrieval, and token usage accounting.
- **Response Accuracy (+25%)**: Custom evaluation framework with 4 metrics (`AccuracyMetric`, `LatencyMetric`, `CostMetric`, `SafetyMetric`) comparing models like GPT-4o, Claude 3.5 Sonnet, and Gemini Pro.
- **Compute Cost Reduction (20% - 73%)**: Kubernetes & OpenShift platform optimization leveraging Horizontal Pod Autoscalers (HPA), Spot/Preemptible node routing, and request right-sizing modeled in `scripts/cost_optimization_analyzer.py` ($3,810/yr cluster savings).
- **Model Deployment Time (-40%)**: Automated GitHub Actions CI/CD workflows for automated testing, model benchmarking evaluation gates, and security scanning.

---

## Services & Ports

| Service | Tech Stack | Port | Description |
|---|---|---|---|
| **Web Console UI** | HTML5 / Vanilla CSS / JS | 8000 | Interactive dark-mode dashboard with trace visualization |
| **API Gateway** | C# / ASP.NET Core 8 / YARP | 8080 | Reverse proxy with JWT auth, token-bucket rate limiting |
| **Agent AI Service** | Python 3.12 / FastAPI / LangGraph | 8000 | Autonomous multi-step agents & pgvector RAG pipeline |
| **LLM Evaluator** | Python 3.12 / FastAPI | 8001 | Multi-model benchmarking runner & executive reporting |
| **PostgreSQL** | PostgreSQL 16 + pgvector | 5432 | Vector database for document embeddings & state store |
| **Prometheus** | Prometheus v2.54 | 9090 | Metrics collection & scrape configs |
| **Grafana** | Grafana 11.2 | 3000 | Pre-provisioned agent performance & infra dashboards |

---

## Quick Start

### 1. One-Click Automated Demo

Run the end-to-end interactive demo script (executes all 39 tests, invokes all 3 agents, runs a multi-model benchmark, and outputs compute cost savings):

```bash
./scripts/run_demo.sh
```

### 2. Local Containerized Stack

```bash
# 1. Copy environment variables (defaults to mock LLM, no API keys required)
cp .env.example .env

# 2. Start all services locally
make up

# 3. Open the Interactive Web Console
open http://localhost:8000/
```

---

## Developer Commands

```bash
make test             # Run all 39 unit & integration tests
make lint             # Run Ruff linter with zero errors
make cost-analysis    # Run the OpenShift compute cost optimization report
make build            # Build Docker container images
make up               # Start full Docker Compose stack
make down             # Stop and clean up containers
make health           # Check health endpoints across services
```

---

## Infrastructure & OpenShift Deployments

### Kubernetes (Kustomize)
```bash
# Dev environment overlay
kubectl apply -k k8s/overlays/dev/

# Production environment overlay (HA replicas, NetworkPolicies, Quotas)
kubectl apply -k k8s/overlays/prod/
```

### OpenShift
```bash
# Apply OpenShift Edge TLS Routes
oc apply -f k8s/openshift/routes.yaml

# Bind restricted-v2 SecurityContextConstraints
oc apply -f k8s/openshift/scc-binding.yaml
```

### Helm Chart
```bash
# Install or upgrade using Helm
helm upgrade --install enterprise-ai ./helm/enterprise-agent-ai
```

---

## Repository Layout

```
├── .github/workflows/          # CI/CD pipelines (CI, ML evaluation, security)
├── helm/enterprise-agent-ai/   # Production Helm Chart
├── k8s/
│   ├── base/                   # Base Kubernetes manifests & NetworkPolicies
│   ├── overlays/               # Kustomize dev & prod overlays
│   └── openshift/              # OpenShift Routes & SCC restricted-v2 bindings
├── monitoring/
│   ├── prometheus/             # Prometheus configuration
│   └── grafana/                # Agent performance & infra dashboards
├── scripts/
│   ├── cost_optimization_analyzer.py  # OpenShift compute cost model
│   └── run_demo.sh             # Turnkey end-to-end interactive demo
├── services/
│   ├── agent-api/              # FastAPI + LangGraph Agent Microservice & Web Console
│   ├── llm-evaluator/          # Commercial LLM Benchmarking & Evaluation Service
│   └── gateway/                # C# / ASP.NET Core 8 YARP Gateway
├── docker-compose.yml          # Multi-service local composition
├── Makefile                    # Developer automation targets
└── pyproject.toml              # Unified Python tooling configuration
```

---

## License

Proprietary — Enterprise Internal Use Only
