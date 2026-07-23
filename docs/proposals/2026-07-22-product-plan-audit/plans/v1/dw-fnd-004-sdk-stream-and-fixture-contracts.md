---
feature_id: DW-FND-004
title: SDK, stream, and fixture contracts
release: v1
status: proposed
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [sdk, web, api]
surfaces: [web, pwa, desktop, tests]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-LC, SRC-DW, SRC-FE, SRC-LCJS, SRC-LG]
evidence_pins:
  langchain_docs: 7b9215d
  frontend: 8866d39
  canonical_plan: 06f0515
  langchainjs: ee76ea0
  langgraph: 31f90df
dependencies: [DW-FND-001, DW-FND-003, DW-FND-005]
contract_gates: [SPIKE-STREAM-001]
optional_contract_gates: [SPIKE-STREAM-002, SPIKE-HITL-001, SPIKE-CANCEL-001, SPIKE-CHECKPOINT-001, SPIKE-SUBAGENT-001, SPIKE-ARTIFACT-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DIRECT-STREAM-001]
last_reviewed: 2026-07-23
---

# SDK, stream, and fixture contracts

## User outcome

A user sees each message, tool call, reasoning/todo projection, approval, subagent update, checkpoint, and task-status change exactly once—even after disconnect, source failure, tab sleep, or device return. The interface states honestly when a source cannot support an action, and demo/fixture behavior exercises the same normalized contract as live behavior without claiming upstream support.

This plan is proposed and blocked on named contract spikes. `SPIKE-STREAM-001`
proves only the base transport/replay/reconnect cells. Submit/multitask, HITL,
cancellation, checkpoint, subagent, artifact, and optional direct-stream behavior
remain independently gated by their own spikes and fallbacks; none is smuggled into
the base stream claim.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| Classic LangSmith Deployment exposes assistants, threads, runs, state, streaming, and deployment-scoped crons. | Documented at `7b9215d` | High | Use as the public live baseline through a source adapter. |
| Event Streaming protocol v2 subscribes with `POST /threads/{thread_id}/stream/events` and resumes with JSON `since`; durable `event_id` deduplicates while `seq` orders replay/session. | Gated/beta documentation | High as prose; live support unverified | Keep v2 capability-gated and pin minimum server/client versions through `SPIKE-STREAM-001`. |
| Legacy thread streaming and resumable run-join can use `Last-Event-ID` under their own contracts. | Documented | High | Implement separate cursor strategies; never generalize `Last-Event-ID` to protocol v2. |
| Frontend `useStream` documents `stream.submit(...)`, while the wire protocol can use `run.start`/`input.respond`; `stream.send()` and `stream.interrupt()` are unsupported assumptions. | Documented/contradicted | High | Expose normalized mutation services; do not make a React helper the universal wire API. |
| HITL preserves `action_requests[]`, aligned `review_configs[]`, and an ordered decision entry per action. | Documented | High | Preserve exact batch shape and order end to end; do not flatten to one approval. |
| Agent Server documents multitask strategies including `reject`, `rollback`, `interrupt`, and `enqueue`, defaulting to `enqueue`. | Documented for Agent Server | High | Expose only advertised strategies; do not infer them for local/private adapters. |
| Official prose and generated contracts can disagree about exact frontend resume calls. | Direct audit finding | High | Accepted pinned-package/live-contract evidence outranks both for implementation. |
| The prototype demonstrates rich stream tabs but simulates much behavior. | Prototype evidence at `8866d39` | High | Use it for projection and interaction coverage, not transport authority. |
| The pinned LangGraph Python SDK already owns protocol-v2 subscription, replay deduplication, reconnect, and bounded async lifecycle mechanics. | Direct source evidence at `SRC-LG`; installed/live contract unverified | High for reuse direction | FastAPI composes the public SDK behind a source adapter; TypeScript does not recreate upstream protocol mechanics. |
| The pinned LangChain.js repository separates a low-level core, provider adapters, internal fixtures/standard tests, and explicit package exports. | Direct source evidence at `SRC-LCJS` | High for package method | Add `packages/domain`, keep fixtures private, and narrow the SDK to the Deep Work application API. |

