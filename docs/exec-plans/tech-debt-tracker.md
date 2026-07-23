# Technical debt tracker

| ID | Status | Owner | Trigger | Debt and deletion test |
|---|---|---|---|---|
| DEBT-001 | open | architecture | Wave 1 scaffold | Wave 0 checks graph validity and generated drift but does not inspect runtime imports. Delete when intentional illegal Python/TypeScript/package imports fail with actionable architecture diagnostics. |
| DEBT-002 | open | developer-experience | Wave 1 scaffold | Root `make doctor/bootstrap/dev-demo/check` commands do not exist. Delete when documented commands exist, are deterministic, and are exercised from a clean clone. |
| DEBT-003 | open | documentation | first generated OpenAPI | `docs/generated/openapi.json` is absent because no API exists. Delete when FastAPI generation is deterministic and drift-checked. |
| DEBT-004 | open | platform | SPIKE-WORKTREE-001 | Collision-free full-stack worktree isolation is designed but unproven. Delete after two concurrent fixture stacks pass the accepted isolation matrix. |
| DEBT-005 | open | orchestration | SPIKE-SYMPHONY-001 | Symphony is not installed or configured. Delete only after the pinned tracker/security/recovery pilot passes; otherwise close as declined and retain manual dispatch. |

Debt must have an owner, trigger, and objective deletion test. It cannot waive
secret, tenant, credential, accessibility, or data-loss boundaries.
