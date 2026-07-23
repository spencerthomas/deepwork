---
exec_plan_id: DW-EXEC-M1-TS-LOCK
title: Wave 1 TypeScript first-lock and frozen-install proof
status: draft
superseded_by: null
owner: typescript-lock-integration
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-QUAL-001]
issue: local:DW-M1-TS-LOCK-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: medium
governed_paths: [pnpm-lock.yaml, docs/proposals/2026-07-23-ts-proof-consumer-drafts/DW-EXEC-M1-TS-LOCK.md]
contract_gates: []
decision_gates: [DEC-025]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, docs/PLANS.md, docs/exec-plans/active/DW-EXEC-PROGRAM-CANONICAL.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/SECURITY.md, docs/RELIABILITY.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-QUAL-001-07, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-TS-SCAFFOLD]
blockers: []
---

# Wave 1 TypeScript first-lock and frozen-install proof

Plan state: **prepared for independent review**. This draft is deliberately
unindexed and non-dispatchable. Review feedback may amend only this file; a later
coordinator transition owns reviewer metadata, index registration, and any
dispatch decision.

## Purpose and observable result

After a future, freshly and independently accepted terminal TypeScript source
cell, create the first root `pnpm-lock.yaml` from the already reviewed manifests
with the exact pinned Node and pnpm toolchain. Prove that a frozen install accepts
that lock and that resolving the same manifests again produces byte-identical lock
content.

This cell owns dependency resolution only. It contributes bounded lock/install
evidence to `AC-DW-FND-001-03`, `AC-DW-QUAL-001-07`, and
`AC-DW-QUAL-001-08`; it completes none of those scenarios and earns zero v1 E2E
credit. It grants no source, manifest, test, configuration, or generated-file
repair.

## Context and orientation

