.PHONY: help install lint format test up down logs clean check

PYTHON ?= python3
UV ?= uv

help:
	@echo "Convo Glasses - Development Makefile"
	@echo "------------------------------------"
	@echo "install      Install local Python dependencies for API and Worker"
	@echo "lint         Run code linters (ruff, mypy)"
	@echo "format       Run code formatters (ruff format)"
	@echo "test         Run unit and integration tests (pytest)"
	@echo "check        Run format check, lint, and tests"
	@echo "up           Start services with Docker Compose"
	@echo "down         Stop services with Docker Compose"
	@echo "logs         Follow Docker Compose logs"
	@echo "clean        Clean build caches, logs, and temp files"

install:
	@if command -v $(UV) >/dev/null 2>&1; then \
		echo "Installing with uv..."; \
		$(UV) pip install -e services/api -e services/worker -r services/api/requirements-dev.txt -r services/worker/requirements-dev.txt; \
	else \
		echo "Installing with pip..."; \
		$(PYTHON) -m pip install -e services/api -e services/worker -r services/api/requirements-dev.txt -r services/worker/requirements-dev.txt; \
	fi

lint:
	@echo "=== Linting services/api ==="
	ruff check services/api
	mypy services/api/src
	@echo "=== Linting services/worker ==="
	ruff check services/worker
	mypy services/worker/src

format:
	ruff format services/api services/worker
	ruff check --fix services/api services/worker

test:
	@echo "=== Testing services/api ==="
	pytest services/api
	@echo "=== Testing services/worker ==="
	pytest services/worker

check: lint test

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
