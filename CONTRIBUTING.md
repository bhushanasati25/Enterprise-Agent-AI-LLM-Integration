# Contributing to Enterprise Agent AI & LLM Integration

Thank you for your interest in contributing to the **Enterprise Agent AI & LLM Integration** platform! We welcome contributions from the community and internal engineering teams.

---

## 🛠️ Development Setup

1. **Prerequisites**:
   - Python 3.12+
   - Docker & Docker Compose
   - `uv` (recommended) or `pip`
   - (Optional) .NET 8 SDK & `kubectl`

2. **Clone and Configure**:
   ```bash
   git clone https://github.com/bhushanasati25/Enterprise-Agent-AI-LLM-Integration.git
   cd Enterprise-Agent-AI-LLM-Integration
   cp .env.example .env
   ```

3. **Install Dependencies & Run Tests**:
   ```bash
   make test
   ```

4. **Verify Code Quality**:
   ```bash
   make lint
   ```

---

## 📋 Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Ensure all 41 test suites pass:
   ```bash
   make test
   ```
3. Ensure the linter reports zero errors:
   ```bash
   make lint
   ```
4. If adding new agent workflows, custom evaluation metrics, or API routes, include corresponding unit tests under `services/<service-name>/tests/`.
5. Open a Pull Request referencing relevant issues.

---

## 🧪 Testing Guidelines

- **Agent AI Service**: Place tests under `services/agent-api/tests/`. Ensure mock LLM providers are utilized so tests do not require live API keys.
- **LLM Evaluator**: Place metric tests under `services/llm-evaluator/tests/test_metrics.py` and benchmark tests under `test_benchmark_runner.py`.
- **Infrastructure Manifests**: Validate Kustomize overlays using `kubectl kustomize k8s/overlays/dev` and `k8s/overlays/prod`.
