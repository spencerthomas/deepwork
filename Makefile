SHELL := /bin/sh

# Root command contract for humans and agents. Each target delegates to the
# existing, reviewed per-workspace command so there is one stable entry point.
# Targets that the scaffold has not yet implemented report the gap and fail
# rather than inventing a passing substitute.

.PHONY: help doctor bootstrap dev-demo check check-toolchain check-architecture check-docs check-oss \
	test-unit test-contract test-e2e-demo test-recovery test-security-boundary test-visual test-hosted \
	test-performance test-postgres test-product-demo-unit test-product-demo

help:
	@echo "Deep Work command contract:"
	@echo "  make doctor             Report toolchain prerequisites (API + agent env + Node/pnpm)"
	@echo "  make bootstrap          Install API, agent, and web dependencies"
	@echo "  make dev-demo           Start the credential-free local product (./dev)"
	@echo "  make check              Run all workspace checks (pnpm + API + agent)"
	@echo "  make check-architecture Run architecture import/boundary checks"
	@echo "  make check-docs         Validate and drift-check repository documentation"
	@echo "  make check-oss          Audit OSS license, attribution, trademark, and CI pinning"
	@echo "  make test-unit          Run TypeScript and Python unit suites"
	@echo "  make test-contract      Run the API contract suite"
	@echo "  make test-e2e-demo      Run the credential-free browser task journey"
	@echo "  make test-recovery      Prove a completed local task survives an API restart"
	@echo "  make test-postgres      Prove PostgreSQL migration, outbox, restart, concurrency, and scope"
	@echo "  make test-product-demo-unit Check the sealed dual-stack driver and harness contract"
	@echo "  make test-product-demo  Run sealed two-cell browser/isolation acceptance (peer required)"
	@echo "  make test-security-boundary Prove reusable credentials stay outside client/sandbox artifacts"
	@echo "  make test-visual        Run blocking desktop/phone screenshot comparisons"
	@echo "  make test-hosted        Run the fail-closed hosted golden journey"
	@echo "  make test-performance   Run the 1,000-task desktop/phone browser budget"

doctor:
	@python3 tools/doctor/check.py
	@echo "== API toolchain =="
	@$(MAKE) -C apps/api doctor
	@echo "== Agent toolchain =="
	@$(MAKE) -C packages/agent doctor

bootstrap:
	$(MAKE) -C apps/api bootstrap
	$(MAKE) -C packages/agent bootstrap
	pnpm install

dev-demo:
	./dev

check:
	$(MAKE) check-toolchain
	$(MAKE) check-oss
	pnpm check
	$(MAKE) -C apps/api check
	$(MAKE) -C packages/agent check

check-toolchain:
	python3 -m unittest discover -s tools/doctor/tests -p 'test_*.py'

check-oss:
	python3 -m unittest discover -s tools/oss_audit/tests -p 'test_*.py'
	python3 tools/oss_audit/check.py --report output/oss-audit/report.json

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
	pnpm test:e2e-demo

test-recovery:
	$(MAKE) -C apps/api test-local-backup
	pnpm test:recovery

test-postgres:
	$(MAKE) -C apps/api test-postgres

test-product-demo-unit:
	python3 -m unittest discover -s tools/product_demo/tests -p 'test_*.py'
	python3 -m unittest discover -s tools/worktree/tests -p 'test_*.py'
	python3 tools/worktree/harness.py doctor --root .

test-product-demo:
	@test -n "$(DEEPWORK_PRODUCT_DEMO_PEER)" || (echo "DEEPWORK_PRODUCT_DEMO_PEER is required" >&2; exit 2)
	python3 tools/worktree/harness.py exercise --root . --peer-root "$(DEEPWORK_PRODUCT_DEMO_PEER)" --namespace-a dw-iso-a --namespace-b dw-iso-b --evidence-dir "$${DEEPWORK_PRODUCT_DEMO_EVIDENCE:-/tmp/deepwork-product-demo-evidence}"
	python3 tools/worktree/harness.py verify --evidence-dir "$${DEEPWORK_PRODUCT_DEMO_EVIDENCE:-/tmp/deepwork-product-demo-evidence}" --require-no-cross-observation --require-clean-teardown

test-security-boundary:
	pnpm test:security-boundary

test-visual:
	pnpm test:visual

test-hosted:
	pnpm test:hosted

test-performance:
	pnpm test:performance
