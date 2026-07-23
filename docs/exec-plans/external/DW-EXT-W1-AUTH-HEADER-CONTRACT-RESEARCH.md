---
packet_id: DW-EXT-W1-AUTH-HEADER-CONTRACT-RESEARCH
title: External dispatch - API-key and workspace-header contract research
status: ready-for-external-dispatch
base_commit: b9d244438c90a3031983b9705407b3dd5d4c33f9
branch: external/research/auth-header-contract-spikes
owner: external-auth-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-AUTH-002, AC-DW-ONB-001-01, AC-DW-ONB-002-01, AC-DW-FND-003-01, AC-DW-FND-003-02, AC-DW-FND-003-08, AC-DW-QUAL-001-03, AC-DW-QUAL-001-04]
allowed_paths: [tools/contract-spikes/auth/**, docs/references/research/auth-contract-spikes/**, docs/exec-plans/external/DW-EXT-W1-AUTH-HEADER-CONTRACT-RESEARCH.md]
dependencies: [SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-LCPY@592055e15e138f5369dce95dd049ce22430996e2, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-account]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
---

# External dispatch - API-key and workspace-header contract research

## Dispatch identity

- Exact base SHA:
  `b9d244438c90a3031983b9705407b3dd5d4c33f9`.
- Branch to create:
  `external/research/auth-header-contract-spikes`.
- ExecPlan: this file.
- This packet is research/probe work. It does not authorize application auth
  implementation, credential storage, provider adapters, or capability enablement.
- This packet is for an external worker. The program coordinator has not assigned
  its implementation scope to an internal agent.

## Purpose and observable result

Produce the source-precedence-aware API-key/workspace-header matrix required by
`SPIKE-AUTH-002` for Deep Work's public classic baseline. The result must
distinguish personal and workspace-/organization-scoped keys, every required API
plane, exact documented/generated header names, workspace/tenant context, negative
behavior, and the safe fallback.

Each operation retains separate, provenance-bearing observations and then derives
one final conclusion. Observations use the repository's canonical evidence
precedence:

1. accepted live-contract spike plus executable fixtures for pinned versions;
2. installed public APIs/generated schemas and official primary documentation;
3. accepted ADRs, architecture, product sense, and product specifications;
4. pinned research and reference-code evidence; and
5. prototype, mock, screenshot, or fixture-only evidence.

Every observation records its tier, source ID/URL, revision/version, date, exact
claim, fixture/hash, and contradiction links. The final row conclusion is one of
`accepted-live`, `blocked-live-evidence`, `rejected`, or `unknown`; it is not a
replacement for the underlying documented, installed/generated, and live
observations. The validator must reject an accepted row with an unresolved
same-tier or higher-tier contradiction and require an owner, blocker, and fallback
for every unresolved conflict.

Documentation or source internals alone never become `accepted-live`. Absence of a
non-production account must not block documented/installed/negative probe-kit work.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/auth/**
docs/references/research/auth-contract-spikes/**
docs/exec-plans/external/DW-EXT-W1-AUTH-HEADER-CONTRACT-RESEARCH.md
```

`tools/contract-spikes/auth/**` may own an isolated Python manifest, `uv.lock`,
tests, schema validators, scrubber, synthetic server, and opt-in live probes. It
must not change an existing root/application/package manifest or lock.

Do not change:

```text
apps/**
packages/**
tools/contract-spikes/langchain/**
docs/references/research/langchain-contract-spikes/**
docs/product-specs/**
docs/design-docs/**
docs/references/source-ledger.md
docs/generated/**
docs/exec-plans/index.md
docs/exec-plans/active/**
docs/exec-plans/completed/**
docs/plans/**
CI or root manifests/locks
```

The active LangChain contract accelerator is independent and disjoint. This packet
may cite compatible public versions but must not edit, wait on, or claim acceptance
from that task's outputs. The coordinator reconciles any version difference later.

## Exact evidence dependencies

Pinned read-only local evidence:

- `SRC-LC` at `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`;
- `SRC-LCPY` at `592055e15e138f5369dce95dd049ce22430996e2`;
  and
- `SRC-LG` at `31f90df3e6b0268fa77fd2d118a917d420b84a68`.

Execution dependencies:

- current official LangSmith/LangGraph documentation;
- reviewed public package-index access;
- an isolated probe lock pinning Python, LangSmith/LangGraph clients, generated
  schemas, and transitive versions; and
- only for `accepted-live`, an explicitly supplied non-production classic account
  whose tier, region, workspace/organization scope, server revision, authentication
  context, and synthetic data are recorded.

No production credential, customer account, reusable endpoint, browser-stored key,
or copied environment may be used. If a safe sandbox is absent, all live-dependent
rows remain `blocked-live-evidence`.

## Required operation and negative matrix

Build the required-plane inventory from official contracts before selecting any
route. Each operation row must retain the HTTP method, official documented route
template, verified service/host class, plane, operation name, and whether the
route/host is documented, installed/generated, or live-confirmed. At minimum,
classify the public classic operations Deep Work requires for:

- credential validation and authorized organization/workspace enumeration;
- classic deployment/control-plane read and capability discovery;
- classic Agent Server/data-plane health, assistant/graph, thread, and run
  operations; and
- any required workspace/organization selection accompanying those calls.

Do not invent a route, host, header, tenant field, workspace field, key prefix,
entitlement, or error shape. If the official/public contract does not establish an
operation, retain the observations and derive `unknown` or `rejected`.

For each operation, test or model:

- personal key with no workspace context;
- personal key with each officially documented workspace/tenant context;
- workspace-/organization-scoped key with its documented context;
- missing authorization;
- missing required workspace/tenant context;
- wrong or conflicting workspace/tenant context;
- unsupported key family or key/plane combination;
- caller-supplied forwarding, host, cookie, tracing, or alternate authorization
  headers; and
- permission denied, revoked key, inaccessible workspace, and sanitized provider
  errors where the public/live contract permits.

Live negative probes must be read-only, rate-bounded, synthetic, and explicitly
safe for the account. Never deliberately send a valid secret to an unverified host.
Never store an actual header value: evidence records exact header names and
redacted/synthetic placeholders only.

## Required retained outputs

Under `docs/references/research/auth-contract-spikes/`, retain:

- `matrix.json`: one row per method/official-route-template/service-host-class/
  plane/operation/key-class/context combination with package/server/account/
  region/auth/date, separate provenance-bearing observations at every available
  evidence tier, exact header names, redacted request schema, sanitized
  response/error schema, unresolved conflicts, final conclusion, owner/blocker,
  and fallback;
- `report.md`: required-plane inventory, contradictions, reviewer-ready recommended
  dispositions, downstream acceptance IDs, and recommended server-only adapter
  boundary. Only independent reviewers record final acceptance or rejection;
- `fixtures/`: synthetic and sanitized positive/negative request/response
  transcripts with hashes and scrub attestations;
- `versions.json`: interpreter, packages, generated schemas, server revision,
  account tier, region, and collection date;
- `scrub-report.json`: zero secret, credential-reference, customer/tenant value,
  account-specific reusable instance endpoint, raw authorization value, cookie,
  and environment-dump findings. Official route templates and generic verified
  service/host classes remain in evidence because the endpoint half of the matrix
  requires them;
  and
- `commands.txt`: exact commands and exit statuses without secrets or environment
  dumps.

The probe kit must include an offline synthetic server that asserts header
selection, stripping, redaction, error normalization, and fail-closed behavior.
It must not become production adapter code.

## Acceptance IDs and qualification

Every `AC-*` row below is supporting auth/header research evidence only. This
packet does not satisfy an application, integration, browser, persistence,
two-source, or release scenario by itself.

| ID | Required evidence |
|---|---|
| `SPIKE-AUTH-002` | Personal and workspace-/organization-scoped key rows cover every required classic plane with exact documented/public header names, negative cases, sanitized live evidence where required, and explicit fallback. |
| `AC-DW-ONB-001-01` | Supports server-side API-key session/workspace selection without exposing the key; the product scenario still requires application persistence/browser/log proof. |
| `AC-DW-ONB-002-01` | Supports the auth/header part of a verified classic source probe; assistant/invocation capability proof remains in source/runtime cells. |
| `AC-DW-FND-003-01` | Supports only the revoked/unauthorized auth-error and credential-redaction slice; two-source isolation and partial workspace behavior remain application integration evidence. |
| `AC-DW-FND-003-02` | Supports only synthetic auth/workspace/forwarding-header selection and stripping; FastAPI host/redirect/SSRF/open-proxy rejection remains application integration evidence. |
| `AC-DW-FND-003-08` | Proves only that this probe/evidence corpus contains no credential reference or reusable secret; normalized application source-view proof remains downstream. |
| `AC-DW-QUAL-001-03` | Supports the named-gate conclusion for key/header combinations; release-manifest omission/disablement remains coordinator/release evidence. |
| `AC-DW-QUAL-001-04` | Supports only the auth/header abuse slice through synthetic stripping, redaction, and cross-workspace negative fixtures; the full cross-layer security suite remains downstream. |

`SPIKE-AUTH-002` is not accepted merely because a public SDK constructs a request.
Any decision-table row requiring live behavior remains blocked until a sanctioned
non-production request confirms it.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/auth
uv sync --project tools/contract-spikes/auth --frozen
uv run --project tools/contract-spikes/auth --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/auth --frozen python -m auth_contract_spikes.inventory --output docs/references/research/auth-contract-spikes/versions.json
uv run --project tools/contract-spikes/auth --frozen python -m auth_contract_spikes.validate_matrix docs/references/research/auth-contract-spikes/matrix.json --require-complete-cross-product --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/auth --frozen python -m auth_contract_spikes.scrub docs/references/research/auth-contract-spikes
uv lock --project tools/contract-spikes/auth --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/auth --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
git diff --name-only b9d244438c90a3031983b9705407b3dd5d4c33f9
```

Only with explicitly supplied, non-production classic-account access, run:

```bash
uv run --project tools/contract-spikes/auth --frozen pytest -m live_contract --live-profile non-production-classic --evidence-dir docs/references/research/auth-contract-spikes/live
uv run --project tools/contract-spikes/auth --frozen python -m auth_contract_spikes.scrub docs/references/research/auth-contract-spikes/live
```

The live command fails closed when the profile is absent. It must not print or
persist tokens, raw authorization/cookie values, reusable endpoints, workspace or
customer names, raw provider bodies, or environment dumps.

## Deterministic fallback

Until each required row is independently accepted:

- enable only the exact validated key/header/account/plane combination;
- reject unsupported workspace selection rather than emitting a guessed `X-*`
  header;
- keep provider credentials server-side and expose only an opaque credential
  reference internally;
- keep the affected source operation unavailable with a typed explanation;
- retain the credential-free demo for unrelated product work; and
- keep OAuth under its separate `SPIKE-AUTH-001` gate.

If no required live row can be accepted, return a complete documented/installed
matrix with `blocked-live-evidence`; do not label the classic API-key baseline
ready.

## Handoff and review

Commit only allowed paths on the named branch. Keep this packet current with
progress, source precedence, contradictions, exact evidence state, decisions,
commands, and blockers. The author cannot accept their own research.
Runtime-contract, security, and product reviewers decide every matrix row and the
overall spike independently.

The coordinator alone updates the source ledger, product plans, application
adapters, normalized contracts, capability flags, program/index, or release state.
No worktree creation, push, merge, deployment, publication, production mutation,
credential collection, or private-beta enablement is authorized by this packet.
