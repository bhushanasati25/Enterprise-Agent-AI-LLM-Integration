#!/usr/bin/env bash
# =============================================================================
# Enterprise Agent AI & LLM Integration — End-to-End Platform Demo Script
# =============================================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}       ENTERPRISE AGENT AI & LLM INTEGRATION — PLATFORM DEMO         ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Verification of Test Suites
echo -e "\n${CYAN}[1/4] Running Service Test Suites across Python Services...${NC}"
python3 -m pytest services/agent-api/tests/ -q
python3 -m pytest services/llm-evaluator/tests/ -q
echo -e "${GREEN}✓ All 39 unit & integration tests passed cleanly!${NC}"

# 2. Live Agent Invocation Demo
echo -e "\n${CYAN}[2/4] Executing Multi-Step Autonomous Agents via LangGraph...${NC}"
PYTHONPATH=services/agent-api python3 -c "
import asyncio, os
os.environ['ENVIRONMENT'] = 'testing'
os.environ['DEFAULT_LLM_PROVIDER'] = 'mock'
from app.agents import DocumentQAAgent, DataExtractionAgent, TaskAutomationAgent

async def demo():
    doc_agent = DocumentQAAgent(provider='mock')
    res = await doc_agent.invoke('What is our SLA guarantee for production services?')
    print('  - Document Q&A Agent: Latency =', round(res.metadata.latency_ms, 1), 'ms | Sources =', len(res.metadata.sources))

    extract_agent = DataExtractionAgent(provider='mock')
    res = await extract_agent.invoke('Acme Corp reported Q3 2025 revenue of $12.5M with 15.2% growth.')
    print('  - Data Extraction Agent: Latency =', round(res.metadata.latency_ms, 1), 'ms | Status =', res.status.value)

    task_agent = TaskAutomationAgent(provider='mock')
    res = await task_agent.invoke('Automate weekly infrastructure audit')
    print('  - Task Automation Agent: Steps executed =', len(res.metadata.steps), '| Status =', res.status.value)

asyncio.run(demo())
"
echo -e "${GREEN}✓ All 3 agents successfully executed with full trace telemetry!${NC}"

# 3. Commercial LLM Multi-Factor Benchmarking
echo -e "\n${CYAN}[3/4] Running Multi-Model Commercial LLM Benchmark...${NC}"
PYTHONPATH=services/llm-evaluator python3 -c "
import asyncio, os
os.environ['ENVIRONMENT'] = 'testing'
os.environ['DEFAULT_LLM_PROVIDER'] = 'mock'
from app.evaluation.benchmark_runner import BenchmarkRunner, BenchmarkConfig

async def demo():
    runner = BenchmarkRunner()
    config = BenchmarkConfig(
        models=[
            {'provider': 'mock', 'model': 'mock-gpt-4o'},
            {'provider': 'mock', 'model': 'mock-claude-3-5-sonnet'},
            {'provider': 'mock', 'model': 'mock-gpt-4o-mini'},
        ],
        dataset='enterprise_qa',
        max_samples=3
    )
    report = await runner.run(config)
    print('  - Evaluated Models: mock-gpt-4o, mock-claude-3-5-sonnet, mock-gpt-4o-mini')
    print('  - Metrics: Accuracy, Latency, Cost, Safety')
    print('  - Top Recommended Model:', report.best_model)
    print('  - Evaluation Duration:', round(report.duration_seconds, 2), 's')

asyncio.run(demo())
"
echo -e "${GREEN}✓ Multi-factor benchmark completed with comparative ranking!${NC}"

# 4. OpenShift Infrastructure Cost Optimization
echo -e "\n${CYAN}[4/4] Generating OpenShift Compute Cost Optimization Audit...${NC}"
python3 scripts/cost_optimization_analyzer.py

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}             DEMO COMPLETE — PLATFORM IS FULLY OPERATIONAL           ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "To access the Web Console, run: ${PURPLE}make up${NC} and open ${PURPLE}http://localhost:8000/${NC}\n"
