# F18 · Schedules & Activity

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M3 · Depth: implementation-ready*

Sources: [UI spec §3.5](../03-ui-spec.md) · [Architecture §6, §10](../02-architecture.md) · [MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [Roadmap M3](../04-roadmap.md) · [Frontend plan Phase E](../06-frontend-implementation.md) · [Org intelligence](../07-org-intelligence.md) · [Lifecycle/auth follow-up](../../research/12-lifecycle-auth-followup.md) · [UI contract gap-fill](../../research/21-gapfill-ui-contract.md) · [Runtime tiers gap-fill](../../research/23-gapfill-runtime-tiers.md) · [Competitor teardown](../../research/03-competitor-teardown.md) · [Decisions](../decisions.md)

## 1. Scope

Owns the two shell tabs from UI spec §3.5 plus the cron plumbing beneath them:

| In scope | Out of scope (neighbor) |
|---|---|
| **Schedules tab**: org-wide cron list aggregated across agent sources; per-schedule prompt/input, next-run, enable/disable, edit, delete | Org-analyst / consolidation schedule **templates** and what they do → [F22](./22-org-intelligence-v1.md) (this spec provides the surface they prefill) |
| **`CronEditor`** component (`packages/ui`, inventory item in UI spec §4) | Channels/`deliver_to` **delivery** (Slack etc.) — 0.4.0-dev only; field is flagged-off here, owned by a future channels feature (post-v1 backlog, no spec yet) |
| `define_schedule` (project) vs UI-created cron distinction/merge rules | Agent config editor where `schedules/` files are edited → [F17 fleet manager](./17-fleet-manager.md); this spec's list deep-links there |
| **Run history** per schedule → task detail; run↔schedule correlation metadata | Tracing-metadata convention ownership → F22 (we consume + extend it with schedule keys) |
| **Activity tab**: cross-agent recent-runs feed, filters, pagination, slim counts | Charts/analytics — Deep Work deep-links out rather than re-implementing observability (doc 02 §10, following D-003's wrapper stance); LangSmith deep links only (P-002; doc 06 Phase E) |
| **Untrusted-content rendering rule** for fired-run/webhook payloads (component + where it applies) | Agent-side payload wrapping middleware (`packages/agent` → [F14](./14-agent-package.md)); thread-view rendering internals → [F09](./09-task-detail-and-streaming.md) (we define the boundary contract it consumes) |
| SDK surface (`packages/sdk` crons client) and pass-through via the `apps/server` key proxy (P-005 → [F28](./28-backend-glue-service.md)) | Any Deep Work-side database or scheduler — none exists in v1 (D-003; doc 02 §1) |

Roadmap anchor: M3 — "Schedules CRUD (crons API) + Activity feed; untrusted-payload rendering" ([04-roadmap](../04-roadmap.md)). v1 release criterion 5 requires untrusted-payload boundaries on **all** webhook/schedule content.

## 2. Dependencies & seams

| Dependency / seam | Direction | Detail |
|---|---|---|
| Agent Server crons API (`POST /runs/crons`, `POST /runs/crons/search`) | consumes | Verified surface: mda binary calls both against the **deployment's own Agent Server**, not the control plane ([research 20](../../research/20-gapfill-mda-api.md) fact 2; [research 12](../../research/12-lifecycle-auth-followup.md) §1). Per-deployment ⇒ org-wide view = fan-out |
| [F07 app shell](./07-app-shell-and-navigation.md) | consumes | Both tabs are shell routes in `apps/web` (Next.js, D-022) under the six-tab IA (P-002; doc 03 §2) |
| [F04 `AgentSource` registry](./04-sdk-and-agent-sources.md) (`packages/sdk`, built M1) | consumes | Same multi-source aggregation primitive as the task inbox (`threads.search` aggregation, UI spec §3.1) |
| [F28 `apps/server` key proxy](./28-backend-glue-service.md) (P-005, FastAPI) | consumes | All crons/threads calls pass through the existing proxy route; **no new server state, no new routes** for this feature |
| [F22 org intelligence](./22-org-intelligence-v1.md) | mutual | F22's org-analyst template opens `CronEditor` prefilled; F22 owns the run-metadata convention (`task_type/agent/actor/tenant/repo/surface`, doc 02 §10; `repo` supersedes `context` per F22 §9-7) — this spec adds the `surface:"schedule"` + `deepwork_schedule_id` keys (§4.3) |
| [F09 task detail & streaming](./09-task-detail-and-streaming.md) | provides | `UntrustedContent` boundary component + the "external-origin message" flag in the normalized stream layer; F09 must wrap flagged messages in thread view |
| [F17 fleet manager](./17-fleet-manager.md) agent detail (doc 03 §3.4 *Schedules* tab) | provides | Reuses `ScheduleList` + `CronEditor` filtered to one agent; single implementation |
| [F19 notifications](./19-notifications-and-push.md) | seam | UI-created cron run payloads carry `webhook` (assumption A1, §9-Q3) so fired runs join the one run-completion push pipeline (doc 02 §7) |
| LangSmith tracing deep links | consumes | `TracePill` per fired run (doc 02 §10: trace is ground truth) |
| Runtime-tier capability matrix | constrains | Crons exist on MDA + LangSmith Deployment; **absent on the pure-OSS tier** ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 9; doc 02 §2); `langgraph dev` support unverified (§9-Q6) |

## 3. Design

### 3.1 Schedules tab

- **Data**: fan out `POST /runs/crons/search` to every registered agent source (via proxy), merge, sort by next-run ascending. Sources that 404/405 the endpoint are marked *schedules unsupported* (expected on pure-OSS tier); sources that error are shown as an unreachable-source banner row — never silently dropped.
- **Row** (table, LangSmith-style per doc 03 §3.4): schedule name/prompt-preview (one line, mono for `input` JSON) · agent chip (source + assistant) · cron expression + human-readable phrase · **next run** (relative + absolute in viewer TZ; schedule's own TZ shown as secondary when it differs) · origin badge (§3.3) · enabled state · last-fire status glyph (from run history, §3.4) · overflow menu (edit / duplicate / delete / view runs / open agent config).
- **Actions**:
  - **Create**: toolbar CTA → `CronEditor` (§3.2). Create goes to the selected source's `POST /runs/crons`.
  - **Edit**: implemented as **create-new-then-delete-old** — the only strategy verified to exist upstream (mda itself reconciles by delete + recreate, research 20 fact 11). Create first, delete second, so a failure never loses the schedule; the seconds-wide double-fire window is accepted and documented in the confirm dialog. The new cron is stamped `metadata.deepwork.replaces: <old cron id>` at create (§4.3), so a failed delete leaves a machine-findable orphan pair rather than two anonymous twins (§5 edit-race repair). If a native update endpoint exists (§9-Q2) swap it in behind the same SDK method.
  - **Delete**: confirm dialog shows the full definition and offers "copy as JSON" before deleting (a delete operation exists — mda deletes MDA-owned crons on deploy; exact path per Agent Server API reference, §9-Q2).
  - **Enable/disable**: ships **only if** the M3-entry API probe finds a pause/enabled field (§9-Q2). Fallback if absent: the toggle is omitted; "disable" degrades to delete-with-export (definition downloadable for later recreation). No Deep Work DB exists to stash disabled definitions (doc 02 §1) — we do not fake a toggle we can't honor.
  - Project-origin schedules (§3.3) get **no destructive actions** — edit/delete deep-link to the agent's `schedules/` config in [F17](./17-fleet-manager.md), because `mda deploy` will clobber UI changes (research 20 fact 11).
- **States** (doc 03 §7 bar): loading = skeleton rows, never spinners; empty = teaching state ("No schedules yet — create one, or start from an org-analyst template" linking F22's gallery); error/degraded per-source as above, with healthy sources still rendered.

### 3.2 CronEditor (`packages/ui`)

Mirrors the verified `define_schedule` contract (research 20 fact 11: 5-field cron + **exactly one of** `prompt | input`, optional `timezone`, optional `deliver_to`):

| Field | Behavior |
|---|---|
| Agent | source + assistant picker (from registry); disabled sources excluded |
| Cron | 5-field expression input with plain-language preview and **next 3 fires** rendered in both the schedule TZ and viewer TZ (client-computed, `cron-parser` or equivalent) |
| Timezone | IANA select; defaults to viewer TZ; omitted field = server default (UTC per open-swe/Fleet precedent, [research 10](../../research/10-openswe-fleet.md)) — displayed explicitly, never implied |
| Prompt / Input | XOR toggle: markdown textarea (prompt) or JSON editor (input); enforcing exactly-one client-side |
| deliver_to | Rendered greyed with "requires channels (0.4.0-dev)" — behind the dev-channel feature flag the roadmap risk register already mandates ([04-roadmap](../04-roadmap.md): "feature-flag dev-channel-only UI"); shape when enabled: `{channel, to: provider_thread\|provider_conversation, auto_post}` (research 20 fact 10) |
| Guardrails | Interval < 1 h ⇒ warning with estimated fires/day; < 5 min ⇒ typed-confirmation ("I understand") — client-side only, Deep Work cannot enforce server-side (§5 storms) |

Thread mode (`ephemeral` default vs `persistent {id}`, research 20 fact 11) is displayed read-only for project schedules; UI-created crons are v1-ephemeral until the public cron payload schema is verified (§9-Q3).

### 3.3 Origin: `define_schedule` vs UI-created

Both kinds coexist in one Agent Server cron store; the list must distinguish them because their lifecycles differ:

| Origin | Created by | Lifecycle | Badge |
|---|---|---|---|
| `project` | `schedules/` + `mda deploy` reconciliation (delete-and-recreate after revision DEPLOYED; skipped with `--no-wait`) — research 20 facts 2, 11 | Owned by the repo; survives only until next deploy rewrites it | "project" (mono, links to agent config) |
| `ui` | Deep Work `POST /runs/crons` | Owned by the workspace; Deep Work stamps `metadata.deepwork = {origin:"ui", created_by:<actor>, v:1, replaces?:<old cron id>}` on the cron payload (`replaces` on edit swap only, §3.1; assumption A1, §9-Q3) | "manual" |
| `unknown` | Anything else (other tools, SDK scripts) | Read-only display + delete | "external" |

Detection: `deepwork.origin` when present; else the marker mda stamps on its own crons — **not yet recovered from the binary** (§9-Q1). Until Q1 resolves, heuristics: a cron matching a `schedules/`-declared entry (name/expression equality via the agent's Context Hub copy) is `project`; the risk that `mda deploy` deletes UI-created crons wholesale is tracked in §10-R1.

### 3.4 Run history per schedule → task detail

Fired runs are threads (ephemeral mode creates one per fire; persistent reuses one — research 20 fact 11). Correlation is metadata, no new storage:

- **UI-created crons**: the cron's run payload carries `metadata: {surface:"schedule", deepwork_schedule_id:<cron_id>, ...F22 convention keys}` (assumption A1 — cron payload assumed to mirror run-create incl. `metadata`/`webhook`; §9-Q3). History = `threads.search({metadata:{deepwork_schedule_id}})` on that source — the exact primitive the inbox already uses (doc 03 §3.1).
- **Project crons (MDA)**: the runtime stamps identity `source.provider = "schedule"` (research 20 fact 13) and `metadata.owner` scoping (fact 9). Whether a schedule id/name reaches thread metadata is unverified (§9-Q4); until then, history for project crons filters `provider=schedule` + assistant and is labeled "all schedule fires for this agent".
- Each history row: fire time · thread status chip · link to **task detail** (F09 thread view) · `TracePill` (LangSmith run URL — doc 02 §10). The F22 tracing convention makes the same runs findable in LangSmith; keys must match exactly (seam contract, §4.3).

### 3.5 Activity tab

- **Purpose**: compact cross-agent audit feed — "what ran, when, ended how" — not analytics (P-002 boundary, §3.7).
- **Data source**: aggregated `threads.search({sortBy:'updated_at', status?})` across sources — the **Agent Server data plane**, deliberately *not* LangSmith `POST /runs/query`, whose tiered gateway limits (doc 07 Layer 1: 10/10s for ≤7-day windows; gateway table: 15/10s — [research 20](../../research/20-gapfill-mda-api.md) fact 8; discrepancy noted, budget to the lower) make it unfit for a hot list path. `/runs/query` is reserved for nothing in this feature; anything needing it deep-links out.
- **Row** (denser than inbox rows): status dot · agent chip · title/first-prompt preview · `task_type` chip (from F22 metadata) · relative time · interrupt badge · → task detail · `TracePill`. Rows whose thread originated from a schedule/webhook (`surface:"schedule"` / provider ≠ http) show a small "scheduled" glyph and their previews render inside the untrusted boundary (§3.6).
- **Filters** (sidebar, URL-as-state via nuqs per doc 03 conventions): agent/source · `task_type` · status · time window (24h/7d/30d/custom). All applied to `threads.search` params where supported (status), else client-side on the merged page.
- **Pagination**: per-source cursors (limit/offset), k-way merge by `updated_at`, "load more" fetches the next page from whichever sources are exhausted at the merge frontier — identical to the inbox aggregation strategy (doc 03 §3.1); virtualized list per doc 03 §7.
- **Storm ergonomics**: ≥3 consecutive rows from the same schedule collapse into one grouped row ("×N fires of <schedule>, last at …") — this makes a misconfigured every-minute cron visible instead of unusable (§5).
- **States**: skeleton rows while loading; empty state per filter combination ("Nothing ran in this window — widen the range or dispatch a task"); degraded = per-source banner, feed continues from healthy sources.

### 3.6 Untrusted-content rendering rule

Doc 02 §10 adopts Claude Routines' `<routine-fire-payload>` prompt-injection defense verbatim: only the pre-stored schedule prompt is the task; fired/webhook payloads reach the model as untrusted data ([research 03](../../research/03-competitor-teardown.md)). This spec owns the **UI half** — the same distrust must survive into rendering:

- `UntrustedContent` component (`packages/ui`): visibly framed ("external content" micro-label), markdown rendered inert — raw HTML stripped, images not auto-fetched (click-to-load), links show full destination on hover and are `rel="noopener nofollow"`, no content-derived action buttons or deep links are synthesized from the body.
- **Applies wherever a fired payload or external/webhook body is displayed**: Schedules tab payload previews (`input` JSON of externally-created crons), run-history previews, Activity row previews for schedule/webhook-origin threads, and — via F09 — thread-view messages flagged external-origin.
- **Contract to F09**: the SDK normalization layer (doc 03 §5 — one normalization at the SDK boundary) marks messages `untrusted: true` when thread/run metadata says `surface ∈ {schedule, webhook}` or MDA identity `source.provider ∈ {schedule, slack}` (research 20 fact 13). F09 must render `untrusted` messages inside `UntrustedContent`; this spec ships the component and the flag.
- The stored schedule **prompt** itself is trusted authored content and renders normally; the distinction is provenance, not content type.

### 3.7 Observability-slim (P-002)

What Activity shows vs what links out — the honest split (doc 02 §10: "Deep Work deep-links out rather than re-implementing observability", the D-003 wrapper stance applied; P-002 slims Observability to counts + deep links, with the final call confirmed at M3 entry per doc 06 Phase E):

| Deep Work shows | LangSmith owns (deep link) |
|---|---|
| Count strip over the **already-fetched** filtered window: total / running / needs-review / failed — computed client-side from the merged `threads.search` page, zero extra API calls | Latency, cost/spend, token usage, feedback charts, clustering, Insights reports (F22 provisions those) |
| Last-fire status glyph per schedule | Full run trees, per-run I/O inspection |
| "Open in LangSmith ↗" per filter context (per-agent tracing project URL, per F22 conventions) | Dashboards, automations, alerts |

The v0 concept's `/observability` charts stay folded/flagged off (doc 06 §2 gap 6 + decision 2). If a cheap authenticated stats read later justifies more, that is a P-002 revision, not silent scope growth.

## 4. Contracts

### 4.1 Endpoint usage (per agent source, via `apps/server` proxy — P-005)

| Call | Purpose | Verification status |
|---|---|---|
| `POST {deployment}/runs/crons/search` | list schedules | Verified (mda binary, research 20 fact 2; doc 02 §6) |
| `POST {deployment}/runs/crons` | create | Verified (same) |
| delete cron (path TBD) | delete / edit-swap / disable-fallback | Operation exists (mda delete-and-recreate, research 20 fact 11); exact path unrecovered → §9-Q2. **Do not guess in code**: resolve from the Agent Server OpenAPI (`/openapi.json`, [research 01](../../research/01-managed-deep-agents.md)) at M3 entry |
| `POST {deployment}/threads/search` | run history + Activity feed | Verified (doc 03 §3.1 already builds on it) |

### 4.2 `packages/sdk` surface

```ts
interface ScheduleSource {                      // implemented per AgentSource
  capabilities(): Promise<{crons: boolean, pause: boolean}>;  // probe once, cache
  listSchedules(): Promise<Schedule[]>;
  createSchedule(def: ScheduleDef): Promise<Schedule>;
  deleteSchedule(id: string): Promise<void>;
  replaceSchedule(id: string, def: ScheduleDef): Promise<Schedule>; // create-then-delete; stamps deepwork.replaces:<old id> on the new cron (§3.1)
  scheduleRuns(s: Schedule, cursor?: Cursor): Promise<Page<ActivityItem>>;
}
type Schedule = {
  id: string; sourceId: string; assistantId: string;
  cron: string;                    // 5-field
  timezone?: string;               // IANA; absent = server default
  payload: {prompt: string} | {input: unknown};   // exactly one
  origin: 'project' | 'ui' | 'unknown';
  enabled?: boolean;               // only if pause capability exists
  nextRunAt?: string;              // server value if present, else client-computed + `computed:true`
  threadMode?: 'ephemeral' | {persistentId: string};
  metadata: Record<string, unknown>; // incl. deepwork {origin, created_by, v, replaces?} (§3.3, §4.3)
};
type ActivityItem = {
  threadId: string; sourceId: string; assistantId: string;
  status: ThreadStatus; updatedAt: string;
  taskType?: string; surface?: string; interruptCount: number;
  traceUrl?: string; untrusted: boolean;         // §3.6 flag
};
```

### 4.3 Metadata convention (seam to F22 — keys must not fork)

| Key | Stamped on | By | Value |
|---|---|---|---|
| `surface` | fired runs/threads | agent middleware / cron payload | `"schedule"` (extends F22's `surface` enum) |
| `deepwork_schedule_id` | fired runs/threads | UI-created cron payload (A1) | cron id |
| `metadata.deepwork.origin` | the cron object; preserved onto its fired runs/threads | Deep Work on cron create | `"ui" \| "project"` |
| `metadata.deepwork.replaces` | the new cron object on edit swap | `replaceSchedule` create-then-delete (§3.1) | obsolete cron id — edit-repair deletes the cron it names (§5) |
| `task_type`, `agent`, `actor`, `tenant`, `repo` | every run (`repo`: coding tasks) | F22 convention (doc 02 §10; `repo` supersedes its `context` — F22 §9-7) | consumed for Activity filters |

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Deployment deleted while crons listed / source unreachable | Schedules from that source render greyed with error banner + retry; row actions disabled; removing the source from the registry removes its rows (crons live in the deployment — nothing to orphan on our side, but see §10-R4 for delete-vs-deployment races) |
| Cron targets a deleted/missing assistant | Cross-check `assistantId` against the source's assistants list; badge "target agent missing"; only offered action = delete/export |
| Disabled-agent schedules | Same cross-check path; if assistant exists but source is paused in the registry, badge "source disabled — will still fire server-side" (crons run on the server regardless of Deep Work's registry state — surfaced honestly) |
| Timezone/DST transitions | Next-fire preview computed with IANA TZ rules; CronEditor warns when a schedule falls in the 01:00–03:00 window of a DST-observing zone (skip/double-fire semantics of the server are undocumented → §9-Q5); all displayed times carry explicit TZ labels |
| Next-run drift | Server `next_run` (if the search payload provides one, §9-Q2) is truth; client-computed values are labeled and re-derived on refetch (60 s poll while tab visible); never persisted |
| Schedule storms (every-minute cron) | CronEditor guardrails (§3.2); Activity collapse-grouping (§3.5); enqueue default `multitask_strategy` means persistent-thread fires **queue** behind a still-running fire (doc 02 §7, research 20 fact 4) — backlog depth shown on the schedule row when >1 queued |
| Fired payload contains markup/injection content | `UntrustedContent` everywhere per §3.6; agent side already covered by doc 02 §10 |
| Edit race (create-new succeeded, delete-old failed) | Both crons exist; the new cron's `deepwork.replaces` marker (§3.1, §4.3) names the obsolete id, so the list detects a cron whose `replaces` target still exists and surfaces a one-click "finish edit (delete old)" repair row |
| `/runs/crons/search` rate-limited (2000/10s general gateway bucket, research 20 fact 8) | Fan-out throttled, per-source results cached 30 s, jittered refresh; Activity pagination never issues parallel unbounded fan-out |
| Source on pure-OSS tier | Capability probe returns `crons:false`; Schedules tab shows "unsupported on this backend" row (research 23 fact 9) — no phantom empty state |

## 6. Security & privacy

- **Untrusted boundaries** are a v1 release criterion (roadmap criterion 5): all schedule/webhook content renders per §3.6; acceptance test includes an injection-shaped payload fixture.
- **Key handling**: crons CRUD needs a workspace/service key; all calls go through the `apps/server` proxy (P-005; `langgraph-nextjs-api-passthrough` pattern per doc 03 §3.6) — key reaches the browser only in explicit local mode.
- **No RBAC in v1**: any workspace member with the app configured can create/delete schedules (team RBAC is explicitly post-v1 backlog, [04-roadmap](../04-roadmap.md)). The confirm dialogs name the blast radius ("fires as the deployment, visible to the workspace").
- **Secrets in prompts**: CronEditor warns on secret-shaped strings (`lsv2_`, `ghp_`, PEM headers) in prompt/input — cron payloads are stored server-side and readable by anyone who can list crons.
- **Provenance everywhere** (doc 02 §10): every fired run shows schedule id, TZ, and trace link; the UI never renders schedule output as if a human authored it.
- Identity: fired runs execute under the deployment's schedule identity (`source.provider="schedule"`, research 20 fact 13), not the creating user — displayed on the schedule row to avoid "ran as me" confusion.

## 7. Acceptance criteria

1. Schedules tab lists crons from ≥2 simultaneously configured sources, with unsupported/unreachable sources visibly distinguished (no silent drops).
2. Create → fire → run appears in schedule run history → opens task detail → `TracePill` resolves to the LangSmith run. Correlation works via `deepwork_schedule_id` with zero Deep Work-side storage.
3. Edit swaps create-then-delete atomically from the user's view; a forced delete-failure leaves a repairable state, never a lost schedule.
4. Project-origin schedules are badged, non-editable in place, and deep-link to agent config; UI-origin schedules carry the `deepwork.origin` stamp verifiable via raw cron metadata.
5. CronEditor enforces 5-field cron + XOR prompt/input + explicit TZ display; sub-hourly warning and sub-5-minute typed confirmation fire; `deliver_to` visible only under the dev-channel flag.
6. Activity feed filters (agent, task_type, status, time) round-trip through the URL (nuqs); pagination merges ≥2 sources in correct `updated_at` order; list is virtualized.
7. An injection-shaped fired payload renders inside `UntrustedContent` in: schedule payload preview, run-history preview, Activity row, and (with F09) thread view — verified by fixture test; images not fetched, HTML inert.
8. Activity issues no `POST /runs/query` calls (asserted in an integration test against the proxy log); count strip derives solely from fetched pages.
9. Every analytical affordance is a deep link to LangSmith; no chart components render in either tab (P-002 audit; doc 02 §10).
10. Demo mode: both tabs fully functional against fixtures with zero credentials (doc 06 decision 4).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | M3-entry API probe: resolve cron delete/update/pause paths + search payload fields (`next_run`? `timezone`? metadata?) from a live deployment's `/openapi.json`; record in this spec's §9 | beta deployment access | §9 Q2/Q3/Q5/Q6 answered with citations; SDK method table updated |
| 2 | `packages/sdk`: `ScheduleSource` + capability probe + normalized `Schedule`/`ActivityItem` types + fixtures | 1, M1 `AgentSource` registry | Unit tests incl. probe caching, origin detection, merge sort; fixtures cover all origins/states |
| 3 | `packages/ui`: `CronEditor` (fields, previews, guardrails, flagged `deliver_to`) + `UntrustedContent` | tokens/preset (M0) | Storybook stories; injection fixture renders inert; XOR + guardrail logic unit-tested |
| 4 | Schedules tab: aggregated list, origin badges, create/edit/delete flows, error/unsupported states | 2, 3 | Acceptance 1–5 pass against `langgraph dev` or fixtures |
| 5 | Run history: correlation metadata stamped on create; history panel; task-detail + trace links | 2, 4 | Acceptance 2 passes end-to-end on a real deployment |
| 6 | Activity tab: feed, filters (nuqs), k-way pagination, collapse-grouping, count strip, LangSmith deep links | 2 | Acceptance 6, 8, 9 pass; virtualization verified on 1k-row fixture |
| 7 | F09/F22 seam wiring: `untrusted` flag in SDK normalization; metadata keys reconciled with F22 conventions doc | 2, F22 draft | Cross-spec key table (§4.3) identical in both specs; F09 consumes the flag |
| 8 | Hardening: storm/edge fixtures (§5), rate-limit throttling, secret-shaped-string warning, a11y pass | 4–6 | Acceptance 7, 10 pass; §5 table each has a test or explicit waiver |

## 9. Open questions

1. **mda ownership marker**: how `mda deploy` identifies "MDA-owned" crons to delete-and-recreate — specific metadata key, or *all* crons on the deployment (which would clobber UI-created ones)? Not recoverable from binary strings so far ([research 20](../../research/20-gapfill-mda-api.md) fact 11). Blocking for §3.3 guarantees; test empirically with the beta account.
2. **Cron delete/update/pause API shape**: only `POST /runs/crons` + `/runs/crons/search` are verified; delete exists behaviorally (mda), but exact path, any PATCH/update, an `enabled`/pause field, and whether search returns `next_run_date`/`timezone` are unverified. Resolve from live `/openapi.json` (task 1) — never invent.
3. **UI-created cron payload schema** (assumption A1): does the public cron-create body mirror run-create (incl. `metadata`, `webhook`, `multitask_strategy`) and does it create ephemeral threads per fire? Research only documents `define_schedule`'s contract, not the raw API's.
4. **Schedule id in fired-thread metadata (MDA)**: does the runtime stamp a schedule name/id on threads it fires, or only `source.provider="schedule"` (research 20 fact 13)? Determines whether project-cron run history can be per-schedule rather than per-agent.
5. **DST semantics server-side**: skip vs double-fire at transitions for TZ-aware crons — undocumented.
6. **`langgraph dev` cron support**: does the in-mem runtime accept/execute crons? Determines dev-loop testability (research 23 documents the tier matrix but not this).
7. **Cron quotas**: per-workspace cron count limits are explicitly unpublished for MDA beta (research 20 open questions) — affects storm guardrail thresholds.
8. **Rate-limit figure discrepancy**: doc 07 cites 10/10s for `/runs/query` (≤7d windows), research 20 cites 15/10s from the gateway table — reconcile against the live cloud doc; we budget to 10/10s meanwhile (moot for the feed, which avoids the endpoint, but F22 shares this budget).
9. **Whether crons require a paid plan tier** on classic Deployments (cron-jobs doc is cited in research 23 sources but plan-gating wasn't extracted) — affects the "schedules unsupported" messaging.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| R1: `mda deploy` deletes UI-created crons (Q1 worst case) | Med | High — silent schedule loss | Until Q1 resolves: warning banner on UI-created schedules attached to MDA sources; Deep Work-triggered deploys snapshot-and-restore UI crons; CLI deploys outside Deep Work documented as unsafe |
| R2: No pause/update endpoint exists (Q2) | Med | Med — enable/disable degrades to delete+export; edit keeps delete-recreate | Degradation designed in (§3.1); toggle simply doesn't ship rather than lying |
| R3: Cron payload rejects `metadata` (Q3/A1) | Low-Med | High — per-schedule run history breaks for UI crons | Fallback correlation: assistant + `provider=schedule` + fire-time window matching (fuzzy, labeled as such); escalate upstream (OSS-first policy: gaps go upstream, doc 02 §8) |
| R4: Deployment deleted between list and action → confusing 404s | Med | Low | All mutations re-probe source health first; 404 surfaces as "source gone" with registry cleanup prompt |
| R5: Beta API drift (crons surface changes under 0.4.0-dev) | High | Low-Med | Same mitigation as roadmap risk register: pinned SDK, canary deployment in CI, capability probe rather than hardcoded assumptions |
| R6: Activity fan-out cost grows with source count | Med | Med — rate limits + latency | 30 s cache, jitter, per-source cursors, cap default window to 7d; virtualization keeps DOM flat |
| R7: Untrusted-boundary gaps in surfaces added later (chips, toasts, notifications) | Med | High — injection defense is a release criterion | `untrusted` flag lives in the normalized type (§4.2) so every consumer must handle it; lint rule: raw markdown render of `ActivityItem`/payload fields forbidden outside `UntrustedContent` |
