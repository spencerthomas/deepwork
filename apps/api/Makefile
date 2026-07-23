SHELL := /bin/sh

UV := uv
PYTHON_VERSION := 3.12
export UV_CACHE_DIR := $(CURDIR)/.uv-cache
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv

.PHONY: bootstrap build check contract doctor format format-check lint package-check test typecheck

doctor:
	@$(UV) --version
	@$(UV) python find $(PYTHON_VERSION)
	@$(UV) run --frozen python --version

bootstrap:
	$(UV) sync --python $(PYTHON_VERSION) --frozen --all-groups

format:
	$(UV) run --frozen ruff format .
	$(UV) run --frozen ruff check --fix .

format-check:
	$(UV) run --frozen ruff format --check .

lint:
	$(UV) run --frozen ruff check .

typecheck:
	$(UV) run --frozen mypy src tests scripts

test:
	$(UV) run --frozen pytest --disable-socket --allow-unix-socket

contract:
	$(UV) run --frozen pytest --disable-socket --allow-unix-socket tests/contract_tests

build:
	$(UV) build --no-sources

package-check: build
	$(UV) run --frozen python scripts/check_package.py

check: format-check lint typecheck test contract build
