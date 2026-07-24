# Technical debt tracker

| ID | Status | Owner | Trigger | Debt and deletion test |
|---|---|---|---|---|
| DEBT-001 | resolved | architecture | Wave 1 scaffold | Resolved: `pnpm check-architecture` runs the repository-wide Python/TypeScript runtime-import checker, verifies every declared intentional-failure fixture emits its exact actionable rule, and then runs the package-local boundary checks. The normal root `pnpm check` invokes this gate before format, lint, type, test, and build work. |
| DEBT-002 | resolved | developer-experience | Wave 1 scaffold | Resolved: `make test-e2e-demo` starts the credential-free API-backed stack through Playwright, completes the representative create → plan approval → result browser journey, rejects non-loopback browser traffic, retains failure artifacts under `output/playwright/`, and runs in the enforced GitHub checks workflow. Pinned execution evidence is recorded in the [quality score](../QUALITY_SCORE.md) at tested commit `7edd55f5390e8fdd4616364deb686d664dc6ed4f`, Playwright 1.61.1, Google Chrome 150.0.7871.182, 2026-07-24 AEST, credential-free local fixture tier with no provider account, Australia/Melbourne, evidence class `executed-local-browser-acceptance`. |
| DEBT-003 | resolved | documentation | first generated OpenAPI | Resolved: the API exists and `apps/api/openapi.json` is generated deterministically by `scripts/export_openapi.py` (`make -C apps/api openapi`) and drift-checked by `tests/contract_tests/test_openapi.py`, which runs in `make -C apps/api check`. |
| DEBT-004 | open | platform | SPIKE-WORKTREE-001 | Collision-free full-stack worktree isolation is designed but unproven. Delete after two concurrent fixture stacks pass the accepted isolation matrix. |
| DEBT-005 | open | orchestration | SPIKE-SYMPHONY-001 | Symphony is not installed or configured. Delete only after the pinned tracker/security/recovery pilot passes; otherwise close as declined and retain manual dispatch. |

Debt must have an owner, trigger, and objective deletion test. It cannot waive
secret, tenant, credential, accessibility, or data-loss boundaries.