## Scope, ownership, and non-goals

### In scope

- Framework-neutral `packages/domain` with client-safe identities, capability/status/error values, normalized event schemas, deterministic reducers, and selectors.
- Browser-safe TypeScript SDK with independent Deep Work query services, mutation services, application-stream transport, generated `/api/v1` client primitives, DTO mapping, cancellation, and typed errors.
- FastAPI source adapters and a credential-safe application stream as the v1 baseline; React streaming remains a consumer, not the transport owner.
- Server-side protocol-v2, legacy-thread-stream, resumable-run-join, polling/full-hydration, and fixture-source adapters composed from pinned public SDKs.
- Normalized application event envelope, server-owned upstream cursor/dedupe/recovery, client-owned opaque application cursor, ordered domain reducer, bounded cache, and full-state recovery.
- Exact HITL batch, queue/multitask strategy, cancellation, checkpoint, subagent, artifact, tool, reasoning, todo, and status projection seams.
- Server-side per-source aggregation with stable identities, independent continuation tokens, watermarks, and partial errors exposed through one Deep Work API cursor.
- Private language-neutral `internal/fixtures` with deterministic clocks, IDs, transcripts, capability manifests, and latency/failure cases; Python source conformance lives with `apps/api`, while TypeScript `internal/adapter-tests` proves generated transport, DTO, client, and reducer behavior.
- SDK compatibility/versioning rules across Next.js 16 web/PWA, Tauri v2, and FastAPI `/api/v1`.

### Ownership

- FastAPI owns actor/source authorization, secret-bearing adapter selection, capability detection, upstream cursors/reconnect, per-source aggregation, application queries/mutations, and the normalized application stream.
- `packages/domain` owns client-safe domain types, statuses, capabilities, safe error codes, normalized event variants, reducers, and selectors.
- `packages/sdk` owns the generated/wrapped Deep Work API client, application-stream client, request cancellation, DTO-to-domain mapping, and optional leaf React bindings. It contains no provider SDK or credential-reference type.
- The Next.js application owns React hooks such as `useTaskStream`, projection subscription lifetime, route hydration, and view state.
- `packages/ui` receives normalized props and events only; it cannot import raw upstream or transport types.
- The Python `packages/agent` owns agent implementation and emits upstream-supported behavior; it does not define the product SDK or application persistence.
- `internal/fixtures` owners maintain normalized golden transcripts. API owners prove Python source-adapter conformance under `apps/api/tests/contract/sources`; `internal/adapter-tests` proves TypeScript client/DTO/reducer conformance with network isolation.

### Non-goals

- A direct-browser LangChain/provider client in the v1 baseline, one React hook for queries/mutations/streaming, or exposing raw upstream event types to components.
- Invented `stream.send()`, `stream.interrupt()`, global thread search, public Fleet CRUD, `/v1/deepagents/*`, arbitrary MDA routes, or client-side credential storage.
- Treating protocol v2 as universally available, treating a reconnect as run cancellation, or using one cursor format across all adapters.
- Flattening HITL batches, reordering decisions, or converting unsupported capabilities into empty-success responses.
- Persisting complete raw event streams indefinitely in Postgres.
- Exposing a server `authRef`, provider endpoint credential, forwarding header, or provider cursor to any client contract.

## Primary journeys

### Start, observe, and complete a classic run

1. The Next.js client calls a normalized mutation service with an idempotency key and selected `AgentSource`.
2. FastAPI authorizes the actor/source and selects the verified classic adapter.
3. The client subscribes only to the Deep Work application stream; FastAPI uses the source's advertised upstream stream/recovery contract through the pinned public Python SDK.
4. The server preserves/deduplicates upstream identity, emits validated source/thread/run-qualified application envelopes, and the pure domain reducer projects messages, tools, todos, approvals, artifacts, subagents, and status.
5. Query services reconcile terminal state; disconnecting the client never cancels the run.

### Disconnect and recover

