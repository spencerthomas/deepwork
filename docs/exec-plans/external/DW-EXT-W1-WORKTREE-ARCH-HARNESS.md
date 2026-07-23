---
packet_id: DW-EXT-W1-WORKTREE-ARCH-HARNESS
title: External dispatch - worktree isolation and architecture harness
status: implemented-awaiting-coordinator-review
base_commit: 85187827e018d4aeee4a4e4bd685de49cb2f5a6a
branch: external/platform/worktree-architecture-harness
owner: external-platform-harness-worker
reviewers: [architecture, developer-experience, security]
risk: medium
acceptance_ids: [SPIKE-HARNESS-ARCH-001, SPIKE-WORKTREE-001, AC-DW-FND-001-03, AC-DW-FND-001-05, AC-DW-QUAL-001-07, AC-DW-QUAL-001-09, AC-ENG-03]
allowed_paths: [tools/architecture/**, tools/worktree/**, internal/fixtures/architecture/**, internal/fixtures/worktree/**, docs/references/research/harness-isolation/**, docs/exec-plans/external/DW-EXT-W1-WORKTREE-ARCH-HARNESS.md]
dependencies: [local:DW-M1-ROOT-TS-001, local:DW-M1-API-001, local:DW-M1-AGENT-001, local:DW-M1-TS-SCAFFOLD, local:DW-M1-PRODUCT-DEMO-001]
created: 2026-07-23
---

# External dispatch - worktree isolation and architecture harness

## Dispatch identity

- Exact base SHA: `85187827e018d4aeee4a4e4bd685de49cb2f5a6a`.
- Branch to create: `external/platform/worktree-architecture-harness`.
- ExecPlan: this file.
- Start state: architecture-harness implementation may begin. Final
  `SPIKE-WORKTREE-001` acceptance remains blocked until
  `local:DW-M1-TS-SCAFFOLD` and `local:DW-M1-PRODUCT-DEMO-001` are terminal.
- This packet is for an external worker. The program coordinator has not assigned
  it to an internal agent.

## Purpose and observable result

Implement two related but separately decidable harnesses:

1. a repository architecture checker whose positive and intentional negative
   fixtures enforce Python, TypeScript, browser/server, public/private, provider,
   credential, environment, cycle, raw-fetch, and generated-drift boundaries with
   actionable diagnostics; and
2. a collision-safe worktree namespace allocator and proof runner for two
   disposable fixture stacks, covering paths, ports, database/schema, object
   prefix, browser origin/storage, logs/traces/metrics, evidence, restart,
   teardown, and cross-observation.

The architecture harness may reach accepted evidence independently. The worktree
harness may be implemented and self-tested now, but the spike is not accepted
until the real product-demo dependency supplies web/API/worker/Postgres/object/
telemetry composition and the two-worktree matrix passes.

## Allowed paths

The worker may change only:

```text
tools/architecture/**
tools/worktree/**
internal/fixtures/architecture/**
internal/fixtures/worktree/**
docs/references/research/harness-isolation/**
docs/exec-plans/external/DW-EXT-W1-WORKTREE-ARCH-HARNESS.md
```

Do not change root manifests or locks, package manifests or locks, application
source, shared generated documents, CI, `docs/plans/**`, another ExecPlan, or the
program index. Do not create broad cleanup commands or operate on a home,
repository-root, or unresolved environment-variable path.

## Dependencies and blockers

Satisfied at the exact base:

- `local:DW-M1-ROOT-TS-001`;
- `local:DW-M1-API-001`; and
- `local:DW-M1-AGENT-001`.

Required before complete architecture acceptance:

- `local:DW-M1-TS-SCAFFOLD`, so the accepted domain/SDK/UI edges are present.

Required before `SPIKE-WORKTREE-001` acceptance:

- `local:DW-M1-PRODUCT-DEMO-001`, providing the complete credential-free fixture
  stack. Until then, retain the canonical single-full-stack-worktree fallback and
  report the worktree spike as `implemented-not-accepted`.

The controlled two-stack exercise in this spike is the only permitted pre-
acceptance concurrency test. It must use loopback-only disposable resources,
preflight distinct allocations, fail before startup on collision, and tear down
only resources carrying the exact exercise namespace.

## Interfaces and invariants

### Architecture checker

- `tools/architecture/graph.json` remains the machine-readable authority.
- A failing diagnostic names the importing file, violated rule, legal direction,
  architecture anchor, and one local reproduction command.
- Intentional negative fixtures cover UI-to-SDK, domain-to-framework/browser,
  SDK/UI-to-provider or raw network, FastAPI/SQLAlchemy wrong-layer imports,
  credential/reference leakage, environment reads, private upstream modules,
  cycles, missing ESM extensions, and generated drift.
- The checker fails when a negative fixture unexpectedly passes and when a clean
  fixture unexpectedly fails. No secret/tenant boundary may be waived.

### Worktree harness

- Allocation is deterministic from an explicit safe namespace and never from an
  unresolved branch/path alone.
- The manifest includes workspace path, ports, database and schema, object
  prefix, browser origin/storage key, telemetry resource attributes, log/proof
  paths, process identities, and teardown token.
- Reservation is atomic and rejects duplicates before a process starts.
- Teardown is idempotent, namespace-scoped, refuses broad paths/PIDs/resources,
  and cannot stop or read a peer namespace.
- Restart reuses or deliberately rotates resources according to a recorded rule;
  it never silently attaches to a peer.
- Evidence contains synthetic identifiers only and no environment dump, secret,
  credential reference, customer value, or raw provider payload.

## Acceptance IDs and proof

| ID | Required evidence |
|---|---|
| `SPIKE-HARNESS-ARCH-001` | Positive and intentional negative fixtures for every named boundary; actionable deterministic diagnostics; clean repository pass. |
| `SPIKE-WORKTREE-001` | Two real product-demo worktrees concurrently pass distinct-resource, no-cross-observation, restart, scoped teardown, and cleanup verification. |
| `AC-DW-FND-001-03` | An illegal UI-to-SDK edge fails and names the file and allowed direction. |
| `AC-DW-FND-001-05` | Both worktrees differ across all required resource/evidence dimensions and cannot read or stop one another. |
| `AC-DW-QUAL-001-07` | A clean checkout can reproduce package-boundary failure and repair evidence. |
| `AC-DW-QUAL-001-09` | Architecture knowledge/graph drift fails with an owned repair path. |
| `AC-ENG-03` | Deep import, server-only browser import, omitted ESM extension, or explicit unsafe boundary is rejected by a package-local command. |

Passing fixture self-tests does not satisfy `SPIKE-WORKTREE-001` or
`AC-DW-FND-001-05`; only the terminal product-demo matrix does.

## Exact validation commands

The worker must implement these exact stable commands and retain sanitized output:

```bash
python3 -m unittest discover -s tools/architecture/tests -p 'test_*.py'
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json
python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -m unittest discover -s tools/worktree/tests -p 'test_*.py'
python3 tools/worktree/harness.py doctor --root .
python3 tools/worktree/harness.py self-test --root . --fixtures internal/fixtures/worktree --evidence-dir docs/references/research/harness-isolation/evidence/self-test
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
git diff --name-only 85187827e018d4aeee4a4e4bd685de49cb2f5a6a
```

After `local:DW-M1-PRODUCT-DEMO-001` is terminal, run the exact final matrix:

```bash
python3 tools/worktree/harness.py exercise --root . --peer-root ../deepwork-isolation-peer --namespace-a dw-iso-a --namespace-b dw-iso-b --evidence-dir docs/references/research/harness-isolation/evidence/product-demo
python3 tools/worktree/harness.py verify --evidence-dir docs/references/research/harness-isolation/evidence/product-demo --require-no-cross-observation --require-clean-teardown
```

If the peer checkout or product-demo command is unavailable, do not substitute a
mock success. Record the missing dependency and stop at implemented-not-accepted.

## Handoff and review

Commit only allowed paths on the named branch. Record progress, discoveries,
decisions, exact commands, results, retained evidence, and remaining blocker in
this packet. An external author cannot approve their own work. Architecture,
developer-experience, and security reviewers must accept the diff before the
coordinator integrates it. Integration, index/generated updates, root command
wiring, CI, push, merge, deployment, and cleanup of external worktrees remain
coordinator/human actions.

## Progress

- [x] 2026-07-23 — Verified the exact worktree, branch, seed
  `7eb7900f49f8cd4e21aa72b472e3267acaf65e24`, clean status, implementation-base
  ancestry, and an implementation-base diff containing only this ExecPlan.
- [x] 2026-07-23 — Implemented the architecture checker, fixtures, and
  deterministic
  diagnostics.
- [x] 2026-07-23 — Implemented the collision-safe worktree allocator, fixture
  self-test, and
  truthful product-demo gate.
- [x] 2026-07-23 — Retained sanitized self-test and product-demo blocker
  evidence and ran the exact validation commands.
- [x] 2026-07-23 — Completed independent architecture, developer-experience,
  and security cross-review; corrected the findings and received final
  `ACCEPT` verdicts.

## Surprises and discoveries

- 2026-07-23 — `local:DW-M1-TS-SCAFFOLD` is not present at the prepared seed.
  Consequence: architecture fixtures may prove the planned TypeScript boundaries,
  but complete architecture acceptance remains dependency-gated until the real
  domain/SDK/UI source edges are integrated and rechecked.
- 2026-07-23 — `local:DW-M1-PRODUCT-DEMO-001` is not present at the prepared
  seed. Consequence: the worktree harness must stop at
  `implemented-not-accepted`; fixture self-tests cannot satisfy
  `SPIKE-WORKTREE-001` or `AC-DW-FND-001-05`.
- 2026-07-23 — Independent review found fail-open architecture coverage, Python
  layer/cycle, environment, generated-view, and lexical-boundary gaps. The
  corrected checker now requires real source coverage, preserves executable
  template expressions, scans secret shapes in comments, enforces Python
  edges/cycles, and gates acceptance on graph lifecycle status.
- 2026-07-23 — Independent security review found incomplete symlink, evidence
  provenance, schema, driver trust, reservation recovery, and cross-process
  proof. The corrected harness now uses private atomic state, immutable Git-blob
  driver/contract provenance, a private HMAC receipt authority, strict nested
  evidence schemas, reviewed cleanup/recovery, transactionally resumable dual
  release, and multiprocess collision tests.

## Decision log

- 2026-07-23 — The architecture and worktree implementations use only Python
  standard-library tooling within their governed paths. Rationale: root/package
  manifests and dependency locks are outside this packet, and the exact commands
  must run from a credential-free checkout.
- 2026-07-23 — The primary worker retains this ExecPlan and research evidence
  paths while disjoint subagents own only the architecture and worktree
  implementation paths. Rationale: this prevents write collisions and preserves
  an independently reviewable change boundary.
- 2026-07-23 — Product-demo `exercise` must report the missing real dependency
  and exit non-zero rather than converting fixture evidence into acceptance.
  Rationale: the packet explicitly forbids mock success.
- 2026-07-23 — Architecture coverage and graph lifecycle are separate gates.
  Rationale: empty or partial package directories cannot prove a boundary, and
  `planned-wave-1` must not become accepted merely because fixtures pass.
- 2026-07-23 — A real product-demo driver is executable only when a static
  contract and driver match immutable reviewed Git blobs. Retained evidence is
  bound to a private per-run receipt authority, and reservations remain
  fail-closed until reviewed cleanup plus resumable dual release are proven.

## Validation and retained evidence

Implementation validation on 2026-07-23:

```text
architecture unit tests -> 20 passed
clean architecture check -> exit 0; dependency-gated; implemented-not-accepted
architecture fixtures -> 1 positive and 23 exact negative fixtures passed
worktree unit tests -> 35 passed
worktree doctor -> exit 0; harness ready; product demo unavailable
worktree self-test -> exit 0; all 8 checks true; implemented-not-accepted
product-demo exercise -> exit 3 before startup; missing peer checkout
product-demo verify -> exit 4; blocker evidence correctly rejected
```

Retained sanitized evidence:

- `docs/references/research/harness-isolation/evidence/self-test/self-test.json`
  — SHA-256
  `eb8b1920935e7fb0a1048925a7f4d8727fc69397f99a08af86c134a641b60ff0`;
- `docs/references/research/harness-isolation/evidence/product-demo/exercise.json`
  — SHA-256
  `833cce6efb78f5484ac4aecda23809d45aae702dc58b603d6f559e116b8ba253`.

The remaining documentation, diff, allowed-path, and commit evidence is recorded
in `docs/references/research/harness-isolation/validation.md`.

## Outcomes and retrospective

The bounded implementation is complete and awaiting coordinator integration. It
delivers a graph-driven architecture checker with actionable diagnostics,
positive and intentional-negative fixtures, explicit dependency/lifecycle
coverage, and generated-drift enforcement. It also delivers a deterministic
namespace allocator, atomic collision store, scoped restart/teardown,
credential-safe evidence, immutable reviewed-driver provenance, private receipt
authority, and a future real product-demo exercise/recovery protocol.

`SPIKE-HARNESS-ARCH-001` remains dependency-gated because the prepared seed does
not contain the TypeScript scaffold and graph status remains `planned-wave-1`.
`SPIKE-WORKTREE-001` and `AC-DW-FND-001-05` remain
`implemented-not-accepted` because the peer checkout and reviewed real
product-demo contract/driver are absent. The single-full-stack-worktree fallback
therefore remains active. No merge, push, deployment, publication, live
credential use, or external cleanup occurred.
