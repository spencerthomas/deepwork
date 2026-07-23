# Technical debt tracker

| ID | Status | Owner | Trigger | Debt and deletion test |
|---|---|---|---|---|
| DEBT-001 | resolved | architecture | Wave 1 scaffold | Resolved: `pnpm check-architecture` runs the repository-wide Python/TypeScript runtime-import checker, verifies every declared intentional-failure fixture emits its exact actionable rule, and then runs the package-local boundary checks. The normal root `pnpm check` invokes this gate before format, lint, type, test, and build work. |
| DEBT-002 | open | developer-experience | Wave 1 scaffold | Root `Makefile` provides `doctor/bootstrap/dev-demo/check/check-architecture/check-docs/test-unit/test-contract`, each delegating to the reviewed per-workspace command across `apps/api`, `packages/agent`, and the pnpm/Turbo TypeScript workspaces. `.github/workflows/checks.yml` now exercises `make bootstrap` + `make check-docs/check-architecture/check` from a clean clone on every pull request. Remaining gap: `make test-e2e-demo` is declared but unimplemented (reports the gap and fails). Delete when `test-e2e-demo` exists deterministically and is part of the enforced contract. |
| DEBT-003 | resolved | documentation | first generated OpenAPI | Resolved: the API exists and `apps/api/openapi.json` is generated deterministically by `scripts/export_openapi.py` (`make -C apps/api openapi`) and drift-checked by `tests/contract_tests/test_openapi.py`, which runs in `make -C apps/api check`. |
| DEBT-004 | open | platform | SPIKE-WORKTREE-001 | Collision-free full-stack worktree isolation is designed but unproven. Delete after two concurrent fixture stacks pass the accepted isolation matrix. |
| DEBT-005 | open | orchestration | SPIKE-SYMPHONY-001 | Symphony is not installed or configured. Delete only after the pinned tracker/security/recovery pilot passes; otherwise close as declined and retain manual dispatch. |

Debt must have an owner, trigger, and objective deletion test. It cannot waive
secret, tenant, credential, accessibility, or data-loss boundaries.