1. Client connectivity drops while a run continues.
2. The SDK retains only an opaque short-lived Deep Work application cursor and bounded projection checkpoint keyed by actor/session/source/task/run.
3. On reconnect, FastAPI reauthorizes and its source adapter resumes using protocol v2 `since`, verified legacy behavior, official run join, or full hydration according to the advertised source capability.
4. Durable identities suppress duplicate projections; gaps or expired cursors trigger full authoritative hydration.
5. The UI labels recovery/freshness and never invents missing events.

### Submit an ordered approval batch

1. A normalized interrupt preserves aligned `actionRequests[]` and `reviewConfigs[]`.
2. The user supplies one permitted decision per action in the original order.
3. A mutation service validates batch identity, order, allowed decision type, edited arguments, current interrupt version, and idempotency key.
4. The source adapter uses the exact accepted `submit`/resume or `input.respond` contract.
5. Stale/duplicate responses converge without applying an approval twice.

### Aggregate several sources

1. The SDK requests one application page from FastAPI with authorized source scope.
2. FastAPI requests each verified source independently, merges normalized results by update time and stable source/thread key, and retains each provider watermark/cursor server-side.
3. A failed source contributes a partial error; healthy pages remain visible.
4. The opaque Deep Work next cursor lets FastAPI request only sources whose remaining watermark could affect the requested range; it exposes no provider cursor to the browser.

## Complete state matrix

| State | SDK/transport behavior | Required product behavior |
|---|---|---|
| Query loading | Abortable, bounded request with source context. | Region skeleton; preserve shell and unrelated sources. |
| Empty result | Return typed empty collection and evaluated source scope. | Honest empty state, not unsupported state. |
| Stream connecting | SDK connects to the authorized Deep Work stream; FastAPI chooses only a verified source adapter. | Show connecting without claiming run stopped. |
| Stream live | Apply normalized events in deterministic order and bound memory. | Announce meaningful state, not every token. |
| Duplicate event | Ignore by adapter-specific durable identity plus source/run key. | No duplicate message/tool/status. |
| Out-of-order event | Buffer within verified bound or force reconciliation; never silently reorder beyond contract. | Show recovery only if user impact exists. |
| Protocol-v2 disconnect | FastAPI preserves `seq`/`event_id` semantics and resumes upstream with `since` only when capability/version is true; client resumes with an opaque application cursor. | Reconnecting state; run remains active. |
| Legacy disconnect | FastAPI uses adapter-specific legacy recovery only where documented; the browser never constructs the provider header/cursor. | Same normalized reconnect UX, distinct server-side implementation evidence. |
| Cursor expired/gap | FastAPI stops incremental projection, fetches authoritative full thread/run state, and emits a normalized hydration boundary for deterministic rebuild. | Label recovered snapshot/freshness; no false completeness. |
| Browser background/sleep | Release or pause client resources according to policy; never send cancel. | Run continues; foreground rejoin. |
| User cancel requested | Call a verified cancel service independently from stream unsubscribe and await source confirmation. | Show cancelling substate until confirmed. |
| Network offline | Make no live calls; preserve safe bounded projection locally if allowed. | Read-only, timestamped state; mutations disabled. |
| Reconnect after auth expiry | Reauthenticate before resuming or hydrating. | Prompt sign-in and preserve safe return target. |
| Permission lost | Stop subscription, clear protected in-memory data, return typed permission error. | Explain affected source; healthy sources continue. |
| Unsupported capability | Return `CapabilityUnavailable` with evidence state. | Omit/disable action with explanation, never empty success. |
| Unknown runtime contract | Adapter remains disabled. | Discovery/verification path; no guessed request. |
| Contract/schema mismatch | Quarantine unsafe event, record sanitized contract error, stop reducer for affected stream. | Source-scoped `UpstreamContractError` and recovery/support code. |
| Partial aggregate | Return healthy items, failed source records, and stable continuation. | Results remain usable; retry source independently. |
| Stale HITL interrupt | Reject submission before/at source using current batch version. | Refetch current interrupt; do not show approved state. |
| Duplicate HITL submit | Idempotency returns original outcome. | One decision history entry. |
| Invalid/misaligned HITL batch | Contract validation fails; no decision request sent. | Explain source-contract failure; preserve raw data only in protected diagnostics. |
| Fixture success | Fixture source and private transcript corpus provide deterministic clocks/IDs/events and zero external network. | Same API/component/projection contract with Demo marker. |
| Fixture injected failure | Deterministic failure at named sequence. | Same error/recovery states as live adapter. |
| Mobile / constrained client | Use bounded pages, lazy subagent/tool detail, and resumable foreground behavior. | No desktop-only stream action; memory remains within budget. |

