---
feature_id: DW-FND-003
title: Application service, state ownership, and security
release: v1
status: proposed
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [api, security, platform]
surfaces: [api, web, pwa, desktop]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-LC, SRC-DW, SRC-DP, SRC-DA, SRC-LCPY, SRC-LG, SRC-FASTAPI, SRC-SQLA]
evidence_pins:
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  deepagents: 7794b61
  langchain_python: 592055e
  langgraph: 31f90df
dependencies: [DW-FND-001]
contract_gates: [SPIKE-AUTH-002, SPIKE-SOURCE-001, SPIKE-STREAM-001]
optional_contract_gates: [SPIKE-AUTH-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DIRECT-STREAM-001]
last_reviewed: 2026-07-23
---

# Application service, state ownership, and security

## User outcome

A user can sign in, connect multiple authorized runtime sources, return to durable preferences and task metadata, and continue using healthy sources when another fails. Credentials and tenant boundaries remain server-side; Deep Work never invents ownership over LangSmith runtime records or exposes a generic upstream proxy.

This plan proposes Python 3.12, FastAPI, and PostgreSQL as the application-service boundary. It is prepared for review, not implementation-ready. The authentication, control-plane, deployment, MDA, and Fleet request matrices must be accepted from named spikes before any affected live adapter is enabled.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| V1 requires sessions, source registry, selected workspace, GitHub installations, notification preferences, idempotency, and cross-source aggregation. | Product requirement | High | “No database” is incompatible with v1; Deep Work needs durable application-owned state. |
| LangSmith owns assistants/agents, deployments, threads, runs, checkpoints, and traces. | Documented external boundary at `7b9215d` | High for classic deployment | Store references and projections only; never clone runtime authority into Postgres. |
| Control-plane and deployment/data-plane APIs have distinct endpoints and authentication requirements. | Documented in parts; exact matrix incomplete | Medium | Use target-specific adapters and block unverified header/endpoint combinations via `SPIKE-AUTH-001`. |
| The audited plans assumed unsupported global thread search, public Fleet CRUD, `/v1/deepagents/*`, and arbitrary MDA connector routes. | Contradicted/unknown contracts | High | Remove generic passthrough and aggregate per source using only verified operations. |
| Managed Deep Agents is private beta and capability-detected; classic LangSmith Deployment is the supported public baseline. | Audited docs posture | High baseline; low MDA | MDA lives behind `SPIKE-MDA-001`, not in the default application-service contract. |
| Python aligns with LangChain/deepagents and provides a clear server-side credential boundary while TypeScript remains the client contract. | Proposed architecture | Medium until review | FastAPI publishes `/api/v1` OpenAPI; TypeScript SDK consumes the reviewed schema. |
| The pinned LangGraph Python SDK implements protocol-v2 subscription, cursor-aware reconnect, replay deduplication, and bounded async lifecycle behavior. | Direct source evidence at `SRC-LG`; public/live pairing unverified | High for reuse direction | Compose its pinned public async API behind an adapter; do not recreate protocol mechanics in routers or React. |
| The reference Python packages use package-local environments, explicit public surfaces, async lifecycle, and narrow protocol boundaries. | Direct source evidence at `SRC-DA`/`SRC-LCPY` | High for engineering method | Package API and worker as independently runnable processes from one application distribution with typed ports/adapters. |

## Scope, ownership, and non-goals

### In scope

