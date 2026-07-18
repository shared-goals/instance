.DEFAULT_GOAL := help

.PHONY: help acceptance test lint format check dev

PYTEST ?= uv run pytest
RUFF ?= uv run ruff
UVICORN ?= uv run uvicorn
TEST ?= tests

help:
	@printf "Shared Goals instance targets:\n"
	@printf "  make acceptance        Run HTTP acceptance tests\n"
	@printf "  make test              Run all tests, or TEST=path for one slice\n"
	@printf "  make lint              Run Ruff lint checks\n"
	@printf "  make format            Format Python code with Ruff\n"
	@printf "  make check             Run the commit-gate validation\n"
	@printf "  make dev               Start the local API server\n"

acceptance:
	@printf "Running HTTP acceptance tests...\n"
	$(PYTEST) -q tests/acceptance

test:
	@printf "Running tests: $(TEST)\n"
	$(PYTEST) -q $(TEST)

lint:
	@printf "Running Ruff lint checks...\n"
	$(RUFF) check .

format:
	@printf "Formatting Python code with Ruff...\n"
	$(RUFF) format .

check: lint
	@printf "Running commit-gate checks...\n"
	$(PYTEST) -q tests

dev:
	$(UVICORN) shared_goals_instance.app:create_app --factory --reload
