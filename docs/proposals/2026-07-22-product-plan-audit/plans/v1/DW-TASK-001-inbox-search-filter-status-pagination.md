---
feature_id: DW-TASK-001
title: Task inbox, search, filtering, status, and pagination
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [task-experience, source-platform, application-platform, web]
surfaces: [web, pwa, desktop, api]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
evidence_pins:
  frontend: 8866d39
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
dependencies: [DW-ONB-002, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates:
  - SPIKE-THREADS-001
last_reviewed: 2026-07-22
---

# Task inbox, search, filtering, status, and pagination

## User outcome

A user can scan all tasks they are authorized to see across configured sources, find a task by useful text and metadata, understand why it needs attention, and paginate without duplicates or missing rows. Partial source failure is visible and contained. Deep Work aggregates per source; it does not depend on a nonexistent global thread-search API.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype inbox groups fixture tasks, filters by status, toggles grouping, and links to detail. | Prototype evidence at `8866d39`; functional locally over fixtures only | Preserve the scan model while replacing static filtering with URL state and real source queries. |
| Canonical UI intent calls for Needs you, Running, and Recent, with status chips and source/context metadata. | Internal intent at `06f0515` | Define one canonical status reducer and attention priority. |
| Thread search exists per deployment/source, but a single organization-wide cross-source search is not established. | Documented per source; global assumption contradicted | Query sources independently, normalize, and merge in the application service. |
| Provider cursors, filters, and sortable fields can differ by pinned server/SDK version. | Unknown until live fixture | `SPIKE-THREADS-001` pins query and pagination semantics; Postgres projection provides a deterministic fallback. |

## Scope and ownership

### In scope

- Inbox groups: Needs you, Running, Queued, Recent, Failed, and Archived where supported locally.
- Canonical task status independent of raw thread/run strings.
- Search over title, latest user-visible summary, source, agent, repository, branch, and locally indexed identifiers.
- Filters for status, attention reason, source, agent/assistant, task kind, repository, and updated time.
- Stable URL state and cursor-based pagination across multiple sources.
- Unread/last-seen state, stale-source indicators, refresh, and empty/error/offline behavior.
- Mobile list, desktop dense table/list, keyboard navigation, and virtualization.

### Out of scope

- Cross-tenant or unauthorized search.
- Full-text indexing of hidden reasoning, raw tool arguments, credentials, or arbitrary artifact bodies.
- A replacement for LangSmith trace/run search.
- Bulk destructive task operations.

### Ownership

- FastAPI owns per-source query fan-out, authorization, normalization, status reduction, merge ordering, pagination tokens, and degraded-result diagnostics.
- Postgres owns the minimal task projection, source watermarks, locally authored title/archive/unread state, and searchable safe summaries.
- LangSmith sources remain authoritative for threads, runs, interrupts, and runtime timestamps.
- Next.js owns URL filter state, accessible list rendering, virtualization, and optimistic unread transitions.

## Canonical task status

The reducer consumes thread state, latest run, pending interrupts, local archive state, queue entries, and source health. Priority is deterministic:

1. `archived` when the local task is archived.
2. `needs_review` when a current unresolved interrupt exists.
3. `running` when a latest nonterminal run is executing.
4. `queued` when a run or accepted submission is waiting.
5. `failed` when the latest terminal run failed and has not been superseded.
6. `cancelled` when the latest terminal run was cancelled and has not been superseded.
7. `done` when the latest run completed successfully.
8. `draft` when a local task exists but no run has started.
9. `unknown` when source evidence is incomplete or contradictory.

Raw provider strings never render directly as product status. Reducer fixtures record the source payload and expected canonical result.

## Primary journey

1. Opening `/tasks` requests the first normalized page using URL filters.
2. FastAPI queries each eligible source in parallel, applies per-source authorization, merges live results with the local projection, and returns rows plus source diagnostics.
3. Needs-you rows appear first, then active work, then recent terminal work ordered by stable `updatedAt` and `taskId` tie-breaker.
4. The user filters or searches; the URL updates so back/forward and copied links reproduce the view.
5. Selecting a task opens its detail route while preserving the inbox return state.
6. Pagination advances using an opaque application cursor that contains no credential or raw provider token visible to the client.
7. Background refresh patches rows without reordering a row the user is focused on until an explicit refresh boundary or status-priority change demands it.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Initial loading | Render row skeletons matching final geometry and keep filters operable only when safe. | Replace with results, empty state, or scoped error. |
| Loaded with results | Show canonical status, source, agent, safe preview, update time, unread, and attention reason. | Open, filter, search, refresh, paginate. |
| Empty workspace | Teach connect-source and create-task actions. | Connect or create. |
| Empty filter/search | State which criteria removed results and provide Clear filters. | Adjust or clear without losing route context. |
| One source failed | Show partial results plus a source-specific stale/error banner. | Retry that source or open source settings. |
| All sources failed | Use a full error state; never present cached data as current. | Retry, inspect sources, or use explicitly labelled cached view. |
| Cached/offline | Show last-sync time on every group and disable mutations. | Revalidate when online. |
| Background refresh | Preserve focus and scroll; announce material count/status changes. | Apply stable patch or invite refresh. |
| Row becomes needs-review | Promote at the next safe update boundary and announce once. | Open approval/task. |
| Row deleted at source | Mark unavailable before removing from current focused view. | Refresh; retain local audit reference if policy permits. |
| Permission revoked | Remove sensitive preview immediately and show an access-lost row/state. | Reauthenticate or switch workspace. |
| Unknown status | Use neutral chip and diagnostic-safe copy. | Reprobe source; do not guess done/failed. |
| First page | Previous disabled; opaque next cursor if more results. | Advance. |
| Middle page | Previous state reconstructed from client history; stable rows. | Back or next. |
| End page | Next disabled with an explicit end state. | Change query or back. |
| Stale cursor | Server returns a typed cursor-expired result. | Restart at page one and restore nearest row if possible. |
| Mobile | One-column rows prioritize title, attention, status, source, and time. | Filters open in a labelled sheet. |

## Proposed interfaces and runtime fallback

```ts
type TaskStatus =
  | "draft" | "queued" | "running" | "needs_review"
  | "done" | "failed" | "cancelled" | "archived" | "unknown";

interface TaskSummary {
  taskId: string;
  sourceId: string;
  threadId: string;
  assistantId: string;
  title: string;
  preview?: string;
  status: TaskStatus;
  attentionReasons: string[];
  context: { agent?: string; repository?: string; branch?: string; kind?: string };
  updatedAt: string;
  unread: boolean;
  freshness: "live" | "stale" | "cached";
}

interface TaskPage {
  items: TaskSummary[];
  nextCursor?: string;
  sourceDiagnostics: Array<{ sourceId: string; state: "ok" | "stale" | "error"; checkedAt: string }>;
}
```

`GET /api/v1/tasks` accepts normalized filters and returns `TaskPage`. The application cursor references a server-side or signed pagination snapshot containing per-source cursors and the merge boundary. It is versioned and expiry-bounded.

`SPIKE-THREADS-001` must pin the Python and TypeScript clients and capture, per supported source: thread search filters, assistant/graph filtering, sort stability, provider cursor behavior, interrupt visibility, deleted threads, and permission errors.

Deterministic fallback when a source lacks adequate search is a Postgres projection populated from user-created tasks, direct detail reads, and bounded source synchronization. Search results then carry `freshness: "cached"`; no result is represented as exhaustive. Fleet or MDA sources without a validated listing capability can still open known thread IDs but do not silently participate in global results.

## Persistence and security

- The projection stores only fields needed for navigation, authorization, safe search, and reconciliation. Raw message bodies, reasoning, tool arguments, and artifacts are excluded by default.
- Every row is keyed by Deep Work tenant, source, and provider thread identity; globally unique task IDs are opaque application IDs.
- Queries re-authorize source and workspace membership. Cached rows are not proof of current permission.
- Search input is length-bounded and parameterized. Opaque cursors are signed or server-held, expire, and reveal no provider cursors or tenant IDs.
- Safe previews are derived only from user-visible messages or agent summaries and pass untrusted-content handling.
- Archive and unread are Deep Work application state and are never written into provider metadata unless a separate verified mapping is accepted.

## Responsive and accessible behavior

- Rows are reachable and activatable with keyboard, with one unambiguous accessible name including title, status, source, and attention reason.
- Desktop supports `j`/`k` navigation without overriding text-entry contexts; Enter opens and Space performs only a documented secondary action.
- Virtualization preserves focus, correct list position metadata, and screen-reader access to row content.
- Filters use native-labelled controls in a desktop sidebar and mobile sheet; active-filter count is announced.
- Status uses text and icon/shape in addition to color. Running animation is removed under reduced motion.
- Refresh never steals focus; live updates use a throttled polite announcement.

## Metrics and guardrails

- p50/p95 first-page latency and search latency by number of sources.
- Partial-source failure rate, stale-result rate, and cursor-expiry rate.
- Inbox-to-task-open rate and needs-review time-to-open.
- Status-reducer unknown/conflict rate.
- Search zero-result rate by filter family, without storing raw query text unless consented and redacted.
- Guardrail: no unauthorized cached row preview after a permission-revocation fixture.

## Dependencies and rollout

- Depends on source registry/capabilities, domain identity, status reducer, persistence, and security foundations.
- Phase 0: accept thread-query fixtures and reducer golden tests.
- Phase 1: single classic source with URL filters and cursor pagination.
- Phase 2: multi-source merge with partial-failure diagnostics.
- Phase 3: projection-backed search, offline cache, and virtualization.
- Roll back live aggregation per adapter while retaining clearly stale projection rows and direct known-task access.

## Executable acceptance scenarios

```gherkin
Scenario: Results from two sources merge without a global API
  Given source A and source B each return a deterministic thread fixture
  When the user opens the inbox
  Then FastAPI queries both sources separately
  And returns one list ordered by canonical priority, updatedAt, and taskId
  And no organization-wide thread-search endpoint is called

Scenario: One source fails without hiding the failure
  Given source A returns three tasks and source B times out
  When the inbox loads
  Then the three source A tasks are visible
  And source B has an error diagnostic with retry
  And the page does not claim all sources are current

Scenario: Canonical status favors a pending interrupt
  Given a thread fixture has a running run and an unresolved current interrupt
  When the status reducer evaluates it
  Then the task status is needs_review
  And the attention reason identifies the pending approval

Scenario: Revoked permission removes cached content
  Given a cached task row has a preview
  And the source fixture now returns forbidden
  When background refresh runs
  Then the preview is removed from the response and UI
  And the row becomes an access-lost state
```
