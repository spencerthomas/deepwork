---
exec_plan_id: DW-EXEC-M1-FIXTURE-TS-CONSUMER
title: Wave 1 language-neutral fixture TypeScript consumer proof
status: draft
superseded_by: null
owner: typescript-fixture-conformance
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-004
supporting_feature_ids: [DW-FND-001, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-FIXTURE-TS-CONSUMER-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: 9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2
last_verified_commit: null
risk: medium
governed_paths: [packages/domain/**, packages/sdk/**, internal/adapter-tests/**, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-TS-CONSUMER.md]
contract_gates: [SPIKE-STREAM-001]
decision_gates: [DEC-022, DEC-023, DEC-025, DEC-031, DEC-035]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, packages/domain/AGENTS.md, packages/sdk/AGENTS.md, docs/PLANS.md, docs/exec-plans/active/DW-EXEC-PROGRAM-CANONICAL.md, docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md, docs/exec-plans/active/DW-EXEC-M1-TS-VERIFY.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md, docs/SECURITY.md, docs/RELIABILITY.md]
scenario_ids: [AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-004-06, AC-DW-FND-005-01, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-FIXTURE-CONTRACT, local:DW-M1-TS-VERIFY-001]
blockers: []
---

# Wave 1 language-neutral fixture TypeScript consumer proof

Plan state: **prepared for independent review**. This plan is a downstream,
non-dispatchable draft. It requires both an independently accepted fixture corpus
and terminal TypeScript executable verification.

## Purpose and observable result

Consume the exact accepted `internal/fixtures/product-demo/**` corpus read-only
from a private TypeScript conformance project. Prove that public domain semantics
and SDK mapping seams can preserve source-qualified identity, deterministic order,
duplicate handling, partial failure, safe unknown/malformed classification, and
capability honesty across language-neutral cases.

The fixture corpus remains a fixture-owned schema, not the `/api/v1` or normalized
production wire. This cell contributes bounded evidence to the stable scenario
IDs in front matter and earns zero v1 E2E completion. It does not prove live
parity, product-demo integration, a generated client, provider transport, or a
browser journey.

## Context and orientation

The plan-authoring base is
`9e9dd1cbae54c315d726ca5debf0f2d76bb6c4a2` on branch
`external/planning/w1-ts-proof-consumers`. Fixture successor
`75228c07dfa867f677fc176c1bb2423c7113aff8` is `REWORK REQUIRED`; it is not
accepted and cannot satisfy `local:DW-M1-FIXTURE-CONTRACT`. TypeScript candidate
`1bf66e1` is also rework-required and likewise cannot satisfy the TS chain.

`internal/fixtures/product-demo/**` is owned by the fixture corpus cell.
`DEC-035` requires Python source conformance to remain with `apps/api` and
TypeScript DTO/reducer/client conformance to live in
`internal/adapter-tests/**`. This plan edits neither the corpus nor Python/API
code.

## Scope

### In scope

- Create a manifest-free private TypeScript harness under
  `internal/adapter-tests/**` using only tooling and package archives already
  accepted by the terminal TypeScript verification cell.
- Read the exact accepted product-demo corpus, schemas, manifests, cases,
  negative matrix, hashes, and deterministic evidence without modifying them.
- Add only the smallest domain reducer/selector/event semantics and SDK mapping
  seam repairs required by accepted language-neutral assertions.
- Rerun UI checks as read-only downstream evidence after any domain repair;
  `packages/ui/**` is never committable in this cell.
- Exercise start, content, tool, ordered interrupt presentation data, checkpoint
  observation, reconnect boundary, replay dedupe, logical delay, completion,
  unknown, malformed classification, partial failure, and source-collision cases.
- Add reducer/mapping failure cases for duplicate/out-of-order records, invalid
  source/run qualification, capability/evidence mismatch, malformed values,
  unknown records, unsafe terminal inference, interrupt misalignment, and partial
  source failure.
- Use only public `@deepwork/domain` and `@deepwork/sdk` entry points from the
  adapter-test project; no deep source imports.
- Keep all package manifests, workspace importer metadata, dependency fields,
  peer ranges, lifecycle scripts, and `pnpm-lock.yaml` byte-identical to the
  terminal TypeScript verification input.
- Reach independent acceptance and a Coordinator-recorded terminal handoff
  before `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001` may generate OpenAPI or SDK
  transport in the overlapping SDK/adapter-test paths.
- Keep this living plan current.

### Non-goals

- Editing `internal/fixtures/product-demo/**`, `apps/api/**`, `packages/ui/**`,
  root manifests/config, `pnpm-lock.yaml`, generated files, apps, architecture
  tools, indexes, program/umbrella plans, product specs, or `docs/plans/**`.
- Treating fixture envelope fields, case categories, logical sequence, or expected
  assertions as the production API/event wire.
- Hand-writing a generated OpenAPI client, inventing a FastAPI DTO, endpoint,
  provider discriminator, cursor, resume call, HITL submission, checkpoint fork,
  or live success response.
- Claiming Python/API conformance, full application parity, live-contract parity,
  network isolation outside this TypeScript test project, accessibility, browser
  behavior, or E2E completion.
- Generating `docs/generated/openapi.json`, adding
  `@deepwork/sdk/product-demo`, or implementing any public API transport. Those
  belong only to the later API-to-SDK bridge after this cell is terminal.
- Installing a new dependency, publishing, deploying, provider access, push,
  merge, or release.

### Permissions and risk boundary

- Committable paths are exactly the four governed entries in front matter.
- The accepted fixture tree and terminal `pnpm-lock.yaml` are read-only.
- No external/provider network, credential, production data, private registry,
  lifecycle script, publish, deployment, signing, migration, push, merge, or
  destructive operation is permitted.
- Existing accepted locked dependencies may be used only through an offline,
  frozen, lifecycle-disabled install. Exact Node/Corepack paths and accepted
  Corepack/store/metadata-cache inventories are rechecked before Corepack's first
  invocation, with Corepack networking disabled.
- No manifest, dependency, peer, workspace-importer, or lifecycle-script delta
  may be committed by this cell. If one is genuinely necessary, abort this cell,
  create a separately reviewed stable-ID manifest/lock cell, amend this plan's
  dependency list to that terminal cell, obtain fresh review, and only then
  resume. Never edit a manifest or the lock opportunistically here.
- Architecture, TypeScript/DX, security, and product/contract review are required.
  The author cannot approve or dispatch the result.

## Authoritative sources and prerequisites

- `local:DW-M1-FIXTURE-CONTRACT` must be terminal-success at an exact independently
  accepted full SHA. Candidate `75228c07dfa867f677fc176c1bb2423c7113aff8`
  is `REWORK REQUIRED` and remains nonterminal.
- `local:DW-M1-TS-VERIFY-001` must be terminal-success at an exact independently
  accepted full SHA and lock digest.
- The dependency graph is acyclic:
  `TS source -> TS lock -> TS verification -> private fixture TS consumer ->
  API/SDK bridge`, while the fixture corpus independently reaches acceptance
  before joining at this cell and the final-wire API consumer joins only at the
  later bridge.
- Product/contract authority is `DW-FND-004`; supporting constraints come from
  `DW-FND-001`, `DW-FND-005`, `DW-QUAL-001`, `DEC-022/023/025/031/035`, and the
  accepted fixture corpus.
- `SPIKE-STREAM-001` remains open. Production transport/replay/hydration stays
  unavailable; fixture semantics cannot close the spike.

## Interfaces and invariants

### Read-only corpus boundary

- Tests verify the accepted corpus commit and digest before consumption.
- Every repository package-manifest path and byte, `.npmrc`, workspace
  configuration, and terminal lock is anchored to the terminal TypeScript
  verification commit; every nested `internal/adapter-tests/**/package.json` is
  forbidden. The private harness contains only directories and regular files;
  symlinks and special files are rejected before execution and at final proof.
- Corpus validation runs first using its own accepted standard-library checker.
- Git diff and digest checks prove the fixture tree is byte-unchanged after all
  TypeScript commands.
- The adapter-test project may load JSON as test data. Shipped domain/SDK source
  must not import `internal/fixtures` or depend on fixture paths at runtime.

### Language-neutral parity

- The TypeScript harness derives assertions from the corpus's explicit expected
  values rather than duplicating expected order/terminal/capability logic in a
  second handwritten table.
- Source/thread/run keys remain qualified even when two synthetic sources reuse
  external thread and run strings.
- Replay duplicates reduce exactly once; out-of-order or conflicting records fail
  with stable safe diagnostics.
- Logical-delay visibility uses fixture ticks only; no wall clock, sleep, timeout,
  or performance claim is permitted.
- Partial failure retains healthy source results and a source-qualified safe
  error. Unknown/permission/gated capability states never become success.

### Reducer and mapping failure behavior

- Reducers are deterministic, immutable, and total over accepted domain inputs.
- Malformed fixture envelopes fail in the private decoder before reducer entry.
- Unknown safe records remain observable as unknown; they do not invent a public
  event discriminator.
- Completion requires an explicit accepted terminal record. Disconnect, absent
  data, elapsed time, or fixture end-of-file cannot infer terminal success.
- Ordered interrupt request/config arrays remain aligned and repeated action names
  remain ordered. This cell does not create or submit decisions.
- Failure output contains stable safe codes and fixture case IDs, not raw
  untrusted content or secrets.

### Generated/client-boundary honesty

- FastAPI/Pydantic/OpenAPI remains the future production wire authority.
- If no accepted generated client exists, this cell asserts that absence and uses
  a private test-only fixture decoder feeding public domain/SDK seams.
- No `packages/sdk/src/generated/**`, public route, provider cursor, or guessed DTO
  is created from corpus JSON.
- A passing private fixture mapper proves only that the seam can consume accepted
  language-neutral cases. It is not generated-client or live adapter parity.
- This plan's issue is exactly
  `local:DW-M1-FIXTURE-TS-CONSUMER-001`. The inverted
  `local:DW-M1-TS-FIXTURE-CONSUMER-001` alias is invalid. Public generation is
  owned by downstream `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`, never this
  issue.

## State matrix

| State | Required behavior | Evidence or recovery |
|---|---|---|
| Fixture candidate still under review | Do not consume it. | Await exact independent acceptance or bounded rework. |
| TS verify nonterminal | Do not install or author executable claims. | Await terminal verification SHA and lock digest. |
| Accepted corpus validation fails | Stop; do not repair corpus. | Return exact case/rule/digest failure to fixture owner. |
| Fixture bytes change during work | Fail the cell. | Revert only the unauthorized consumer-caused mutation and restart from accepted corpus. |
| Manifest/workspace importer delta appears | Fail before proof. | Remove it; this cell is manifest-free. |
| Dependency addition is needed | Abort this cell. | Create a stable-ID manifest/lock cell, amend dependencies here, and obtain fresh review before resuming. |
| External network is attempted | Fail the command and cell. | Preserve the sanitized target class and command; do not retry online. |
| Lifecycle script is discovered or invoked | Fail the command and cell. | Escalate as a dependency/provenance violation. |
| Fixture has ignored/untracked output, a symlink, or a special file | Fail the cell. | Return the exact relative path and safe type to the fixture owner. |
| Positive case maps/reduces incorrectly | Fail with case ID and safe diagnostic. | Repair only domain/SDK/internal consumer paths and add regression coverage. |
| Negative case passes | Fail closed. | Strengthen decoder/mapper/reducer without weakening corpus. |
| Unknown/malformed input | Preserve unknown or reject safely as declared. | Never cast or promote it to success. |
| Partial source failure | Keep healthy source projection and qualified error. | No whole-result collapse when separable. |
| Generated client absent | State it explicitly. | Use private fixture decoder; claim no generated parity. |
| API/SDK bridge starts before this cell is terminal | Block generation and path transfer. | Require exact accepted commit, independent verdict, and Coordinator terminal handoff first. |
| All consumer proof passes | Record corpus/lock digests and exact scope. | Stop at independent review with zero E2E credit. |

## Milestones

### Milestone 1 — Freeze accepted inputs

Record terminal fixture and TS verification SHAs, fixture corpus digest, lock
digest, accepted case/rule inventory, and a clean read-only baseline.

Acceptance:

- Both front-matter dependencies are terminal and independently accepted.
- Corpus validator passes twice with identical deterministic output.
- Fixture tree and lock digests are recorded before TypeScript work.

### Milestone 2 — Establish the private consumer boundary

Create a manifest-free `internal/adapter-tests/**` harness with package-local
configuration, its own boundary checker, and public domain/SDK imports. Add a
private fixture decoder that validates only the accepted fixture format and
cannot ship as an SDK/generated client.

Acceptance:

- No new workspace importer or package-manifest delta exists.
- No shipped domain/SDK source imports the corpus.
- No deep package import, provider type, endpoint, cursor, or generated directory
  is introduced.
- The harness's package-local boundary checker and deliberate negative fixtures
  reject deep/private imports, illegal package direction, shipped fixture
  imports, generated-wire invention, and provider/runtime coupling.
- Offline frozen install succeeds without lock change or new dependency.

### Milestone 3 — Prove positive language-neutral parity

Consume the accepted positive cases and assert source qualification, order,
dedupe, logical-delay visibility, terminal authority, unknown preservation,
partial failure, and capability honesty.

Acceptance:

- Every accepted positive case is consumed exactly once by the harness.
- Expected case assertions drive TypeScript checks without a duplicate handwritten
  truth table.
- The two-source collision produces distinct thread and run keys.
- Fixture evidence never becomes `live-contract` evidence.

### Milestone 4 — Prove reducer and mapping failures

Consume the accepted negative matrix and add TypeScript-only mapping/reducer
failure cases for boundaries the corpus cannot express as a passing envelope.

Acceptance:

- Every accepted negative case fails with its declared stable fixture rule code
  before domain reduction.
- TypeScript-specific cases prove duplicate/conflict, order, identity,
  capability/evidence, interrupt alignment, terminal inference, malformed,
  unknown, and partial-source behavior.
- Failure messages remain bounded and sanitized.

### Milestone 5 — Reprove packages, inputs, and handoff

Run affected domain/SDK checks, read-only downstream UI checks, and private
consumer format/lint/type/test/build, then prove fixture and lock bytes unchanged.

Acceptance:

- Domain/SDK format, lint, typecheck, unit, boundary, build, and package checks
  remain green; UI format, lint, typecheck, unit, boundary, build, and package
  checks rerun read-only after domain repair.
- Adapter-test format/lint/typecheck/test/build and boundary checks are green with
  external networking denied and lifecycle scripts disabled.
- Fixture full-tree digest, accepted Git tree identity, clean ignored/untracked
  status, and lock bytes match before and after.
- Fresh architecture, DX, security, and product/contract review accepts the exact
  commit or returns bounded rework.
- After acceptance, the Coordinator records this issue terminal before the
  API/SDK bridge takes sequential ownership of overlapping
  `packages/sdk/**` and `internal/adapter-tests/**` paths.

## Progress

- [x] 2026-07-23 AEST — Drafted from the exact supplied base; no install,
  implementation, fixture mutation, or package command was run.
- [x] 2026-07-23 AEST — Recorded fixture successor
  `75228c07dfa867f677fc176c1bb2423c7113aff8` as `REWORK REQUIRED`, not accepted.
- [x] 2026-07-23 AEST — Recorded TS candidate `1bf66e1` as rework-required.
- [x] 2026-07-23 AEST — Initial exact three-file candidate received architecture,
  DX, and security `REWORK REQUIRED` verdicts and product/contract `ACCEPT`;
  the correction remains limited to those files plus the new API/SDK bridge
  plan.
- [x] 2026-07-23 AEST — Separated private fixture proof from downstream public
  generation and recorded the exact consumer and bridge issue identities.
- [ ] Independent plan review accepts the exact corrected four-plan candidate.
- [ ] Fixture corpus and TS verification dependencies become terminal.
- [ ] Milestones 1-5 complete in an authorized consumer worktree.

## Surprises & Discoveries

- 2026-07-23 AEST — The fixture corpus is intentionally language-neutral but not
  the production event wire. Consequence: the TypeScript consumer needs a private
  test decoder and explicit generated-client absence, not an SDK DTO copied from
  fixture JSON.
- 2026-07-23 AEST — The current accepted lock does not yet exist and future
  consumer work may reveal a dependency need. Consequence: this cell may not
  opportunistically change the lock; any dependency delta forces a separate
  reviewed lock sequence.
- 2026-07-23 AEST — Because `internal/*` is already a workspace glob, adding an
  adapter-test package manifest after the terminal lock would create a new
  importer and invalidate frozen-lock proof. Consequence: this cell uses a
  manifest-free harness; any future importer requires a new stable-ID
  manifest/lock cell and a re-reviewed dependency edge.

## Decision Log

- 2026-07-23 AEST — Decision: join the accepted fixture and TypeScript chains only
  at this consumer cell. Rationale: the neutral corpus must not depend on current
  TS implementation, and TS proof must not treat an unaccepted corpus as test
  authority. Consequence: the DAG is acyclic and both terminal verdicts are
  independently required.
- 2026-07-23 AEST — Decision: keep fixture decoding private to
  `internal/adapter-tests`. Rationale: FastAPI/OpenAPI/event schema remains the
  production wire authority and `SPIKE-STREAM-001` is open. Consequence: passing
  corpus tests cannot be advertised as generated-client or live parity.
- 2026-07-23 AEST — Decision: prohibit dependency changes in the baseline consumer
  execution. Rationale: this plan cannot both change a manifest and validate
  against an unchanged frozen lock. Consequence: a necessary dependency produces
  a new stable-ID manifest/lock sequence, an explicit amended dependency, and
  fresh review before consumer proof resumes.
- 2026-07-23 AEST — Decision: make fixture immutability a full-tree property.
  Rationale: byte-only checks can miss symlinks, special files, or ignored output.
  Consequence: the private harness supplies a standard-library digest checker
  over sorted relative paths, file types, modes, and bytes and rejects unsafe
  entries.
- 2026-07-23 AEST — Decision: terminalize private conformance before public
  generation. Rationale: this plan intentionally proves generated-client absence
  and overlaps future SDK/adapter-test paths. Consequence:
  `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001` depends on this issue's exact
  terminal result and becomes the sole downstream generated-transport owner.

## Detailed implementation approach

1. Start from a reviewed dispatch commit that descends from the exact terminal TS
   verification result and independently accepted fixture corpus.
2. Verify both ancestors, accepted fixture Git tree identity, deterministic
   validator output, full-tree digest, clean ignored/untracked fixture status,
   terminal lock bytes, exact Node/pnpm versions, and generated-client absence.
3. Create the manifest-free adapter-test harness using only accepted locked
   tooling, packed public domain/SDK artifacts, public entry points, and its own
   package-local boundary checker.
4. Add the private fixture decoder and positive parity matrix, deriving
   expectations from the corpus.
5. Add accepted negative-corpus and TypeScript-specific reducer/mapping failure
   tests.
6. Run affected package and consumer checks through an offline network-denial
   wrapper with lifecycle scripts disabled; prove no manifest, lock, corpus,
   ignored/untracked, or generated-client mutation; commit only governed files;
   then stop for fresh independent review.
7. After independent acceptance, hand the exact commit and proof to the
   Coordinator for a terminal transition. Do not begin OpenAPI/SDK generation
   before that explicit transition.

## Validation and proof

Representative required commands from repository root after both dependencies are
terminal:

```text
set -euo pipefail
accepted_fixture_commit="<accepted full 40-character fixture SHA>"
terminal_ts_verify_commit="<accepted full 40-character TS verification SHA>"
reviewed_consumer_dispatch_commit="<reviewed full 40-character consumer dispatch SHA>"
test "${#accepted_fixture_commit}" -eq 40
test "${#terminal_ts_verify_commit}" -eq 40
test "${#reviewed_consumer_dispatch_commit}" -eq 40
git cat-file -e "${accepted_fixture_commit}^{commit}"
git cat-file -e "${terminal_ts_verify_commit}^{commit}"
git cat-file -e "${reviewed_consumer_dispatch_commit}^{commit}"
git merge-base --is-ancestor "$accepted_fixture_commit" "$reviewed_consumer_dispatch_commit"
git merge-base --is-ancestor "$terminal_ts_verify_commit" "$reviewed_consumer_dispatch_commit"
git merge-base --is-ancestor "$reviewed_consumer_dispatch_commit" HEAD
test "$(git status --porcelain)" = ""
test -z "${NPM_TOKEN:-}"
test -z "${NODE_AUTH_TOKEN:-}"
git diff --exit-code "$accepted_fixture_commit" HEAD -- internal/fixtures/product-demo
test "$(git rev-parse "$accepted_fixture_commit:internal/fixtures/product-demo")" = \
  "$(git rev-parse HEAD:internal/fixtures/product-demo)"
test -z "$(git status --porcelain=v1 --untracked-files=all --ignored=matching -- internal/fixtures/product-demo)"
git show "$terminal_ts_verify_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
git diff --exit-code "$terminal_ts_verify_commit" HEAD -- \
  package.json pnpm-workspace.yaml pnpm-lock.yaml \
  packages/domain/package.json packages/sdk/package.json
test -z "$(find internal/adapter-tests -name package.json -print -quit 2>/dev/null || true)"
test -z "$(find internal/adapter-tests ! -type f ! -type d -print -quit 2>/dev/null || true)"
! test -e packages/sdk/src/generated
test -f packages/domain/tests/support/deny-external-network.mjs
test -f packages/domain/tests/support/probe-external-network-denial.mjs

proof_tmp="$(mktemp -d "${TMPDIR:-/tmp}/dw-fixture-ts-consumer.XXXXXX")"
case "$proof_tmp" in "${TMPDIR:-/tmp}"/dw-fixture-ts-consumer.*) ;; *) exit 1 ;; esac
mkdir "$proof_tmp/home"
cleanup_fixture_consumer_proof() {
  chmod -R u+w "$proof_tmp" 2>/dev/null || true
  rm -rf "$proof_tmp"
}
trap cleanup_fixture_consumer_proof EXIT HUP INT TERM
git ls-tree -r --name-only "$terminal_ts_verify_commit" \
  | awk '/(^|\/)package\.json$/' | sort >"$proof_tmp/manifests-accepted.txt"
{ printf '%s\n' package.json; find apps packages internal -name package.json -not -path '*/node_modules/*'; } \
  | sort >"$proof_tmp/manifests-current.txt"
cmp "$proof_tmp/manifests-accepted.txt" "$proof_tmp/manifests-current.txt"
while IFS= read -r manifest; do
  git show "$terminal_ts_verify_commit:$manifest" | cmp - "$manifest"
done <"$proof_tmp/manifests-accepted.txt"
git show "$terminal_ts_verify_commit:.npmrc" | cmp - .npmrc
git show "$terminal_ts_verify_commit:pnpm-workspace.yaml" | cmp - pnpm-workspace.yaml

PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check \
  >"$proof_tmp/fixture-validator-1.txt" 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 internal/fixtures/product-demo/validate.py --check \
  >"$proof_tmp/fixture-validator-2.txt" 2>&1
cmp "$proof_tmp/fixture-validator-1.txt" "$proof_tmp/fixture-validator-2.txt"
python3 -B internal/adapter-tests/scripts/fixture-tree-digest.py \
  internal/fixtures/product-demo >"$proof_tmp/fixture-tree-before.txt"
shasum -a 256 pnpm-lock.yaml >"$proof_tmp/lock-before.txt"

network_guard="$PWD/packages/domain/tests/support/deny-external-network.mjs"
network_probe="$PWD/packages/domain/tests/support/probe-external-network-denial.mjs"
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
env -i PATH="$trusted_path" HOME="$proof_tmp/home" \
  COREPACK_HOME="$accepted_corepack_home" COREPACK_ENABLE_NETWORK=0 \
  COREPACK_ENV_FILE=0 NODE_OPTIONS="--import=$network_guard" \
  "$accepted_node_bin" "$network_probe"
pnpm_offline_guarded() {
  env -i PATH="$trusted_path" HOME="$proof_tmp/home" \
    XDG_CACHE_HOME="$accepted_metadata_cache" \
    COREPACK_HOME="$accepted_corepack_home" \
    COREPACK_ENABLE_NETWORK=0 COREPACK_ENV_FILE=0 \
    NODE_OPTIONS="--import=$network_guard" \
    NPM_CONFIG_USERCONFIG=/dev/null NPM_CONFIG_GLOBALCONFIG=/dev/null \
    NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
    NPM_CONFIG_ALWAYS_AUTH=false NPM_CONFIG_OFFLINE=true \
    NPM_CONFIG_IGNORE_SCRIPTS=true NPM_CONFIG_STORE_DIR="$accepted_offline_store" \
    NPM_CONFIG_CACHE_DIR="$accepted_metadata_cache" TMPDIR="$proof_tmp" \
    "$accepted_corepack_bin" pnpm --offline --ignore-scripts "$@"
}
node_guarded() {
  env -i PATH="$trusted_path" HOME="$proof_tmp/home" \
    COREPACK_HOME="$accepted_corepack_home" COREPACK_ENABLE_NETWORK=0 \
    COREPACK_ENV_FILE=0 NODE_OPTIONS="--import=$network_guard" \
    "$accepted_node_bin" "$@"
}
adapter_run() {
  env -i PATH="$trusted_path" HOME="$proof_tmp/home" \
    XDG_CACHE_HOME="$accepted_metadata_cache" \
    COREPACK_HOME="$accepted_corepack_home" COREPACK_ENABLE_NETWORK=0 \
    COREPACK_ENV_FILE=0 NODE_OPTIONS="--import=$network_guard" \
    NPM_CONFIG_USERCONFIG=/dev/null NPM_CONFIG_GLOBALCONFIG=/dev/null \
    NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ NPM_CONFIG_OFFLINE=true \
    NPM_CONFIG_IGNORE_SCRIPTS=true NPM_CONFIG_STORE_DIR="$accepted_offline_store" \
    NPM_CONFIG_CACHE_DIR="$accepted_metadata_cache" TMPDIR="$proof_tmp" \
    "$accepted_node_bin" internal/adapter-tests/run.mjs "$@"
}
test "$(pnpm_offline_guarded --version)" = "10.34.5"
pnpm_offline_guarded install --frozen-lockfile
git diff --exit-code -- pnpm-lock.yaml

pnpm_offline_guarded --filter @deepwork/domain format-check
pnpm_offline_guarded --filter @deepwork/sdk format-check
pnpm_offline_guarded --filter @deepwork/ui format-check
pnpm_offline_guarded exec oxfmt --check internal/adapter-tests
pnpm_offline_guarded --filter @deepwork/domain lint
pnpm_offline_guarded --filter @deepwork/sdk lint
pnpm_offline_guarded --filter @deepwork/ui lint
pnpm_offline_guarded exec oxlint internal/adapter-tests
pnpm_offline_guarded --filter @deepwork/domain typecheck
pnpm_offline_guarded --filter @deepwork/sdk typecheck
pnpm_offline_guarded --filter @deepwork/ui typecheck
pnpm_offline_guarded --filter @deepwork/domain test
pnpm_offline_guarded --filter @deepwork/sdk test
pnpm_offline_guarded --filter @deepwork/ui test
pnpm_offline_guarded --filter @deepwork/domain check-architecture
pnpm_offline_guarded --filter @deepwork/sdk check-architecture
pnpm_offline_guarded --filter @deepwork/ui check-architecture
node_guarded internal/adapter-tests/scripts/check-boundaries.mjs
pnpm_offline_guarded --filter @deepwork/domain build
pnpm_offline_guarded --filter @deepwork/sdk build
pnpm_offline_guarded --filter @deepwork/ui build
adapter_run --mode typecheck --work-dir "$proof_tmp/typecheck"
adapter_run --mode test --work-dir "$proof_tmp/test"
adapter_run --mode test --case diagnostics-sanitization \
  --work-dir "$proof_tmp/diagnostics"
adapter_run --mode build --work-dir "$proof_tmp/build"
pnpm_offline_guarded --filter @deepwork/domain package-check
pnpm_offline_guarded --filter @deepwork/sdk package-check
pnpm_offline_guarded --filter @deepwork/ui package-check

python3 -B internal/adapter-tests/scripts/fixture-tree-digest.py \
  internal/fixtures/product-demo >"$proof_tmp/fixture-tree-after.txt"
cmp "$proof_tmp/fixture-tree-before.txt" "$proof_tmp/fixture-tree-after.txt"
shasum -a 256 pnpm-lock.yaml >"$proof_tmp/lock-after.txt"
cmp "$proof_tmp/lock-before.txt" "$proof_tmp/lock-after.txt"
git diff --exit-code "$accepted_fixture_commit" HEAD -- internal/fixtures/product-demo
test "$(git rev-parse "$accepted_fixture_commit:internal/fixtures/product-demo")" = \
  "$(git rev-parse HEAD:internal/fixtures/product-demo)"
test -z "$(git status --porcelain=v1 --untracked-files=all --ignored=matching -- internal/fixtures/product-demo)"
git show "$terminal_ts_verify_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
git diff --exit-code "$terminal_ts_verify_commit" HEAD -- \
  package.json pnpm-workspace.yaml pnpm-lock.yaml \
  packages/domain/package.json packages/sdk/package.json
test -z "$(find internal/adapter-tests -name package.json -print -quit)"
test -z "$(find internal/adapter-tests ! -type f ! -type d -print -quit)"
{ printf '%s\n' package.json; find apps packages internal -name package.json -not -path '*/node_modules/*'; } \
  | sort >"$proof_tmp/manifests-current-final.txt"
cmp "$proof_tmp/manifests-accepted.txt" "$proof_tmp/manifests-current-final.txt"
while IFS= read -r manifest; do
  git show "$terminal_ts_verify_commit:$manifest" | cmp - "$manifest"
done <"$proof_tmp/manifests-accepted.txt"
git show "$terminal_ts_verify_commit:.npmrc" | cmp - .npmrc
git show "$terminal_ts_verify_commit:pnpm-workspace.yaml" | cmp - pnpm-workspace.yaml
! test -e packages/sdk/src/generated
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check
consumer_candidate_commit="$(git rev-parse HEAD)"
test "${#consumer_candidate_commit}" -eq 40
git merge-base --is-ancestor "$reviewed_consumer_dispatch_commit" "$consumer_candidate_commit"
git diff --name-only "$reviewed_consumer_dispatch_commit" "$consumer_candidate_commit" \
  | awk '
      /^packages\/domain\// { next }
      /^packages\/sdk\// { next }
      /^internal\/adapter-tests\// { next }
      /^docs\/exec-plans\/active\/DW-EXEC-M1-FIXTURE-TS-CONSUMER\.md$/ { next }
      { bad = 1; print > "/dev/stderr" }
      END { exit bad }
    '
test "$(git status --porcelain)" = ""
```

`internal/adapter-tests/run.mjs` is required to create an exact temporary
consumer under the supplied `--work-dir`, pack the already built domain and SDK
packages with scripts disabled, install only those local archives plus already
locked TypeScript/Vitest tooling offline, and expose distinct typecheck, test, and
build modes. The package matrix must retain domain/SDK/UI typecheck-before-build;
the dependency-ordered domain/SDK builds must finish before the first packed
consumer mode. The runner may not add a workspace importer, reach a registry,
reuse a developer-global package store as unstated authority, or import package
source paths. `fixture-tree-digest.py` must use only the Python standard library,
walk sorted relative paths using `lstat`, include relative path, entry type, mode,
and file bytes, and reject symlinks and special files.

The diagnostics-sanitization case must supply credential-shaped strings, control
characters, HTML/script-shaped content, and oversized untrusted values. Retained
output is limited to bounded stable codes and fixture case IDs; the raw values
must be absent.

Required retained evidence:

- exact terminal dependency SHAs and independent verdicts;
- accepted fixture Git tree ID, full-tree digest, clean ignored/untracked status,
  corpus version/case/rule inventory, and terminal lock digest before/after;
- positive case-to-TypeScript assertion matrix;
- accepted negative and TypeScript-specific failure matrix;
- source-collision, replay-dedupe, logical-delay, terminal, partial-failure,
  capability/evidence, unknown, and malformed results;
- proof that no shipped domain/SDK source imports fixtures and no generated client
  was invented;
- read-only UI downstream reproof after domain repair, with no UI diff;
- manifest-free harness, package-local boundary checker, deliberate boundary
  negatives, no-network, lifecycle-disabled frozen lock, read-only corpus, exact
  changed-file scope; and
- bounded feature-scenario contribution with zero E2E completion.

## Review requirements

- Architecture verifies public-only imports, private fixture decoder ownership,
  legal package direction, and absence of corpus/runtime coupling.
- Developer Experience/TypeScript verifies deterministic corpus discovery,
  actionable failure output, package-local commands, and frozen-lock reproduction.
- Security verifies read-only scrubbed inputs, no external network, safe failure
  diagnostics, and no secret/provider/unsafe-content leakage.
- Product/contract verifies fixture semantics are not promoted to production wire,
  live capability, generated client, application parity, or E2E completion.

## Idempotence, rollback, and recovery

The corpus validator and consumer tests are read-only and deterministic. The
validated temporary directory has an immediate cleanup trap; cleanup is limited
to that exact directory even on failure or interruption. Repeated runs against
the same accepted inputs must produce the same ordered results. Failures preserve
case IDs and safe diagnostics. Repair only governed domain/SDK/adapter-test/plan
files; never rewrite an accepted fixture, manifest, or lock to make a test pass.

If a dependency or importer is needed, abort before further proof; create a new
stable-ID reviewed manifest/lock cell; then amend the dependency list here and
obtain fresh independent review before resuming. Before integration, rollback
reverts only this cell's governed diff. There is no provider, database, browser,
registry, or production state to clean up.

## Rollout and handoff

There is no production rollout. Hand the exact independently accepted consumer
commit, terminal input SHAs/digests, parity/failure matrices, proof transcript,
reviewer verdicts, and changed-file list to the Coordinator. The Coordinator
must record `local:DW-M1-FIXTURE-TS-CONSUMER-001` terminal before dispatching
`local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`. API conformance, generated
contracts, `apps/web`, the API-backed product demo, browser accessibility, and
live parity remain separately sequenced cells.

## Outcomes & Retrospective

Pending terminal dependencies, execution, and independent review. Completion must
state exact positive/negative coverage, corpus and lock immutability, generated
client absence, explicit Coordinator terminal handoff, deviations, remaining
runtime gates, and zero E2E completion. The later bridge, not this plan, records
any separately accepted generated authority.
