# F08 · Task inbox

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1 · Depth: implementation-ready*

Sources: [UI spec §3.1/§4/§7](../03-ui-spec.md) · [frontend plan Phase A/B](../06-frontend-implementation.md) · [agent-inbox research](../../research/13-agent-inbox.md) · [LangChain UIs research](../../research/04-langchain-uis.md) · [UI contract gap-fill](../../research/21-gapfill-ui-contract.md) · [MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [architecture §7/§10](../02-architecture.md) · [roadmap M1](../04-roadmap.md) · [org intelligence Layer 1](../07-org-intelligence.md)

## 1. Scope

The inbox is the home screen (`/tasks`): the status-grouped, filterable list of every task across the user's configured agent sources, plus the New-task composer modal. This spec owns the inbox **experience** — row anatomy, grouping, status semantics, unread model, refresh strategy, cross-source pagination, filters/URL state, composer UX, and all list states. Roadmap: M1 "Task inbox (threads.search aggregation, status chips, filters) + New-task composer" ([roadmap](../04-roadmap.md)).

**Not owned here** (link, don't duplicate): the `AgentSource` registry, `DataProvider` interface, and raw `threads.search` client → [F04 · SDK & agent sources](./04-sdk-and-agent-sources.md); task detail & streaming; approvals inbox (UI spec §3.3); rubric semantics → [F16 · Verification & rubrics](./16-verification-and-rubrics.md); run-metadata analytics → [F22 · Org intelligence v1](./22-org-intelligence-v1.md). Catalog: [features README](./README.md).

## 2. Dependencies & seams

| Dependency | What the inbox needs from it | Cite |
|---|---|---|
| D-022 — Next.js frontend | Inbox is a route in `apps/web` (App Router); client component over virtualized list | [decisions](../decisions.md) |
| P-005 (provisional) — Python FastAPI `apps/server` glue | Key/streaming-proxy path for browser→deployment calls when keys are server-held. P-005 explicitly supersedes the Next-routes glue still described in [02 §1/§11](../02-architecture.md)/[06 Phase B](../06-frontend-implementation.md) (amended on ratification) → §9 | decisions |
| D-003 — no Deep Work backend/DB | Org is the source of truth; unread state, drafts, seen-timestamps are client-side only (§3.3); nothing inbox-specific is persisted server-side | decisions |
| F04 SDK (`packages/sdk`) | Source registry; per-source `threads.search` fan-out; normalized `TaskSummary`; `DataProvider` with `fixtures` and `live` impls ([06 Phase B](../06-frontend-implementation.md)) | [F04](./04-sdk-and-agent-sources.md) |
| `packages/ui` | `TaskRow`/`TaskList`/`StatusChip`/`EmptyState` per component inventory (UI spec §4); tokens/preset already seeded | [03 §4](../03-ui-spec.md) |
| Platform API | `threads.search({metadata, limit≤100, offset, sortBy:'updated_at', sortOrder:'desc', status?})` per source ([13](../../research/13-agent-inbox.md), [04 L13–14](../../research/04-langchain-uis.md)); thread statuses `idle\|busy\|interrupted\|error` | research |

Seams: the inbox consumes only `DataProvider` (swap fixtures↔live; demo mode stays credential-free per [06 §4](../06-frontend-implementation.md)). Composer's rubric field is a pass-through string to F16. Metadata stamped at creation is the same convention [F22](./22-org-intelligence-v1.md)/[07 Layer 1](../07-org-intelligence.md) rely on for tracing.

## 3. Design

### 3.1 Row anatomy

Fixed-height **72px** rows (agent-inbox measured 71px; we round to the 4px grid), 12-col grid, `px-4 gap-3`, hover `bg-gray-50/90`, divider `border-gray-100` ([13 · UX patterns](../../research/13-agent-inbox.md), [03 §3.1](../03-ui-spec.md)):

| Cols | Region | Content |
|---|---|---|
| 1–7 | Identity | 8px **unread dot** (primary-dark / dark: primary-light; hidden when read, space reserved) · **title** `text-sm font-semibold truncate` · below it one-line **preview** `text-sm text-gray-*` truncate |
| 8–9 | Context chip | Coding: `owner/repo` in mono pill; else agent name pill. Second line (optional): source name when >1 source configured |
| 10 | Status chip | §3.2; interrupt-count badge (`×N`) appended when N>1 |
| 11–12 | Time | Relative (`2m`, `3h`, `Yesterday`), right-aligned `text-xs`; absolute timestamp in `title` tooltip |

Title = first human message, truncated (the cross-UI convention, [04 L14](../../research/04-langchain-uis.md)). Preview = last narration text, else the `in_progress` todo `content`, else last tool name ([03 §3.1](../03-ui-spec.md)). Both rendered as **plain text only** (§6). Whole row is a link to `/tasks/[source]/[threadId]` — both segments come from the row's `TaskSummary` (`sourceId` + `id`), per the [F07 §4.1](./07-app-shell-and-navigation.md) route map; keyboard `j/k` + `Enter` per UI spec §7.

### 3.2 Status chips & grouping

Chip = pill + 6px dot ([03 §3.1](../03-ui-spec.md)). Five states, derived from thread status (the only field `threads.search` reliably returns per row):

| Chip | Color | Pulse | Derivation |
|---|---|---|---|
| Running | blue (primary-dark/light) | subtle dot pulse; off under `prefers-reduced-motion` | `thread.status === 'busy'` |
| Needs review | amber | no | `status === 'interrupted'` |
| Done | green | no | `status === 'idle'` with ≥1 message |
| Failed | red | no | `status === 'error'` |
| Queued | gray | no | Client-derived: optimistic row awaiting first lifecycle event, or `idle` thread with zero assistant output. No server "pending" signal in search results → §9 |

Status colors are never the accent ([03 §1.1](../03-ui-spec.md)). Interrupt-count badge: rendered only when the search payload carries interrupt data for the thread (deep-agents-ui showed per-thread interrupt-count badges, [04 L14](../../research/04-langchain-uis.md)); exact field availability is unverified → §9. Fallback: chip without count — never issue N× `getState` calls for the list.

**Grouping** (presentation over one merged, `updated_at`-desc stream):

1. **Needs you** — Needs review rows (the product's top pillar: agents blocked on humans, [01](../01-vision.md)).
2. **Running** — Running + Queued.
3. **Recent** — Done + Failed, time-bucketed **Today / Yesterday / This Week** (+ **Earlier** for the remainder — addition beyond [03 §3.1](../03-ui-spec.md)'s named buckets), deep-agents-ui pattern.

Group/bucket headers: uppercase micro-labels (12px/600/+5% tracking), sticky within scroll; empty groups are omitted.

### 3.3 Data: aggregation, pagination, refresh

**Per-source query** (verbatim from [03 §3.1](../03-ui-spec.md)): `client.threads.search({metadata: {assistant_id | graph_id}, limit: 25, offset, sortBy: 'updated_at', sortOrder: 'desc', status?})` — UUID → `assistant_id`, graph name → `graph_id` ([04 L13](../../research/04-langchain-uis.md)). Fan-out over all registry sources with `Promise.allSettled`; per-source state `{offset, exhausted, buffer, error?}`.

**The merge problem — v1 answer (honest).** There is no global cursor across deployments. v1 uses per-source offset pages + K-way merge with a **safe-emit watermark**: render merged rows whose `updated_at ≥ W`, where `W = min` over active (non-exhausted, non-errored) sources of that source's oldest fetched `updated_at`; newer-but-unconfirmable rows stay buffered. *Load more* fetches the next page from the source(s) defining `W`, then recomputes. Dedupe key `(sourceId, threadId)`. Accepted flaws, stated up front: offset pagination is unstable under `updated_at` churn (a thread updating mid-scroll can be skipped or duplicated until the next full refresh); errored sources are excluded from the watermark so the rest of the list still paginates (§3.6). Every poll refresh re-fetches pages `1..depth` and rebuilds. ≤ a handful of sources is the design envelope (settings registry, [03 §3.6](../03-ui-spec.md)).

**Refresh strategy — recommendation: polling, not stream presence.** The Agent Streaming Protocol is thread-scoped (`POST /threads/{id}/stream/events`, [21](../../research/21-gapfill-ui-contract.md)); there is no cross-thread/org event feed, and one SSE connection per row does not scale. So:

- Poll the page-1 fan-out every **30s**; tighten to **10s** while any loaded row is Running/Queued; **pause entirely** on `document.hidden`; refetch immediately on window focus, after composer success, and when the push fan-out (run-completion webhooks → Web Push, [02 §7](../02-architecture.md)) delivers a notification.
- Threads already open in a detail view hold a `useStream`; their `lifecycle` events patch that row in the shared cache (no extra requests).
- Budget: 5 sources × 6 req/min ≪ the 2000/10s gateway limit ([20](../../research/20-gapfill-mda-api.md)). Multi-tab dedupe via a `BroadcastChannel` poll leader is a nice-to-have (task 6).
- Revisit if the platform ships an org-level event feed → §9.

**Unread — definition & storage (D-003: no server DB; PROPOSAL, flagged provisional).** A row is unread iff `thread.updated_at > seenAt[sourceId:threadId]` — seen state keys on the composite `(sourceId, threadId)`, same as the dedupe key (§3.3), never `threadId` alone; mark-seen, unread evaluation, and mark-all-read all use it. Mark-seen on opening task detail; threads created from this device start seen; "Mark all read" action in the list header. Store: `localStorage["deepwork.inbox.seen.v1"]` = `{ ["<sourceId>:<threadId>"]: ISO-8601 }`, LRU-capped at 5,000 entries; unavailable/corrupt storage degrades to all-read without error. This is **per-device only** — cross-device unread requires a per-user server-side niche (LangGraph Store user namespace / MDA per-user memory) and is deferred → §9. We explicitly do **not** write read-state into thread metadata: it is shared across viewers (team persona, [01](../01-vision.md)) and would pollute org data.

### 3.4 Filters & URL state (nuqs)

URL is the state ([03 §3.1](../03-ui-spec.md); shared conventions [03 §4](../03-ui-spec.md)). Param scheme:

| Param | Values | Default | Push-down |
|---|---|---|---|
| `status` | `needs-you \| running \| done \| failed \| queued` | unset = all | Server `status`: `interrupted`/`busy`/`idle`/`error`; `queued` filters client-side |
| `agent` | `<sourceId>:<assistantRef>` (registry id + UUID or graph name) | all | Restricts fan-out to one source + its metadata filter |
| `repo` | `owner/name` | all | Server-side via `metadata: {repo}` (arbitrary-key metadata filter, same mechanism as `assistant_id`) |
| `q` | free text | — | Client-side substring over loaded title/preview (no server text search → §9) |
| `depth` | int ≥ 1 | 1 | Pages fetched per source; restores scroll depth on back-nav |

nuqs with `history: 'push'` for `status`/`agent`/`repo`, `replace` for `q`/`depth`. Contextual sidebar (Tasks tab, [03 §2](../03-ui-spec.md)): status list (counts computed from loaded rows, labeled "of loaded"), agent list from the F04 registry, repo list from distinct loaded `metadata.repo` values (GitHub App repo list enriches this at M2).

### 3.5 New-task composer (modal from the navbar CTA)

[03 §3.1](../03-ui-spec.md) specifies a modal off the `[New task]` CTA (the v0 concept's `/tasks/new` page is superseded; keep the route as a deep-link that opens the modal over the inbox).

| Field | Control | Required | Notes |
|---|---|---|---|
| Prompt | auto-growing textarea, ⌘Enter submits | yes (non-empty trimmed) | Draft auto-saved to `sessionStorage` on change |
| Agent | picker: source → assistant | yes; default = registry default | |
| Template | segmented: Research · Writing · Coding | yes; default per agent | = `task_type` assistant configs over one agent (D-014, [02 §3](../02-architecture.md)). Coding gated until M2 (no sandbox in M1, [roadmap](../04-roadmap.md)) |
| Environment | sandbox-snapshot picker | when Coding | Environments = named snapshots + `setup.sh` (D-015, [02 §4](../02-architecture.md)); M2 |
| Repo / branch | repo picker + branch input | repo when Coding; branch optional, default `deepwork/<slug>` | Git flow [02 §4](../02-architecture.md); M2 |
| Require plan approval | toggle | default from template | Jules `requirePlanApproval` pattern ([03 §3.1](../03-ui-spec.md)) |
| Rubric | collapsed "Verification" section: markdown textarea, template default preloaded | optional | Pass-through to `RubricMiddleware` config → [F16](./16-verification-and-rubrics.md); lands M2 per [roadmap](../04-roadmap.md), behind a flag in M1 |

Validation: client-side schema (zod); submit disabled until valid; per-field inline errors on blur.

**Creation flow (optimistic + recoverable):** (1) generate client UUID → `metadata.deepwork_task_id`; (2) disable submit (in-flight guard); (3) `DataProvider.createTask` creates the thread with the full metadata convention (§4); (4) optimistic **Queued** row appears atop *Running*, keyed by the client UUID; (5) first run submitted (with `webhook` param for push fan-out, [02 §7](../02-architecture.md)); (6) navigate to `/tasks/[source]/[threadId]`, modal closes, next poll reconciles the optimistic row. **Failure recovery:** thread-create fails → modal stays open, inline error, draft intact. Thread created but run-submit fails → no orphan hidden: row renders a "Failed to start" variant (Failed chip + Retry that re-submits the run against the *existing* thread — never a second thread). **Double-submit protection:** in-flight guard + `deepwork_task_id` dedupe in the provider's pending set; the server-side `if_not_exists` create param ([20 L9](../../research/20-gapfill-mda-api.md)) is the candidate hard guarantee — exact semantics unverified → §9.

### 3.6 List states

- **Loading:** 8 skeleton rows at exact row geometry + group-header skeletons — skeletons, never spinners ([03 §7](../03-ui-spec.md)).
- **Empty, no sources configured:** "Connect an agent" variant → settings/onboarding CTA.
- **Empty, sources but no threads:** teaching state ([03 §7](../03-ui-spec.md): every empty state teaches the next action): headline + three sample-prompt chips (one per template) that open the composer prefilled.
- **Error (all sources failed):** if a previous good list exists, keep it with a "Stale — last updated Xs ago" banner; else full-pane error card with per-source detail (collapsed) + Retry.
- **Degraded (some sources failed):** rows from healthy sources render normally; inline banner strip "N of M agent sources unreachable — Retry" naming the failed source(s); failed sources drop out of the pagination watermark (§3.3); auto-retry each poll; banner clears on recovery. Per-source, not global — one broken deployment must never blank the inbox.

### 3.7 Performance

Virtualized list (fixed 72px rows make this trivial — `@tanstack/react-virtual` or equivalent chosen in Phase A hygiene), sticky group headers, memoized row rendering keyed on `(threadId, status, updatedAt, unread)`. Target: 1,000 merged rows scroll at 60fps ([03 §7](../03-ui-spec.md) requires inbox virtualization).

## 4. Contracts

**Required of F04 `DataProvider`** (shapes owned by [F04](./04-sdk-and-agent-sources.md); this is the inbox's requirements list): (a) `listTasks({filters, depth})` returning per-source envelopes `{sourceId, threads[]} | {sourceId, error}` so the UI can render degraded states — never a flattened all-or-nothing result; (b) normalized `TaskSummary` per thread: `{id, sourceId, title, preview, status, updatedAt, metadata, interruptCount?}`; (c) `createTask(draft)` implementing §3.5 steps 3–5 with the idempotency key; (d) identical behavior from the `fixtures` implementation for tests/demo ([06 Phase B](../06-frontend-implementation.md)).

**Thread metadata convention — what "task" means.** A *task* is a thread on a configured source. Threads created by Deep Work are stamped at creation (client-side, in `threads.create` metadata) with the same convention [07 Layer 1](../07-org-intelligence.md) mandates for run metadata, so inbox filters and LangSmith dashboards cut on the same keys (cross-ref [F22](./22-org-intelligence-v1.md)):

| Key | Values | Purpose |
|---|---|---|
| `deepwork_task_id` | UUID | Idempotency + optimistic-row reconciliation |
| `task_type` | `coding \| research \| writing` | Template; filter + tracing partition |
| `agent` | assistant name/id | Tracing convention ([02 §10](../02-architecture.md)) |
| `surface` | `web \| desktop \| mobile \| schedule \| dcode` | Origin surface ([02 §10](../02-architecture.md)) |
| `repo`, `branch` | `owner/name`, string | Coding context chip + server-side repo filter |
| *(platform)* `assistant_id`/`graph_id`, `owner` | stamped by SDK / MDA identity | Search key ([04 L13](../../research/04-langchain-uis.md)); tenant scoping ([20 L14](../../research/20-gapfill-mda-api.md)) |

**Foreign threads** (created by Studio, agent-chat-ui, schedules without our stamps) still match the `assistant_id`/`graph_id` search and **must render**: title falls back to first human message, context chip = agent name, no template metadata. The inbox is a truthful view of the org's threads, not only of Deep Work's.

**Unread store:** `deepwork.inbox.seen.v1` → `Record<"sourceId:threadId", ISO8601>`, LRU 5,000 (§3.3). Provisional under D-003.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Thread with no human message | Title fallback: assistant name + created time; never blank row |
| Malformed thread/interrupt payload | Row renders with raw-fallback title, chip from status only; never crashes the list (agent-inbox `improper_schema` lesson, [13](../../research/13-agent-inbox.md)) |
| Offset drift (thread updates mid-pagination) | Duplicate suppressed by `(sourceId, threadId)` dedupe; a skipped thread reappears on next poll rebuild — documented, not "fixed" |
| Thread deleted between poll and click | Detail route 404s gracefully → toast + row removed on next poll |
| 401/403 from one source mid-poll | Treated as degraded source with "Reconnect" action (key expiry ≠ outage); other sources unaffected |
| Clock skew between sources | Ordering uses server `updated_at` verbatim; relative times computed from client clock with 30s floor ("just now") |
| `localStorage` unavailable (private mode) | Unread degrades to all-read silently; composer drafts fall back to in-memory |
| Composer: create ok, run-submit fails | "Failed to start" row + Retry on same thread (§3.5); no orphan, no duplicate |
| Double-click / double ⌘Enter | One thread (in-flight guard + `deepwork_task_id` dedupe) |
| >5,000 seen entries | LRU eviction; evicted old threads may re-show unread — accepted (they're deep in *Earlier*) |
| All sources empty after filter | Filter-specific empty state with "Clear filters" action, distinct from true zero-state |

## 6. Security & privacy

- **Untrusted text everywhere:** titles/previews derive from user prompts and agent output. Render as plain text (React text nodes; no `dangerouslySetInnerHTML`, no markdown in rows) — same untrusted-content posture as webhook payloads ([02 §10](../02-architecture.md)). Hostile-title XSS is an acceptance test (§7.12).
- **Credential paths:** browser talks to sources directly only in local/localStorage mode; otherwise via the key/streaming proxy (P-005 `apps/server`, provisional). Inbox code never reads or logs keys; degraded-state banners show source *names*, never URLs-with-credentials or raw error bodies.
- **Tenant scoping is server-side:** MDA identity stamps `metadata.owner` and fails closed ([20 L14](../../research/20-gapfill-mda-api.md)); the inbox never widens a query beyond what the caller's identity returns, and adds no client-side "cross-tenant" merging beyond the user's own configured sources.
- **Local data minimization (D-003):** unread map holds source/thread IDs + timestamps only — no titles/content; composer drafts live in `sessionStorage` (tab-scoped) and are cleared on successful submit.

## 7. Acceptance criteria

1. With ≥2 configured sources (fixtures + `langgraph dev`), the inbox renders one merged list in `updated_at` desc order; no row older than the watermark appears above one newer (property test on the merge module).
2. Rows are exactly 72px with all five anatomy regions (§3.1); 1,000-row fixture list scrolls at 60fps with virtualization; initial load shows skeletons, never spinners.
3. Status chips map exactly per §3.2 table; Running pulses; pulse disabled under `prefers-reduced-motion`.
4. Groups render Needs you → Running → Recent with Today/Yesterday/This Week/Earlier buckets; empty groups omitted; headers sticky.
5. `status`/`agent`/`repo`/`q`/`depth` round-trip through the URL: hard reload and back-button restore the identical list (nuqs).
6. Unread dot shows for updated-since-seen threads, clears on detail open, survives reload, respects the 5,000-entry cap.
7. While any Running row is visible, changes on the server appear within 10s; zero polling requests while the tab is hidden; immediate refetch on focus.
8. Composer: invalid states cannot submit; a successful submit produces exactly one thread + one run and navigates to detail; a forced run-submit failure produces a retryable "Failed to start" row and retry does not create a second thread; double-click produces one thread.
9. With one of three sources returning 500: healthy rows render, the degraded banner names the failed source within one poll cycle, and recovery clears it automatically.
10. Zero-state variants: no-sources → connect CTA; sources-but-no-threads → three sample-prompt chips that open a prefilled composer. Both actionable.
11. Keyboard: `j`/`k` moves row focus, `Enter` opens, the CTA/composer opens via palette; visible focus states (UI spec §7).
12. A fixture thread titled `<img src=x onerror=alert(1)>` renders as literal text (no script execution, no markup interpretation).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Status-mapping + `TaskSummary` normalization (pure module in `packages/sdk`) | F04 types | §3.2 table encoded; unit tests incl. malformed payloads |
| 2 | `TaskRow`/`StatusChip` in `packages/ui` against fixtures | 1; Phase A tokens | Storybook states: all 5 chips, unread, foreign thread, XSS fixture; 72px verified |
| 3 | Grouping/bucketing presenter (pure) | 1 | Unit tests: group order, bucket boundaries at local midnight, empty-group omission |
| 4 | Multi-source merge paginator with watermark + dedupe | F04 fan-out | Property tests: ordering invariant, dedupe, errored-source exclusion; Load-more targets limiting source |
| 5 | Inbox route in `apps/web`: virtualized list + skeletons | 2, 3, 4 | AC 1–4; 60fps on 1k fixture rows |
| 6 | Poll/invalidation hook (visibility-aware cadence, focus refetch, detail-stream patch-in) | 5 | AC 7; request log shows 0 hidden-tab calls; optional BroadcastChannel leader |
| 7 | nuqs filter params + contextual sidebar | 5 | AC 5; push-down verified against `langgraph dev` (status + metadata.repo) |
| 8 | Unread store + dot wiring + Mark-all-read | 5 | AC 6; private-mode degradation test |
| 9 | Composer modal, M1 field set (prompt/agent/template/plan-toggle; rubric+coding fields flagged) | F04 `createTask` | Validation matrix; drafts survive modal close |
| 10 | Optimistic creation, failure recovery, double-submit protection | 9, 6 | AC 8; forced-failure integration tests |
| 11 | Empty/error/degraded/stale states | 5, 6 | AC 9–10; per-source banner naming |
| 12 | E2E (`langgraph dev` fixture agent) + a11y/keyboard pass | 5–11 | AC 11–12; axe clean in both themes |

## 9. Open questions

1. **Catalog timing:** [decisions.md](../decisions.md) landed mid-draft (parallel session) and confirms D-003/D-022/P-005 as cited; `features/README.md` was still absent at writing — verify neighbor numbering/titles (esp. [F22](./22-org-intelligence-v1.md), not yet drafted) against the catalog when it lands.
2. **P-005 ratification:** provisional — FastAPI `apps/server` glue supersedes the Next-routes description still present in [02 §1/§11](../02-architecture.md), [05](../05-oss-setup.md), and [06 Phase B](../06-frontend-implementation.md) (amend on ratification). Reversal after M0 migrates the inbox's proxy path and §6 credential-path language.
3. **Interrupt counts in `threads.search` results:** deep-agents-ui rendered interrupt-count badges from list data ([04 L14](../../research/04-langchain-uis.md)) — confirm which response field carries interrupts (and whether MDA/hosted tiers include it) in M0 Spike 3 golden transcripts.
4. **Queued detectability:** is a pending (enqueued) run visible in thread status or search payload, or is Queued permanently client-derived (§3.2)?
5. **`if_not_exists` semantics** on thread creation ([20 L9](../../research/20-gapfill-mda-api.md)): usable as the hard idempotency guarantee for §3.5, or client-side dedupe only?
6. **Server-side text search:** any `q` push-down (LangSmith thread search API) or client-side forever?
7. **Cross-device unread:** post-v1 candidate niches — LangGraph Store user namespace vs MDA per-user memory (`/memories/user/`, 0.4.0-dev) — pick one when D-003 is revisited.
8. **Org-level event feed:** does any tier expose a cross-thread event stream (or workspace webhook) that could replace polling? None found in protocol v2 ([21](../../research/21-gapfill-ui-contract.md)).
9. **`human_response_needed` status:** agent-inbox lists it as a thread status ([13](../../research/13-agent-inbox.md)); confirm whether current Agent Server emits it and whether it maps to Needs review.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Offset pagination drift produces visible skips/dupes on busy orgs | Med | Med | Watermark + dedupe + frequent page-1 rebuilds; documented honestly (§3.3); revisit if platform adds cursors |
| `@langchain/react`/SDK 1.0.x churn breaks search/normalization assumptions | High | Low-Med | All platform reads behind F04; golden-transcript contract tests (M0 Spike 3); pins + renovate ([04 risks](../04-roadmap.md)) |
| Per-device unread feels broken to multi-device users | Med | Low-Med | Copy states the limitation; push notifications carry the cross-device signal; §9.7 upgrade path |
| Polling cadence trips gateway limits with many tabs/sources | Low | Med | Visibility pause + BroadcastChannel leader; cadence config in one constant |
| Composer scope creep (M2 fields: coding env/repo, rubric) delays M1 | Med | Med | M1 field set is prompt/agent/template/plan-toggle; M2 fields behind flags with reserved layout (§3.5) |
| MDA invocation gating blocks live-source testing | Med | High | Fixtures provider + `langgraph dev` cover every AC; MDA is additive ([02 §12](../02-architecture.md)) |
