# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Convenience targets. Each one is a thin wrapper over the commands in CLAUDE.md "The gate".

.DEFAULT_GOAL := help
.PHONY: help setup lint format type test test-all docs reuse gate

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install every package and dev tool, then the git hooks
	uv sync --all-packages --all-groups
	uv run pre-commit install

lint: ## Lint, format check and import contracts
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports

format: ## Apply ruff fixes and formatting
	uv run ruff check --fix .
	uv run ruff format .

type: ## Strict type check
	uv run mypy

test: ## Fast tests with the coverage gate (excludes slow, render, network, gpu, hardware)
	uv run pytest -q --cov --cov-fail-under=85

# pytest exits with 5 when a marker selects no tests (true until the sim lands); that is not a failure here.
test-all: test ## Fast tests plus the slow and render suites
	uv run pytest -q -m "slow" || [ $$? -eq 5 ]
	MUJOCO_GL=$${MUJOCO_GL:-egl} uv run pytest -q -m "render" || [ $$? -eq 5 ]

reuse: ## REUSE licensing check (isolated external tool, ADR-010)
	uvx --from 'reuse[charset-normalizer]==6.3.0' reuse lint

docs: ## Build the docs site strictly (available from S04)
	@if [ -f mkdocs.yml ]; then uv run mkdocs build --strict; \
	else echo "No mkdocs.yml yet: the docs site arrives in session S04."; fi

gate: lint type test ## The default local gate
