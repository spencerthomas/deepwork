---
exec_plan_id: DW-EXEC-M1-TS-VERIFY
title: Wave 1 TypeScript executable package proof and bounded repair
status: draft
superseded_by: null
owner: typescript-package-verification
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-001
supporting_feature_ids: [DW-FND-002, DW-FND-004, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-TS-VERIFY-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: medium
governed_paths: [packages/domain/**, packages/sdk/**, packages/ui/**, docs/exec-plans/active/DW-EXEC-M1-TS-VERIFY.md]
contract_gates: [SPIKE-HARNESS-ARCH-001]
decision_gates: [DEC-022, DEC-025, DEC-031, DEC-042]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, packages/domain/AGENTS.md, packages/sdk/AGENTS.md, packages/ui/AGENTS.md, docs/PLANS.md, docs/exec-plans/active/DW-EXEC-PROGRAM-CANONICAL.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/active/DW-EXEC-M1-TS-PACKAGES-SCAFFOLD.md, docs/exec-plans/active/DW-EXEC-M1-TS-LOCK.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-002-design-system-shell-and-demo-mode.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/SECURITY.md, docs/RELIABILITY.md]
scenario_ids: [AC-DW-FND-001-03, AC-DW-FND-002-06, AC-DW-FND-004-06, AC-DW-FND-005-01, AC-DW-QUAL-001-07, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-TS-LOCK-001]
blockers: []
---

# Wave 1 TypeScript executable package proof and bounded repair

Plan state: **prepared for independent review**. This draft is intentionally
unindexed and non-dispatchable. It becomes executable only after the terminal
first-lock cell is independently accepted.

## Purpose and observable result

Starting from the exact terminal lock commit, execute and, where necessary, make
bounded package-local repairs to the domain, SDK, and UI package contracts. Prove
format, lint, clean-source typecheck, tests, build, pack contents, JavaScript and
TypeScript clean-consumer use, intentional negative-boundary failures, global unit
network denial, and component-level accessibility behavior without changing the
shared lock.

This cell contributes package evidence to the stable scenario IDs in front
matter. It does not prove application composition, a product demo, a live
provider, a generated FastAPI client, complete WCAG qualification, or any v1 E2E
scenario. E2E completion credited by this cell is exactly zero.

## Context and orientation

The authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2` on
`external/planning/w1-ts-proof-consumers`. At that base the package source exists
but executable proof is intentionally absent. Candidate `1bf66e1` is
**REWORK REQUIRED** for three scanner-bypass families and one plan overstatement;
it is not accepted source. A later accepted TS source commit must first flow
through `local:DW-M1-TS-LOCK-001`.

The legal graph is `sdk -> domain` and `ui -> domain`. Domain is framework,
environment, provider, browser, Node, generated-wire, and I/O free. SDK is
browser-safe and has no UI/provider/server-secret dependency. UI is presentational
and has no SDK/network/route/fixture/generated/provider dependency.

## Scope

### In scope

- Run package-local and workspace-filtered format-check, lint, typecheck, unit,
  build, pack, architecture/boundary, and package-consumer commands.
- Repair only code, tests, scripts, styles, TypeScript configs, README/guidance,
  and dependency-neutral package metadata under `packages/domain/**`,
  `packages/sdk/**`, or `packages/ui/**`.
- Prove typecheck before any package build so stale or prebuilt `dist` cannot
  satisfy public package imports.
- Prove each package archive contains only declared public artifacts and no
  source/tests/scripts/lock/local path/workspace protocol leakage.
- Install packed archives into empty offline ESM consumers, import runtime public
  exports, and compile a TypeScript consumer against packed declarations.
- Prove intentional negative fixtures cover every emitted boundary rule and
  include lexical/import-expression bypass families rather than only obvious
  static imports.
- Prove unexpected external networking fails across ordinary unit suites.
- Prove the initial UI component's semantic names, state text, action gating,
  keyboard-native action, unsafe-content rendering, focus styles, non-color
  meaning, reduced-motion/forced-colors posture, long content, and narrow reflow
  at component level.
- Keep this living plan current.

### Non-goals

- Editing `pnpm-lock.yaml`, root/shared manifests/config, Turbo, workspace files,
  architecture tools, generated docs/contracts, apps, fixtures, adapter tests,
  indexes, program/umbrella plans, product specs, or `docs/plans/**`.
- Adding/updating/removing any dependency, peer, optional dependency, workspace
  importer/spec, package-manager config, or lifecycle hook. No such delta may be
  committed by this cell. If one is needed, abort and return this plan to draft;
  a separately reviewed manifest/lock plan must receive a stable ID, become an
  explicit terminal front-matter dependency, and pass fresh independent review
  before a successor verification attempt.
- Implementing a generated client, real transport, provider SDK, endpoint, cursor,
  credential, fixture consumer, app route, product demo, Storybook host, browser
  E2E, publication, or deployment.
- Claiming automated component tests alone meet full WCAG 2.2 AA release
  qualification.

### Permissions and risk boundary

- Committable paths are exactly the four governed entries in front matter.
- The terminal `pnpm-lock.yaml` is read-only. Any byte change stops the cell.
- Package installation is offline and uses only the accepted frozen lock with
  lifecycle scripts disabled. Clean consumers use only packed local archives and
  exact packages already present in the accepted read-only store and metadata
  cache. Exact Node/Corepack paths and their recorded aggregate inventories are
  rechecked before Corepack's first invocation, with Corepack networking disabled.
- A reviewed Node preload denies external socket/HTTP/fetch/WebSocket access for
  tests, build, pack, and consumer commands. A deliberate outbound-attempt
  negative proves the guard is active. Credential-bearing environment variables
  are absent, and pack/install/prepare/prepack/postpack hooks are forbidden or
  explicitly disabled.
- External/provider network, credentials, production data, publish, deploy,
  signing, push, merge, migration, and destructive operations are prohibited.
- Repairs must address a reproduced failure and preserve public/package
  boundaries. No check may be weakened or bypass fixture removed to obtain green.
- Independent architecture, TypeScript/DX, security, and accessibility review are
  required. The author cannot approve the result.

## Authoritative sources and prerequisites

- Terminal prerequisite: `local:DW-M1-TS-LOCK-001` at an exact independently
  accepted full SHA with frozen/no-drift evidence.
- Source prerequisite: that lock commit must descend from a fresh accepted
  `local:DW-M1-TS-SCAFFOLD`, not the rework-required `1bf66e1`.
- Product/quality owners: `DW-FND-001`, `DW-FND-002`, `DW-FND-004`,
  `DW-FND-005`, and `DW-QUAL-001`.
- Architecture/engineering: root and package `AGENTS.md`, `ARCHITECTURE.md`,
  `docs/design-docs/engineering/conventions.md`, and decisions
  `DEC-022/025/031/042`.
- `SPIKE-HARNESS-ARCH-001` remains open. Package-local green and deliberate
  negative proof is its deterministic fallback; this cell cannot close or modify
  the global harness.

## Interfaces and invariants

### Domain

- Public source/thread/run identities remain source-qualified and immutable.
- Capability state, safe reason, evidence class, observation, adapter version,
  and contract version are runtime-validated where constructed from unknown
  input. Invalid timestamp/calendar forms and out-of-vocabulary values fail
  closed.
- Runtime vocabulary arrays and returned evidence/key objects cannot be mutated to
  alter later behavior.
- No framework, browser, Node, provider, network, environment, SDK, UI, fixture,
  or generated transport enters shipped source.

### SDK

- Query, mutation, and stream ports remain distinct and framework-neutral.
- Unknown/unverified capabilities return a safe unavailable result without a
  request. Retry posture cannot encourage blind retry of an unknown contract.
- No UI, React, Next.js, provider, Node-only, environment-secret, or raw live
  transport dependency is introduced.

### UI

- UI consumes domain public values and React only.
- Unknown/unavailable capability states never render an enabled action.
- Accessible structure does not hard-code a document heading level that a caller
  cannot compose safely; names and semantic hierarchy remain caller-compatible.
- User strings render as text; raw executable HTML is absent.

### Package proof

- Typecheck runs in a clean tree before build and must not self-resolve to stale
  `dist`.
- Boundary scanners must reject static imports, re-exports, dynamic imports,
  comment/whitespace-separated forms, deep/self imports, and raw forbidden APIs as
  applicable. Tests must prove the scanner itself cannot be bypassed by the known
  lexical families.
- Unit network denial covers all three package suites, not one mocked `fetch`
  call.
- Packed consumers compile TypeScript and execute JavaScript using only tarballs
  and public exports.
- The accepted lock remains byte-identical throughout.

## State matrix

| State | Required behavior | Evidence or recovery |
|---|---|---|
| Lock dependency nonterminal | Do not install or execute. | Return to coordinator. |
| Dirty tree or pre-existing `dist` | Stop before typecheck. | Start a clean worktree; do not broadly delete user files. |
| Frozen install rejects lock | Stop; do not edit lock/manifests. | Return exact dependency failure to lock/source owners. |
| Format/lint/type failure | Reproduce package-locally. | Repair only governed package files and rerun full affected matrix. |
| Boundary green-source failure | Fail with rule, file, legal destination, and command. | Move code to legal owner; do not suppress rule. |
| Negative fixture unexpectedly passes | Treat as scanner bypass. | Strengthen scanner and retain an intentional regression fixture. |
| Unit attempts external network | Fail deterministically. | Replace with owned fake/fixture or explicit integration lane; no allow-all. |
| Build succeeds but typecheck failed | Cell remains failed. | Build is not type proof. |
| Archive leaks private/workspace content | Fail package-check. | Correct manifest/export/files boundary without lock change. |
| JS consumer passes but TS consumer fails | Cell remains failed. | Repair declarations/exports or consumer harness in governed paths. |
| Accessibility assertion fails | Treat as component regression. | Repair semantics/styles/tests; do not claim full release qualification. |
| Dependency/importer/lifecycle change appears necessary | Abort; commit no manifest delta. | Create a stable-ID manifest/lock plan, amend this dependency list, and obtain fresh review before a successor attempt. |
| All package proof passes | Record exact transcript and diff. | Stop at fresh independent review. |

## Milestones

### Milestone 1 — Establish clean executable preconditions

Verify the terminal lock SHA, clean worktree, exact Node/pnpm versions, absence of
package build output, frozen install, and lock byte identity.

Acceptance:

- No `dist` or `.tsbuildinfo` can influence the first typecheck.
- Offline frozen install succeeds without lifecycle scripts or lock change.
- The external-network guard's deliberate attempt fails before package proof.
- Package-local reproduction commands are available through accepted manifests.

### Milestone 2 — Prove formatting, lint, clean typecheck, and boundaries

Run format-check, lint, typecheck-before-build, and package boundary checks for all
three packages. Exercise every deliberate negative fixture and known lexical
bypass family.

Acceptance:

- All positive source checks pass.
- Every intentional negative fixture fails with all declared stable rule codes.
- Emitted rule-code inventory equals covered rule-code inventory.
- Comment, whitespace, re-export, and dynamic/import-expression bypass cases are
  retained and fail.

### Milestone 3 — Prove tests, network denial, and accessibility

Run package unit suites with external networking denied and targeted UI
accessibility/component assertions.

Acceptance:

- Domain identity/capability/view-state failure cases pass, including two-source
  thread and run collisions.
- SDK unavailable/mapping/port tests make no request for unknown capabilities and
  classify failure/retry honestly.
- The named diagnostics-sanitization regression feeds credential-shaped,
  control-character, markup-shaped, and oversized sentinels and proves none
  appears in captured output.
- All three ordinary unit suites fail on an injected external network attempt.
- Tests, build, pack, and clean-consumer commands run with the same external
  network guard and credential-free environment.
- UI semantic/action/unsafe-content/long-content/focus/contrast/motion/reflow
  component checks pass, explicitly short of full browser/manual WCAG sign-off.

### Milestone 4 — Prove build, pack, and empty consumers

Build packages in dependency order, inspect tarballs, install only tarballs into
empty offline consumers, execute public JavaScript imports, and compile minimal
TypeScript consumers.

Acceptance:

- Package builds and packs succeed through declared public exports.
- Package manifests contain no install/prepare/prepack/postpack lifecycle hook,
  and pack runs with lifecycle execution disabled.
- Tarballs contain no private source/tests/scripts/lock/workspace protocol/local
  path or undeclared artifact.
- Domain, SDK, and UI consumers compile using TypeScript `7.0.2` from the accepted
  offline store; runtime imports then succeed.
- UI consumer resolves React peer/types and CSS/preset entry points from declared
  package metadata.

### Milestone 5 — Independent executable review

Rerun the complete matrix after any repair, verify the lock and path scope, record
scenario contribution limits, commit only governed files, and stop.

Acceptance:

- Architecture, DX/TypeScript, security, and accessibility reviewers accept the
  exact commit or return bounded rework.
- Lock SHA-256 is unchanged from the terminal lock cell.
- No application, fixture parity, generated-client, provider, or E2E completion
  is claimed.

## Progress

- [x] 2026-07-23 AEST — Drafted from the supplied base without installing or
  executing package tooling.
- [x] 2026-07-23 AEST — Recorded `1bf66e1` as rework-required, not terminal.
- [x] 2026-07-23 AEST — Initial exact three-file candidate received architecture,
  DX, and security `REWORK REQUIRED` verdicts and product/contract `ACCEPT`;
  amendments remain limited to these three plan files.
- [ ] Independent plan review accepts the exact draft candidate.
- [ ] Terminal lock commit is supplied and verified.
- [ ] Milestones 1-5 complete in an authorized verification worktree.

## Surprises & Discoveries

- 2026-07-23 AEST — Prior review showed exact rule-code counts can still miss
  scanner bypass families. Consequence: this plan requires executable
  grammar-family negative cases, not only a declared-code matrix.
- 2026-07-23 AEST — Prior clean-consumer scripts executed JavaScript but did not
  compile a TypeScript consumer. Consequence: runtime import and declaration
  consumption are separate required gates.
- 2026-07-23 AEST — Package-local typecheck can accidentally resolve another
  workspace package from stale `dist`. Consequence: first typecheck runs before
  build in a clean tree and must prove source-based resolution.

## Decision Log

- 2026-07-23 AEST — Decision: allow bounded package-local repair after a failing
  executable check, but forbid lock/root changes. Rationale: the source cell
  cannot honestly predict every executable failure, while shared dependency
  resolution needs separate ownership. Consequence: repairs stay reviewable and a
  dependency delta stops this cell.
- 2026-07-23 AEST — Decision: component accessibility proof is required but earns
  no full WCAG or E2E credit. Rationale: jsdom/component assertions can prove
  semantics and contract regressions but not real browser, viewport, contrast, or
  assistive-technology qualification. Consequence: application/release cells keep
  those gates.

## Detailed implementation approach

1. Start from an exact reviewed verification-dispatch commit descending from the
   terminal lock. Compare the lock blob directly with that terminal commit and
   record its digest.
2. Prove the reviewed Node external-network preload blocks an injected attempt
   before DNS/socket creation. Run an offline frozen install with lifecycle
   scripts disabled and prove the lock is unchanged.
3. Run typecheck before build, then format-check, lint, architecture checks,
   deliberate negative fixtures, unit/network/accessibility tests.
4. Reproduce each failure with the narrow package command. Repair only governed
   package files, add a regression case, and rerun every affected and downstream
   package check.
5. Build, pack, inspect, install into offline empty consumers, compile TypeScript,
   and execute JavaScript public imports.
6. Rerun the full matrix after repairs, update this plan, commit only governed
   paths, and validate the committed candidate through terminal-lock ancestry,
   exact lock-blob comparison, exact changed-file scope, and a clean worktree.
   Stop for fresh review.

## Validation and proof

Representative required commands from repository root:

```text
set -euo pipefail
terminal_lock_commit="<accepted full 40-character SHA>"
reviewed_verify_dispatch_commit="<reviewed verification-plan dispatch SHA>"
test "${#terminal_lock_commit}" -eq 40
git cat-file -e "${terminal_lock_commit}^{commit}"
test "${#reviewed_verify_dispatch_commit}" -eq 40
git cat-file -e "${reviewed_verify_dispatch_commit}^{commit}"
git merge-base --is-ancestor "$terminal_lock_commit" "$reviewed_verify_dispatch_commit"
test "$(git rev-parse HEAD)" = "$reviewed_verify_dispatch_commit"
test "$(git status --porcelain)" = ""
test -z "${NPM_TOKEN+x}${NODE_AUTH_TOKEN+x}"
git show "$terminal_lock_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
shasum -a 256 pnpm-lock.yaml
test ! -d packages/domain/dist
test ! -d packages/sdk/dist
test ! -d packages/ui/dist
! rg -n '"(preinstall|install|postinstall|prepare|prepack|postpack)"\s*:' packages/domain/package.json packages/sdk/package.json packages/ui/package.json
network_guard="$PWD/packages/domain/tests/support/deny-external-network.mjs"
network_probe="$PWD/packages/domain/tests/support/probe-external-network-denial.mjs"
test -f "$network_guard"
test -f "$network_probe"
accepted_node_bin="<exact Node binary recorded by terminal lock evidence>"
accepted_corepack_bin="<exact Corepack binary recorded by terminal lock evidence>"
accepted_corepack_home="<absolute verified Corepack cache recorded by terminal lock cell>"
accepted_offline_store="<absolute verified pnpm store recorded by terminal lock cell>"
accepted_metadata_cache="<absolute verified pnpm metadata cache recorded by terminal lock cell>"
expected_node_sha256="<terminal lock evidence SHA-256>"
expected_corepack_sha256="<terminal lock evidence SHA-256>"
expected_corepack_tree_sha256="<terminal lock evidence aggregate SHA-256>"
expected_store_tree_sha256="<terminal lock evidence aggregate SHA-256>"
expected_metadata_tree_sha256="<terminal lock evidence aggregate SHA-256>"
test -x "$accepted_node_bin"
test -x "$accepted_corepack_bin"
test -d "$accepted_corepack_home"
test -d "$accepted_offline_store"
test -d "$accepted_metadata_cache"
test ! -w "$accepted_offline_store"
test ! -w "$accepted_metadata_cache"
for digest in "$expected_node_sha256" "$expected_corepack_sha256" \
  "$expected_corepack_tree_sha256" "$expected_store_tree_sha256" \
  "$expected_metadata_tree_sha256"; do test "${#digest}" -eq 64; done
test "$(shasum -a 256 "$accepted_node_bin" | awk '{print $1}')" = "$expected_node_sha256"
test "$(shasum -a 256 "$accepted_corepack_bin" | awk '{print $1}')" = "$expected_corepack_sha256"
test "$(find "$accepted_corepack_home" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_corepack_tree_sha256"
test "$(find "$accepted_offline_store" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_store_tree_sha256"
test "$(find "$accepted_metadata_cache" -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = "$expected_metadata_tree_sha256"
trusted_path="$(dirname "$accepted_node_bin"):/usr/bin:/bin"
test "$(env -i PATH="$trusted_path" "$accepted_node_bin" --version)" = "v24.18.0"
verify_tmp="$(mktemp -d "${TMPDIR:-/tmp}/dw-ts-verify.XXXXXX")"
case "$verify_tmp" in "${TMPDIR:-/tmp}"/dw-ts-verify.*) ;; *) exit 1 ;; esac
mkdir "$verify_tmp/home"
cleanup_ts_verify_proof() {
  chmod -R u+w "$verify_tmp" 2>/dev/null || true
  rm -rf "$verify_tmp"
}
trap cleanup_ts_verify_proof EXIT HUP INT TERM
env -i PATH="$trusted_path" HOME="$verify_tmp/home" \
  COREPACK_HOME="$accepted_corepack_home" COREPACK_ENABLE_NETWORK=0 \
  COREPACK_ENV_FILE=0 NODE_OPTIONS="--import=$network_guard" \
  "$accepted_node_bin" "$network_probe"
pnpm_offline_guarded() {
  env -i PATH="$trusted_path" HOME="$verify_tmp/home" \
    XDG_CACHE_HOME="$accepted_metadata_cache" \
    COREPACK_HOME="$accepted_corepack_home" \
    COREPACK_ENABLE_NETWORK=0 COREPACK_ENV_FILE=0 \
    NODE_OPTIONS="--import=$network_guard" \
    NPM_CONFIG_USERCONFIG=/dev/null NPM_CONFIG_GLOBALCONFIG=/dev/null \
    NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
    NPM_CONFIG_ALWAYS_AUTH=false NPM_CONFIG_OFFLINE=true \
    NPM_CONFIG_IGNORE_SCRIPTS=true NPM_CONFIG_STORE_DIR="$accepted_offline_store" \
    NPM_CONFIG_CACHE_DIR="$accepted_metadata_cache" TMPDIR="$verify_tmp" \
    "$accepted_corepack_bin" pnpm "$@"
}
test "$(pnpm_offline_guarded --version)" = "10.34.5"
pnpm_offline_guarded install --frozen-lockfile --offline --ignore-scripts
git show "$terminal_lock_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
pnpm_offline_guarded --filter @deepwork/domain typecheck
pnpm_offline_guarded --filter @deepwork/sdk typecheck
pnpm_offline_guarded --filter @deepwork/ui typecheck
pnpm_offline_guarded --filter @deepwork/domain format-check
pnpm_offline_guarded --filter @deepwork/sdk format-check
pnpm_offline_guarded --filter @deepwork/ui format-check
pnpm_offline_guarded --filter @deepwork/domain lint
pnpm_offline_guarded --filter @deepwork/sdk lint
pnpm_offline_guarded --filter @deepwork/ui lint
pnpm_offline_guarded --filter @deepwork/domain check-architecture
pnpm_offline_guarded --filter @deepwork/sdk check-architecture
pnpm_offline_guarded --filter @deepwork/ui check-architecture
pnpm_offline_guarded --filter @deepwork/domain test
pnpm_offline_guarded --filter @deepwork/sdk test
pnpm_offline_guarded --filter @deepwork/ui test
pnpm_offline_guarded --filter @deepwork/domain exec vitest run \
  tests/security/diagnostics-sanitization.test.ts \
  >"$verify_tmp/diagnostics-sanitization.txt" 2>&1
! rg -n 'dw_secret_NEVER_ECHO|<script>never-echo</script>|CONTROL_NEVER_ECHO|OVERSIZED_NEVER_ECHO' \
  "$verify_tmp/diagnostics-sanitization.txt"
pnpm_offline_guarded --filter @deepwork/domain build
pnpm_offline_guarded --filter @deepwork/sdk build
pnpm_offline_guarded --filter @deepwork/ui build
pnpm_offline_guarded --filter @deepwork/domain package-check
pnpm_offline_guarded --filter @deepwork/sdk package-check
pnpm_offline_guarded --filter @deepwork/ui package-check
git show "$terminal_lock_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check
candidate_commit="<full SHA after committing only governed verification files>"
test "${#candidate_commit}" -eq 40
git cat-file -e "${candidate_commit}^{commit}"
test "$(git rev-parse HEAD)" = "$candidate_commit"
git merge-base --is-ancestor "$terminal_lock_commit" "$candidate_commit"
git show "$terminal_lock_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
for manifest in packages/domain/package.json packages/sdk/package.json packages/ui/package.json; do
  git show "$terminal_lock_commit:$manifest" >"$verify_tmp/$(basename "$(dirname "$manifest")").package.json"
done
env -i PATH="$trusted_path" HOME="$verify_tmp/home" \
  NODE_OPTIONS="--import=$network_guard" \
  "$accepted_node_bin" - "$verify_tmp" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");
const tmp = process.argv[2];
const fields = [
  "dependencies", "devDependencies", "optionalDependencies", "peerDependencies",
  "peerDependenciesMeta", "engines", "packageManager",
];
for (const name of ["domain", "sdk", "ui"]) {
  const before = JSON.parse(fs.readFileSync(path.join(tmp, `${name}.package.json`), "utf8"));
  const after = JSON.parse(fs.readFileSync(`packages/${name}/package.json`, "utf8"));
  for (const field of fields) {
    if (JSON.stringify(before[field] ?? null) !== JSON.stringify(after[field] ?? null)) {
      throw new Error(`${name}: forbidden manifest delta in ${field}`);
    }
  }
  for (const hook of ["preinstall", "install", "postinstall", "prepare", "prepack", "postpack"]) {
    if ((before.scripts?.[hook] ?? null) !== (after.scripts?.[hook] ?? null)) {
      throw new Error(`${name}: forbidden lifecycle delta in ${hook}`);
    }
  }
}
NODE
git diff --name-only "$reviewed_verify_dispatch_commit" "$candidate_commit" \
  | awk '
      /^packages\/domain\// { next }
      /^packages\/sdk\// { next }
      /^packages\/ui\// { next }
      /^docs\/exec-plans\/active\/DW-EXEC-M1-TS-VERIFY\.md$/ { next }
      { bad = 1; print > "/dev/stderr" }
      END { exit bad }
    '
test -z "$(git status --porcelain)"
```

The accepted implementation may refine package-local commands when the source
rework changes manifest scripts, but it must retain every distinct proof category:
format, lint, clean typecheck, positive and negative boundaries, tests, global
network denial, component accessibility, build, pack inspection, JavaScript
consumer execution, TypeScript consumer compilation, and the named sanitized
diagnostics regression with raw-sentinel absence assertion.

Required retained evidence:

- terminal source and lock SHAs, independent verdicts, and lock digest;
- exact command/exit-code transcript before and after repairs;
- emitted versus covered boundary-rule inventory and named scanner-bypass cases;
- sanitized diagnostic regressions proving credential-shaped, control-character,
  markup-shaped, and oversized untrusted input is absent from bounded output;
- package/unit network-denial evidence;
- the accepted offline store identity, disabled lifecycle-hook audit, and injected
  guard self-test proving rejection before DNS/socket creation;
- typecheck-before-build evidence;
- tarball inventory and empty-consumer JavaScript/TypeScript results;
- component accessibility assertions and explicit manual/browser deferral;
- exact changed files and unchanged lock; and
- bounded scenario contributions with zero E2E completion.

## Review requirements

- Architecture: package direction, public exports, scanner completeness, no
  generated/provider/fixture leakage.
- Developer Experience/TypeScript: clean source resolution, reproducible commands,
  build/pack/type consumer proof, actionable diagnostics.
- Security: global no-network unit posture, archive content, dependency/lock
  integrity, untrusted content, no secret/provider boundary.
- Accessibility/product UI: semantic composition, action gating, names, focus,
  state communication, non-color meaning, motion/contrast/reflow contract, and
  honest proof limits.
- Product/contract: stable scenario contribution only; no generated/live/app/E2E
  overstatement.

## Idempotence, rollback, and recovery

Checks are rerunnable from the same accepted lock. The validated temporary
directory has an immediate cleanup trap, and package/consumer scripts must create
and clean only descendants of that directory on success, failure, or interruption.
Repairs are additive or narrow and must retain regression tests. A failed command
preserves sanitized diagnostics; do not edit root config, lock, or tests to
conceal it. No dependency/importer/lifecycle delta may be committed here. If one
is needed, abort, return the plan to draft, create a stable-ID manifest/lock cell,
amend front matter to depend on its exact terminal result, and obtain fresh
independent review before a successor attempt.

Before integration, rollback reverts only this cell's package/plan diff. Packed
archives and consumer directories must be created under exact temporary
directories and removed only by their owning scripts. There is no production,
provider, database, or registry state.

## Rollout and handoff

There is no production rollout. Hand the exact independently accepted verification
commit, unchanged lock digest, transcripts, archive/consumer evidence, reviewer
verdicts, and changed-file list to the coordinator. Only then may a fixture
consumer or product-demo cell treat TypeScript executable proof as terminal.

## Outcomes & Retrospective

Pending execution and independent review. Completion must distinguish authored
source, repaired source, commands actually run, component-level accessibility,
deferred generated/client/application proof, and zero E2E completion.
