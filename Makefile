# Makefile for healthcare-graph-agent
# Common tasks for development, testing, and deployment

.PHONY: help install install-dev test lint format typecheck clean run-agent deploy-azure load-data validate-config list-tools list-domains test-domain test-core

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code with black and isort"
	@echo "  make typecheck     - Run type checking with mypy"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make run-agent     - Run the agent (uses AGENT_PROVIDER from .env)"
	@echo "  make azure-prepare - Copy src/ and config/ to azure-functions/"
	@echo "  make azure-local   - Run Azure Functions locally"
	@echo "  make deploy-azure  - Deploy Azure Functions (quick)"
	@echo "  make deploy-azure-full - Deploy with full setup script"
	@echo "  make load-data     - Load sample data into Cosmos DB"
	@echo ""
	@echo "Modular architecture commands:"
	@echo "  make validate-config - Validate domain configuration"
	@echo "  make list-tools      - List all available tools"
	@echo "  make list-domains    - List enabled domains"
	@echo "  make test-core       - Run core tests"
	@echo "  make test-domain DOMAIN=<name> - Run tests for a specific domain"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Testing
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Code quality
lint:
	black --check src/ cli/ scripts/
	isort --check-only src/ cli/ scripts/
	flake8 src/ cli/ scripts/ --max-line-length=100

format:
	black src/ cli/ scripts/
	isort src/ cli/ scripts/

typecheck:
	mypy src/ cli/

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

# Running
run-agent:
	python run_agent.py

run-agent-azure:
	python run_agent.py --azure

run-agent-gradient:
	python run_agent.py --gradient

test-db:
	python run_agent.py --test

# Azure Functions
azure-local: azure-prepare
	cd azure-functions && func start

azure-prepare:
	@echo "Copying shared directories to azure-functions/..."
	rm -rf azure-functions/src azure-functions/config
	cp -r src azure-functions/src
	cp -r config azure-functions/config
	@echo "Done. Ready for local development or deployment."

deploy-azure: azure-prepare
	cd azure-functions && func azure functionapp publish referral-network-api --python

deploy-azure-full:
	cd azure-functions && ./deploy-azure.sh

# Data management
load-data:
	python scripts/load_sample_data.py

explore-data:
	python scripts/explore_graph.py

export-powerbi:
	python scripts/export_for_powerbi.py

# Modular architecture
validate-config:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); r.load_domains(); print('Config valid, loaded', len(r.list_tools()), 'tools')"

list-tools:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); r.load_domains(); print('\\n'.join(r.list_tools()))"

list-domains:
	python -c "from src.core.tool_registry import ToolRegistry; r = ToolRegistry(); print('\\n'.join(r.get_enabled_domains()))"

# Test by domain
test-domain:
	pytest tests/domains/$(DOMAIN)/ -v

test-core:
	pytest tests/core/ -v
