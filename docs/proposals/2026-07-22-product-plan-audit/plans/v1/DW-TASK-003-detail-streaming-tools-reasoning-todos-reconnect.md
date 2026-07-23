---
feature_id: DW-TASK-003
title: Task detail, streaming, tools, reasoning, todos, and reconnect
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [task-experience, source-platform, agent-runtime, web, desktop]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP, SRC-LCPY, SRC-LCJS, SRC-LG]
evidence_pins:
  frontend: 8866d39
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  langchain_python: 592055e
  langchainjs: ee76ea0
  langgraph: 31f90df
dependencies: [DW-TASK-001, DW-TASK-002, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates:
  - SPIKE-STREAM-001
  - SPIKE-STREAM-002
  - SPIKE-STREAM-003
last_reviewed: 2026-07-23
---

# Task detail, streaming, tools, reasoning, todos, and reconnect

## User outcome

A user can open a task at any point, understand what the agent has done and what it is doing now, inspect safe tool and subagent progress, see todos and artifacts without losing message context, and recover from backgrounding or network loss without duplicated or invented events.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype renders fixture narration, tool cards, approvals, browser evidence, terminal, run context, and subagent panels. | Prototype evidence at `8866d39`; interactive but simulated | Use it as interaction evidence; define normalized runtime projections and all failure states. |
| LangChain frontend documentation describes `useStream`, content blocks, tools, queues, join/rejoin, and HITL. | Documented at `7b9215d` | Reuse its interaction/event lessons behind the Deep Work application stream; do not make a React hook the query/mutation API or give the browser provider credentials. |
| Pinned LangGraph Python code already implements protocol-v2 replay, deduplication, reconnect, and bounded async lifecycle concerns. | Direct source evidence at `SRC-LG`; public/live pairing unverified | Compose its public async API in a FastAPI source adapter and test it; do not reimplement upstream protocol mechanics in TypeScript. |
| Pinned docs describe run/thread resumability with `Last-Event-ID`, while protocol-v2 event-stream docs describe a request-body `since` cursor and durable `event_id` deduplication. | Contradicted within the pinned documentation | `SPIKE-STREAM-001` must identify the exact deployed transport. No generic resume-header assumption is allowed. |
| `submit` and multitask strategies vary by SDK/server generation. | Documented in parts; live compatibility unknown | `SPIKE-STREAM-002` pins submit, enqueue, interrupt, and cancellation behavior. |

## Scope and ownership

### In scope

- Historical thread hydration plus live run events.
- Streaming user-visible text, optionally exposed reasoning summaries/content blocks, tool calls and output, lifecycle, checkpoints, todos, interrupts, artifacts, and subagent summaries.
- Collapsible tool cards with running, complete, error, and incomplete states.
- Todo tray and run-panel mirror with deterministic progress.
- Reconnect after transient loss, tab backgrounding, device sleep, and navigation away/back.
- Event normalization, deduplication, ordering, schema-tolerant unknown events, and stale-run detection.
- Trace links and source/runtime diagnostics.

### Out of scope

- Exposing hidden chain-of-thought or provider-private reasoning not explicitly delivered for user display.
- Treating trace data as the primary message stream.
- Running provider mutations directly from React render state.
- Fabricating tool output, progress percentages, or subagent state when the runtime does not supply them.
- Offline dispatch; offline is a read-only cached experience in v1.

### Ownership

- FastAPI query services own authorized task/thread/run hydration and normalized history snapshots; source adapters own upstream protocol selection, credentials, provider cursors, replay, and recovery.
- FastAPI mutation services own explicit run commands, responses, cancellation, reconciliation, and conversion of validated provider events into the versioned application-stream envelope.
- `packages/sdk` owns only the browser-safe application-stream transport, envelope validation, request cancellation, and DTO-to-domain mapping.
- `packages/domain` owns deterministic event identity, ordering, deduplication, reconciliation, and projection into UI-safe task state without React, HTTP, or provider types.
- Next.js owns rendering, stick-to-bottom behavior, viewport restoration, lazy panels, and accessibility announcements.
- Postgres owns task identity, application cursor/recovery metadata, provider cursor metadata where required server-side, and bounded cached projections; LangSmith remains runtime-authoritative. Ephemeral presentation state stays client-owned.
- The Python agent package emits the documented Deep Work state fields for todos, artifacts, rubric, and subagents.

## Primary journey

1. Opening `/tasks/{taskId}` first requests an authorized history snapshot with task, thread, latest run, messages, current interrupt, todos, artifacts, and a source freshness marker.
2. If a run is active and the source supports live transport, the browser connects to the application stream while the FastAPI source adapter joins upstream using the accepted protocol from `SPIKE-STREAM-001`.
3. FastAPI validates and normalizes each provider event into a versioned application event. `packages/sdk` validates that envelope and maps it to `packages/domain`, whose pure reducer orders, deduplicates, reconciles, and projects task state.
4. Text deltas update the current user-visible content block. Tool deltas update the matching call by call ID and namespace. Full snapshots reconcile rather than append blindly.
5. The user can expand tool cards, reasoning summaries, todos, subagent cards, files, and trace links without interrupting the run.
6. When the app backgrounds, it may disconnect the application stream without cancelling the run. Returning reauthorizes and supplies only an opaque application cursor; the server adapter resumes the verified upstream contract or rehydrates durable state.
7. On terminal lifecycle, the projection reconciles once more from durable thread/run state before displaying Done, Failed, or Cancelled.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Initial history loading | Render stable message/run-panel skeletons. | Hydrate, not-found, forbidden, or error. |
| Historical idle | Show complete history and last source sync time. | Start follow-up or refresh. |
| Connecting live | Keep hydrated history visible and mark live status pending. | Connected, fallback polling, or reconnect error. |
| Live streaming | Render ordered deltas; show Stop/steer only when supported. | Interrupt, reconnect, or terminal. |
| Text block streaming | Preserve markdown stability and announce in throttled chunks. | Finalize block on snapshot/lifecycle. |
| Reasoning available | Collapsed by default, labelled as provider-supplied reasoning/summary. | Expand; redact/omit if policy or source disallows. |
| Reasoning unavailable | Do not render an empty Thinking panel. | None required. |
| Tool requested/running | Show name, safe arg summary, elapsed state, and approval status if relevant. | Output, error, approval, or incomplete. |
| Tool output streaming | Append/diff by call ID; bound memory and rendering. | Complete or error. |
| Tool payload malformed | Show an unknown/raw-safe card with copyable support ID, not a crash. | Continue other events. |
| Todo absent | Hide tray; do not imply zero work if source lacks capability. | Appear on later state. |
| Todo active | Show completed/total and item states from durable values. | Update by snapshot. |
| Subagent active | Show supplied name/task/status; no invented percent. | Complete, fail, block, or become stale. |
| Awaiting approval | Canonical status becomes needs-review and the current interrupt is visible. | Decide through HITL plan. |
| Transient disconnect | Keep last event, show reconnecting, prevent unsafe duplicate mutation. | Resume/rejoin or fallback rehydrate. |
| Resume cursor rejected/expired | Reject or expire the opaque application cursor, rehydrate durable state, dedupe with the domain reducer, then let the server adapter join current head if verified. | Live or stale read-only. |
| Backgrounded | Release client transport without cancel; retain only task identity and a short-lived scoped application cursor where policy permits. | Reauthorize and rehydrate/resume on foreground. |
| Source unreachable | Show last known state as stale with timestamp. | Retry; no false terminal state. |
| Permission revoked | Remove sensitive payloads from active view/cache as policy requires. | Reauthenticate or leave. |
| Run failed | Show normalized failure category, safe message, trace link, and retry eligibility. | Retry via task actions. |
| Run terminal | Reconcile durable truth and stop live indicators. | Follow-up, review, archive, or branch. |
| Offline | Read cached user-visible history only, visibly stale; composer mutation disabled. | Reconnect and rehydrate. |
| Long history | Virtualize/lazy-mount while preserving anchors and findability. | Load older pages on demand. |

## Proposed interfaces and runtime fallback

```ts
type NormalizedEvent =
  | { type: "message.delta"; eventId: string; messageId: string; blockId: string; text: string }
  | { type: "message.snapshot"; eventId: string; message: unknown }
  | { type: "tool.delta"; eventId: string; callId: string; namespace?: string; delta: unknown }
  | { type: "state.snapshot"; eventId: string; values: unknown }
  | { type: "checkpoint"; eventId: string; checkpointId: string; parentId?: string }
  | { type: "interrupt"; eventId: string; interrupt: unknown }
  | { type: "lifecycle"; eventId: string; phase: string }
  | { type: "unknown"; eventId?: string; schemaTag?: string };

interface TaskProjection {
  taskId: string;
  threadId: string;
  runId?: string;
  status: string;
  messages: unknown[];
  toolCalls: Record<string, unknown>;
  todos?: unknown[];
  subagents?: Record<string, unknown>;
  currentInterrupt?: unknown;
  artifacts: unknown[];
  stream: { state: "idle" | "connecting" | "live" | "reconnecting" | "stale"; applicationCursor?: string };
}
```

Application query/mutation operations include `GET /api/v1/tasks/{id}`, paged history reads, a versioned authorized application-stream endpoint, and separate command endpoints. Exact paths remain OpenAPI review outputs. The React hook consumes framework-neutral `packages/sdk` transport plus the pure `packages/domain` reducer; it is presentation integration, not the domain API.

`SPIKE-STREAM-001` must capture golden transcripts from a pinned classic Agent Server and pinned public Python SDK for protocol v2, including the actual upstream resume cursor, event ID, reconnect request, TTL/expiry, replay, deduplication, backgrounding, and cross-instance behavior. It must also capture the separate application-stream envelope/cursor consumed by the TypeScript SDK. The accepted FastAPI adapter chooses exactly one verified upstream mechanism for that source version; the browser never constructs it.

`SPIKE-STREAM-002` must verify `submit` plus `multitaskStrategy` values and what happens to in-flight runs, queued messages, interrupts, and errors. Unsupported strategies are removed from that source manifest.

`SPIKE-STREAM-003` must verify content-block, tools-channel, subagent namespace, todo/state, checkpoint, and interrupt shapes emitted by the starter agent.

Deterministic fallback is server-authorized durable history/state rehydration plus bounded polling of the active run. On upstream or application-cursor failure, FastAPI rebuilds a normalized snapshot and joins only through the verified current-head mechanism; the domain reducer reconciles it. The fallback may lose transient token animation but must not lose durable messages, duplicate tool cards, or claim seamless replay.

## Persistence and security

- Persist only bounded normalized user-visible projections and server-side provider/application cursor metadata needed for recovery; do not store raw authorization headers or unbounded event logs by default. Client storage may contain only a short-lived actor/session/source/task-scoped opaque application cursor.
- Validate every event against size, nesting, content-type, and schema limits before rendering or caching.
- Render markdown, URLs, images, code, and tool output as untrusted content with sanitization, safe link policy, and no automatic script/HTML execution.
- Reasoning content follows explicit provider and product policy; hidden reasoning is never inferred from traces or internal state.
- Authorization is checked on history, stream establishment, reconnection, and every command. A cursor is not authorization.
- Trace links are generated from verified source metadata and do not embed secrets.

## Responsive and accessible behavior

- Mobile uses one message column with run-panel content in labelled tabs/sheets; the composer and current approval remain reachable without covering content.
- Desktop preserves a maximum readable thread width and a collapsible run rail.
- New streaming text is announced in throttled polite regions only when the user is at the live edge; historical hydration is not read aloud wholesale.
- Tool cards use real buttons with `aria-expanded`, textual state, keyboard access, and bounded code regions.
- Stick-to-bottom pauses when the user scrolls away and offers **Jump to latest** with an unread event count.
- Reduced motion disables pulse/spinner loops where a static progress label suffices.
- Virtualization preserves headings, focus, message anchors, and branch/checkpoint links.

## Metrics and guardrails

- Time to first hydrated content, time to live connection, and first user-visible delta.
- Reconnect attempts, success, cursor-expiry, replayed event, and duplicate-event suppression rates.
- Projection reconciliation conflict and unknown-event rates by source/server version.
- Long-task memory/DOM size and dropped-frame budget.
- Tool-card and todo engagement, without logging sensitive arguments or output.
- Guardrails: zero duplicated user-visible messages in reconnect golden tests; zero hidden-reasoning exposure; zero false Done while source truth remains active/unknown.

## Dependencies and rollout

- Depends on identities/status reducer, source manifests, task creation, HITL normalization, and security boundaries.
- Phase 0: accept all stream golden transcripts and projection reducer fixtures.
- Phase 1: classic source history plus live text/lifecycle.
- Phase 2: tools, todos, checkpoints, interrupts, and subagent projection.
- Phase 3: mobile background/reconnect and bounded offline cache.
- Adapters roll out by source/server-version capability. On regression, disable live transport for that adapter and use explicit polling/rehydration rather than downgrade to an unverified protocol.

## Executable acceptance scenarios

```gherkin
Scenario: Protocol cursor expiry does not duplicate content
  Given a golden stream transcript has messages and tool calls before disconnect
  And the resume cursor is expired
  When the client reconnects with its opaque application cursor
  Then FastAPI selects verified upstream recovery or rehydrates durable state
  And the domain reducer reconciles the normalized snapshot/events
  And each message and tool call appears exactly once
  And the UI labels the transition as reconnected rather than claiming replay continuity

Scenario: Unknown tool payload cannot crash the task
  Given the source emits a tool event with an unrecognized schema
  When the FastAPI source adapter validates and safely normalizes the event
  Then the task continues rendering
  And a safe Unknown tool event card shows a support identifier
  And the raw unsafe payload is not inserted as HTML

Scenario: Hidden reasoning remains hidden
  Given a trace fixture contains internal model reasoning not present in user-visible stream blocks
  When the task detail renders
  Then no reasoning panel is created from the trace
  And only explicitly delivered user-visible content is shown

Scenario: One source without resumable streaming uses the honest fallback
  Given a source manifest has stream protocol none and active-run polling true
  When the user opens an active task
  Then durable history renders and run state is polled
  And the UI does not advertise token-level live replay
```