## Proposed interfaces

```ts
type RuntimeKind = "classic" | "mda" | "fleet" | "local" | "fixture";
type CapabilityState = "available" | "unavailable" | "gated" | "permission-denied" | "unknown";
type CapabilityEvidenceClass = "documented" | "live-contract" | "fixture";

interface CapabilityEvidence<T> {
  state: CapabilityState;
  value?: T;
  observedAt: string;
  adapterVersion: string;
  contractVersion: string;
  evidenceClass: CapabilityEvidenceClass;
  safeReason?: string;
}

interface AgentSourceView {
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
  capabilities: SourceCapabilities;
  version: number;
}

interface SourceCapabilities {
  invoke: CapabilityEvidence<boolean>;
  threads: CapabilityEvidence<boolean>;
  stream: CapabilityEvidence<"protocol-v2" | "legacy" | "run-join" | "poll" | "none">;
  hitl: CapabilityEvidence<boolean>;
  multitaskStrategies: CapabilityEvidence<ReadonlyArray<"reject" | "rollback" | "interrupt" | "enqueue">>;
  checkpoints: CapabilityEvidence<boolean>;
  subagents: CapabilityEvidence<boolean>;
  schedules: CapabilityEvidence<"none" | "read" | "write" | "source-owned">;
  sandbox: CapabilityEvidence<boolean>;
  deploy: CapabilityEvidence<boolean>;
  configure: CapabilityEvidence<boolean>;
  contextHub: CapabilityEvidence<boolean>;
}

interface NormalizedEvent<T = unknown> {
  sourceId: string;
  threadId: string;
  runId?: string;
  eventId: string;
  sequence?: string | number;
  observedAt: string;
  kind: string;
  payload: T;
}

interface HitlBatch {
  sourceId: string;
  threadId: string;
  runId: string;
  interruptId: string;
  version: string;
  actionRequests: readonly ActionRequest[];
  reviewConfigs: readonly ReviewConfig[];
  status: "pending" | "submitting" | "accepted" | "stale" | "failed" | "cancelled";
}

interface HitlSubmission {
  interruptId: string;
  expectedVersion: string;
  decisions: readonly HitlDecision[]; // same length and order as actionRequests
  idempotencyKey: string;
}
```

Service separation:

- `TaskQueryService` calls FastAPI for normalized tasks/threads/runs and opaque application pagination; it never calls provider sources.
- `TaskMutationService` calls FastAPI to start, submit, steer, cancel, retry, branch, and answer interrupts; server adapters own upstream methods.
- `TaskStreamService` connects/resumes/hydrates through the Deep Work application stream and emits normalized envelopes; it does not own mutations or upstream credentials/cursors.
- `useTaskStream` subscribes to `TaskStreamService` and a reducer; it cannot call guessed raw upstream methods.
- FastAPI `/api/v1` supplies application-owned queries/mutations, source probing/aggregation, and the v1 application stream. OpenAPI generation cannot erase source capability distinctions.

## Runtime capability and fallback

| Runtime/transport | Supported posture | Fallback |
|---|---|---|
| Classic deployment + protocol v2 | FastAPI adapter enables only when minimum version and live transcript pass `SPIKE-STREAM-001`; upstream resumes with `since` and dedupes durable `event_id`. | Separate verified server-side legacy or run-join adapter; otherwise full hydration/poll where documented. |
| Classic deployment legacy stream | Server-side source fallback where captured contract passes; adapter-specific recovery never enters the public client API. | Authoritative query/polling with reduced live UX. |
| MDA | Capability-detected private-beta adapter after `SPIKE-MDA-001` and stream spike. | Classic deployment source or explanatory unavailable state; no guessed custom route. |
| Fleet | Read/invoke only for operations accepted by `SPIKE-FLEET-001`; streaming follows returned deployment/source contract if verified. | Open/use the deployment as a classic source; no Fleet CRUD assumption. |
| Local | Development-only verified Agent Server contract with loopback restrictions. | Fixture mode. |
| Fixture | Always available for supported contributor/demo journeys, network denied. | Reset transcript; never fall through to live. |

