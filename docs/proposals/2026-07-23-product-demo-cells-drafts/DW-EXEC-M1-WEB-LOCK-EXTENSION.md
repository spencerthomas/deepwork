---
exec_plan_id: DW-EXEC-M1-WEB-LOCK-EXTENSION
title: Extend the shared TypeScript lock for the terminal web and generated client
status: draft
superseded_by: null
owner: web-lock-integration
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-004, DW-QUAL-001]
issue: local:DW-M1-WEB-LOCK-EXTENSION-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: cad9d8a778c88f837d690d79ba84735660531f9d
last_verified_commit: null
risk: medium
governed_paths: [pnpm-lock.yaml, docs/proposals/2026-07-23-product-demo-cells-drafts/DW-EXEC-M1-WEB-LOCK-EXTENSION.md]
contract_gates: []
decision_gates: [DEC-004, DEC-025]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/exec-plans/active/DW-EXEC-M1-WEB-SHELL-HARNESS.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-002-06, AC-DW-FND-004-06, AC-DW-QUAL-001-07, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [DW-EXEC-M1-WEB-SHELL-HARNESS, local:DW-M1-FIXTURE-API-SDK-CONTRACT-001]
blockers: []
---

# Extend the shared TypeScript lock for the terminal web and generated client

Plan state: **prepared for independent review**. This plan is an unindexed,
non-dispatchable draft carried over from an external planning bundle. It
depends on `DW-EXEC-M1-WEB-SHELL-HARNESS` (an unreviewed draft in this same
archive) and on `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`, which resolves only
to an unindexed draft in PR #9's
`docs/proposals/2026-07-23-ts-proof-consumer-drafts/` archive. Treat every
claim below as proposed, not authoritative, until a coordinator promotes a
rebased version to `docs/exec-plans/active/`.

## Purpose and observable result

Starting from an exact integration base containing both terminal
`DW-EXEC-M1-WEB-SHELL-HARNESS` source/importer and terminal
`local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`, extend the accepted root
`pnpm-lock.yaml` to represent their final manifests. Prove two resolutions are
byte-identical and a lifecycle-disabled frozen offline install accepts the result.

This is a lock-only cell. The exact approved manifest delta is **zero bytes**:
the terminal web-source owner owns `apps/web/package.json`, and the terminal
API-SDK bridge owns `packages/sdk/package.json`. This plan reads those final
manifests and every other workspace manifest but edits none. If resolution needs
a manifest change, the cell stops and returns to that owner.

The result supplies dependency evidence only. It completes no feature scenario,
does not execute package tests/build/browser proof, and earns zero
`E2E-V1-*` or live-contract credit.

## Context

The first TypeScript lock/verification chain covers the original domain/SDK/UI
packages. The web app introduces a final `apps/web` importer and the generated
client adds accepted SDK source/scripts without transferring manifest ownership.
The lock extension must start only after both entire upstream cells are terminal;
a mid-plan importer milestone is not a dependency.

The acyclic chain is:

```text
terminal TS verify -> terminal web source ----------------\
fixture/API/TS consumer -> terminal API-SDK bridge --------+-> web lock
web lock -> web TS reverify -> product demo
```

This draft is unindexed and non-dispatchable. Before dispatch the Coordinator
records exact terminal dependency SHAs, confirms their common integration base,
updates reviewed metadata without changing scope, and prepares one lock-only
worktree.

## Scope

### In scope

- Change the existing root `pnpm-lock.yaml` only as deterministically required by
  the byte-final accepted workspace manifests.
- Verify exact Node `24.18.0`, pnpm `10.34.5`, Corepack path/artifact, public npm
  registry origin, store/cache inventories, workspace importers, peers,
  integrity, and resolution schemes.
- Resolve the lock twice from identical manifest bytes and compare exact output.
- Run a frozen, offline, lifecycle-disabled workspace install and prove it leaves
  the lock and all manifests unchanged.
- Record exact inputs, versions, lock digests, importer inventory, commands,
  results, discoveries, and handoff in this plan.

### Non-goals