The plan-authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2` on branch
`external/planning/w1-ts-proof-consumers` in worktree
`/Users/tomspencer/dev/deepwork/worktrees/external-planning-ts-proof-consumers`.
That base declares Node `24.18.0`, pnpm `10.34.5`, Turbo `2.10.6`,
TypeScript `7.0.2`, Oxfmt `0.60.0`, and Oxlint `1.75.0`. Package manifests also
pin Vitest `4.1.10`; UI declares the React peer range `^19.2.0` and exact
development versions React `19.2.8`, React DOM `19.2.8`, React types `19.2.17`,
React DOM types `19.2.3`, Testing Library DOM `10.4.1`, Testing Library React
`16.3.2`, and jsdom `29.1.1`. SDK and UI declare
`@deepwork/domain: workspace:*`.

The TypeScript candidate `1bf66e1` is **REWORK REQUIRED**. It is not accepted
source and cannot satisfy this plan's dependency. The lock cell starts only from
the exact full SHA of a later fresh independent acceptance of
`local:DW-M1-TS-SCAFFOLD`. No SHA in this draft predicts that result.

## Scope

### In scope

- Create exactly one root `pnpm-lock.yaml` from the accepted manifests.
- Verify Node distribution/binary and Corepack/pnpm artifact provenance, every
  root/package manifest pin and workspace/peer spec, exact registry origin, lock
  importers, package snapshots, and integrity fields before handoff.
- Run one frozen, script-disabled workspace install and one subsequent
  lockfile-only resolution.
- Compare the first generated lock snapshot byte-for-byte with the final lock.
- Record exact commands, versions, outputs, accepted source SHA, lock digest, and
  changed-file scope in this living plan.

### Non-goals

- Editing any `package.json`, source, test, package script, TypeScript config,
  Turbo config, workspace config, generated file, index, program/umbrella plan,
  product specification, or `docs/plans/**`.
- Fixing install, peer, source, build, type, lint, test, pack, accessibility, or
  consumer failures.
- Running package format, lint, typecheck, test, build, pack, or application
  commands.
- Publishing, deployment, provider access, live capability proof, push, merge, or
  release.

### Permissions and risk boundary

- Committable paths are exactly `pnpm-lock.yaml` and this ExecPlan.
- Lock and install commands run offline against a pre-provisioned, read-only
  package store whose artifacts and metadata were independently verified as
  originating from `https://registry.npmjs.org/` for the exact accepted
  manifests. An incomplete store stops the cell; it does not authorize live
  fallback. A credential-free isolated pnpm invocation ignores user/global
  registry, proxy, and auth configuration. Lifecycle scripts remain disabled.
- No provider, application, production, customer, signing, or registry-publish
  credential is permitted.
- Ignored `node_modules` and pnpm-store material may exist only as transient
  install output; none may be committed or treated as a governed source path.
- If dependency resolution requires a manifest/source/config change, stop and
  return the exact failure to the TypeScript source owner. This cell has no repair
  authority.
- Independent developer-experience, supply-chain/security, and TypeScript
  boundary review are required. The author cannot approve or dispatch this plan.

## Authoritative sources and prerequisites

- Product and quality: `DW-FND-001`, `DW-QUAL-001`.
- Architecture and method: root `AGENTS.md`, `ARCHITECTURE.md`,
  `docs/design-docs/engineering/conventions.md`, and `DEC-025`.
- Upstream cell: `local:DW-M1-TS-SCAFFOLD` must be terminal-success after a fresh
  independent review. The review must explicitly supersede the rework-required
  `1bf66e1` candidate.
- The execution base must contain the accepted root/package manifests and no
  `pnpm-lock.yaml`. If a lock already exists, stop for coordinator reconciliation;
  do not overwrite or normalize it.
- Live providers and optional runtime capabilities are unavailable and irrelevant
  to this lock-only proof.

## Interfaces and invariants

- `.node-version` and root `engines.node` remain exactly `24.18.0`.
- Root `packageManager` remains exactly `pnpm@10.34.5`; Corepack is the invocation
  boundary.
- Every direct package/tool version, workspace dependency spec, and peer range
  remains the exact accepted manifest value.
- The lock must represent all workspace importers without adding a package,
  changing a dependency range, running lifecycle scripts, or resolving a private
  beta/live-provider dependency.
- Node `24.18.0` and pnpm `10.34.5` are pre-provisioned from independently
  verified official artifacts. Record published checksum/signature evidence,
  resolved Node/Corepack executable paths, Corepack artifact tree, package-store
  tree, metadata-cache tree, and their accepted SHA-256 inventory values;
  Corepack networking is disabled before its first invocation.
- Pnpm resolution runs with an isolated credential-free configuration containing
  only the accepted executable path, verified Corepack cache, project config,
  `https://registry.npmjs.org/`, and non-secret process requirements.
  User/global `.npmrc`, registry/proxy/auth overrides, and tokens are not inherited
  or printed.
- Every non-workspace package record carries accepted registry integrity.
  `git+`, GitHub shorthand, `file:`, `link:`, arbitrary tarball, private-host, and
  credential-bearing resolutions fail the cell.
- `pnpm-lock.yaml` is the only new dependency artifact. No package-local lock is
  allowed.
- A frozen install must not modify the lock. A repeated lockfile-only resolution
  must be byte-identical to the first generated lock.
- Any peer, integrity, registry, platform, unsupported-engine, or resolution
  anomaly is a failure for review, not permission to repair source or manifests.

## State matrix

| State | Required behavior | Evidence or recovery |
|---|---|---|
| TS source not freshly accepted | Do not execute. | Record the nonterminal dependency and return to coordinator. |
| Candidate is `1bf66e1` or an unreviewed successor | Reject it as an execution base. | Require a fresh independent terminal verdict and full SHA. |
| Node or pnpm version mismatch | Stop before lock creation. | Provision the exact pinned toolchain outside this diff and rerun preflight. |
| Existing root lock | Stop; do not overwrite. | Coordinator determines whether this first-lock plan is superseded. |
| Verified package store incomplete | Stop before resolution. | Provision and independently verify the exact npmjs artifacts outside this cell, then issue a new reviewed dispatch; never fall back online. |
| Registry/auth/proxy override detected | Stop before resolution. | Use the isolated credential-free invocation; never print a secret value. |
| Node/Corepack/pnpm/store/cache provenance unavailable or mismatched | Stop before resolution. | Obtain independently accepted official checksum/signature and aggregate inventory evidence outside this diff. |
| Resolution/peer/integrity failure | Leave source and manifests unchanged. | Return failure to owning cell or dependency review. |
| Frozen install changes/rejects lock | Fail the cell. | Preserve first lock and transcript for review; grant no source repair. |
| Second resolution drifts | Fail with byte diff and package/importer context. | Do not commit until the owning source/manifests are reconciled. |
| Lock succeeds | Record digest, versions, provenance summary, and exact scope. | Hand to fresh independent review; do not start verification. |

## Milestones

### Milestone 1 — Accept the exact terminal source and toolchain

Record the fresh accepted TypeScript source SHA and reproduce its reviewer
verdict. Verify root/package manifest versions, workspace specs, peer range,
project `.npmrc`, Node distribution, and Corepack/pnpm artifact against the
inventory in this plan before creating any lock.

Acceptance:

- `local:DW-M1-TS-SCAFFOLD` is terminal-success at one full accepted SHA.
- The exact accepted Node binary prints `v24.18.0`; the exact accepted Corepack
  path with networking disabled resolves pnpm `10.34.5`; executable and aggregate
  Corepack/store/metadata-cache hashes equal retained provisioning evidence.
- The isolated pnpm environment is offline, identifies
  `https://registry.npmjs.org/` as the sole accepted origin, uses the recorded
  verified store, and passes no registry authentication.
- The accepted execution base has no root lock and no dirty or untracked
  out-of-scope file.

### Milestone 2 — Create the first lock without lifecycle execution

Run the exact lockfile-only command through the isolated Corepack wrapper and
inspect the resulting workspace importers, package snapshots, peer resolution,
registry source, and integrity metadata.

Acceptance:

- One root `pnpm-lock.yaml` exists and parses under pnpm `10.34.5`.
- No accepted manifest, source, configuration, index, or generated file changed.
- Every non-workspace package has registry integrity and no forbidden resolution
  scheme or host appears.
- A SHA-256 digest of the first lock is retained in this plan.

### Milestone 3 — Prove frozen install and no drift

Copy the first lock into a validated `mktemp -d` and install an immediate cleanup
trap. Before any install can create a virtual-store lock, remove only the root
lock and resolve afresh from manifests under the same isolated
toolchain/store/cache environment. Compare the independently regenerated bytes
with the first snapshot, restore the first bytes, then run the script-disabled
frozen install and compare again. Restore the first bytes on every failure path.

Acceptance:

- The subsequent lockfile-only command exits zero.
- `cmp` exits zero against the first-lock snapshot.
- Frozen install then exits zero and does not modify the restored lock.
- The failure-safe trap restores the first lock and removes only the validated
  owned temporary directory on every exit path.

### Milestone 4 — Independent lock handoff

Record the exact diff, lock digest, command transcript, dependency inventory, and
known environment limitations. Commit only the two governed files and stop.

Acceptance:

- Fresh independent DX and security/supply-chain review returns `ACCEPT` or
  bounded rework.
- No package validation, scenario completion, or E2E claim is recorded.
- The accepted lock commit becomes the sole prerequisite for
  `local:DW-M1-TS-VERIFY-001`.

## Progress

- [x] 2026-07-23 AEST — Drafted at the exact supplied base; no install, lock, or
  implementation command was run.
- [x] 2026-07-23 AEST — Recorded that `1bf66e1` is rework-required and cannot
  satisfy the source dependency.
- [x] 2026-07-23 AEST — Initial exact three-file candidate received architecture,
  DX, and security `REWORK REQUIRED` verdicts and product/contract `ACCEPT`;
  the correction remains limited to those files plus the new API/SDK bridge
  plan.
- [ ] Independent plan review accepts the exact draft candidate.
- [ ] Coordinator records reviewed metadata and terminal TypeScript source SHA.
- [ ] Milestones 1-4 execute in a fresh authorized lock-only worktree.

## Surprises & Discoveries

- 2026-07-23 AEST — The host seen by the coordinator previously exposed Node 20
  and pnpm 9 while repository declarations require Node `24.18.0` and pnpm
  `10.34.5`. Consequence: execution must verify the exact toolchain before
  creating the lock; a globally available fallback cannot be used.
- 2026-07-23 AEST — The source candidate named in the coordinator update is under
  rework, not terminal. Consequence: this draft intentionally contains no
  execution-base SHA beyond its plan-authoring base.

## Decision Log

- 2026-07-23 AEST — Decision: separate first-lock work from source authoring and
  executable package proof. Rationale: shared dependency resolution is a narrow
  coordinator-owned mutation, while source repair and executable proof have
  different paths and reviewers. Consequence: the DAG is TS source -> lock ->
  executable verification.
- 2026-07-23 AEST — Decision: disable lifecycle scripts during lock and frozen
  install proof. Rationale: the current packages require dependency availability,
  not third-party install execution, and the lock cell has no code-execution
  authority beyond pnpm itself. Consequence: a package that needs lifecycle
  execution requires separate security review rather than a silent exception.

## Detailed implementation approach

1. Start from the exact coordinator-provided reviewed dispatch commit that
   contains this plan and the freshly accepted TS source.
2. Verify branch/base ancestry, clean scope, absence of a lock, exact Node/pnpm
   versions and provenance, project configuration, and every accepted root/package
   manifest pin/spec.
3. Construct a credential-free isolated Corepack/pnpm invocation pinned to the
   verified package-manager cache, pre-verified read-only package store, offline
   mode, and `https://registry.npmjs.org/` provenance. Run the first lockfile-only
   resolution with lifecycle scripts disabled.
4. Capture the lock digest and a temporary byte snapshot.
5. Under an immediate failure-safe trap and before any virtual-store lock exists,
   remove only the root lock, resolve independently from manifests, compare with
   the snapshot, and restore the first bytes. Then run the frozen install and
   prove the restored root lock is unchanged.
6. Inspect dependency/provenance output, update only this living plan, commit only
   the lock and plan, and stop at independent review.

## Validation and proof

Run from repository root only after the future accepted source dependency is
terminal:

```text
set -euo pipefail
accepted_ts_source_commit="<freshly accepted full 40-character SHA>"
reviewed_lock_dispatch_commit="<reviewed lock-plan dispatch SHA descending from accepted source>"
test "${#accepted_ts_source_commit}" -eq 40
git cat-file -e "${accepted_ts_source_commit}^{commit}"
test "${#reviewed_lock_dispatch_commit}" -eq 40
git cat-file -e "${reviewed_lock_dispatch_commit}^{commit}"
git merge-base --is-ancestor "$accepted_ts_source_commit" "$reviewed_lock_dispatch_commit"
test "$(git rev-parse HEAD)" = "$reviewed_lock_dispatch_commit"
test "$(git status --porcelain)" = ""
test ! -e pnpm-lock.yaml
test ! -d node_modules
test -z "$(find apps packages internal -type d -name node_modules -prune -print -quit)"
test "$(cat .node-version)" = "24.18.0"
test -z "${NPM_TOKEN+x}${NODE_AUTH_TOKEN+x}"
accepted_node_bin="<absolute Node binary from accepted provisioning evidence>"
accepted_corepack_bin="<absolute Corepack binary from accepted provisioning evidence>"
verified_corepack_home="<absolute pre-verified Corepack cache directory>"
verified_pnpm_store="<absolute pre-verified read-only pnpm store>"
verified_pnpm_metadata_cache="<absolute pre-verified read-only pnpm metadata cache>"
expected_node_sha256="<accepted 64-character SHA-256>"
expected_corepack_sha256="<accepted 64-character SHA-256>"
expected_corepack_tree_sha256="<accepted 64-character aggregate SHA-256>"
expected_store_tree_sha256="<accepted 64-character aggregate SHA-256>"
expected_metadata_tree_sha256="<accepted 64-character aggregate SHA-256>"
test -x "$accepted_node_bin"
test -x "$accepted_corepack_bin"
test -d "$verified_corepack_home"
test -d "$verified_pnpm_store"
test -d "$verified_pnpm_metadata_cache"
test ! -w "$verified_pnpm_store"
test ! -w "$verified_pnpm_metadata_cache"
for digest in "$expected_node_sha256" "$expected_corepack_sha256" \
  "$expected_corepack_tree_sha256" "$expected_store_tree_sha256" \
  "$expected_metadata_tree_sha256"; do test "${#digest}" -eq 64; done
test "$(shasum -a 256 "$accepted_node_bin" | awk '{print $1}')" = "$expected_node_sha256"
test "$(shasum -a 256 "$accepted_corepack_bin" | awk '{print $1}')" = "$expected_corepack_sha256"
test "$(find "$verified_corepack_home" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_corepack_tree_sha256"
test "$(find "$verified_pnpm_store" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_store_tree_sha256"
test "$(find "$verified_pnpm_metadata_cache" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_metadata_tree_sha256"
trusted_path="$(dirname "$accepted_node_bin"):/usr/bin:/bin"
test "$(env -i PATH="$trusted_path" "$accepted_node_bin" --version)" = "v24.18.0"
env -i PATH="$trusted_path" "$accepted_node_bin" -e 'const fs=require("node:fs");const expected="auto-install-peers=false\nengine-strict=true\nsave-exact=true\nstrict-peer-dependencies=true\n";if(fs.readFileSync(".npmrc","utf8")!==expected)process.exit(1)'
env -i PATH="$trusted_path" "$accepted_node_bin" -e 'const r=require("./package.json"),d=require("./packages/domain/package.json"),s=require("./packages/sdk/package.json"),u=require("./packages/ui/package.json");const ok=r.packageManager==="pnpm@10.34.5"&&r.engines.node==="24.18.0"&&r.devDependencies.turbo==="2.10.6"&&r.devDependencies.typescript==="7.0.2"&&r.devDependencies.oxfmt==="0.60.0"&&r.devDependencies.oxlint==="1.75.0"&&d.devDependencies.vitest==="4.1.10"&&s.dependencies["@deepwork/domain"]==="workspace:*"&&s.devDependencies.vitest==="4.1.10"&&u.dependencies["@deepwork/domain"]==="workspace:*"&&u.peerDependencies.react==="^19.2.0"&&u.devDependencies.react==="19.2.8"&&u.devDependencies["react-dom"]==="19.2.8"&&u.devDependencies["@types/react"]==="19.2.17"&&u.devDependencies["@types/react-dom"]==="19.2.3"&&u.devDependencies["@testing-library/dom"]==="10.4.1"&&u.devDependencies["@testing-library/react"]==="16.3.2"&&u.devDependencies.jsdom==="29.1.1"&&u.devDependencies.vitest==="4.1.10";if(!ok)process.exit(1)'
shasum -a 256 .node-version .npmrc package.json packages/domain/package.json packages/sdk/package.json packages/ui/package.json
lock_tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/dw-ts-lock.XXXXXX")"
case "$lock_tmp_dir" in "${TMPDIR:-/tmp}"/dw-ts-lock.*) ;; *) exit 1 ;; esac
mkdir "$lock_tmp_dir/home"
lock_snapshot="$lock_tmp_dir/pnpm-lock.first.yaml"
restore_lock_and_cleanup() { if test -f "$lock_snapshot"; then cp "$lock_snapshot" pnpm-lock.yaml; rm "$lock_snapshot"; fi; chmod -R u+w "$lock_tmp_dir" 2>/dev/null || true; rm -rf "$lock_tmp_dir"; }
trap restore_lock_and_cleanup EXIT HUP INT TERM
pnpm_isolated() { env -i PATH="$trusted_path" HOME="$lock_tmp_dir/home" XDG_CACHE_HOME="$verified_pnpm_metadata_cache" COREPACK_HOME="$verified_corepack_home" COREPACK_ENABLE_NETWORK=0 COREPACK_ENV_FILE=0 NPM_CONFIG_USERCONFIG=/dev/null NPM_CONFIG_GLOBALCONFIG=/dev/null npm_config_registry=https://registry.npmjs.org/ npm_config_always_auth=false npm_config_ignore_scripts=true npm_config_offline=true npm_config_store_dir="$verified_pnpm_store" npm_config_cache_dir="$verified_pnpm_metadata_cache" "$accepted_corepack_bin" pnpm "$@"; }
test "$(pnpm_isolated --version)" = "10.34.5"
test "$(pnpm_isolated config get registry)" = "https://registry.npmjs.org/"
pnpm_isolated install --lockfile-only --offline --ignore-scripts
! rg -n 'git\+|github:|file:|link:|_authToken:|_auth:' pnpm-lock.yaml
python3 - <<'PY'
from pathlib import Path
import re

lines = Path("pnpm-lock.yaml").read_text(encoding="utf-8").splitlines()
start = lines.index("packages:") + 1
end = lines.index("snapshots:")
entries: dict[str, list[str]] = {}
current: str | None = None
for line in lines[start:end]:
    if re.match(r"^  \S.*:$", line):
        current = line.strip()[:-1]
        entries[current] = []
    elif current is not None:
        entries[current].append(line)
missing = [name for name, block in entries.items() if not any("integrity:" in line for line in block)]
forbidden = [
    (name, line.strip())
    for name, block in entries.items()
    for line in block
    if re.search(r"(?:git\+|github:|file:|link:|_authToken:|_auth:)", line, re.I)
    or ("http://" in line)
    or ("https://" in line and "https://registry.npmjs.org/" not in line)
]
if not entries or missing or forbidden:
    raise SystemExit(f"lock provenance failure: entries={len(entries)} missing_integrity={missing} forbidden={forbidden}")
print(f"lock provenance verified: {len(entries)} registry package records with integrity")
PY
cp pnpm-lock.yaml "$lock_snapshot"
shasum -a 256 pnpm-lock.yaml
rm pnpm-lock.yaml
pnpm_isolated install --lockfile-only --offline --ignore-scripts
cmp "$lock_snapshot" pnpm-lock.yaml
cp "$lock_snapshot" pnpm-lock.yaml
pnpm_isolated install --frozen-lockfile --offline --ignore-scripts
cmp "$lock_snapshot" pnpm-lock.yaml
pnpm_isolated store status
pnpm_isolated list --depth Infinity --json
rm "$lock_snapshot"
chmod -R u+w "$lock_tmp_dir" 2>/dev/null || true
rm -rf "$lock_tmp_dir"
trap - EXIT HUP INT TERM
git diff --check
git status --short
```

Required retained evidence:

- accepted TS source SHA and independent verdict;
- Node distribution/binary, Corepack/pnpm executable and artifact tree,
  read-only store and metadata-cache inventories, exact registry, isolated
  config, manifest, lockfile, and direct/transitive provenance;
- exact root/package manifest assertions, workspace importers/specs, peer range,
  non-workspace integrity records, and forbidden-resolution scan;
- first/final lock SHA-256 digests and both `cmp` exit codes;
- frozen-install and repeated-resolution exit codes;
- exact changed-file inventory showing only the two governed files; and
- explicit zero source repair, zero package-proof, and zero E2E credit.

The plan-authoring task runs no command above. Its permitted checks are
documentation generation/checking, diff whitespace, candidate file inventory, and
Git scope inspection only.

## Review requirements

- Architecture verifies that the lock introduces no illegal package edge.
- Developer Experience verifies exact toolchain reproduction, frozen install, and
  actionable failure handling.
- Security verifies registry/integrity provenance, disabled lifecycle scripts,
  absence of credentials, and no dependency confusion/private registry surprise.
- Product/contract review confirms this is contributor proof only and enables no
  live capability or scenario completion.

Any finding that requires changing a manifest or source returns to the owning TS
cell. This plan may be amended only to clarify or strengthen lock proof.

## Idempotence, rollback, and recovery

Preflight and inspection are read-only. The lockfile-only and frozen-install
commands are rerunnable against the same accepted inputs; independent regeneration
and byte identity are the success criteria. The immediate trap restores the first
lock and removes only the validated `mktemp -d` contents on success, failure, or
interruption. On failure, preserve diagnostics and change no out-of-scope file.
Do not use broad cleanup, reset, or lock regeneration to hide drift.

Before integration, rollback is a reviewed revert of only `pnpm-lock.yaml` and
this plan's implementation update. There is no database, provider, user, registry,
or production state to recover.

## Rollout and handoff

There is no product rollout. Hand the exact independently accepted lock commit,
lock digest, provenance summary, full transcript, and changed-file list to the
coordinator. The coordinator may then dispatch `local:DW-M1-TS-VERIFY-001` from
that exact terminal lock commit. The acyclic downstream order is verification,
then private `local:DW-M1-FIXTURE-TS-CONSUMER-001`, then generated transport
`local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`. No consumer, bridge, web, or
product-demo work starts from lock proof alone.

## Outcomes & Retrospective

Pending execution and independent review. Completion must state the exact source
and lock commits, dependency provenance, command results, deviations, and whether
the verification cell may start. It must retain zero E2E completion.