- Python 3.12 FastAPI application service with Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, structured logs, metrics, and OpenTelemetry/LangSmith tracing where safe.
- One `deepwork-api` Python distribution with separate API and worker entry points deployed as independent processes. The API accepts work; the worker executes durable jobs from a transactional PostgreSQL outbox/job table.
- Versioned `/api/v1` application operations and an OpenAPI artifact consumed by `packages/sdk`.
- Server-managed sessions, actors, tenant/org/workspace context, source registrations, source capability snapshots, onboarding progress, preferences, and audit records.
- Encrypted credential references, secret rotation metadata, GitHub installation IDs, push subscriptions, notification preferences, and webhook/idempotency state.
- Per-source query fan-out, stable aggregation, bounded concurrency, source-scoped pagination, and partial failure.
- Allowlisted target-specific adapters for classic LangSmith Deployment, capability-gated MDA/Fleet, local development, GitHub, and push.
- A versioned FastAPI application stream as the v1 boundary for web, PWA, Tauri, and future mobile. The server composes the pinned official async LangGraph SDK and keeps upstream credentials/cursors inside the adapter boundary.
- S3-compatible object storage for Deep Work-owned attachments, quarantined imports, and generated exports, with PostgreSQL metadata, authorization, scanning state, retention, and deletion records.
- Bounded retries, leases, idempotency, reconciliation, dead-letter visibility, and shutdown recovery for accepted background work. Redis/Celery is not a default dependency and requires measured need.
- Health/readiness, migration compatibility, retention, deletion, backup/restore, and operational recovery contracts.

### Ownership

- FastAPI owns application authorization, session enforcement, `/api/v1`, normalized orchestration, adapter selection, capability probing, upstream streaming, per-source aggregation, redaction, and audit-event creation.
- The worker owns durable webhook processing, notification delivery, scheduled/reconciliation work, import scanning, and other accepted asynchronous jobs; it uses the same application use cases and ports without importing HTTP routers.
- Postgres owns only Deep Work application records and bounded projections listed below.
- Object storage owns approved Deep Work bytes; provider-owned artifacts remain references unless an owning feature explicitly approves a bounded cache.
- The separate Python `packages/agent` owns agent runtime code and pinned LangChain/deepagents dependencies; it cannot read application-service tables or secret stores directly.
- LangSmith/Agent Server owns deployments, assistants/agents, threads, runs, events, checkpoints, interrupts, sandboxes, schedules where supported, and traces.
- `packages/domain` owns client-safe semantic models and reducers. The TypeScript SDK owns the generated/wrapped Deep Work API client and application-stream client; React hooks remain in the web application layer.
- Web/PWA and Tauri consume the same `/api/v1` and SDK contracts. Tauri receives no broader upstream access.

### Non-goals

- Replacing LangSmith as runtime authority or copying full threads, traces, artifacts, or sandbox files into Postgres.
- A generic URL/method/header proxy, user-authored connector routing, or browser access to raw provider credentials.
- Direct browser-to-provider transport in the v1 baseline, provider cursor persistence in clients, or accepted jobs held only in FastAPI process memory.
- Public Fleet CRUD, `/v1/deepagents/*`, global upstream thread search, reimplementing `mda deploy`, or arbitrary MDA custom routes.
- A pure-OSS runtime backend in v1, enterprise RBAC administration, or native mobile service APIs beyond PWA needs.
- Claiming that one credential or workspace header is valid across control and deployment planes before verification.

## State ownership and retention

