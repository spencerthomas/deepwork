---
exec_plan_id: DW-EXEC-M1-WEB-TS-REVERIFY
title: Reverify TypeScript packages, generated client, adapters, and web
status: draft
superseded_by: null
owner: web-typescript-reverification
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-002
supporting_feature_ids: [DW-FND-001, DW-FND-004, DW-FND-005, DW-SURF-001, DW-QUAL-001]
issue: local:DW-M1-WEB-TS-REVERIFY-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: cad9d8a778c88f837d690d79ba84735660531f9d
last_verified_commit: null
risk: medium
governed_paths: [docs/exec-plans/active/DW-EXEC-M1-WEB-TS-REVERIFY.md]
contract_gates: [SPIKE-HARNESS-ARCH-001, SPIKE-PWA-001]
decision_gates: [DEC-004, DEC-006, DEC-022, DEC-023, DEC-025, DEC-033, DEC-034]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/DESIGN.md, docs/FRONTEND.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/QUALITY_SCORE.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/surfaces/dw-surf-001-responsive-web-pwa-offline-and-push.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-WEB-SHELL-HARNESS.md, docs/exec-plans/active/DW-EXEC-M1-WEB-LOCK-EXTENSION.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-002-01, AC-DW-FND-002-02, AC-DW-FND-002-03, AC-DW-FND-002-05, AC-DW-FND-002-06, AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-004-06, AC-DW-FND-005-01, AC-DW-SURF-001-01, AC-DW-QUAL-001-05, AC-DW-QUAL-001-07, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-WEB-LOCK-EXTENSION-001]
blockers: []
---

# Reverify TypeScript packages, generated client, adapters, and web

## Purpose and observable result

From the exact terminal web lock extension, run one bounded, immutable-input
proof across:

- `packages/domain`, `packages/sdk`, and `packages/ui`;
- the accepted generated product-demo API client and handwritten mapping;
- `internal/adapter-tests`;
- the responsive `apps/web` source/importer; and
- the browser-local UI harness.

Prove format, lint, clean-source typecheck-before-build, unit/contract tests,
intentional architecture negatives, generated drift, build/pack/clean-consumer
use, web production build, and responsive/accessibility/no-request browser
behavior at the final lock.

This is a proof-only cell. Its sole governed source path is this living ExecPlan.
All application/package/generated/adapter/fixture/manifest/lock files are
immutable inputs. A failure is returned to the exact owner and requires a
successor source or bridge candidate, a successor lock extension, and a complete
successor re-verification. The verifier never repairs code, regenerates committed
output in place, edits a manifest/lock, weakens a test, or creates a second owner.

The result supports only bounded scenario contributions. It completes zero
feature scenarios, zero `E2E-V1-*` scenarios, and proves no API-backed product
demo, live provider, PWA install/push, desktop, or native behavior.

## Context

The required chain is terminal:

```text
TS verify -> web source -------------------------------\
fixture/API/TS consumer -> API-SDK bridge --------------+-> web lock
web lock -> this immutable re-verification -> product demo
```

`local:DW-M1-WEB-LOCK-EXTENSION-001` carries the exact terminal source and bridge
ancestry and final lock digest, so it is this plan's only direct dependency. The
Coordinator records all transitive SHAs and reviewer verdicts before dispatch.

The browser-local harness is a single web process with synthetic in-browser
state. It is not a full-stack application worktree and makes zero API,
application, or external request. It therefore does not consume the one-active-
full-stack allowance while `SPIKE-WORKTREE-001` remains open.

## Scope

### In scope

- Validate exact Node/Corepack/pnpm/store/cache and final lock provenance before
  package execution.
- Run the accepted network-denial preload/wrapper for unit, contract, build,
  pack, clean-consumer, adapter, and web commands.
- Frozen offline install with lifecycle scripts disabled and zero lock/manifest
  drift.
- Domain/SDK/UI format, lint, typecheck before build, unit, architecture negative,
  build, pack, JavaScript consumer, and TypeScript consumer proof.
- Deterministic OpenAPI/generated-client drift checks and product-demo SDK public
  import/mapping/error/security contract proof.
- Private language-neutral fixture adapter matrix with fixture and lock bytes
  unchanged.
- Web format, lint, typecheck, tests, production build, standalone inventory,
  browser-local proof, harness reset, console/network summary, responsive/reflow,
  keyboard/focus, reduced motion, forced colors, and automated accessibility.
- Architecture positive/negative and canonical documentation checks.
- Record exact input SHAs, commands, results, evidence digests, failures,
  decisions, and outcome in this plan only.

### Non-goals

- Modifying any source, test, script, generated file, fixture, adapter, manifest,
  lock, root/config, architecture tool, canonical/index/generated document,
  another ExecPlan, or `docs/plans/**`.
- Installing online, resolving a dependency, running a lifecycle script, changing
  a browser binary/cache, or downloading a browser/tool.
