SHELL := /bin/sh

UV := uv
PYTHON_VERSION := 3.12
OFFLINE_UV := $(UV) --offline --no-python-downloads
export UV_CACHE_DIR := $(CURDIR)/.uv-cache
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv
LOCAL_BACKUP_TESTS := tests/unit_tests/test_sqlite_backup.py tests/contract_tests/test_sqlite_backup_restore.py

.PHONY: bootstrap build check contract doctor format format-check lint offline-ready openapi package-check test test-local-backup test-local-recovery test-postgres typecheck

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

test: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket

test-local-backup: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket $(LOCAL_BACKUP_TESTS)

test-local-recovery: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket \
		$(LOCAL_BACKUP_TESTS) \
		tests/unit_tests/test_local_runner.py::test_expired_source_lease_is_taken_over_after_owner_process_is_killed

test-postgres: offline-ready
	@test -n "$(DEEPWORK_TEST_DATABASE_URL)" || { \
		echo "DEEPWORK_TEST_DATABASE_URL must identify a disposable local PostgreSQL database" >&2; \
		exit 2; \
	}
	@DEEPWORK_TEST_DATABASE_URL="$(DEEPWORK_TEST_DATABASE_URL)" \
		$(OFFLINE_UV) run --frozen python -m deepwork_api.bootstrap.test_database_guard
	@DEEPWORK_DATABASE_URL="$(DEEPWORK_TEST_DATABASE_URL)" \
		$(OFFLINE_UV) run --frozen deepwork-migrate upgrade
	@DEEPWORK_DATABASE_URL="$(DEEPWORK_TEST_DATABASE_URL)" \
		$(OFFLINE_UV) run --frozen alembic -c alembic.ini check
	@DEEPWORK_TEST_DATABASE_URL="$(DEEPWORK_TEST_DATABASE_URL)" \
		$(OFFLINE_UV) run --frozen pytest --disable-socket \
		--allow-hosts=127.0.0.1 tests/integration_tests

contract: offline-ready
	$(OFFLINE_UV) run --frozen pytest --disable-socket --allow-unix-socket tests/contract_tests

build: offline-ready
	$(OFFLINE_UV) build --no-sources

openapi: offline-ready
	$(OFFLINE_UV) run --frozen python scripts/export_openapi.py --write

package-check: offline-ready build
	$(OFFLINE_UV) run --frozen python scripts/check_package.py

check: format-check lint typecheck test contract build