| State | Authoritative owner | Deep Work persistence | Proposed retention/deletion |
|---|---|---|---|
| Actor and Deep Work session | Deep Work | Actor, session hash/reference, issue/revoke timestamps, client binding | Session expiry plus bounded revocation evidence; actor deletion policy |
| Org/workspace selection | Provider for membership; Deep Work for selection | Provider identifiers, display metadata, last verification | Until selection changes, access is revoked, or account is deleted |
| Agent source and capabilities | Deep Work registry; provider proves reachability | Endpoint class, assistant binding, auth reference, workspace context, last probe/result | Until removed; retain redacted audit tombstone |
| Credential material | Encrypted secret store | Opaque reference, type, fingerprint, key version, expiry/revocation metadata | Until replaced/revoked/removed; ciphertext deleted under policy |
| GitHub installation | GitHub for installation; Deep Work for binding | Installation ID, account/repository scope metadata, last verification | Installation lifetime plus audit tombstone |
| Push subscription/device preference | Deep Work/browser push service | Endpoint encrypted or protected, key material, device label, preference | Until unsubscribe, expiry, provider rejection, or deletion |
| Webhook/idempotency | Deep Work | Event hash/key, source, status, timestamps, safe result | Bounded operational window |
| Background job/outbox | Deep Work | Tenant, kind, payload reference, idempotency key, lease, attempts, result/error class, timestamps | Operational/forensic window by job class; content minimized |
| Deep Work attachment/import/export bytes | Deep Work object store | PostgreSQL metadata plus quarantined/active/deleted object reference, hash, size, media type, scan and authorization state | Owning feature policy; lifecycle deletion is auditable |
| Rename/archive/unread/display preferences | Deep Work | Actor-scoped metadata keyed by application task/source identity | User-controlled; deleted with account/workspace policy |
| Agent/thread/run/checkpoint/trace | LangSmith/Agent Server | Stable source-qualified reference and bounded cache/projection only | External policy; local cache TTL/delete |
| Artifact/file/sandbox | Source runtime or artifact owner | Provenance and access reference only unless owning plan approves bounded cache | Source policy; cache TTL and authorization recheck |
| Demo state | Fixture repository | Isolated synthetic session/namespace | Reset or short expiry; never merged with live identity |

## Primary journeys

### Register and use a source

1. An authenticated actor selects an authorized org/workspace.
2. FastAPI accepts a source descriptor and secret through a source-type-specific operation, validates format, encrypts the credential, and stores only its reference in the source record.
3. The adapter probes the minimum documented endpoints for that runtime tier and records each capability as true, false, unknown, or gated with evidence time/version.
4. The TypeScript SDK receives a client-safe `AgentSource` without secret material.
5. Queries fan out only to selected/authorized sources; results carry stable source-qualified identities and per-source errors.
6. On credential revocation, that source moves to needs-attention while healthy sources remain available.

### Aggregated task query

1. The client requests `/api/v1/tasks` with an opaque Deep Work page cursor and authorized source scope.
2. FastAPI validates actor/workspace/source access and fans out through per-source adapters with bounded concurrency.
3. Each adapter uses only its verified pagination/search contract; no global upstream search is assumed.
4. The service normalizes and merges results with source/thread keys, update watermark, and source-scoped continuation state.
5. A failed source contributes a typed partial error and does not erase healthy results.

### Credential rotation and account deletion

1. The actor replaces or revokes one source credential; mutation is audited and all cached capability/authorization state is invalidated.
2. In-flight safe reads finish or fail with a specific credential-rotated result; new calls use only the new reference.
3. Account deletion revokes sessions and removes Deep Work-owned records/secret material after confirmation.
4. External LangSmith/GitHub resources are enumerated as separately owned and are never silently deleted.

## Complete state matrix