- Editing any `package.json`, `pnpm-workspace.yaml`, root config/manifest,
  `turbo.json`, TypeScript/Next source, generated output, adapter tests, fixture,
  architecture tool, program/index/generated plan, or `docs/plans/**`.
- Fixing source, peer, script, format, lint, type, test, build, pack, generation,
  browser, or accessibility failures.
- Adding a provider/browser/runtime dependency not already present in the two
  terminal manifests.
- Application/server/browser execution, external provider access, credential,
  publish, push, merge, deployment, or release.

### Permissions and risk boundary

Committable paths are exactly the two governed paths in front matter. Package
resolution uses only the accepted public npm registry artifacts and an isolated
credential-free Corepack/pnpm environment. The final proof is offline with
`COREPACK_ENABLE_NETWORK=0`; lifecycle scripts are ignored. User/global npm
configuration, proxy/auth overrides, private registries, tokens, and ambient
stores are not inherited or printed.

One explicitly authorized public npm resolution may occur only if the accepted
store is incomplete and the Coordinator grants it after provenance review.
Otherwise the cell reports `blocked-package-index-evidence`; it never silently
falls back online.

## Interfaces and invariants

- Root Node, package manager, workspace, Turbo, TypeScript, formatter, linter,
  and all accepted manifest bytes remain unchanged.
- The manifest baseline inventory covers every `package.json` under the
  repository, including `apps/web/package.json` and `packages/sdk/package.json`,
  before and after all commands.
- The final lock contains exactly one importer per accepted workspace manifest,
  including `apps/web`, with no missing or extra importer.
- Workspace dependencies remain `workspace:*` or their accepted peer form. No
  `file:`, `link:`, Git, arbitrary tarball, private host, credential-bearing URL,
  or lifecycle mutation appears.
- Every registry package has accepted npmjs integrity/provenance.
- A second lock resolution is byte-identical to the first; a frozen install
  changes neither.
- No executable quality claim belongs here. Only
  `local:DW-M1-WEB-TS-REVERIFY-001` may validate packages/generated/adapter/web
  source at this lock.

## State matrix

| State | Required behavior |
|---|---|
| Either upstream cell nonterminal | Do not dispatch. |
| Upstream SHAs do not share the Coordinator integration base | Stop for integration reconciliation. |
| Manifest inventory differs from reviewed inputs | Stop; return exact path/digest to its owner. |
| Root lock is absent or not the terminal first-lock result | Stop; do not create a competing first lock. |
| Toolchain/provenance mismatch | Stop before lock mutation. |
| Offline store incomplete and no online grant exists | Record `blocked-package-index-evidence`. |
| Resolver requests a manifest/source change | Fail and return to the owner. |
| Peer/integrity/registry anomaly | Fail; do not override it. |
| First extension succeeds | Snapshot bytes/digest and inspect every importer/package delta. |
| Repeated resolution drifts | Fail with exact safe diff. |
| Frozen install changes/rejects lock | Fail; preserve the first snapshot for review. |
| Any manifest byte changes | Fail the cell; manifest delta must be zero. |
| All lock proof passes | Commit lock and this plan only; stop for independent review. |

## Milestones

1. Record terminal web-source and API-SDK-bridge SHAs, their independent verdicts,
   the accepted prior lock SHA/digest, every manifest hash, and exact tool/store
   provenance.
2. Resolve only `pnpm-lock.yaml`; verify importer/package/peer/integrity deltas
   correspond exactly to accepted manifests.
3. Repeat lock resolution from identical inputs, compare exact bytes, then run
   frozen offline lifecycle-disabled install and compare again.
4. Prove zero manifest/source/generated/config drift, commit only governed paths,
   obtain independent TypeScript/DX and supply-chain/security review, and hand the
   exact terminal lock SHA to web re-verification.

## Validation

Exact commands run from repository root through the accepted isolated Corepack
wrapper/environment:

