# Product-demo cells drafts

Status: **non-canonical review history**
Created: 2026-07-23

This package preserves unreviewed product-demo integration planning drafts from
an external planning bundle. These records are not active ExecPlans, are not
indexed, and do not authorize dispatch or implementation. A coordinator may
promote a draft only after independent review, complete active-ExecPlan metadata,
resolvable dependency evidence, and index registration.

Two of these drafts (`DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION.md` and
`DW-EXEC-M1-WEB-LOCK-EXTENSION.md`) name `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`
as a dependency; that identity resolves only to an unindexed draft in PR #9's
`docs/proposals/2026-07-23-ts-proof-consumer-drafts/` archive. Likewise,
`DW-EXEC-M1-WEB-SHELL-HARNESS.md` depends on `local:DW-M1-TS-VERIFY-001`, also
resolvable only inside that same PR #9 archive. None of these are accepted,
reviewed, or indexed ExecPlans, so every dependency edge into and within this
package is currently unresolvable by `tools/docs/check.py`'s standards.

Two drafts also cite commit SHAs in their body text
(`26c698b30ff08d5122cfaeedbd4a95296a7884f4` in
`DW-EXEC-M1-WEB-SHELL-HARNESS.md`, and `3fbdb01be06152cc39e50f6378dfb625daed8998`
in `DW-EXEC-M1-FIXTURE-API-CONSUMER.md`) that do not exist on any branch in
repo history. Before treating any plan in this archive as executable, a future
author must rebase onto real, resolvable commits and either replace or drop
those references.

Before promotion to `docs/exec-plans/active/`, a coordinator must, for every
file in this package:

- assign an independent, non-owner reviewer and set `reviewed_by`/`reviewed_at`;
- move `status` from `draft` to `reviewed` or `active`;
- resolve `gate_review_status` to `reviewed-with-gates` with completed
  `gate_reviewed_by`/`gate_reviewed_at` metadata;
- replace every `local:` dependency with either an indexed, accepted ExecPlan ID
  or a fully specified successor plan, including the cross-references into PR
  #9's proposal drafts described above;
- rebase `base_commit` and `last_verified_commit` (and any commit SHAs cited in
  the body) onto commits that actually exist in repo history; and
- register the plan in `docs/exec-plans/index.md`.

## Contents

- `DW-EXEC-M1-FIXTURE-API-CONSUMER.md`
- `DW-EXEC-M1-PRODUCT-DEMO-API-RUNTIME-LOCK.md`
- `DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION.md`
- `DW-EXEC-M1-WEB-LOCK-EXTENSION.md`
- `DW-EXEC-M1-WEB-SHELL-HARNESS.md`
- `DW-EXEC-M1-WEB-TS-REVERIFY.md`
