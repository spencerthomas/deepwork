---
exec_plan_id: DW-EXEC-M1-FIXTURE-API-SDK-CONTRACT
title: Wave 1 final-wire fixture API to public SDK contract
status: draft
superseded_by: null
owner: api-sdk-contract-generation
reviewed_by: []
reviewed_at: null
primary_feature_id: DW-FND-004
supporting_feature_ids: [DW-FND-001, DW-FND-003, DW-FND-005, DW-QUAL-001]
issue: local:DW-M1-FIXTURE-API-SDK-CONTRACT-001
created: 2026-07-23
last_updated: 2026-07-23
base_commit: c9faefda05d3a6f069d93cbd0e938a31e557218b
last_verified_commit: null
risk: high
governed_paths: [docs/generated/openapi.json, packages/sdk/src/generated/**, packages/sdk/src/product-demo/**, packages/sdk/package.json, packages/sdk/scripts/generate-product-demo-client.mjs, packages/sdk/scripts/check-product-demo-contract.mjs, packages/sdk/scripts/package-check.mjs, packages/sdk/tests/product-demo-client.test.ts, packages/sdk/tests/product-demo-contract-drift.test.ts, internal/adapter-tests/**, docs/proposals/2026-07-23-ts-proof-consumer-drafts/DW-EXEC-M1-FIXTURE-API-SDK-CONTRACT.md]
contract_gates: [SPIKE-STREAM-001, SPIKE-HITL-001, SPIKE-CHECKPOINT-001]
decision_gates: [DEC-022, DEC-023, DEC-025, DEC-031, DEC-034, DEC-035, DEC-037]
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: [AGENTS.md, ARCHITECTURE.md, packages/domain/AGENTS.md, packages/sdk/AGENTS.md, docs/AGENTS.md, docs/PLANS.md, docs/SECURITY.md, docs/RELIABILITY.md, docs/exec-plans/active/DW-EXEC-PROGRAM-CANONICAL.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-CONTRACT.md, docs/exec-plans/active/DW-EXEC-M1-FIXTURE-TS-CONSUMER.md, docs/exec-plans/active/DW-EXEC-M1-TS-LOCK.md, docs/exec-plans/active/DW-EXEC-M1-TS-VERIFY.md, docs/design-docs/architecture/application-architecture.md, docs/design-docs/engineering/conventions.md, docs/design-docs/decisions/index.md, docs/product-specs/acceptance-scenarios.md, docs/product-specs/foundations/dw-fnd-001-repository-oss-and-delivery-foundation.md, docs/product-specs/foundations/dw-fnd-003-application-service-state-and-security.md, docs/product-specs/foundations/dw-fnd-004-sdk-stream-and-fixture-contracts.md, docs/product-specs/foundations/dw-fnd-005-domain-identity-status-and-audit-model.md, docs/product-specs/quality/dw-qual-001-accessibility-performance-security-testing-and-release.md]
scenario_ids: [AC-DW-FND-001-07, AC-DW-FND-003-05, AC-DW-FND-004-04, AC-DW-FND-004-05, AC-DW-FND-004-06, AC-DW-FND-005-01, AC-DW-QUAL-001-08]
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: [local:DW-M1-API-001, local:DW-M1-FIXTURE-TS-CONSUMER-001, local:DW-M1-TS-VERIFY-001]
blockers: []
---

# Wave 1 final-wire fixture API to public SDK contract

Plan state: **prepared for independent review**. This plan is an unindexed,
non-dispatchable draft. It cannot generate or publish transport code until all
three front-matter dependencies are independently accepted and Coordinator-
terminal at exact commits.

## Purpose and observable result

Generate one deterministic checked-in OpenAPI document from the accepted final
fixture API wire, generate the browser-safe TypeScript DTO/operation layer from
that document, and expose the reviewed public subpath
`@deepwork/sdk/product-demo`. The public client maps generated DTOs into stable
`@deepwork/domain` values without copying fixture envelopes into the production
wire or guessing a route, field, status, cursor, header, or success response.

The result gives the later web lock/reverification and product-demo integration
one accepted API-to-SDK seam. It proves only credential-free fixture transport,
offline contract generation, DTO/domain mapping, and package consumption. It
earns zero live-contract, provider, browser, application-integration, durability,
or `E2E-V1-*` credit.

## Context and orientation

The plan-authoring base is
`c9faefda05d3a6f069d93cbd0e938a31e557218b` on
`external/planning/w1-ts-proof-consumers`. At that commit:

- `@deepwork/sdk` exposes only its root public entry point and intentionally has
  no generated client;
- `docs/generated/openapi.json`, `packages/sdk/src/generated/**`, and
  `packages/sdk/src/product-demo/**` do not exist;
- the private plan
  `DW-EXEC-M1-FIXTURE-TS-CONSUMER` correctly treats the language-neutral fixture
  envelope as test input rather than API wire;
- the TypeScript lock and verification cells prohibit generated transport and
  package-manifest mutation; and
- `local:DW-M1-API-001` is the completed API scaffold record in this
  checkout. It establishes the API ownership boundary but does **not** provide
  the required final-wire contract; that contract remains a review blocker until
  an accepted successor records exact evidence.

Root architecture makes FastAPI/Pydantic/OpenAPI the application-wire authority
and `packages/sdk` the browser-safe transport/mapping owner. The accepted fixture
corpus is a language-neutral conformance source, not an OpenAPI generator. The
private TypeScript fixture consumer proves corpus/domain parity but must reach a
terminal handoff before this cell takes sequential ownership of overlapping SDK
and `internal/adapter-tests/**` paths.

## Scope

### In scope

- Consume the exact terminal final-wire API consumer, including its
  API-owned deterministic OpenAPI exporter.
- Generate `docs/generated/openapi.json`; never hand-edit it.
- Generate only the product-demo DTO and operation layer under
  `packages/sdk/src/generated/**` from that committed schema.
- Add the handwritten public fixture client and DTO/domain mapping under
  `packages/sdk/src/product-demo/**`.
- Add `./product-demo` to `@deepwork/sdk` exports and add dependency-neutral
  generation/check scripts to `packages/sdk/package.json`.
- Strengthen the exact SDK package-check script so a packed empty consumer
  imports `@deepwork/sdk/product-demo` at runtime and typechecks it from the
  archive.
- Add deterministic generation, contract-drift, mapping, safe-error,
  URL/header, capability-evidence, and fixture/live-separation tests in the exact
  governed script/test paths.
- Take sequential ownership of the now-terminal private adapter-test tree and add
  one downstream cross-language harness under `internal/adapter-tests/**`; it
  exercises the accepted API fixture projection through generated DTOs and the
  public SDK subpath without importing the corpus as application wire.
- Keep the root lock, root/workspace manifests, API source, fixture corpus,
  domain package, UI package, web app, generated indexes, canonical plans, and
  product specs byte-unchanged.
- Keep this living plan current through implementation and independent handoff.

### Non-goals

- Editing `apps/api/**`. The API consumer is the only owner of its OpenAPI export
  entry point and final response/request contracts.
- Editing `internal/fixtures/product-demo/**` or deriving public DTOs directly
  from its envelope, expected assertions, logical ticks, negative matrix, or
  case categories.
- Adding, updating, or removing a dependency, peer, optional dependency,
  workspace importer, package manager field, lifecycle hook, or
  `pnpm-lock.yaml` entry.
- Editing `packages/domain/**`, `packages/ui/**`, `apps/web/**`, root manifests,
  root configuration, architecture manifests, the ExecPlan index, program
  plans, generated indexes other than the exact OpenAPI artifact, or
  `docs/plans/**`.
- Hand-writing OpenAPI, generated DTOs, endpoint paths, accepted status codes,
  request headers, command/job fields, pagination, replay, resume, HITL,
  checkpoint, provider, or live-stream contracts.
- Starting an API/web/browser/database/object/telemetry service, reaching a
  provider or registry, using credentials, publishing, deploying, pushing,
  merging, or releasing.
- Claiming that a fixture request proves durable execution, authenticated live
  parity, browser behavior, full application integration, or E2E completion.

### Permissions and risk boundary

- Committable paths are exactly the governed entries in front matter.
- `apps/api/scripts/export_openapi.py`, `apps/api/Makefile`, and
  `apps/api/openapi/deepwork-api-v1.json` are read-only in this cell and are
  solely owned by the terminal API consumer. That upstream cell must expose
  `openapi-export` and read-only `openapi-check` Make targets plus an exporter
  output option that can write an explicit regular scratch file. If those files,
  targets, or final artifact are absent, provisional, nondeterministic, or not
  part of the accepted API commit, this cell blocks and returns to the API
  owner. This bridge never adds or repairs an API exporter.
- `packages/sdk/package.json` may change only its `exports` and `scripts` values.
  Dependency, peer, optional-dependency, package-manager, `files`, and lifecycle
  fields remain byte-equivalent in meaning to the terminal TypeScript input.
- The terminal `pnpm-lock.yaml` is read-only. Any required dependency/importer
  delta aborts this cell and requires a new stable-ID manifest/lock plan plus
  fresh review before a successor attempt.
- Generation and tests run offline with the accepted Python and Node toolchains,
  external networking denied, lifecycle scripts disabled, credential variables
  absent, and all scratch output confined to a validated `mktemp -d`.
- Generated output contains no timestamp, hostname, absolute path, random value,
  environment value, credential, raw fixture body, or tool/provider content.
- Independent API-contract, architecture, TypeScript/DX, security, and
  product/contract review is mandatory. The author cannot approve, index,
  dispatch, integrate, or terminalize the result.

## Authoritative sources and prerequisites

### Persistent terminal dependencies

| Dependency | Exact terminal evidence required | Why it is required |
|---|---|---|
| `local:DW-M1-API-001` | Completed API scaffold record plus a separately accepted successor commit with the final `/api/v1/demo/**` OpenAPI operation/status/error contract, API-owned `apps/api/scripts/export_openapi.py`, `apps/api/Makefile` targets, `apps/api/openapi/deepwork-api-v1.json`, and deterministic two-export proof | Establishes the API owner; successor evidence is the sole source of public wire truth |
| `local:DW-M1-FIXTURE-TS-CONSUMER-001` | Independently accepted private corpus/domain/reducer proof; exact corpus and lock digests; explicit no-generated-client and no-manifest result; Coordinator terminal handoff | Prevents the fixture schema from being promoted and serializes overlapping SDK/adapter-test ownership |
| `local:DW-M1-TS-VERIFY-001` | Independently accepted package verification commit and unchanged first-lock digest | Supplies accepted public package, pack, boundary, toolchain, and offline-store evidence |

The private consumer alias is exactly
`local:DW-M1-FIXTURE-TS-CONSUMER-001`. The inverted alias
`local:DW-M1-TS-FIXTURE-CONSUMER-001` is invalid and must not appear in the final
web or product-demo dependency chain.

The API dependency is acceptable only when its wire is final for the fixture
product-demo integration. A provisional process-local mutation response that
later changes path, status, command/job correlation, pending/terminal shape, or
error semantics when PostgreSQL/worker durability is composed is not final-wire
evidence and blocks generation. The accepted API may use an in-memory fixture
adapter, but the exported command-intake and observation contract must remain
wire-compatible with the later `202 pending` durable implementation.

All three dependencies must be ancestors of the reviewed bridge dispatch commit.
Directly listing TS verification is intentional even though the private
consumer also depends on it: the bridge independently anchors package and lock
provenance for generated-source and packed-consumer proof.

### Acyclic downstream handoff

The reconciled sequence is:

```text
accepted TS source -> first TS lock -> TS verify
                                      -> private fixture TS consumer ---\
accepted fixture corpus -> final-wire API consumer ---------------------+-> API/SDK bridge
terminal web-shell source + API/SDK bridge -> web lock extension
                                           -> web TS reverify
API/SDK bridge + terminal web-shell source + web TS reverify -> product demo
```

The bridge never depends on a web cell. Downstream planning must use these exact
stable identities:

| Role | Exact identity |
|---|---|
| Private fixture TypeScript proof | `local:DW-M1-FIXTURE-TS-CONSUMER-001` |
| Final API-to-SDK bridge | `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001` |
| Web lock extension | `local:DW-M1-WEB-LOCK-EXTENSION-001` |
| Final web TypeScript verification | `local:DW-M1-WEB-TS-REVERIFY-001` |
| Product-demo integration | `DW-EXEC-M1-PRODUCT-DEMO-INTEGRATION` |

The web-shell source/importer plan must be terminal before lock-extension
dispatch; a mid-plan importer milestone is not a dispatchable dependency. The
web lock-extension cell consumes that exact terminal web source plus the exact
accepted bridge manifest and generated/public SDK source. The web
re-verification cell consumes that exact lock extension. The product-demo plan
must depend on this bridge rather than assigning generated transport to the
private fixture consumer.

### Open external gates

`SPIKE-STREAM-001`, `SPIKE-HITL-001`, and `SPIKE-CHECKPOINT-001` remain open.
Generated fixture DTOs cannot close them. Any corresponding action remains
unavailable or gated with fixture evidence and constructs no live request.

## Interfaces and invariants

### Single-owner OpenAPI flow

- The final API consumer alone owns
  `apps/api/scripts/export_openapi.py`, the `openapi-export` and
  `openapi-check` targets in `apps/api/Makefile`, the generated
  `apps/api/openapi/deepwork-api-v1.json`, and the Pydantic/FastAPI source that
  determines the schema.
- The exporter accepts only an explicit regular output file, creates no
  repository state implicitly, canonicalizes object keys and operation order,
  ends with one newline, and emits no timestamp/path/environment data.
- This bridge owns only the downstream generated artifact
  `docs/generated/openapi.json`. It first verifies the API-owned canonical
  artifact, invokes the accepted exporter twice into scratch files, requires all
  three byte streams to match, then promotes those exact bytes.
- No other cell may hand-edit the generated document or generate a second API
  schema. If the upstream command changes, the bridge returns to review.

### Generated DTO and operation boundary

- `packages/sdk/scripts/generate-product-demo-client.mjs` uses Node standard
  library only. It parses the committed OpenAPI document, resolves only local
  schema references, sorts every emitted operation/type/member deterministically,
  emits DTO types, operation metadata, and runtime guards only from explicitly
  supported schema constructs, and rejects cycles or unsupported constructs with
  stable safe codes rather than guessing.
- Generated source lives only under `packages/sdk/src/generated/**`, includes the
  OpenAPI SHA-256 in a machine-owned header, and is never edited by hand.
- The generator selects only accepted product-demo operations by their stable
  OpenAPI operation IDs. Missing, duplicate, renamed, extra, or structurally
  unsupported required operations fail closed.
- Accepted paths, methods, request/response media types, status codes, problem
  shapes, command/job correlation, and DTO fields come only from OpenAPI. Tests
  do not substitute a handwritten endpoint table as a second authority.
- `packages/sdk/scripts/check-product-demo-contract.mjs` regenerates into scratch,
  compares path/type/file inventories and bytes, verifies the embedded schema
  digest, compares a supplied terminal SDK manifest with the current manifest
  after excluding only `exports` and `scripts`, and reports stable drift
  diagnostics. It never rewrites files in check mode.
- `packages/sdk/package.json` adds exactly these dependency-neutral script keys:
  `generate:product-demo-client` runs
  `node scripts/generate-product-demo-client.mjs --schema
  ../../docs/generated/openapi.json --output src/generated`; and
  `check:product-demo-contract` runs
  `node scripts/check-product-demo-contract.mjs --schema
  ../../docs/generated/openapi.json --generated src/generated --check`.
  Existing script meanings remain unchanged.

### Public product-demo subpath

- `packages/sdk/package.json` exports exactly
  `@deepwork/sdk/product-demo` from built
  `dist/product-demo/index.{js,d.ts}` while preserving the existing root export.
- The subpath exposes `ProductDemoFixtureClient`,
  `createProductDemoFixtureClient`, required fixture request/result types, and
  stable safe errors. It does not expose raw corpus envelopes, API implementation
  models, generated internals, provider clients, credentials, arbitrary headers,
  or a live-capability facade.
- The client uses only accepted generated operation definitions. A caller may
  supply the browser `fetch` implementation, the exact application-owned API
  origin, and a bounded in-memory CSRF-token provider. The client accepts only
  same-origin or the exact validated loopback origin, resolves fixed generated
  relative paths, sends the host-only session cookie through the fixed accepted
  credentials mode, and adds only the exact generated `X-CSRF-Token` mutation
  header. It cannot accept arbitrary path, redirect, header, cookie, session ID,
  or credential overrides.
- Query, command intake, and command/job observation remain distinct. Fetch
  abort/unsubscribe/disconnect is not a server cancel and never infers terminal
  success.
- Non-2xx and malformed responses map to bounded safe failures. Raw response
  bodies, secrets, HTML, tool text, and untrusted provider content are never
  retained in public errors.

### DTO to domain mapping

- Generated DTOs remain wire values; they never enter `packages/domain`.
- Every response begins as `unknown` and passes the generated OpenAPI runtime
  guard before handwritten mapping. Mapping under
  `packages/sdk/src/product-demo/**` then validates domain-specific
  discriminators, source/thread/run qualification, ordered records, capability
  envelope, evidence class, freshness, authoritative completion, and command/job
  correlation before constructing domain values.
- Identical provider-native IDs from different synthetic sources remain distinct.
  Reconnect, timeout, disconnect, end-of-file, absent data, or a pending command
  never becomes terminal.
- Ordered interrupt request/config/decision arrays remain aligned. Tool content
  remains untrusted and bounded. Unknown records remain observable unknowns;
  malformed values fail closed.
- A response marked `mode: fixture` or `evidenceClass: fixture` remains fixture
  evidence through every mapping. No fixture row becomes `documented`,
  `live-contract`, provider availability, durable success, or E2E proof.
- No request body or query may contain the server-issued session identity. CSRF
  tokens remain in memory, never enter URLs/storage/logs/errors/evidence, and are
  requested only for generated mutation operations.

### Cross-language adapter proof

- The downstream harness under `internal/adapter-tests/**` consumes an actual
  sanitized response produced by the accepted API fixture application in an
  offline in-process test mode, then feeds those bytes through the generated
  DTO boundary and public `@deepwork/sdk/product-demo` client/mapping.
- The harness may use the accepted corpus only to select case IDs and independently
  compare final semantic outcomes. It never imports fixture envelope types into
  shipped SDK source and never treats fixture `expected` fields as API DTOs.
- API response bytes, committed OpenAPI, generated source, and mapped domain
  outcome are separate retained evidence layers. A mismatch fails with a stable
  layer-qualified code.
- All cross-language test output is sanitized, bounded, deterministically
  ordered, and contains only synthetic identities.

## State matrix

| State | Required behavior | Evidence or recovery |
|---|---|---|
| Any dependency nonterminal | Do not generate or edit governed implementation paths. | Return exact missing terminal ID/SHA to the Coordinator. |
| API exporter absent or owned by both cells | Block. | API consumer owns the three exact API artifacts; bridge owns none under `apps/api/**`. |
| API wire is provisional or synchronous-only | Block. | Return path/status/job-shape mismatch to API owner; do not generate a client. |
| Two API exports differ | Fail generation. | Preserve sanitized byte diff and exporter command; repair only in API cell. |
| OpenAPI has unsupported or ambiguous required operation | Fail closed. | Return stable operation/schema code; do not guess. |
| Generated pass one and two differ | Fail generation. | Preserve path/byte inventory and repair deterministic generator logic. |
| Committed OpenAPI or generated source drifts | Fail check. | Regenerate from the same accepted API commit; never hand-edit. |
| Package dependency/importer/lock delta appears | Abort. | Create a separately reviewed manifest/lock cell before any successor attempt. |
| Public subpath missing from packed archive | Fail package proof. | Repair only governed SDK manifest/check/source paths. |
| Root SDK export regresses | Fail package proof. | Restore compatibility; subpath addition cannot replace the root export. |
| Wire DTO fails domain validation | Return bounded safe mapping failure. | Add regression test; never cast or relax domain semantics. |
| Fixture evidence is promoted | Fail security/product proof. | Preserve fixture mode/evidence class and unavailable live behavior. |
| Arbitrary URL/header/cookie/session/redirect requested | Refuse before request. | Return stable safe client error. |
| Mutation has no bounded CSRF token | Refuse before request. | No token value appears in the safe failure. |
| External network or credential access attempted | Fail command and cell. | Retain sanitized target class only; do not retry online. |
| All offline contract proof passes | Record exact schema/client digests and zero E2E/live credit. | Stop for fresh independent review. |

## Milestones

### Milestone 1 — Freeze terminal sources and sole ownership

Record all three accepted dependency commits, independent verdicts, fixture and
lock digests, final API operation inventory, exact exporter files/command, and a
clean dispatch baseline.

Acceptance:

- every front-matter dependency is terminal and an ancestor of dispatch;
- the private fixture consumer records generated-client absence and has stopped
  before this cell takes SDK/adapter-test ownership;
- API ownership of `apps/api/scripts/export_openapi.py`, `apps/api/Makefile`,
  and `apps/api/openapi/deepwork-api-v1.json` is explicit and bridge scope
  contains no API path;
- root/workspace manifests and `pnpm-lock.yaml` match terminal TS verification.

### Milestone 2 — Prove deterministic final-wire OpenAPI export

Run the API-owned read-only check and exporter twice in isolated scratch paths,
compare both results to the API-owned canonical artifact, inspect semantic
inventory, scan forbidden fields, and promote the identical canonical result to
`docs/generated/openapi.json`.

Acceptance:

- both exports and `apps/api/openapi/deepwork-api-v1.json` are byte-identical and
  have one terminal newline;
- schema contains the required final product-demo catalog, projection,
  command-intake, command-status, and reset operations with stable operation IDs;
- schema contains the durable-compatible pending/correlation/problem shapes
  required by the downstream product demo;
- schema contains no credential value, `authRef`, arbitrary target URL/header,
  corpus path, raw fixture expectation, or live-provider success claim.

### Milestone 3 — Generate and check the SDK contract twice

Generate from the same committed OpenAPI into two scratch roots and require
identical path inventories and bytes. Promote one exact result, then require the
check script to reproduce it with zero drift.

Acceptance:

- two generated trees and embedded schema digests are identical;
- the committed generated tree equals scratch output byte-for-byte;
- a scratch-only schema mutation for removed operation, changed status, changed
  required field, and renamed discriminator makes the checker fail with one
  declared stable drift code per mutation;
- rerunning write generation produces no Git diff.

### Milestone 4 — Expose public mapping and packed consumption

Implement the handwritten product-demo client/mapping, dependency-neutral
manifest export/scripts, unit/negative tests, and packed clean-consumer proof.

Acceptance:

- `@deepwork/sdk/product-demo` imports from the packed archive in JavaScript and
  compiles in an empty TypeScript consumer;
- the existing `@deepwork/sdk` root export remains compatible;
- DTO/domain tests cover qualified identity, order, replay, logical delay,
  reconnect, explicit terminal authority, partial failure, unknown/malformed
  input, tool trust/bounds, ordered interrupt alignment, and capability evidence;
- URL/header/redirect, raw-error, fixture-to-live promotion, and terminal
  inference negatives fail closed; session IDs are absent from request
  bodies/queries and CSRF tokens remain bounded in-memory mutation inputs only;
- no dependency or lock delta exists.

### Milestone 5 — Prove cross-language separation and hand off

Run the API projection-to-public-SDK harness, all affected package checks,
generation checks, architecture/docs checks, and exact scope/immutability proof.

Acceptance:

- API response, OpenAPI DTO, generated source, and mapped domain layers remain
  distinguishable and agree for every selected positive/negative case;
- fixture envelope fields never become public wire or shipped SDK dependencies;
- API, fixture, domain, UI, web, root, lock, canonical/index, and unrelated paths
  are byte-unchanged;
- fresh independent API-contract, architecture, DX, security, and
  product/contract reviewers accept the exact commit;
- the handoff records zero live/provider/browser/application/E2E completion.

## Progress

- [x] 2026-07-23 AEST — Added the bridge during planning-only correction from
  exact clean base `c9faefda05d3a6f069d93cbd0e938a31e557218b`; no generation,
  install, implementation, manifest, lock, or runtime command was run.
- [x] 2026-07-23 AEST — Assigned the API exporter solely to the upstream API
  consumer and made the bridge depend on its accepted final wire.
- [x] 2026-07-23 AEST — Corrected the private fixture-consumer identity and
  separated private corpus proof from public generated transport.
- [ ] Independent plan review accepts the exact corrected four-plan bundle and
  the paired API/web dependency amendments.
- [ ] All three front-matter dependencies become terminal at exact accepted
  commits.
- [ ] Milestones 1-5 execute in one authorized bridge worktree.

## Surprises & Discoveries

- 2026-07-23 AEST — The private fixture TypeScript plan intentionally proves
  generated-client absence. Consequence: public transport cannot be added there;
  it needs this later cell after that plan is terminal.
- 2026-07-23 AEST — The paired product-demo draft assigned public transport to
  the inverted, nonexistent alias
  `local:DW-M1-TS-FIXTURE-CONSUMER-001`. Consequence: downstream plans must use
  the private consumer's real alias only for private proof and this bridge's
  issue for generated transport.
- 2026-07-23 AEST — The paired API and product-demo drafts describe different
  mutation timing unless the API wire is fixed before generation. Consequence:
  process-local fixture implementation is allowed only behind a final,
  durable-compatible `202 pending` command/job contract.
- 2026-07-23 AEST — `packages/sdk/package.json` must gain a public subpath but
  needs no package dependency. Consequence: this cell owns an
  exports/scripts-only manifest change and proves the lock remains identical.
- 2026-07-23 AEST — Docs validation cannot enforce governed-path overlap.
  Consequence: the private consumer must be Coordinator-terminal before this
  bridge takes sequential ownership of SDK and adapter-test paths.

## Decision Log

- 2026-07-23 AEST — Decision: FastAPI owns the sole OpenAPI export entry point.
  Rationale: schema generation must remain adjacent to Pydantic/FastAPI source
  and cannot be split across Python and TypeScript cells. Consequence: this
  bridge treats the three exact API export artifacts as read-only terminal
  inputs.
- 2026-07-23 AEST — Decision: add a separate API-to-SDK bridge after private
  fixture conformance. Rationale: language-neutral fixture proof and public wire
  generation are different evidence tiers. Consequence: the private consumer
  remains manifest-free and generated-client-free.
- 2026-07-23 AEST — Decision: use a repository-owned standard-library generator.
  Rationale: the terminal first lock contains no accepted codegen dependency and
  this cell cannot mutate dependencies. Consequence: unsupported OpenAPI
  constructs fail closed rather than triggering an install or handwritten DTO.
- 2026-07-23 AEST — Decision: export a fixture-specific SDK subpath.
  Rationale: callers need a stable public seam while fixture evidence must remain
  visibly distinct from live provider capability. Consequence:
  `ProductDemoFixtureClient` cannot be presented as a generic/live client.
- 2026-07-23 AEST — Decision: make double generation and a source-break negative
  mandatory. Rationale: a green checked-in hash alone can bless drift.
  Consequence: accepted proof includes independent byte reproduction and checker
  failure against mutated scratch schema.

## Detailed implementation approach

1. Start from a reviewed dispatch commit containing the three exact terminal
   dependencies. Verify ancestry, clean status, accepted lock, package manifests,
   fixture digest, private-consumer terminal handoff, API exporter ownership, and
   the API-owned canonical OpenAPI artifact.
2. Run the API-owned read-only check, invoke its exporter twice into validated
   scratch files, and compare both with its canonical artifact. Parse and scan the
   final operation/schema inventory, then copy those exact accepted bytes to
   `docs/generated/openapi.json`.
3. Implement the standard-library generator and read-only drift checker. Generate
   twice into scratch, compare full sorted file inventories and bytes, then
   promote one exact tree under `packages/sdk/src/generated/**`.
4. Add the public fixture client and strict DTO/domain mapping under
   `packages/sdk/src/product-demo/**`. Use only generated operations and public
   domain imports.
5. Update only `exports` and `scripts` in `packages/sdk/package.json`; strengthen
   the exact package checker and add the two exact SDK test files.
6. Extend terminal private adapter-test artifacts only where required by the
   downstream cross-language harness. Retain prior private parity cases or their
   exact evidence mapping; do not silently drop coverage during ownership
   transfer.
7. Run double generation, scratch mutation negatives, package/unit/boundary/pack
   proof, cross-language mapping, docs, scope, and immutable-input checks.
8. Update this plan with exact evidence, commit only governed paths, and stop for
   fresh independent review. Do not start web lock/reverification or product
   demo work in this cell.

## Validation and proof

### Plan-authoring candidate

From the repository root:

```text
test "$(git branch --show-current)" = "external/planning/w1-ts-proof-consumers"
test "$(git rev-parse HEAD^)" = "c9faefda05d3a6f069d93cbd0e938a31e557218b"
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check c9faefda05d3a6f069d93cbd0e938a31e557218b HEAD
git diff --name-only c9faefda05d3a6f069d93cbd0e938a31e557218b HEAD
test -z "$(git status --porcelain)"
```

As an archived proposal, this draft is intentionally outside active-ExecPlan
validation and must not be used to predict a failing documentation check. Before
promotion, the coordinator must replace the draft metadata with independently
reviewed active-ExecPlan metadata, register the plan in the index, and attach the
accepted final-wire successor evidence for `local:DW-M1-API-001`. Review/index
metadata must not be fabricated merely to make a draft pass.

### Implementation candidate

Representative required commands after reviewed dispatch:

```text
set -euo pipefail
api_commit="<accepted final-wire API consumer SHA>"
private_consumer_commit="<accepted private fixture TS consumer SHA>"
ts_verify_commit="<accepted TS verification SHA>"
dispatch_commit="<reviewed bridge dispatch SHA>"
for commit in "$api_commit" "$private_consumer_commit" "$ts_verify_commit" "$dispatch_commit"; do
  test "${#commit}" -eq 40
  git cat-file -e "${commit}^{commit}"
  git merge-base --is-ancestor "$commit" HEAD
done
test "$(git status --porcelain)" = ""
test -z "${NPM_TOKEN:-}"
test -z "${NODE_AUTH_TOKEN:-}"
test -z "${OPENAI_API_KEY:-}"
git show "$ts_verify_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
git diff --exit-code "$ts_verify_commit" HEAD -- \
  package.json pnpm-workspace.yaml pnpm-lock.yaml
git diff --exit-code "$api_commit" HEAD -- apps/api
git diff --exit-code "$private_consumer_commit" HEAD -- \
  internal/fixtures/product-demo packages/domain
test -f apps/api/scripts/export_openapi.py
test -f apps/api/openapi/deepwork-api-v1.json
rg -n '^openapi-export:' apps/api/Makefile
rg -n '^openapi-check:' apps/api/Makefile

proof_tmp="$(mktemp -d "${TMPDIR:-/tmp}/dw-api-sdk-contract.XXXXXX")"
case "$proof_tmp" in "${TMPDIR:-/tmp}"/dw-api-sdk-contract.*) ;; *) exit 1 ;; esac
cleanup_api_sdk_contract() {
  chmod -R u+w "$proof_tmp" 2>/dev/null || true
  rm -rf "$proof_tmp"
}
trap cleanup_api_sdk_contract EXIT HUP INT TERM
mkdir "$proof_tmp/home" "$proof_tmp/generated-1" "$proof_tmp/generated-2"

make -C apps/api openapi-check
make -C apps/api openapi-export OPENAPI_OUTPUT="$proof_tmp/openapi-1.json"
make -C apps/api openapi-export OPENAPI_OUTPUT="$proof_tmp/openapi-2.json"
cmp "$proof_tmp/openapi-1.json" "$proof_tmp/openapi-2.json"
cmp "$proof_tmp/openapi-1.json" apps/api/openapi/deepwork-api-v1.json
test "$(tail -c 1 "$proof_tmp/openapi-1.json" | od -An -tuC | tr -d ' ')" = "10"
cmp "$proof_tmp/openapi-1.json" docs/generated/openapi.json

node packages/sdk/scripts/generate-product-demo-client.mjs \
  --schema docs/generated/openapi.json --output "$proof_tmp/generated-1"
node packages/sdk/scripts/generate-product-demo-client.mjs \
  --schema docs/generated/openapi.json --output "$proof_tmp/generated-2"
diff -ru "$proof_tmp/generated-1" "$proof_tmp/generated-2"
diff -ru "$proof_tmp/generated-1" packages/sdk/src/generated
node packages/sdk/scripts/check-product-demo-contract.mjs \
  --schema docs/generated/openapi.json \
  --generated packages/sdk/src/generated --check

git show "$ts_verify_commit:packages/sdk/package.json" \
  >"$proof_tmp/sdk-package-baseline.json"
node packages/sdk/scripts/check-product-demo-contract.mjs \
  --schema docs/generated/openapi.json \
  --generated packages/sdk/src/generated \
  --manifest-baseline "$proof_tmp/sdk-package-baseline.json" \
  --manifest packages/sdk/package.json --check

pnpm --offline --ignore-scripts --frozen-lockfile install
pnpm --offline --filter @deepwork/sdk generate:product-demo-client
git diff --exit-code -- packages/sdk/src/generated
pnpm --offline --filter @deepwork/sdk check:product-demo-contract
pnpm --offline --filter @deepwork/sdk format-check
pnpm --offline --filter @deepwork/sdk lint
pnpm --offline --filter @deepwork/sdk typecheck
pnpm --offline --filter @deepwork/sdk exec vitest run \
  tests/product-demo-contract-drift.test.ts
pnpm --offline --filter @deepwork/sdk test
pnpm --offline --filter @deepwork/sdk check-architecture
pnpm --offline --filter @deepwork/sdk build
pnpm --offline --filter @deepwork/sdk package-check
node internal/adapter-tests/run.mjs --suite api-sdk-contract \
  --schema docs/generated/openapi.json --work-dir "$proof_tmp/adapter"

make -C apps/api openapi-export OPENAPI_OUTPUT="$proof_tmp/openapi-final.json"
cmp "$proof_tmp/openapi-1.json" "$proof_tmp/openapi-final.json"
git show "$ts_verify_commit:pnpm-lock.yaml" | cmp - pnpm-lock.yaml
git diff --exit-code "$api_commit" HEAD -- apps/api
git diff --exit-code "$private_consumer_commit" HEAD -- \
  internal/fixtures/product-demo packages/domain
python3 -B tools/docs/generate.py --check
python3 -B tools/docs/check.py
git diff --check "$dispatch_commit" HEAD
git diff --name-only "$dispatch_commit" HEAD | awk '
  /^docs\/generated\/openapi\.json$/ { next }
  /^packages\/sdk\/src\/generated\// { next }
  /^packages\/sdk\/src\/product-demo\// { next }
  /^packages\/sdk\/package\.json$/ { next }
  /^packages\/sdk\/scripts\/generate-product-demo-client\.mjs$/ { next }
  /^packages\/sdk\/scripts\/check-product-demo-contract\.mjs$/ { next }
  /^packages\/sdk\/scripts\/package-check\.mjs$/ { next }
  /^packages\/sdk\/tests\/product-demo-client\.test\.ts$/ { next }
  /^packages\/sdk\/tests\/product-demo-contract-drift\.test\.ts$/ { next }
  /^internal\/adapter-tests\// { next }
  /^docs\/exec-plans\/active\/DW-EXEC-M1-FIXTURE-API-SDK-CONTRACT\.md$/ { next }
  { bad = 1; print > "/dev/stderr" }
  END { exit bad }
'
test "$(git status --porcelain)" = ""
```

The implementation plan must replace the representative `node` and `pnpm`
invocations above with the exact accepted Node/Corepack binary, immutable
offline store/metadata cache, credential-empty environment, external-network
preload, and lifecycle-disabled wrapper recorded by terminal TS verification.
It must likewise use the exact offline Python/uv environment recorded by the
terminal API consumer. A developer-global executable, mutable cache, registry
fallback, or ambient environment is not accepted proof.

Required retained evidence:

- exact terminal dependency and dispatch SHAs, reviewer verdicts, lock/corpus
  digests, and ownership handoff;
- two API export hashes and byte comparison;
- two generated-tree inventories/hashes and byte comparison;
- committed schema/generated equality and no-drift rerun;
- source-break matrix with one stable expected diagnostic per mutation;
- final operation/status/problem/correlation inventory;
- public subpath JavaScript and TypeScript packed-consumer proof;
- DTO/domain positive and failure matrices;
- fixture/live separation, no-request unavailable states, raw-error scrubbing,
  URL/header/redirect denial, and network-denial proof;
- immutable API/fixture/domain/root/lock evidence and exact changed-file list;
  and
- explicit zero live/provider/browser/application/E2E completion.

## Review requirements

- API contract verifies the accepted API wire is final, durable-compatible, and
  the sole OpenAPI source; no operation/status/field is guessed.
- Architecture verifies API -> generated SDK -> handwritten SDK -> domain
  direction, public-only imports, no UI/provider/secret/fixture-runtime leakage,
  and terminal serialization of overlapping paths.
- Developer Experience/TypeScript verifies deterministic standard-library
  generation, drift diagnostics, package export/declarations, offline clean
  consumer, and unchanged lock/dependencies.
- Security verifies schema/output scrubbing, bounded errors, URL/header/redirect
  controls, credential-empty execution, external-network denial, untrusted
  content handling, and no raw fixture/provider body retention.
- Product/contract verifies fixture/live evidence separation, capability honesty,
  correct downstream aliases/DAG, and zero E2E/live overclaim.

## Idempotence, rollback, and recovery

API export, TypeScript generation, checking, and adapter tests are deterministic
for the same accepted commits. All scratch paths are children of one validated
temporary root with an immediate exact-root cleanup trap. Check mode is
read-only. Write mode promotes only a complete schema or generated tree after
both scratch passes agree; interruption before promotion leaves the repository
unchanged, and interruption during promotion leaves a detectable drift failure.

On API schema drift, stop and return to the API owner; never patch OpenAPI or
generated code manually. On unsupported OpenAPI, retain the stable safe code and
return for contract/generator review. On required package dependency/importer
change, abort and create a separately reviewed manifest/lock sequence before a
successor attempt. On fixture/domain mismatch, preserve all four evidence layers
and repair only the owning accepted cell after review.

Before integration, rollback is a reviewed revert of only this bridge's governed
diff. Generated OpenAPI and SDK source are reverted together so no mismatched
schema/client pair remains. There is no database, provider, browser, registry,
credential, or production state to recover.

## Rollout and handoff

There is no production rollout. Hand the Coordinator the exact accepted bridge
commit, terminal input SHAs/digests, final OpenAPI and generated-tree hashes,
operation inventory, source-break and DTO/domain matrices, packed-consumer proof,
reviewer verdicts, exact changed-file list, and open contract gates.

Only after this bridge is Coordinator-terminal may the web lock-extension cell
consume the final SDK manifest/source. Only after that exact lock extension and
`local:DW-M1-WEB-TS-REVERIFY-001` are terminal may the web shell or product-demo
claim executable use of `@deepwork/sdk/product-demo`. The product-demo dependency
must be `local:DW-M1-FIXTURE-API-SDK-CONTRACT-001`; the private fixture consumer
never supplies generated transport. No index, program-plan, integration, push,
merge, deploy, or release action belongs to this cell.

## Outcomes & Retrospective

Pending terminal dependencies, execution, and independent review. Completion
must compare the generated/public seam with the final API operation inventory,
record exact deterministic and failure evidence, state whether any dependency
or lock changed, preserve every open provider gate, name downstream alias/DAG
amendments still required, and report zero live/provider/browser/application
integration and zero `E2E-V1-*` completion.
