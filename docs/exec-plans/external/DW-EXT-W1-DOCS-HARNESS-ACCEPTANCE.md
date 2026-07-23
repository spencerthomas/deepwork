---
packet_id: DW-EXT-W1-DOCS-HARNESS-ACCEPTANCE
title: External dispatch - documentation-harness acceptance
status: ready-for-external-dispatch
base_commit: b9d244438c90a3031983b9705407b3dd5d4c33f9
branch: external/platform/documentation-harness-acceptance
owner: external-documentation-harness-worker
reviewers: [documentation-governance, developer-experience, security]
risk: medium
acceptance_ids: [SPIKE-HARNESS-DOCS-001, AC-DW-QUAL-001-03, AC-DW-QUAL-001-09, AC-ENG-14]
allowed_paths: [tools/docs/**, internal/fixtures/docs/**, docs/references/research/harness-docs/**, docs/exec-plans/external/DW-EXT-W1-DOCS-HARNESS-ACCEPTANCE.md]
dependencies: [integrated:DW-W0.1-DISPATCH-HARDENING@3dbe6629d8053380ab6a8bff6d2fcb462f854256, canonical-doc-corpus@b9d244438c90a3031983b9705407b3dd5d4c33f9]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
---

# External dispatch - documentation-harness acceptance

## Dispatch identity

- Exact base SHA:
  `b9d244438c90a3031983b9705407b3dd5d4c33f9`.
- Branch to create:
  `external/platform/documentation-harness-acceptance`.
- ExecPlan: this file.
- This packet is for an external worker. The program coordinator has not assigned
  its implementation scope to an internal agent.
- The packet accepts or rejects `SPIKE-HARNESS-DOCS-001`; it does not authorize a
  rewrite of the canonical documentation corpus.

## Purpose and observable result

Turn the existing documentation validator into retained, independently reviewable
acceptance evidence for the canonical document taxonomy without regressing any
Wave 0.1 behavior.

At completion:

1. the existing no-argument documentation generation and validation commands
   remain compatible and green on the exact canonical repository corpus;
2. a hermetic positive/negative fixture matrix proves stable diagnostics for every
   failure class required by `SPIKE-HARNESS-DOCS-001`;
3. the acceptance runner fails if a required negative fixture unexpectedly passes,
   a clean fixture fails, a stable rule code disappears, or the canonical corpus
   fails the existing validator;
4. sanitized evidence records the exact base, commands, rule matrix, fixture
   hashes, results, and remaining gaps; and
5. no product specification, design document, roadmap, source ledger, generated
   document, program record, or index is changed to make the harness pass.

## Allowed paths

The worker may change only:

```text
tools/docs/**
internal/fixtures/docs/**
docs/references/research/harness-docs/**
docs/exec-plans/external/DW-EXT-W1-DOCS-HARNESS-ACCEPTANCE.md
```

The following remain coordinator- or canonical-owner paths and are read-only:

```text
docs/exec-plans/index.md
docs/exec-plans/active/**
docs/exec-plans/completed/**
docs/product-specs/**
docs/design-docs/**
docs/generated/**
docs/references/source-ledger.md
docs/PLANS.md
docs/QUALITY_SCORE.md
AGENTS.md
ARCHITECTURE.md
Makefile
package.json
pnpm-lock.yaml
docs/plans/**
```

Do not edit canonical content or generated output to manufacture a green result.
If the current corpus exposes a real defect outside allowed paths, retain the
diagnostic and return an exact coordinator-owned blocker.

## Dependencies and current baseline

The base includes the reviewed Wave 0.1 validator hardening at
`3dbe6629d8053380ab6a8bff6d2fcb462f854256`. At dispatch, the canonical corpus
contains 39 stable feature specifications, 179 feature scenarios, 12 v1 release
scenarios, 43 decisions, and the active/completed/external ExecPlan taxonomy.

Before implementation, record baseline output from:

```bash
python3 -m unittest discover -s tools/docs/tests -p 'test_*.py'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
```

Existing rule behavior, output meaning, supported active-ExecPlan schema,
dispatch-readiness checks, source/proposal precedence, and generated-document
drift detection must remain intact. New rules must be additive or an explicitly
documented correction with a regression fixture. The harness uses only the Python
standard library unless the packet is returned for dependency review; it performs
no network access and needs no credentials.

## Required fixture and diagnostic contract

`internal/fixtures/docs/**` must contain hermetic fixture repositories or
declarative mutations with a machine-readable matrix. Each negative case declares
its expected stable rule code and the smallest triggering file. At minimum the
matrix proves:

- a broken canonical internal link;
- an orphaned canonical document;
- duplicate stable feature, decision, spike, scenario, plan, or issue identity;
- missing or invalid owner, status, source, review/verification, governed-path,
  reviewer, gate-review, or dispatch metadata where the schema requires it;
- an active ExecPlan missing `Progress`, `Surprises & Discoveries`, `Decision
  Log`, or `Outcomes & Retrospective`;
- an invalid ExecPlan status transition or a dispatch-ready plan with unresolved
  dependencies, blockers, gates, or review requirements;
- a changed governed path with stale verification evidence;
- glossary/terminology conflict;
- generated output drift or a hand-edited generated file;
- a canonical claim whose only support is an unaccepted proposal or uncertain
  legacy file;
- a broken canonical index/authority edge; and
- a clean minimal fixture and the real canonical corpus passing.

Fixtures must not resolve imports or links from the parent repository accidentally,
follow a symlink outside their fixture root, depend on wall-clock age alone, or
write outside an explicit temporary/evidence directory. Diagnostics name the rule
code, file, violated invariant, canonical repair owner/path, and one local
reproduction command. Output contains no environment dump or user path beyond the
sanitized repository-relative path.

## Required retained evidence

Under `docs/references/research/harness-docs/`, retain:

- `matrix.json`: one row per required failure/clean case with rule code, fixture,
  expected result, actual result, command, and acceptance ID;
- `report.md`: baseline, implementation summary, compatibility assessment,
  known gaps, deterministic fallback, and an author-recommended
  `implemented-not-accepted`, `blocked`, or `ready-for-independent-review`
  disposition. Only the independent reviewers may record final acceptance or
  rejection;
- `fixtures.json`: fixture file hashes and proof that fixture resolution stayed
  inside the fixture root;
- `commands.txt`: exact commands, interpreter version, base SHA, and exit statuses
  without an environment dump; and
- `evidence/`: bounded machine-readable acceptance output.

Generated evidence must be deterministic after removing explicit timestamps. A
second acceptance run must produce no uncommitted diff.

## Acceptance IDs and qualification

| ID | Required evidence |
|---|---|
| `SPIKE-HARNESS-DOCS-001` | Every named positive/negative fixture is exercised with stable actionable diagnostics; the real canonical corpus passes; the second run is drift-free. |
| `AC-DW-QUAL-001-03` | Proposal-only, unaccepted-spike, and unsupported runtime claims cannot be promoted to canonical/release-ready state by documentation metadata. This packet contributes documentation proof only. |
| `AC-DW-QUAL-001-09` | Governed-path, index/authority, and generated-document drift fail with an owned repair path. Architecture-edge proof remains with `SPIKE-HARNESS-ARCH-001`. |
| `AC-ENG-14` | Partial evidence only: renamed links, documented commands/configuration examples, terminology, and generated references fail this harness before integration. Root `make docs-check` wiring, compiled snippets, and current-model verification remain coordinator/downstream work and cannot be claimed by this packet. |

Passing unit tests without the complete intentional negative matrix does not accept
the spike. This packet may contribute to broader scenarios but cannot mark the
full v1 release or architecture harness accepted.

## Exact validation commands

The worker must preserve and run the existing command contract:

```bash
python3 -m unittest discover -s tools/docs/tests -p 'test_*.py'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
```

The worker must implement and run this acceptance command contract:

```bash
python3 tools/docs/acceptance.py --root . --fixtures internal/fixtures/docs --evidence-dir docs/references/research/harness-docs/evidence
python3 tools/docs/acceptance.py --root . --fixtures internal/fixtures/docs --evidence-dir docs/references/research/harness-docs/evidence --verify-negative
python3 tools/docs/acceptance.py --root . --fixtures internal/fixtures/docs --evidence-dir docs/references/research/harness-docs/evidence --check-no-drift
python3 tools/docs/acceptance.py --root . --verify-scope --base b9d244438c90a3031983b9705407b3dd5d4c33f9 --include-untracked
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
git diff --check b9d244438c90a3031983b9705407b3dd5d4c33f9...HEAD
git diff --name-only b9d244438c90a3031983b9705407b3dd5d4c33f9
git status --short
```

The scope command must fail on any committed, staged, unstaged, or untracked path
outside the exact allowlist. The final committed branch must be clean, and its diff
must contain only allowed paths. If the real canonical corpus fails because of an
out-of-scope defect, do not suppress it: retain the failure, recommend
`blocked-canonical-defect`, and name the exact owner/path for independent review.

## Deterministic fallback

Until independent reviewers accept the complete matrix:

- run the documented manual canonical-map/index/metadata/generated-drift checklist;
- preserve the existing Wave 0.1 validator as the minimum automated gate;
- do not broaden agent-ready implementation or feature migration based on an
  unverified canonical map; and
- represent the spike as `implemented-not-accepted` or
  `blocked-canonical-defect`, never as a partial silent pass.

## Handoff and review

Commit only allowed paths on the named branch. Keep this packet current with
progress, discoveries, decisions, commands, evidence, compatibility observations,
and the final acceptance state. The implementation author cannot approve their own
work. Documentation-governance, developer-experience, and security reviewers must
accept the diff and evidence before the coordinator integrates it.

The coordinator alone updates the program/index, generated canonical views, source
ledger, quality score, root commands, CI, or dispatch policy. No worktree creation,
push, merge, deployment, publication, production mutation, credential use, or
destructive cleanup is authorized by this packet.