| State | API behavior | Client/recovery behavior |
|---|---|---|
| Request loading | Correlation ID and bounded timeout established; no sensitive payload logged. | Region-level loading; duplicate mutation prevented. |
| Healthy / success | Enforce actor, tenant, workspace, and source scope on every request. | Render normalized data and freshness. |
| Empty authorized result | Return empty collection plus evaluated source scope and cursors, not `404`. | Purposeful empty state; creation/onboarding action. |
| Authentication expired | Return typed `401 session_expired`; attempt no upstream mutation. | Freeze mutations, reauthenticate, preserve safe return target. |
| Permission denied | Return typed `403` without leaking resource existence across tenants. | Explain required role or source/workspace change. |
| Unknown or unsupported capability | Return `capability_unavailable` with source and evidence status. | Disable/omit action with explanation; never treat as empty success. |
| Credential revoked | Mark only the source needs-attention; invalidate caches and capability claims. | Healthy sources continue; replace/remove credential. |
| One source fails | Return healthy aggregate plus source-scoped partial errors and stable next cursor. | Keep results; retry failed source independently. |
| All sources fail | Return typed aggregate unavailable result preserving safe last-known metadata only when policy allows. | Full error with per-source recovery; no fixture fallback. |
| Upstream rate limit | Preserve safe retry-after, use bounded backoff/jitter, and avoid retry storms. | Countdown/manual retry without blocking other sources. |
| Upstream timeout/disconnect | Cancel outbound request where safe and mark retryability. | Retry source; streams follow `SPIKE-STREAM-001`. |
| Database unavailable | Readiness fails; mutations, sessions, credentials, and sensitive reads fail closed. | Service-unavailable state; do not serve stale sensitive data. |
| Secret store unavailable | Do not retrieve or accept credentials; healthy operations not requiring secrets may continue only if explicitly safe. | Source operations unavailable with support code. |
| Migration pending/incompatible | Readiness blocks incompatible traffic before serving. | Maintenance response with retry guidance. |
| Duplicate idempotent mutation/webhook | Return original safe outcome; execute side effect once. | Converge without duplicate notification/run. |
| Concurrent/stale mutation | Return `409 stale_version` with current version and safe diff metadata. | Refetch/review; never overwrite silently. |
| Offline client | No request reaches service; service does not infer user intent. | PWA/Tauri show cached read-only state and disable mutation. |
| Reconnect | Reauthorize session/source and refresh capability/freshness before queued UI intent can run. | Resume reads; v1 does not auto-send sensitive offline mutations. |
| Mobile | Same `/api/v1` authorization and payload contract, with bounded page sizes and no desktop-only auth path. | Responsive PWA behavior; no raw key in browser storage. |
| Account deletion running | Mark destructive workflow, revoke sessions, and make retries idempotent. | Show progress and separately owned external resources. |
| Account deletion partial failure | Keep deletion job/audit state and block normal access; never restore deleted secret material silently. | Resume/support path with explicit external ownership. |

## Proposed interfaces

### Service internals and process topology

`apps/api` is one independently installable Python distribution with two
entry points built from the same application and domain modules:

```text
deepwork_api/
  transport/          FastAPI routes, SSE envelopes, auth middleware, webhooks
  application/        use cases, authorization orchestration, transactions
  domain/             Python-only entities, policies, errors, transitions
  ports/              protocols for sources, secrets, objects, jobs, clocks
  adapters/
    persistence/      SQLAlchemy repositories, unit of work, migrations
    sources/          classic, gated MDA/Fleet, local, and fixture adapters
    secrets/          secret-manager/KMS implementation
    objects/          S3-compatible objects and scanner integration
    github/           GitHub App and token broker
    notify/           push, email, and desktop-notification hints
  workers/            outbox leases, handlers, retry/dead-letter/reconciliation
  contracts/          Pydantic request, response, event, and OpenAPI models
  bootstrap/          validated settings, dependency construction, entry points
```

Dependencies point inward: transport and workers call application use cases;
application depends on domain and ports; adapters implement those ports.
Routers do not call provider SDKs or SQLAlchemy models directly. Domain code
does not import FastAPI, SQLAlchemy, provider packages, or environment state.
API and worker deploy as separate processes from the same immutable artifact so
they can scale, drain, restart, and report readiness independently.

