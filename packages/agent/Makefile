PYTHON ?= python3.12
UV ?= uv
PACKAGE_ROOT := $(CURDIR)
UV_CACHE_DIR ?= $(PACKAGE_ROOT)/.uv-cache
UV_PROJECT_ENVIRONMENT ?= $(PACKAGE_ROOT)/.venv
UV_ENV := UV_CACHE_DIR=$(UV_CACHE_DIR) UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT)
UV_RUN := $(UV_ENV) $(UV) run --project $(PACKAGE_ROOT) --frozen

.PHONY: doctor bootstrap lock-check format-check lint typecheck test build package-check check

doctor:
	@command -v $(PYTHON) >/dev/null || { echo "missing Python 3.12: $(PYTHON)"; exit 1; }
	@command -v $(UV) >/dev/null || { echo "missing uv"; exit 1; }
	@$(PYTHON) scripts/doctor.py
	@$(UV) --version

bootstrap:
	$(UV_ENV) $(UV) sync --project $(PACKAGE_ROOT) --frozen --group dev

lock-check:
	$(UV_ENV) $(UV) lock --project $(PACKAGE_ROOT) --check

format-check:
	$(UV_RUN) ruff format --check src tests scripts

lint:
	$(UV_RUN) ruff check src tests scripts

typecheck:
	$(UV_RUN) ty check src scripts

test:
	$(UV_RUN) pytest --disable-socket

build:
	$(UV_RUN) hatchling build --target sdist --target wheel --directory $(PACKAGE_ROOT)/dist

package-check: build
	$(PYTHON) scripts/verify_wheel.py

check: lock-check format-check lint typecheck test package-check