```text
web_source_commit="<exact terminal web source SHA>"
api_sdk_bridge_commit="<exact terminal API-SDK bridge SHA>"
dispatch_commit="<exact reviewed dispatch SHA containing both>"
git merge-base --is-ancestor "$web_source_commit" "$dispatch_commit"
git merge-base --is-ancestor "$api_sdk_bridge_commit" "$dispatch_commit"

find . -name package.json -not -path './node_modules/*' -not -path './.git/*' -print0 | sort -z | xargs -0 shasum -a 256 > "$manifest_inventory"
cp pnpm-lock.yaml "$lock_before"

# One authorized online resolution or the same command offline against the
# independently accepted complete store.
COREPACK_ENABLE_NETWORK=0 pnpm install --offline --ignore-scripts --lockfile-only
cp pnpm-lock.yaml "$lock_first"
COREPACK_ENABLE_NETWORK=0 pnpm install --offline --ignore-scripts --lockfile-only
cmp "$lock_first" pnpm-lock.yaml
COREPACK_ENABLE_NETWORK=0 pnpm install --offline --frozen-lockfile --ignore-scripts
cmp "$lock_first" pnpm-lock.yaml

find . -name package.json -not -path './node_modules/*' -not -path './.git/*' -print0 | sort -z | xargs -0 shasum -a 256 > "$manifest_inventory_after"
cmp "$manifest_inventory" "$manifest_inventory_after"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$dispatch_commit" HEAD
test "$(git diff --name-only "$dispatch_commit" HEAD | sort)" = "$(printf '%s\n' docs/exec-plans/active/DW-EXEC-M1-WEB-LOCK-EXTENSION.md pnpm-lock.yaml | sort)"
test -z "$(git status --porcelain)"
```

The reviewer additionally validates all lock importers, package integrity,
forbidden resolution schemes, unchanged workspace/root configuration, exact
Node/Corepack/pnpm/store/cache provenance, and zero lifecycle/network fallback.
Temporary inventory/snapshot paths must come from validated `mktemp` locations
and are never committed.

Before review/index transition, `tools/docs/check.py` is expected to fail only
with this plan's unindexed/draft/reviewer/gate/date/verification diagnostics and
the unknown API-SDK bridge dependency until that plan is integrated. No
diagnostic may be suppressed by deleting the dependency.

## Progress

- [x] 2026-07-23 — Drafted the terminal-to-terminal web lock extension with
  exact zero-byte manifest ownership.
- [ ] Terminal web source and API-SDK bridge are accepted and integrated.
- [ ] Independent plan review accepts exact scope, toolchain, store, and
  validation requirements.
- [ ] Lock worker returns byte-stable frozen/offline proof and fresh review.

## Surprises & Discoveries

- 2026-07-23 — A previous draft depended on an “accepted importer” milestone
  inside an otherwise nonterminal web plan. Consequence: the web source cell now
  terminalizes in full before this lock cell starts.
- 2026-07-23 — The web and SDK manifests have distinct source owners.
  Consequence: this lock cell's only acceptable manifest delta is exactly zero.

## Decision Log

- 2026-07-23 — Serialize shared lock ownership after both source owners are
  terminal. Rationale: one lock cannot be safely authored in parallel.
- 2026-07-23 — Permit no manifest edit. Rationale: dependency intent must be
  independently reviewed with its source; lock resolution cannot invent it.
- 2026-07-23 — Defer all executable repair and proof. Rationale: lock acceptance
  establishes reproducibility, while the next cell validates behavior.

## Recovery and rollback

The lock resolution is idempotent for identical manifests, toolchain, platform,
and package store. On failure, restore only the first validated lock snapshot,
prove every manifest/source remains unchanged, and keep the cell blocked. Do not
hand-edit YAML or change a dependency.

Rollback after integration proceeds in reverse dependency order: first remove any
web re-verification outcome, then revert this exact lock candidate, then run the
previous terminal TS verification matrix at its accepted lock. If a revert or
postcondition fails, stop with exact evidence; do not modify upstream web/SDK
source or another worktree.

## Outcomes & Retrospective

Pending. Completion records exact terminal input SHAs, manifest and lock digests,
Node/Corepack/pnpm/store/cache provenance, importer/package changes, repeated
resolution/frozen-install results, scope proof, reviewer verdicts, and remaining
blockers. It grants zero package-quality, browser, product-demo, feature, E2E,
live-provider, publish, or deployment acceptance.
