SHELL := /bin/sh

PNPM ?= pnpm
PYTHON ?= python3
UV ?= uv

.PHONY: help doctor bootstrap dev-demo format format-check lint typecheck test build \
	check check-ts check-python check-architecture check-docs contract package-check ci \
	test-unit test-contract test-e2e-demo

help:
	@echo "Deep Work command contract:"
	@echo "  make doctor             Report all workspace toolchain prerequisites"
	@echo "  make bootstrap          Install locked API, agent, and TypeScript dependencies"
	@echo "  make dev-demo           Start the credential-free local product (./dev)"
	@echo "  make check              Run every TypeScript/Python/architecture/contract/docs gate"
	@echo "  make package-check      Verify clean consumers for every publishable package"
	@echo "  make ci                 Run the complete local CI-equivalent gate"

doctor:
	@command -v $(PNPM) >/dev/null || { echo "missing pnpm; install the packageManager version from package.json" >&2; exit 1; }
	@command -v $(PYTHON) >/dev/null || { echo "missing Python; apps/api requires Python 3.12" >&2; exit 1; }
	@command -v $(UV) >/dev/null || { echo "missing uv; install it from https://docs.astral.sh/uv/" >&2; exit 1; }
	@$(PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else "Python 3.12 or newer is required for repository tooling")'
	@$(PNPM) --version
	@$(UV) --version
	@$(MAKE) -C apps/api doctor
	@$(MAKE) -C packages/agent doctor

bootstrap:
	$(PNPM) install --frozen-lockfile
	$(MAKE) -C apps/api bootstrap
	$(MAKE) -C packages/agent bootstrap

dev-demo:
	./dev

format:
	$(PNPM) run format:ts
	$(MAKE) -C apps/api format
	$(MAKE) -C packages/agent format

format-check:
	$(PNPM) run format-check:ts
	$(MAKE) -C apps/api format-check
	$(MAKE) -C packages/agent format-check

lint:
	$(PNPM) run lint:ts
	$(MAKE) -C apps/api lint
	$(MAKE) -C packages/agent lint

typecheck:
	$(PNPM) run typecheck:ts
	$(MAKE) -C apps/api typecheck
	$(MAKE) -C packages/agent typecheck

test:
	$(PNPM) run test:ts
	$(MAKE) -C apps/api test
	$(MAKE) -C packages/agent test

build:
	$(PNPM) run build:ts
	$(MAKE) -C apps/api build
	$(MAKE) -C packages/agent build

check-ts:
	$(PNPM) run check:ts

check-python:
	$(MAKE) -C apps/api check
	$(MAKE) -C packages/agent check

check-architecture:
	$(PNPM) run check-architecture:ts
	$(MAKE) -C apps/api architecture
	$(MAKE) -C packages/agent architecture

check-docs:
	$(PYTHON) tools/docs/generate.py --check
	$(PYTHON) tools/docs/check.py

contract:
	$(PNPM) run contract:ts
	$(MAKE) -C apps/api contract

package-check:
	$(PNPM) run package-check:ts
	$(MAKE) -C apps/api package-check
	$(MAKE) -C packages/agent package-check

check: check-ts check-python check-architecture contract check-docs

ci: check package-check

test-unit: test

test-contract: contract

test-e2e-demo:
	@echo "test-e2e-demo is not implemented yet; use 'make dev-demo' for a manual product run." >&2
	@exit 2
