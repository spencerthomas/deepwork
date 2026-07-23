PYTHON ?= python3
UV ?= uv
PACKAGE_ROOT := $(CURDIR)
UV_CACHE_DIR ?= $(PACKAGE_ROOT)/.uv-cache
UV_PROJECT_ENVIRONMENT ?= $(PACKAGE_ROOT)/.venv
UV_ENV := UV_CACHE_DIR=$(UV_CACHE_DIR) UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT)
UV_RUN := $(UV_ENV) $(UV) run --project $(PACKAGE_ROOT) --frozen

.PHONY: architecture doctor bootstrap lock-check format format-check lint typecheck test integration-test evaluation benchmark coverage build package-check update-evidence check

doctor:
	@command -v $(PYTHON) >/dev/null || { echo "missing supported Python: $(PYTHON)"; exit 1; }
	@command -v $(UV) >/dev/null || { echo "missing uv"; exit 1; }
	@$(PYTHON) scripts/doctor.py
	@$(UV) --version

bootstrap:
	$(UV_ENV) $(UV) sync --project $(PACKAGE_ROOT) --frozen --group dev

lock-check:
	$(UV_ENV) $(UV) lock --project $(PACKAGE_ROOT) --check

format-check:
	$(UV_RUN) ruff format --check src tests scripts

format:
	$(UV_RUN) ruff format src tests scripts
	$(UV_RUN) ruff check --fix src tests scripts

lint:
	$(UV_RUN) ruff check src tests scripts

typecheck:
	$(UV_RUN) ty check src scripts

test:
	$(UV_RUN) pytest --disable-socket tests/unit_tests

integration-test:
	$(UV_RUN) pytest --disable-socket tests/integration_tests

evaluation:
	$(UV_RUN) pytest --disable-socket tests/evaluation

benchmark:
	$(UV_RUN) pytest --disable-socket tests/benchmarks

coverage:
	$(UV_RUN) pytest --disable-socket --cov=deepwork_agent --cov-report=term-missing --cov-fail-under=85 tests/unit_tests tests/integration_tests

architecture:
	$(UV_RUN) pytest --disable-socket tests/unit_tests/test_no_forbidden_imports.py tests/unit_tests/test_no_network.py

build:
	$(UV_RUN) hatchling build --target sdist --target wheel --directory $(PACKAGE_ROOT)/dist

package-check: build
	$(UV_RUN) python scripts/verify_wheel.py

update-evidence: build
	$(UV_RUN) python scripts/verify_wheel.py --update-evidence

check: lock-check format-check lint typecheck architecture coverage evaluation package-check
