.PHONY: build up down test lint clean logs

# =============================================================================
# Enterprise Agent AI & LLM Integration — Makefile
# =============================================================================

# Build all Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "  Gateway:     http://localhost:8080"
	@echo "  Agent API:   http://localhost:8000"
	@echo "  Evaluator:   http://localhost:8001"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3000"

# Stop all services
down:
	docker-compose down

# Run all tests
test: test-agent-api test-evaluator

test-agent-api:
	cd services/agent-api && pytest tests/ -v --tb=short

test-evaluator:
	cd services/llm-evaluator && pytest tests/ -v --tb=short

test-gateway:
	cd services/gateway && dotnet test --verbosity normal

# Cost optimization analysis
cost-analysis:
	python3 scripts/cost_optimization_analyzer.py

# Lint all code
lint: lint-python

lint-python:
	ruff check services/agent-api/ services/llm-evaluator/ scripts/ --fix

# View logs
logs:
	docker-compose logs -f

logs-agent:
	docker-compose logs -f agent-api

logs-evaluator:
	docker-compose logs -f llm-evaluator

logs-gateway:
	docker-compose logs -f gateway

# Clean up
clean:
	docker-compose down -v --rmi local
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# Health check
health:
	@echo "Checking service health..."
	@curl -sf http://localhost:8080/health && echo " ✅ Gateway OK" || echo " ❌ Gateway DOWN"
	@curl -sf http://localhost:8000/health && echo " ✅ Agent API OK" || echo " ❌ Agent API DOWN"
	@curl -sf http://localhost:8001/health && echo " ✅ Evaluator OK" || echo " ❌ Evaluator DOWN"

# Kubernetes deployments
k8s-dev:
	kubectl apply -k k8s/overlays/dev/

k8s-prod:
	kubectl apply -k k8s/overlays/prod/

k8s-dry-run:
	kubectl apply --dry-run=client -k k8s/overlays/dev/