```ts
type RuntimeKind = "classic" | "mda" | "fleet" | "local" | "fixture";
type CapabilityState = "available" | "unavailable" | "gated" | "permission-denied" | "unknown";
type CapabilityEvidenceClass = "documented" | "live-contract" | "fixture";

interface AgentSourceRecord { // server-only conceptual record; never serialized
  id: string;
  tenantId: string;
  label: string;
  runtime: RuntimeKind;
  endpointOrigin: string;
  assistantId: string;
  authRef: string;
  workspace?: { organizationId?: string; workspaceId?: string };
  version: number;
}

interface AgentSourceView { // public packages/domain model
  id: string;
  label: string;
  runtime: RuntimeKind;
  endpointLabel?: string;
  assistant?: { id: string; label?: string };
  health: "healthy" | "degraded" | "needs-attention" | "unknown";
  credential: {
    state: "configured" | "missing" | "expired" | "revoked" | "unknown";
    expiresAt?: string;
  };
  capabilities: Record<string, {
    state: CapabilityState;
    value?: unknown; // narrowed by the named capability in packages/domain
    observedAt: string;
    adapterVersion: string;
    contractVersion: string;
    evidenceClass: CapabilityEvidenceClass;
    safeReason?: string;
  }>;
  version: number;
}

interface ApiProblem {
  type: string;
  code: string;
  title: string;
  safeDetail?: string;
  correlationId: string;
  retryable: boolean;
  sourceId?: string;
  retryAfterSeconds?: number;
  currentVersion?: number;
}
```

Proposed `/api/v1` resource families:

- `/api/v1/session`, `/api/v1/auth/*`, and `/api/v1/workspaces` for Deep Work session and verified identity context.
- `/api/v1/sources` and `/api/v1/sources/{id}/probe` for normalized source registration/capability evidence through target-specific request schemas.
- `/api/v1/tasks` for per-source aggregation and application-owned task metadata; it is not a global upstream search endpoint.
- `/api/v1/preferences`, `/api/v1/push-subscriptions`, `/api/v1/github/installations`, and `/api/v1/webhooks/*` for application-owned state.
- `/api/v1/tasks/{taskId}/stream` (exact route shape remains schema-reviewed) as the credential-safe application stream over the contract accepted by `SPIKE-STREAM-001`; clients never select arbitrary provider hosts or headers.
- `/api/v1/audit-events` for authorized actor/resource-scoped audit review, never raw provider payload replay.

Mutations require an idempotency key where repetition can create an external side effect and an expected resource version where concurrent overwrite is possible. OpenAPI-generated types are reviewed through `DW-FND-004`; the React streaming hook is not the mutation service.

## Runtime capability and fallback

- Classic LangSmith Deployment is the enabled public baseline after exact endpoints/headers are verified by `SPIKE-AUTH-001` and captured contract tests.
- MDA is a private-beta adapter with capability detection and `SPIKE-MDA-001`; absent or failed verification means the source cannot expose MDA-only actions. Deep Work does not recreate `mda deploy`.
- Fleet read/invoke is enabled only for operations accepted by `SPIKE-FLEET-001`; there is no assumed Fleet CRUD.
- Local-direct source support is development-only, loopback-only, explicitly enabled, and subject to stricter host/port rules. Production browsers do not become arbitrary local proxies.
- Every source operation has one of: supported adapter, explanatory capability-unavailable response, or owning feature fallback. Unknown never means supported.
- Per-source aggregation replaces nonexistent global thread search. A source without server-side search may support bounded local filtering of fetched pages with a visible limitation.
- Context Hub, schedules, connectors, sandboxes, and custom routes are exposed only by their owning capability plans and verified adapters.
- FastAPI mediation is the v1 stream fallback and baseline, not an exceptional proxy. `SPIKE-DIRECT-STREAM-001` may approve a browser-direct optimization for one source only after proving short-lived scope, revocation, CORS, replay, audit, and normalized parity; failure leaves the application stream unchanged.

## Persistence and security

