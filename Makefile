SHELL := /bin/sh

# Root command contract for humans and agents. Each target delegates to the
# existing, reviewed per-workspace command so there is one stable entry point.
# Targets that the scaffold has not yet implemented report the gap and fail
# rather than inventing a passing substitute.

.PHONY: help doctor bootstrap dev-demo check check-architecture check-docs \
	test-unit test-contract test-e2e-demo

help:
	@echo "Deep Work command contract:"
	@echo "  make doctor             Report toolchain prerequisites (API + agent env + Node/pnpm)"
	@echo "  make bootstrap          Install API, agent, and web dependencies"
	@echo "  make dev-demo           Start the credential-free local product (./dev)"
	@echo "  make check              Run all workspace checks (pnpm + API + agent)"
	@echo "  make check-architecture Run architecture import/boundary checks"
	@echo "  make check-docs         Validate and drift-check repository documentation"
	@echo "  make test-unit          Run TypeScript and Python unit suites"
	@echo "  make test-contract      Run the API contract suite"
	@echo "  make test-e2e-demo      Not yet implemented (reports the gap)"

doctor:
	@echo "== API toolchain =="
	@$(MAKE) -C apps/api doctor
	@echo "== Agent toolchain =="
	@$(MAKE) -C packages/agent doctor
	@echo "== Node.js =="
	@node --version || { echo "Node.js >=24.14.0 <25 is required (or set DEEPWORK_NODE)" >&2; exit 2; }
	@echo "== pnpm =="
	@pnpm --version || { echo "pnpm is required; enable it with 'corepack enable'" >&2; exit 2; }

bootstrap:
	$(MAKE) -C apps/api bootstrap
	$(MAKE) -C packages/agent bootstrap
	pnpm install

dev-demo:
	./dev

check:
	pnpm check
	$(MAKE) -C apps/api check
	$(MAKE) -C packages/agent check

check-architecture:
	pnpm check-architecture

check-docs:
	python3 tools/docs/generate.py --check
	python3 tools/docs/check.py

test-unit:
	pnpm test
	$(MAKE) -C apps/api test
	$(MAKE) -C packages/agent test

test-contract:
	$(MAKE) -C apps/api contract

test-e2e-demo:
	@echo "test-e2e-demo is not implemented yet (see DEBT-002 and the Wave 1 fixture" >&2
	@echo "loop in docs/PLANS.md). Use 'make dev-demo' for a manual product run." >&2
	@exit 2
