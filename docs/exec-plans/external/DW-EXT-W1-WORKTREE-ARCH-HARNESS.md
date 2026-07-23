---
packet_id: DW-EXT-W1-WORKTREE-ARCH-HARNESS
title: External dispatch - worktree isolation and architecture harness
status: ready-for-external-dispatch
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