- Use envelope encryption with versioned data-encryption keys and a rotatable key-encryption key; database rows store opaque references and safe fingerprints, never plaintext secrets.
- Store application-owned bytes in a private S3-compatible bucket with tenant-qualified object keys, server-side encryption, checksum/size/type validation, quarantine and malware scanning before use, signed-download expiry, and lifecycle deletion. Do not store attachment bodies in relational columns.
- Insert accepted jobs/outbox records in the same transaction as their application state change. Workers lease with bounded expiry, renew safely, make side effects idempotent, expose dead-letter/reconciliation state, and never treat process memory or FastAPI `BackgroundTasks` as durable acceptance.
- Use secure HTTP-only same-site cookies plus CSRF defense for web/PWA; Tauri receives a short-lived device-bound session token through its verified system-browser flow.
- Enforce strict CORS, trusted host/origin policy, request size limits, content types, timeouts, and schema validation before adapter dispatch.
- Prevent SSRF with source-type endpoint templates, allowed schemes/ports/paths, DNS/IP revalidation, redirect denial, private/link-local/metadata network blocks, and egress policy.
- Strip caller-supplied authorization, forwarding, workspace, host, cookie, and tracing headers; adapters construct only accepted headers.
- Validate webhook signature, timestamp, source binding, nonce/idempotency, and replay window before reading payload semantics.
- Use least-privilege database roles and a separate migration identity; test backup restore, tenant isolation, key rotation, and deletion.
- Redact credentials, raw tool content, provider response bodies, repository content, and user prompts from logs/traces by default. Audit records store a redacted change summary.
- Durable caches include source, actor/workspace authorization, observed time, expiry, and contract version; sensitive/stale cache data is never served across authorization changes.
- Keep provider cursors, credentials, and provider error bodies server-side. A client application-stream cursor is opaque, actor/session/source/task scoped, short-lived, and invalidated on authorization or contract changes.

## Responsive and accessible behavior

- API errors supply concise safe text and stable codes so web/PWA/Tauri can render equivalent accessible recovery without parsing provider prose.
- Long operations expose progress/polling state or bounded retry metadata; clients do not rely on indefinite spinners.
- Mobile payloads use bounded pagination and progressive detail; authorization and mutation safety do not weaken for smaller clients.
- Partial-source failures are announced once at the owning region, not once per list row; focus stays on the initiating control for recoverable validation errors.
- Session expiry, permission denial, stale conflict, offline, and destructive confirmation use consistent normalized states from `DW-FND-002`.
- Tauri native notifications and deep links reauthorize through the same API before revealing task content.

## Metrics and guardrails