Direct browser-to-deployment streaming is outside this v1 table. It may be
introduced for one source only after `SPIKE-DIRECT-STREAM-001` proves scoped
short-lived authorization, CORS, revocation, replay, audit, and exact normalized
parity. Failure preserves the FastAPI application-stream baseline.

If official prose, generated OpenAPI, installed client types, and live behavior disagree, the feature remains false until an accepted spike pins the package/server pair and records the chosen call and transcript. Capability evidence includes adapter version and observation time so upgrades force revalidation.

## Persistence and security

- Postgres stores source-qualified task metadata, provider pagination/recovery cursors where necessary, capability evidence, idempotency, and bounded projection checkpoints—not an unbounded raw event archive.
- Browser persistence contains no credentials, credential references, provider cursors, or private/no-store data. Any application resume cursor is opaque, actor/session/source/task/run scoped, short-lived, and expires with authorization.
- `authRef` exists only in the server-owned source record. It is absent from OpenAPI and `packages/domain`/`packages/sdk`; FastAPI constructs target-specific auth/workspace headers and prevents browser-controlled forwarding.
- Logs/traces redact message content, tool arguments/results, HITL edits, artifacts, repository content, URLs with secrets, and raw upstream error bodies by default.
- Normalizers treat upstream strings/content as untrusted; schema validation, size/depth bounds, safe rendering, and artifact provenance precede UI use.
- Fixture transcripts are synthetic or irreversibly scrubbed and reviewed; they cannot contain real actor, repository, deployment, trace, credential, or tool data.
- Stream caches are bounded by task, byte count, event count, age, and inactive subscription lifetime; eviction never implies runtime cancellation.

## Responsive and accessible behavior

- Mobile uses progressive message/tool/subagent detail and bounded virtualization without changing event order or hiding approvals.
- Connection, recovery, stale, source failure, and capability state use text/icon and a polite live region; token streaming does not create continuous screen-reader announcements.
- Focus remains stable when history hydrates or deduplicates. New content does not steal focus; “jump to latest” is explicit.
- Ordered HITL action/config pairing is exposed programmatically, with one labelled decision group per action and a batch summary before submit.
- Offline/reconnect banners include freshness and action; keyboard and touch users can retry, inspect partial sources, and return to latest content.
- Reduced motion disables streaming shimmer/pulse while preserving deterministic content updates.

## Metrics and guardrails