- API/worker/Postgres/object/telemetry/product-demo execution.
- Provider, credential, production data, push, merge, deployment, publication, or
  release acceptance.

### Permissions and risk boundary

Only this plan may change. Ignored build, test, pack, consumer, and browser
artifacts are permitted under their exact accepted package-local paths during
execution and must be cleaned by their bounded scripts before handoff. No broad
cleanup, unresolved glob, home/root deletion, or kill-by-name is permitted.

All package commands are offline and use accepted immutable tool/store/cache
inventories. Browser proof uses the pre-existing accepted browser executable,
one isolated profile, `127.0.0.1:43120`, and the harness's fail-closed request
guards. Missing tools/cache/browser fail the cell; no download or host fallback
is allowed.

## Interfaces and invariants

- The exact terminal lock and every workspace manifest hash remain unchanged
  before, during, and after proof.
- Clean-source TypeScript validation runs before any build output exists.
- Package checks use only named public entries. SDK proof imports
  `@deepwork/sdk/product-demo`; web imports no SDK deep path.
- FastAPI OpenAPI is the HTTP authority. `make -C apps/api openapi-check` is
  read-only; generated client checks fail on any stale output.
- The generated client preserves `202` command receipt, command-status,
  projection-read, typed error, host-only cookie credentials, and
  `X-CSRF-Token` semantics without a generic header bag, client-supplied session,
  arbitrary URL, or provider credential.
- The adapter matrix retains source/workspace/session/case/command/projection
  identity, capability evidence, ordered fixture meaning, unknown/malformed
  behavior, partial failure, idempotency conflict, and safe denial.
- Browser-local harness proof retains `Demo data · UI harness`, permits no
  application/API/external requests, registers no service worker, and never
  becomes product-demo evidence.
- Any generated, adapter, or source drift after a check is failure even if
  outputs appear semantically equivalent.

## State matrix

| State | Required behavior |
|---|---|
| Web lock nonterminal or unreviewed | Do not dispatch. |
| Input SHA/lock/manifest/source inventory mismatch | Stop before install. |
| Node/Corepack/pnpm/store/cache mismatch | Stop; no ambient substitute. |
| Frozen offline install fails or changes lock | Fail and retain exact safe output. |
| Lifecycle or external network attempt | Fail the entire cell. |
| Clean-source typecheck fails | Return to the owning source cell; do not build first. |
| Generated OpenAPI/client drift | Return to API consumer or bridge owner as identified by the diff. |
| Adapter fixture/identity/security mismatch | Return to bridge/fixture owner; do not normalize. |
| Package boundary negative unexpectedly passes | Fail and return to package owner. |
| Pack/clean consumer fails | Fail; no deep/source import workaround. |
| Web format/lint/type/test/build fails | Return to web-source owner. |
| Browser executable/cache absent | Report blocked tool evidence; do not download. |
| Browser makes application/API/external request | Fail; UI harness cannot use it. |
| Accessibility/responsive assertion fails | Return exact route/state/viewport to web-source owner. |
| Cleanup leaves a process/profile/cache/evidence leak | Fail handoff until bounded cleanup succeeds. |
| All checks pass | Update only this plan, commit the proof outcome, obtain independent review. |

## Milestones

1. Freeze exact transitive terminal SHAs, manifest/lock/source/generated/fixture
   inventories, toolchain/store/browser provenance, and clean worktree.
2. Run lifecycle-disabled frozen offline install and clean-source
   package/generated/adapter validation, then build/pack/clean-consumer proof.
3. Run web format/lint/type/test/build and browser-local route/state/viewport/
   accessibility/no-request/reset proof.
4. Rerun generation drift, architecture positive/negative, docs, full inventory,
   scope, cleanup, and clean-status checks.
5. Commit only the updated living plan with evidence digests, obtain independent
   TS/DX, generated-contract, frontend/accessibility, and security review, and
   return the exact terminal proof SHA to the Coordinator.

## Validation

The final accepted package manifests own script aliases. The minimum stable
commands are:

```text
dispatch_commit="<exact terminal web lock SHA>"
test "$(git rev-parse HEAD^)" = "$dispatch_commit"
COREPACK_ENABLE_NETWORK=0 pnpm install --offline --frozen-lockfile --ignore-scripts

# Clean-source package and boundary proof before any build.
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile format-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile lint
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile typecheck
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile check-architecture

# API/generated/SDK/adapter drift and contract proof.
make -C apps/api openapi-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk check:product-demo-contract
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk typecheck
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk check-architecture
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk build
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter @deepwork/sdk package-check
proof_tmp="$(mktemp -d)"
trap 'test -n "$proof_tmp" && test "$proof_tmp" != "/" && rm -rf -- "$proof_tmp"' EXIT
node internal/adapter-tests/run.mjs --suite api-sdk-contract --schema docs/generated/openapi.json --work-dir "$proof_tmp/adapter"

# Build/pack and complete web proof.
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile build
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile package-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web format-check
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web lint
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web typecheck
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web test
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web build

ui_evidence_dir="apps/web/evidence/DW-M1-WEB-TS-REVERIFY"
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web browser-proof -- --host 127.0.0.1 --port 43120 --evidence-dir "$ui_evidence_dir" --viewports 320x800,375x812,768x1024,1440x900 --text-zoom 200 --browser-zoom 400 --require-keyboard-focus --require-reduced-motion --require-forced-colors --require-automated-a11y --require-no-application-requests
COREPACK_ENABLE_NETWORK=0 pnpm --offline --frozen-lockfile --filter ./apps/web harness-reset -- --host 127.0.0.1 --port 43120 --storage-prefix deepwork:ui-harness: --evidence-dir "$ui_evidence_dir"
python3 -B -c 'import json,pathlib; d=json.loads(pathlib.Path("apps/web/evidence/DW-M1-WEB-TS-REVERIFY/browser-proof.json").read_text()); assert d["status"]=="passed"; assert d["application_requests"]==0; assert d["serious_a11y_violations"]==0; assert d["server_process_absent"] and d["browser_process_absent"]'
python3 -B -c 'import json,pathlib; d=json.loads(pathlib.Path("apps/web/evidence/DW-M1-WEB-TS-REVERIFY/reset.json").read_text()); assert d["status"]=="passed"; assert d["remaining_harness_keys"]==0; assert d["service_workers"]==0; assert d["server_process_absent"] and d["browser_process_absent"]'

python3 tools/architecture/check.py --root . --graph tools/architecture/graph.json --fixtures internal/fixtures/architecture --verify-negative
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$dispatch_commit" HEAD
test "$(git diff --name-only "$dispatch_commit" HEAD)" = "docs/exec-plans/active/DW-EXEC-M1-WEB-TS-REVERIFY.md"
test -z "$(git status --porcelain)"
```

The worker captures hashes of all manifests, `pnpm-lock.yaml`, product-demo
fixture corpus, API OpenAPI artifact, SDK generated/mapping source, adapter tests,
domain/UI, and web source before and after and requires exact equality. It also
runs the terminal TS cell's negative-boundary, packed JavaScript/TypeScript
consumer, unit-network-denial, and artifact-inventory commands verbatim; the
Coordinator records those exact inherited commands in the reviewed dispatch.

Before reviewed/index transition, docs validation is expected to report only
this plan's unindexed/draft/reviewer/gate/date/verification diagnostics. Its
direct web-lock dependency is present in this bundle and must not be removed.

## Progress

- [x] 2026-07-23 — Drafted a plan-only immutable-input proof after the terminal
  web lock.
- [ ] Terminal web source, API-SDK bridge, and web lock are integrated with exact
  accepted evidence.
- [ ] Independent plan review accepts the command, evidence, cleanup, and
  no-repair boundaries.
- [ ] Proof-only worker returns a clean plan-only commit and independent verdict.

## Surprises & Discoveries

- 2026-07-23 — Broad package/web governed paths would make this verifier a second
  source owner. Consequence: only the living plan is writable; every failure
  returns to the owning cell.
- 2026-07-23 — The browser-local harness can run without API/backend services.
  Consequence: it remains outside the one-active-full-stack limit while still
  proving responsive/accessibility/no-request behavior.

## Decision Log

- 2026-07-23 — Reverify the entire TypeScript/generated/adapter/web chain at one
  final lock. Rationale: a package-local green result cannot prove final importer
  compatibility.
- 2026-07-23 — Permit no repair. Rationale: immutable proof preserves single
  ownership and requires dependency/lock re-review after any source change.
- 2026-07-23 — Keep browser evidence fixture-labelled and API-free. Rationale:
  UI harness proof cannot satisfy product-demo or live-contract acceptance.

## Recovery and rollback

Each check is repeatable from the exact terminal lock. On failure, stop remaining
commands when continuing could obscure ownership, retain only sanitized evidence,
run exact bounded browser/server/profile cleanup if started, confirm repository
inputs remain unchanged, and return the finding to the owner. Do not commit a
failed proof as terminal success.

Rollback of a terminal proof outcome reverts only this plan commit. It does not
revert source or lock. If a downstream product-demo already depends on the proof,
the Coordinator rolls that work back first. A replacement source then flows
through a new lock extension and full re-verification; old proof is never
relabelled current.

## Outcomes & Retrospective

Pending. Completion records exact terminal dependency SHAs, lock/source/generated/
fixture/tool/browser inventories, all command results, evidence digests, cleanup,
scope proof, reviewer verdicts, and returned owner findings. It must restate zero
E2E/live/product-demo/PWA/desktop/mobile credit.
