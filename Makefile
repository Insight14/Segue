.PHONY: help install lint format test up down logs clean check openapi migrate

VENV_DIR ?= .venv
ifeq ($(wildcard $(VENV_DIR)/bin/python),)
PYTHON ?= python3
PYTEST ?= pytest
RUFF ?= ruff
MYPY ?= mypy
ALEMBIC ?= alembic
else
PYTHON ?= $(VENV_DIR)/bin/python
PYTEST ?= $(VENV_DIR)/bin/pytest
RUFF ?= $(VENV_DIR)/bin/ruff
MYPY ?= $(VENV_DIR)/bin/mypy
ALEMBIC ?= $(VENV_DIR)/bin/alembic
endif
UV ?= uv
export COVERAGE_CORE ?= sysmon

help:
	@echo "Convo Glasses - Development Makefile"
	@echo "------------------------------------"
	@echo "install      Install local Python dependencies for API and Worker"
	@echo "lint         Run code linters (ruff, mypy)"
	@echo "format       Run code formatters (ruff format)"
	@echo "test         Run unit and integration tests (pytest)"
	@echo "openapi      Export OpenAPI schema and TypeScript definitions"
	@echo "migrate      Run Alembic database migrations"
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
	$(RUFF) check services/api
	$(MYPY) services/api/src
	@echo "=== Linting services/worker ==="
	$(RUFF) check services/worker
	$(MYPY) services/worker/src

format:
	$(RUFF) format services/api services/worker
	$(RUFF) check --fix services/api services/worker

test:
	@echo "=== Testing services/api ==="
	$(PYTEST) services/api
	@echo "=== Testing services/worker ==="
	$(PYTEST) services/worker

openapi:
	$(PYTHON) services/api/scripts/export_openapi.py

migrate:
	cd services/api && $(ALEMBIC) upgrade head

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

