# Makefile for referral-network-demo
# Common tasks for development, testing, and deployment

.PHONY: help install install-dev test lint format typecheck clean run-agent deploy-azure load-data

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
	@echo "  make deploy-azure  - Deploy Azure Functions"
	@echo "  make load-data     - Load sample data into Cosmos DB"

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
azure-local:
	cd azure-functions && func start

deploy-azure:
	cd azure-functions && func azure functionapp publish referral-network-api --python

# Data management
load-data:
	python scripts/load_sample_data.py

explore-data:
	python scripts/explore_graph.py

export-powerbi:
	python scripts/export_for_powerbi.py
