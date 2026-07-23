SHELL := /bin/sh

UV := uv
PYTHON_VERSION := 3.12
OFFLINE_UV := $(UV) --offline --no-python-downloads
export UV_CACHE_DIR := $(CURDIR)/.uv-cache
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv

.PHONY: architecture bootstrap build check contract doctor format format-check lint offline-ready openapi package-check test typecheck

offline-ready:
	@test -x "$(UV_PROJECT_ENVIRONMENT)/bin/python" -a -d "$(UV_CACHE_DIR)" || { \
		echo "offline package state is not bootstrapped; run 'make -C apps/api bootstrap' explicitly" >&2; \
		exit 2; \
	}

doctor: offline-ready
	@$(OFFLINE_UV) --version
	@$(OFFLINE_UV) python find $(PYTHON_VERSION)
	@$(OFFLINE_UV) run --frozen python --version

bootstrap:
	$(UV) sync --python $(PYTHON_VERSION) --frozen --all-groups

format: offline-ready
	$(OFFLINE_UV) run --frozen ruff format .
	$(OFFLINE_UV) run --frozen ruff check --fix .

format-check: offline-ready
	$(OFFLINE_UV) run --frozen ruff format --check .

lint: offline-ready
	$(OFFLINE_UV) run --frozen ruff check .

typecheck: offline-ready
	$(OFFLINE_UV) run --frozen mypy src tests scripts

architecture: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket tests/unit_tests/test_architecture.py

test: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket

contract: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket tests/contract_tests

build: offline-ready
	$(OFFLINE_UV) build --no-sources

openapi: offline-ready
	$(OFFLINE_UV) run --frozen python scripts/export_openapi.py --write

package-check: offline-ready build
	$(OFFLINE_UV) run --frozen python scripts/check_package.py

check: format-check lint typecheck test contract build
