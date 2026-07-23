# Architecture and worktree harness validation

Date: 2026-07-23

This record distinguishes implemented fixture proof from acceptance that still
depends on separately owned product code. All commands ran from the exact
worktree
`/Users/tomspencer/dev/deepwork/worktrees/external-worktree-architecture-harness`
on branch `external/platform/worktree-architecture-harness`, seeded at
`7eb7900f49f8cd4e21aa72b472e3267acaf65e24` from implementation base
`85187827e018d4aeee4a4e4bd685de49cb2f5a6a`.

## Implemented proof

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tools/architecture/tests -p 'test_*.py'` | Exit 0; 20 passed |
| `python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json` | Exit 0; checked API/agent zones; TypeScript zones dependency-gated; `implemented-not-accepted` |
| `python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative` | Exit 0; one positive and 23 exact negative fixtures passed |
| `python3 -m unittest discover -s tools/worktree/tests -p 'test_*.py'` | Exit 0; 35 passed, including multiprocess reservation, receipt, recovery, and partial-release coverage |
| `python3 tools/worktree/harness.py doctor --root .` | Exit 0; harness ready; reviewed product-demo contract/driver absent |
| `python3 tools/worktree/harness.py self-test --root . --fixtures internal/fixtures/worktree --evidence-dir docs/references/research/harness-isolation/evidence/self-test` | Exit 0; all eight synthetic isolation checks passed; `implemented-not-accepted` |

Self-test evidence is deterministic and contains synthetic identifiers only:

```text
eb8b1920935e7fb0a1048925a7f4d8727fc69397f99a08af86c134a641b60ff0
docs/references/research/harness-isolation/evidence/self-test/self-test.json
```

## Deliberately blocked real matrix

The exact product-demo exercise returned exit 3 before reserving resources or
starting processes because `../deepwork-isolation-peer` does not exist. Its
blocker evidence records `processes_started: 0`, `resources_reserved: 0`, and
`implemented-not-accepted`.

```text
833cce6efb78f5484ac4aecda23809d45aae702dc58b603d6f559e116b8ba253
docs/references/research/harness-isolation/evidence/product-demo/exercise.json
```

The exact verifier returned exit 4 because blocker evidence is not real
product-demo evidence and has no independent private receipt authority. This is
the required fail-closed result; it is not a failed implementation check.

## Independent review

Disjoint implementation authors cross-reviewed architecture, developer-
experience, and security boundaries. Findings covered missing-source coverage,
Python layer/cycle enforcement, environment and secret scanning, template
interpolation, generated drift, atomic reservation, symlink and permission
safety, evidence schemas/provenance, immutable driver review, private receipts,
teardown recovery, resumable dual release, and cross-process collisions. The
findings were corrected, the expanded suites above passed, and both final
read-only verdicts were `ACCEPT`.

No application package, root/shared manifest, dependency lock, CI file,
`docs/plans/**`, program ledger, another ExecPlan, or generated shared document
was changed. No live credential, network provider, merge, push, deployment,
publication, or worktree cleanup was used.