- Sensitive application mutations with actor-scoped audit event and correlation ID: 100%.
- Credentials returned by browser API, logs, traces, analytics, error bodies, or fixtures: zero.
- Cross-tenant authorization test escapes: zero.
- Duplicate externally effective webhook/idempotent mutation executions: zero.
- Healthy-source result availability during one-source failure: target 100% for separable queries.
- Source probe success/failure/unknown rates segmented by runtime and pinned adapter version.
- p95 `/api/v1` application overhead excluding upstream latency within an accepted budget; fan-out concurrency and timeout guardrails prevent source amplification.
- Guardrails: no arbitrary passthrough, no unknown-as-supported capability, no cross-source ID without `sourceId`, no unbounded retry, and no migration without restore/rollback evidence.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-001` for Python/TypeScript boundaries and CI.
- Service schema/state and migration work lands before live adapter/stream integration. `DW-FND-004/005` consume and refine the public SDK/domain contract in later acyclic work cells; none of the three foundation specs becomes a reciprocal machine blocker.
- `SPIKE-AUTH-002`: exact API-key and workspace header matrix for the classic baseline. Unaccepted cells stay disabled.
- `SPIKE-SOURCE-001`: safe source endpoint, identity, health, and capability probe for each enabled source class.
- `SPIKE-AUTH-001`: optional OAuth identity/control-plane/deployment token-audience matrix. Failure retains the API-key baseline.
- `SPIKE-MDA-001`: private-beta availability, supported discovery/invoke/config/deploy surface, and CLI ownership. MDA remains gated if incomplete.
- `SPIKE-FLEET-001`: exact Fleet read/invoke contract. CRUD is absent unless future evidence creates a separate reviewed plan.
- `SPIKE-STREAM-001`: required before any stream gateway endpoint is considered implementation-ready.
- `SPIKE-DIRECT-STREAM-001`: optional optimization gate only; it cannot block the server-mediated application stream baseline.
- Security threat model, privacy/retention review, data-owner matrix, and backup/restore rehearsal are release gates.

### Proposed rollout

1. Accept state ownership, threat model, adapter policy, error model, and retention decisions.
2. Establish Postgres schema/migrations, object-store quarantine, API/worker entry points, transactional outbox/jobs, session foundation, encryption, audit events, and per-process health/readiness in fixture integration tests.
3. Add source registry with classic-deployment adapter only for verified contract cells.
4. Add per-source aggregation, bounded caches, and the FastAPI application stream over the pinned official Python SDK after captured contract tests.
5. Add GitHub, push, webhook, and deletion workflows behind separate flags.
6. Enable MDA/Fleet adapter cells only after named spikes and security review.
7. Run tenant-isolation, SSRF, replay, key-rotation, migration, restore, worker-crash/lease recovery, object quarantine/deletion, stream reconnect, and partial-source chaos acceptance before cohort rollout.

### Rollback

- Disable an adapter or operation through a server-side capability flag without changing stored source identity.
- Roll back FastAPI and TypeScript SDK only as a schema-compatible pair or through a documented compatibility window.
- Use expand/migrate/contract database changes; restore the prior app before contracting. Irreversible deletion never uses automatic rollback.
- Preserve audit history and idempotency records across rollback. Revoke affected sessions/credentials if a security boundary is uncertain.

## Executable acceptance scenarios

```gherkin
Scenario: One revoked source does not take down the workspace
  Given an actor has two authorized classic deployment sources
  And one source credential is revoked
  When the actor requests /api/v1/tasks
  Then healthy-source tasks are returned
  And the revoked source appears as a typed partial error and needs-attention source
  And no credential is returned to the client

Scenario: The application service is not an open proxy
  Given an authenticated actor controls a proposed source payload
  When they submit an unallowlisted host, redirect, method, header, private IP, or oversized body
  Then FastAPI rejects it before outbound traffic
  And the audit/log record contains only sanitized metadata

Scenario: A webhook side effect executes once
  Given a valid signed webhook fixture with an idempotency key
  When the same event is delivered concurrently and later replayed
  Then one notification or state transition is created
  And every response converges on the original safe outcome
  And the replay attempt is auditable

Scenario: Stale mutation cannot overwrite current state
  Given two clients read source version 7
  And the first client updates the source to version 8
  When the second client submits a mutation expecting version 7
  Then /api/v1 returns a stale_version conflict with current version 8
  And no provider request is sent

Scenario: MDA and Fleet remain gated without accepted contracts
  Given SPIKE-MDA-001 and SPIKE-FLEET-001 are incomplete
  When a source is registered with those runtime labels
  Then unverified operations have gated or unknown capability states
  And no /v1/deepagents route, Fleet CRUD call, or mda deploy reimplementation is attempted

Scenario: Account deletion respects external ownership
  Given an actor owns Deep Work sessions, source references, preferences, and external LangSmith resources
  When they confirm account deletion
  Then Deep Work revokes sessions and deletes application-owned state and secret material idempotently
  And it does not silently delete LangSmith or GitHub resources
  And the remaining external resources are explained before final confirmation

Scenario: Accepted background work survives an API restart
  Given an authorized mutation commits application state and one outbox job
  When the API process stops before the side effect begins
  And a worker later leases the durable job
  Then the side effect executes at most once under its idempotency key
  And retry, lease expiry, terminal failure, and reconciliation remain visible

Scenario: A public source view reveals no credential reference
  Given a source record contains an encrypted credential reference and provider endpoint
  When an authorized web, PWA, or desktop client reads that source
  Then the response contains only safe display metadata, credential state, health, and capability evidence
  And it contains no authRef, token, forwarding header, signed URL, or reusable provider credential
```
