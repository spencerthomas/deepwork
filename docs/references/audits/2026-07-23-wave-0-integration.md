---
title: Wave 0 plan-lock integration record
status: reviewed
verified: 2026-07-23
base_commit: 06f051554bf938e919af5ab7855974098fbf3d2a
reviewed_commit: 500eaa7faff57def970963160b3d8f1e90c94398
owners: [planning, developer-experience]
---

# Wave 0 plan-lock integration record

## Starting inventory

The canonical repository began on branch
`claude/deepwork-project-planning-3y91wd` at
`06f051554bf938e919af5ab7855974098fbf3d2a`. Its tracked worktree was clean.
The complete proposal directory and 11 files under `docs/plans/` were untracked.
No active root `AGENTS.md`, `ARCHITECTURE.md`, `WORKFLOW.md`, canonical topical
documents, or runtime package scaffold existed.

The 11 uncertain files were measured before editing and are listed with line counts
and SHA-256 values in the
[preservation manifest](../legacy-plans/unreviewed-2026-07-22/README.md). Their
original paths remain untracked and byte-identical.

## Evidence pins

- Deep Work planning baseline: `06f051554bf938e919af5ab7855974098fbf3d2a`.
- Accepted frontend evidence:
  `26c698b30ff08d5122cfaeedbd4a95296a7884f4`; tracked worktree clean, with three
  pre-existing untracked `.DS_Store` files.
- LangChain documentation:
  `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`; clean.
- Deep Agents: `7794b61a6e76230e8c7a49bdce808b3728305914`; clean.
- LangChain Python: `592055e15e138f5369dce95dd049ce22430996e2`; clean.
- LangChain.js: `ee76ea0347fb611153e5ec7d0e70fa405f5293a3`; clean.
- LangGraph: `31f90df3e6b0268fa77fd2d118a917d420b84a68`; clean.

No sibling repository was written. The frontend refresh changes only sidebar and
task-detail concept code; its Interrupt/Resume interaction is simulated and is not
runtime proof.

## Integrated change

Wave 0 installs:

- root contributor navigation, architecture, conduct, contribution, and security
  entry points;
- canonical product, roadmap, design, frontend, security, reliability, and quality
  documents;
- indexed design decisions and engineering/application architecture;
- 39 stable product specs in their accepted release/category destinations;
- a canonical acceptance registry retaining 179 feature scenarios and 12 v1
  release scenarios;
- living ExecPlan, completed-plan, template, and technical-debt structure;
- generated coverage, issue/dependency, route, package, architecture, and explicit
  no-schema views;
- source ledger, audits, research, legacy evidence, proposal history, and frontend
  rebaseline evidence; and
- a standard-library documentation checker and deterministic generator.

The exact file list for the review change is the commit/index manifest produced by
`git diff --cached --name-status` before commit or `git show --name-status` after
commit. `docs/plans/**` must never appear in that manifest.

## Validation

Run from repository root:

```bash
python3 tools/docs/generate.py --write
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
test ! -e WORKFLOW.md
```

The documentation check verifies internal canonical links, front matter syntax,
duplicate/dangling feature/scenario/spike/source IDs, feature dependencies and
contract gates, exact release/scenario/decision/spike counts, generated drift,
canonical indexing, architecture JSON, absent root `WORKFLOW.md`, and byte-for-byte
legacy preservation.

## Accepted, amended, deferred, unresolved

`DEC-001` through `DEC-043` are accepted with the amendments in the canonical
decision register. Later briefs `DW-FUT-101..103`, `DW-FUT-201..207`, and
`DW-FUT-301` are accepted but deferred from v1. All 44 `SPIKE-*` contracts remain
open with deterministic fallbacks; none is represented as ready. Symphony and its
root `WORKFLOW.md` remain gated by `SPIKE-SYMPHONY-001`.

## Review boundary and next handoff

No runtime code, application package, root runtime manifest, dependency lock, CI,
deployment configuration, credential, live provider, or sibling repository changed
in Wave 0. Historical originals were not deleted.

The reviewed Wave 0 planning and repository-harness baseline is
`500eaa7faff57def970963160b3d8f1e90c94398`. Wave 0.1 and every later
implementation worktree must descend from that commit or from a reviewed
successor. Give the agent the active scaffold ExecPlan verbatim as its scope,
allow only its listed paths, and require it to stop before UI migration or live
integration. Do not install or run Symphony.