- Duplicate user-visible events after reconnect: zero in contract and end-to-end suites.
- Accepted transcript events represented in normalized projection: 100%, with explicit intentionally ignored transport metadata.
- Fixture/live conformance for declared capability behavior: 100%.
- Raw upstream types imported by `packages/ui` or feature components: zero.
- Stream memory remains within the accepted long-thread/mobile budget; inactive subscriptions release within the agreed interval.
- Partial-source failure keeps healthy-source results available: 100% for separable queries.
- HITL golden tests prove array length/order, allowed decision types, edit schema, idempotency, and stale rejection.
- Guardrails: no protocol-v2 `Last-Event-ID`, no universal `submit` wire claim, no `stream.send()`/`stream.interrupt()`, no unknown-as-supported capability, and no network in fixture tests.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-001` for package boundaries and fixture CI.
- `DW-FND-003` service/schema cells establish `/api/v1`, source authorization, and adapter/stream security before live SDK integration. `DW-FND-005` establishes source-qualified identities/reducer vocabulary before the corresponding mapper cells. These are acyclic work cells, not reciprocal feature-level blockers.
- `SPIKE-STREAM-001` pins Agent Server, LangGraph/LangChain/deepagents, application stream, and generated-contract versions and captures base subscription, messages, tools, protocol-v2/legacy recovery, disconnect, malformed events, terminal reconciliation, and hydration fallback.
- `SPIKE-STREAM-002`, `SPIKE-HITL-001`, `SPIKE-CANCEL-001`, `SPIKE-CHECKPOINT-001`, `SPIKE-SUBAGENT-001`, and `SPIKE-ARTIFACT-001` separately gate their normalized operation/event cells. Their failure leaves the specific capability unavailable without invalidating base streaming.
- `SPIKE-MDA-001` and `SPIKE-FLEET-001` must establish which normalized operations those runtime labels can truthfully expose.
- Security review must accept cursor storage, content redaction, gateway limits, and fixture scrubbing.

### Proposed rollout

1. Freeze normalized domain types, error taxonomy, source capability states, and deterministic reducer fixtures.
2. Implement query/mutation services against FastAPI fixture endpoints and network-denied transcript replay.
3. Run `SPIKE-STREAM-001`; add only accepted classic adapters with independent protocol test suites.
4. Integrate one internal classic deployment for messages/tools/reconnect before HITL/checkpoints/subagents.
5. Add HITL, multitask, cancel/retry, checkpoint, and subagent cells one verified capability at a time.
6. Add MDA/Fleet adapter cells only after their spikes; keep their flags false otherwise.
7. Qualify background/foreground, offline, long-thread, mobile, and partial-source recovery.

### Rollback

- Disable one stream adapter/capability server-side and fall back to a separately verified adapter or authoritative hydration.
- Preserve source registration and durable run authority; rolling back the UI/SDK never cancels an upstream run.
- Maintain at least one compatible SDK/API contract window during deployment. If normalizer safety is uncertain, stop rendering new events and show a source-scoped recovery state rather than applying raw payloads.

## Executable acceptance scenarios

```gherkin
Scenario: Protocol v2 reconnect renders every event once
  Given a pinned classic deployment advertises accepted protocol v2 support
  And a run emits events with sequence and durable event identifiers
  When the application stream drops after sequence 12
  And FastAPI reconnects upstream with since 12 while the client uses only an opaque application cursor
  Then replayed and new events reduce in order
  And every durable event appears exactly once
  And the browser receives no provider credential or upstream cursor
  And no Last-Event-ID header is used for the protocol v2 upstream subscription

Scenario: Expired cursor recovers through authoritative hydration
  Given FastAPI has a saved adapter-specific cursor that the source rejects as expired
  When the client reconnects
  Then incremental reduction stops
  And FastAPI fetches authorized full thread and run state
  And emits a normalized hydration boundary to the SDK
  And it rebuilds a deterministic projection with a recovered freshness marker
  And it does not claim unseen events were replayed

Scenario: Ordered HITL batch survives the full contract
  Given an interrupt contains two actionRequests and two aligned reviewConfigs
  When the user approves the first and edits the second
  Then the SDK sends exactly two normalized decisions in the original order to FastAPI
  And FastAPI selects and invokes the verified source adapter
  And a duplicate submission with the same idempotency key returns the original result
  And a stale expected version applies no decision

Scenario: Aggregate remains usable during partial failure
  Given three authorized sources with independent pagination
  And one returns 401 while another has a next page
  When the client requests the merged task page
  Then healthy tasks are stably ordered with source-qualified keys
  And the failed source contributes a typed partial error
  And the next cursor preserves each source continuation independently

Scenario: Fixture mode is contract-equivalent and network isolated
  Given the complete normalized transcript suite
  When web/PWA tests run with all network access denied
  Then every declared message, tool, HITL, checkpoint, subagent, error, reconnect, and terminal state renders through production reducers
  And no live repository or credential path is invoked

Scenario: Unknown MDA support produces no guessed request
  Given an MDA-labelled source has no accepted SPIKE-MDA-001 evidence
  When a user attempts an MDA-only action
  Then the mutation service returns CapabilityUnavailable
  And no /v1/deepagents path or arbitrary custom route is called
```
