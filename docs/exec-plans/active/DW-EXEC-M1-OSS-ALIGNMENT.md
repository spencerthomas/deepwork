---
exec_plan_id: DW-EXEC-M1-OSS-ALIGNMENT
title: LangChain-shaped OSS integration and repository gates
status: active
superseded_by: null
owner: codex-implementation
reviewed_by: [repository-owner]
reviewed_at: 2026-07-23
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-004, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-OSS-ALIGNMENT
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 5750addb087a28838a04f9c25590e6df70a02c6b
last_verified_commit: 5750addb087a28838a04f9c25590e6df70a02c6b
risk: high
governed_paths: [AGENTS.md, Makefile, package.json, pnpm-lock.yaml, turbo.json, CONTRIBUTING.md, SECURITY.md, .agents/skills/langchain-oss-maintainer/**, .changeset/**, .github/**, .pre-commit-config.yaml, apps/web/**, packages/agent/**, packages/domain/**, packages/sdk/**, packages/ui/**, internal/**, tools/**, docs/exec-plans/active/DW-EXEC-M1-OSS-ALIGNMENT.md]
contract_gates: []
decision_gates: [DEC-022, DEC-025, DEC-031, DEC-032, DEC-042]
gate_review_status: reviewed-with-gates
gate_reviewed_by: [repository-owner]
gate_reviewed_at: 2026-07-23
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PLANS.md, docs/design-docs/engineering/conventions.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-002-06, AC-DW-FND-004-06, AC-DW-FND-005-01]
dispatch_kind: cell
dispatch_ready: true
agent_review_required: true
dependencies: []
blockers: []
---

# LangChain-shaped OSS integration and repository gates

## Purpose and observable result

Implement the repository review accepted by the repository owner on 2026-07-23.
The outcome is one authoritative local and CI validation path, reuse of the
newly landed domain/SDK task contracts rather than a competing copy, a real
`apps/web -> UI` public-package edge, an agent execution boundary that uses
supported Deep Agents human-in-the-loop controls, a repository-owned convention
skill, and contributor/release metadata familiar to LangChain contributors.

This work uses only synthetic, credential-free tests. It does not deploy, publish
packages, merge the pull request, introduce a live provider, or weaken any
existing fail-closed behavior.

## Context

The original base was `813ca1621f2c1eb9e37c606e5b21e17ca5b6c0f9`.
On 2026-07-23 the owner requested a fresh remote comparison. `origin/main`
advanced repeatedly during implementation and reached
`5750addb087a28838a04f9c25590e6df70a02c6b`, 109 commits beyond the original
base. The branch was reconciled repeatedly rather than freezing the earlier
tree. Those ranges landed the canonical domain task model, reducer, SDK
mappings and services, task inbox and operations-room destinations, local
source execution, journey artifacts and rubrics, stricter fixture policy, and
CI runtime updates. Those contracts supersede the initially proposed duplicate
SDK presentation contract.

Current package-local Python and TypeScript tests are green, but the root
`pnpm check` omits both Python projects and package-consumer checks, the root
`contract` task has no contract implementation, and `apps/web` duplicates the
task contract rather than consuming the shared packages. The agent graph approves
plan text but does not configure tool-call interrupts and buffers its nested
executor.

Reference implementations are the locally pinned Deep Agents, LangChain,
LangGraph, and LangChain.js repositories recorded in the source ledger. Only
their supported public APIs and contributor conventions are used.

## Scope

### In scope

- A root `Makefile` that owns doctor, bootstrap, checks, contracts, packages, docs,
  and the full CI-equivalent fan-out.
- Root scripts that cannot pass without running both Python projects.
- Commit-SHA-pinned GitHub Actions, PR/issue templates, dependency updates, and
  pre-commit checks without publication credentials.
- Preserve and gate the newly landed normalized task contracts in domain/SDK;
  do not add a second SDK task vocabulary.
- Reuse the UI package for shared application state presentation and record the
  remaining whole-workspace SDK adapter migration explicitly rather than
  introducing an incompatible partial type alias.
- Deep Agents `interrupt_on` configuration for caller-supplied tools, observable
  nested execution, and deterministic tests for real tool calls and streaming.
- Ecosystem-compatible runtime dependency ranges and package metadata.
- Coverage, offline evaluation, benchmark, integration-test, rendered component,
  and accessibility test entry points that remain credential-free by default.
- Consolidation of repeated TypeScript package-check helpers where it reduces
  maintenance without weakening a boundary rule.
- Updated contributor and security documentation.
- A repository-owned LangChain/OSS maintainer skill and recurring remote audit.

### Non-goals

- Live LangSmith, provider, deployment, authentication, production persistence,
  release publication, package signing, production preview, or repository merge.
- A compatibility claim not exercised by the CI matrix.
- Removing historical plans, proposals, or source evidence.
- Replacing FastAPI application architecture with LangChain library architecture.

## Interfaces and invariants

- `make check` is the normal local check and `make ci` is the exhaustive gate.
  Both name each owning package; neither silently skips Python.
- `pnpm contract` runs a real TypeScript/API contract check or fails.
- `TaskStatus` has one domain-owned normalized vocabulary used by SDK. The
  current web adapter retains its pre-existing presentation vocabulary only
  until a whole-adapter migration can preserve identity and recovery semantics.
- The SDK owns normalized task service contracts; no new convenience duplicate
  may be added to SDK or domain.
- UI imports no SDK. SDK imports only domain. Web consumes UI through its public
  entry.
- Caller-supplied agent tools default to interrupt-before-execution. A caller may
  explicitly override this policy, but disabling plan approval cannot silently
  disable tool authorization.
- Unit tests deny network. Integration/evaluation jobs are separately named and
  remain deterministic unless an explicit future live-test plan permits otherwise.
- CI actions are pinned to full commit SHAs and receive least privilege.

## Milestones

1. Establish root gates and CI/community infrastructure.
2. Connect web to shared domain/SDK/UI contracts.
3. Enforce agent tool authorization and add streaming/evaluation coverage.
4. Broaden tested package compatibility and update contributor documentation.
5. Run clean full validation, commit, push, open a draft PR, and remove the
   temporary worktree.

## Progress

- [x] 2026-07-23 — Repository owner authorized implementation and PR delivery.
- [x] 2026-07-23 — Isolated `agent/langchain-oss-alignment` worktree created.
- [x] 2026-07-23 — Fetched remote and reconciled 109 new main commits.
- [x] Root gates and CI/community infrastructure implemented.
- [x] Reconciled web/shared-package work with the upstream domain/SDK contracts.
- [x] Agent authorization, streaming, and test suites implemented.
- [x] Repository-owned LangChain/OSS maintainer skill implemented.
- [x] Full local CI-equivalent validation complete.
- [x] Ten-minute remote enforcement automation created and activated.
- [ ] PR delivery complete.

## Surprises and discoveries

- 2026-07-23 — The configured GitHub CLI account has an invalid saved token.
  Local implementation may continue; push/PR delivery requires re-authentication.
- 2026-07-23 — Remote main already contained 7,735 lines of task domain, reducer,
  SDK mapping/service, API runner, and inbox work absent from the original base.
  The initial thin SDK task contract would have duplicated and weakened those
  source-qualified identities, so it was removed during rebase reconciliation.
- 2026-07-23 — Remote main moved the TypeScript 6 parser to 6.0.3 through a
  workspace override while the implementation was in flight. Reapplying the
  old 6.0.2 assertion during an intermediate rebase broke all boundary fixtures;
  preserving the current remote parser contract restored 70 domain, 58 SDK,
  and 32 UI tests.
- 2026-07-23 — Clean package consumers inherited a temporary-directory pnpm
  store and could not use the pre-populated workspace store in offline mode.
  Passing the resolved store explicitly made the proof portable.

## Decision log

- 2026-07-23 — Preserve FastAPI's application-oriented layering. LangChain
  conventions apply to public package discipline, agent composition, tests, and
  OSS workflow rather than forcing application code into a library layout.
- 2026-07-23 — Use the domain package as the normalized status authority and the
  SDK as the task-service contract authority.
- 2026-07-23 — Tool interrupts are fail-closed by default for caller-supplied
  tools. Plan approval alone is not treated as machine-enforced tool authority.
- 2026-07-23 — Default CI remains credential-free and offline at test time.
- 2026-07-23 — Preserve the current web presentation adapter until it can be
  migrated atomically to SDK task services; partial type re-exports are rejected
  because the canonical domain status and identity shapes are intentionally
  different.
- 2026-07-23 — Recurring enforcement may fetch and report or open a reviewed
  branch, but may never push to or rewrite `main`, merge, release, or deploy.

## Validation

Run from the repository root:

```bash
make doctor
make check
make contract
make package-check
make docs
make ci
```

The final record must include test counts, package builds, generated-document
drift, the contract check result, and a clean `git status`.

## Recovery

All changes remain on `agent/langchain-oss-alignment` until review. If a package
integration causes drift, revert that bounded commit rather than weakening the
contract. If GitHub authentication remains unavailable, retain the committed
branch and report the exact `gh auth status` blocker; do not publish through an
unreviewed credential path.

## Outcomes and retrospective

The rebased implementation now provides:

- one root Make-based local/CI path covering all TypeScript and Python projects;
- non-vacuous domain, SDK, web, and API contract gates;
- SHA-pinned CI on the repository Node 24.14 contract and an agent Python
  3.11/3.12/3.13/3.14 matrix;
- independently installable agent packaging with compatible runtime ranges;
- separate plan and caller-tool authorization with a real fake-model tool-call
  interrupt test;
- public nested streaming with sanitized progress events;
- LangChain-style unit, integration, evaluation, benchmark, and 95% coverage
  proof;
- issue/PR/security/dependency/pre-commit/Changesets contributor mechanics;
- a versioned LangChain/OSS maintainer skill and active ten-minute remote audit.

`make ci` passed on the rebased working state. TypeScript suites passed 70
domain, 58 SDK, 32 UI, and 118 web tests; explicit TypeScript contracts passed
30 domain, 27 SDK, and 34 web tests. The API passed 224 tests with two gated
live-source tests skipped, and its contract suite passed 36 with one live test
skipped. The agent passed 77 unit/integration tests, three evaluation cases, its
benchmark, 95.58% coverage, reproducible two-build artifact verification, and
an offline clean-wheel install. Documentation validation reported six
drift-free generated documents.

PR publication remains contingent on valid GitHub authentication. Merge,
release, deployment, and production acceptance remain out of scope.
