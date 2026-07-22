# F10 · Approvals inbox

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M2 · Depth: implementation-ready*

Sources: [UI spec §3.3](../03-ui-spec.md) · [frontend plan Phase C](../06-frontend-implementation.md) · [architecture §3/§5/§7](../02-architecture.md) · [roadmap M2](../04-roadmap.md) · [vision pillar 2](../01-vision.md) · [research 13 · agent-inbox](../../research/13-agent-inbox.md) · [research 21 · UI contract](../../research/21-gapfill-ui-contract.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md)

## 1. Scope

The cross-agent surface for everything agents are waiting on — vision pillar 2, "Fleet's headline differentiator, matched in the open" ([01](../01-vision.md)). This spec owns:

- The **Approvals tab**: aggregated list of pending HITL interrupts across all configured agent sources, with counts feeding the shell tab badge and desktop tray (seam to F07, [./07-app-shell-and-navigation.md](./07-app-shell-and-navigation.md)).
- The **interrupt card** experience: single and batched decisions, per-arg editing, reject/respond, mark-resolved, schema-tolerant fallback — the `InterruptCard`/`DecisionForm` components in `packages/ui` ([03 §4](../03-ui-spec.md)).
- **Usage** of the v1 HITL contract (D-010/D-011): payload normalization, `respond()/respondAll()` resume, casing hygiene.

Out of scope (owned by neighbors): push delivery ([./19-notifications-and-push.md](./19-notifications-and-push.md)); the mobile one-tap approve screen ([./20-pwa-and-mobile.md](./20-pwa-and-mobile.md)); authoring `interrupt_on` config / the per-tool Auto-Ask matrix ([./17-fleet-manager.md](./17-fleet-manager.md)); in-thread rendering of interrupts and the `PlanCard` ([./09-task-detail-and-streaming.md](./09-task-detail-and-streaming.md)); filesystem `permissions` rules ([02 §3](../02-architecture.md)).

The v0 concept's approvals screen (`/approvals`, `Approval {kind, command}`, verbs approve/edit/respond/**ignore**) is the legacy agent-inbox shape and is **OFF-contract — rebuilt, not adapted** ([06 §2 gap 2, Phase C](../06-frontend-implementation.md)). Only its visual chrome survives.

## 2. Dependencies & seams

| Dependency | Direction | Seam |
|---|---|---|
| `packages/sdk` data layer (agent-source registry, `useStream`, control-plane client) | consumes | `DataProvider` interface; fixtures + live impls ([06 Phase B](../06-frontend-implementation.md)) |
| F07 app shell | provides | `useApprovalsCount(): {total, bySource}` selector → tab badge, desktop tray count ([03 §6](../03-ui-spec.md)) |
| F09 task detail | both | same interrupt store; in-thread cards and inbox rows key on `interrupt_id` (dedupe, §3.6); F09 owns `PlanCard` |
| F17 fleet manager | upstream | Auto/Ask matrix compiles to `interrupt_on` → what interrupts at all; empty state links there |
| F19 notifications | consumes counts/events | push on new interrupt; notification deep-links to `/approvals?item=<key>` |
| F20 PWA/mobile | consumes | one-tap approve screen reuses `DecisionForm` + this store |
| `apps/server` (FastAPI glue, P-005) | transit | key-proxy mode: all data-plane calls (search, getState, respond, updateState) pass through the server proxy; no approvals state is stored server-side (no DB in v1, [02 §1](../02-architecture.md)) |
| Frontend = Next.js (D-022) | host | Approvals tab route in `apps/web`; URL-as-state via nuqs |
| `packages/agent` | upstream | emits `HITLRequest` via `interrupt_on` on `execute`, `commit_and_open_pr`, flagged MCP tools ([02 §3](../02-architecture.md)) |

## 3. Design

### 3.1 Data flow

1. **Hydrate**: per source in the registry, `threads.search({status:'interrupted', metadata:{assistant_id|graph_id}, limit≤100, offset})` ([03 §3.1](../03-ui-spec.md), [research 13](../../research/13-agent-inbox.md)) → for each hit, `thread.getState().tasks[].interrupts` yields `{interrupt_id, payload}` ([research 21](../../research/21-gapfill-ui-contract.md)). Sources fetch in parallel; one failing source never blocks the rest.
2. **Live update**: threads with an open `useStream` update from `input.requested` events `{interrupt_id, payload}` on the root subscription ([03 §5](../03-ui-spec.md)). Headless client-tool interrupts (`{type:'tool', toolCall}`) are auto-handled when `tools[]` is registered and are **filtered out** — never shown ([research 21](../../research/21-gapfill-ui-contract.md)).
3. **Refresh**: poll while the Approvals tab is visible (default 30 s), revalidate on window focus, refetch on F19 notification tap. Re-hydrate the single thread's state whenever a card is opened (stale-guard, §5).
4. **Normalize once** at the SDK boundary; components never see casing variants except the documented `reviewConfigs` exception ([03 §5](../03-ui-spec.md)). Normalizer output is the internal `InboxItem` (§4).

### 3.2 List

Row anatomy (agent-inbox 12-col fixed-height ~71 px pattern, [research 13](../../research/13-agent-inbox.md)): unread dot · **tool name** (mono) + one-line arg/description preview (≈65-char truncation) · **capability chip** derived from `allowedDecisions` · agent + thread context chip (source name, task title) · relative age. Batched interrupts show an `N actions` stack indicator on the row.

- **Capability chip**: highest capability wins — `approve`/`edit` present → "Needs approval" (green dot); `respond`-only → "Reply requested" (amber); anything else → "Review" (gray). Never hardcoded kinds — chips and sidebar facets derive from `actionName`s and `reviewConfigs` actually present ([06 Phase C](../06-frontend-implementation.md)).
- **Ordering**: oldest-waiting first (an interrupt blocks a run; age = cost). Age derives from the thread's `updated_at` at hydration (per-interrupt timestamp availability → §9-Q3).
- **Grouping**: default flat; sidebar offers group-by-agent with per-group counts, plus dynamic facets by tool name and source. All filter/pagination state in the URL via nuqs (shareable, back-button-safe — agent-inbox pattern).
- **Counts**: badge counts *interrupts*, not threads; `useApprovalsCount()` feeds the F07 tab badge/tray and the per-thread interrupt-count badges in the Task inbox ([03 §3.1](../03-ui-spec.md)).
- Keyboard: `j/k` row navigation, `Enter` open, approval hotkeys inside the card ([03 §7](../03-ui-spec.md)); final map registered with F07's shortcut system.
- Virtualized list; skeleton rows while loading ([03 §7](../03-ui-spec.md)).

### 3.3 Interrupt card

One card per interrupt (= one `HITLRequest`), containing one decision row per `actionRequest`, **in order**:

- **Per-action decision row**: tool name + description, then per-arg fields prefilled from `args` (non-strings JSON-stringified; parsed back on submit with per-field errors — agent-inbox pattern). When `argsSchema`/`args_schema` is present it drives field types, labels, enums, and client-side validation; absent → key/value text fields. Fields are read-only unless `edit` ∈ `allowedDecisions`.
- **Edit⇄Accept auto-switch**: primary button reads *Accept* (`{type:'approve'}`) while pristine; dirtying any field flips it to *Accept edits* (`{type:'edit', editedAction:{name, args}}`). The tool `name` is copied from the `actionRequest` and is **not user-editable** (no tool-swap; §6).
- **Reject vs Respond, kept distinct**: *Reject* opens an optional-message field → `{type:'reject', message?}` — the run **continues**; the tool call receives an error `ToolMessage` (`status:'error'`). *Respond* is a required textarea → `{type:'respond', message}` → `ToolMessage status:'success'` ([research 21](../../research/21-gapfill-ui-contract.md)). Buttons render only for decisions present in `allowedDecisions`.
- **Batch UX**: per-call decision rows collapse to summaries once decided; a progress-dot strip tracks the batch (approve/edit → green, reject → red, respond → amber, undecided → hollow — agent-chat-ui convention per [03 §3.3](../03-ui-spec.md)). Submit stays disabled until every row has a decision (§5.4); an *Approve remaining* shortcut fills the rest with `{type:'approve'}` where allowed. Drafts are client-local, in-memory keyed by `interrupt_id` (lost on reload — acceptable; noted).
- **Mark resolved** (overflow menu, destructive, confirm dialog): force-ends the **whole thread** with no resume — `threads.updateState(threadId, {values: null, asNode: END})`, the agent-inbox force-end semantics ([research 13](../../research/13-agent-inbox.md)). Copy makes the difference explicit: "Reject tells the agent no and lets it continue; Mark resolved ends the task." The legacy `ignore` verb does not exist in v1 and never appears.
- Submitting shows optimistic *Submitting…*; on success the row leaves the list with a toast linking to the resuming task. No undo — resume is irreversible.

### 3.4 Schema-tolerant fallback

Any payload that fails `HITLRequest` parsing (after tolerant reads: both casings, `args ?? arguments`) renders a **raw-JSON card**: pretty-printed payload in a mono code frame, source + agent context, a **copyable thread id**, *Open thread*, and *Mark resolved* as the only mutation. Modeled on agent-inbox's synthetic `improper_schema` interrupt ([research 13](../../research/13-agent-inbox.md)). The list and every card sit inside error boundaries: **the inbox never crashes** (acceptance §7-A4). Parse failures are counted per source for the degraded banner, never thrown.

### 3.5 States

| State | Treatment |
|---|---|
| Loading | skeleton rows, never spinners ([03 §7](../03-ui-spec.md)) |
| Empty | celebratory "Nothing needs you" + teach the next action: link to the Auto/Ask matrix (F17) — "control what asks for approval" ([03 §7](../03-ui-spec.md): every empty state teaches) |
| Error (all sources failed) | full-bleed error + retry |
| Degraded (some sources failed / parse errors) | per-source status chips in the header, "N sources unreachable — retry"; cached rows from dead sources stay visible, flagged *stale*, actions disabled with retry (§5.5) |

### 3.6 Plan-approval interrupts

Plan approvals are ordinary `HITLRequest` interrupts emitted by the plan gate in `packages/agent` and rendered in-thread as the `PlanCard` ([./09-task-detail-and-streaming.md](./09-task-detail-and-streaming.md), [03 §3.2](../03-ui-spec.md)). In this inbox they appear as rows of kind `plan` (detected by `actionName` matching the plan-gate action name published by `packages/agent` — naming convention §9-Q6) with a *Review plan* CTA deep-linking to the task-detail card, where per-step editing lives. The inbox card offers approve/reject(+message) only. **Dedupe is structural**: both surfaces read the same store keyed by `interrupt_id` and both resume via the same `respond()` path — one row, one card, deciding in either place resolves both.

## 4. Contracts

Pinned per D-010/D-011; wire is snake_case, the SDK normalizes once with camelCase canonical ([03 §5](../03-ui-spec.md), [research 21](../../research/21-gapfill-ui-contract.md)). Pins: `@langchain/react` ^1.0.28 + `@langchain/langgraph-sdk` ^1.9.x.

**Interrupt payload** (normalized):

```ts
HITLRequest = {
  actionRequests: Array<{ name: string; args: Record<string, unknown>; description?: string }>,
  reviewConfigs: Array<{
    actionName | action_name: string,                                  // NOT aliased by the SDK — read both
    allowedDecisions | allowed_decisions: ('approve'|'edit'|'reject'|'respond')[],  // read both
    argsSchema? | args_schema?: JSONSchema                              // read both
  }>
}
```

The casing exception is load-bearing: `normalizeHitlInterruptPayload` aliases both casings with camelCase canonical **except** `reviewConfigs`' inner keys ([research 21](../../research/21-gapfill-ui-contract.md)). The normalizer additionally reads `args ?? arguments` on action requests (agent-inbox's `arguments`-only read turned Python `args` into `{}` — [research 13](../../research/13-agent-inbox.md); upstream status §9-Q5).

**Resume** — one decision per `actionRequest`, in order; `respondAll()` for batches of pending interrupts. **Never** the legacy `submit(null, {command:{resume}})` — it does not exist on the v1 submit options type (the current docs HITL page still showing it is stale, [research 21](../../research/21-gapfill-ui-contract.md)):

```ts
stream.respond({ decisions: [
  { type: 'approve' }
| { type: 'edit', editedAction: { name, args } }   // Python edited_action; SDK duplicates both on send
| { type: 'reject', message? }                      // → ToolMessage status 'error'; run continues
| { type: 'respond', message }                      // → ToolMessage status 'success'
]})
// wire: protocol input.respond { namespace, interrupt_id, response, update?, goto?, config?, metadata? }
// batch wire: { responses: [...] }
```

**Hydration**: `thread.getState().tasks[].interrupts` + live `input.requested {interrupt_id, payload}` ([research 21](../../research/21-gapfill-ui-contract.md)).

**Force-end (Mark resolved)**: `threads.updateState(threadId, {values: null, asNode: END})` via the classic Threads API, which every tier exposes ([02 §2](../02-architecture.md); MDA/identity verification §9-Q1).

**Internal model** (ours, defined here):

```ts
InboxItem = {
  key: `${sourceId}:${threadId}:${interruptId}`,
  sourceId: string, threadId: string, interruptId: string,
  agent: { assistantId?: string; graphId?: string; displayName: string },
  kind: 'hitl' | 'plan' | 'malformed',
  payload: HITLRequest | { raw: unknown },          // raw only when kind === 'malformed'
  threadUpdatedAt: string,                           // age proxy (§9-Q3)
  stale: boolean                                     // source unreachable since last confirm
}
```

## 5. Edge cases & failure modes

1. **Stale/expired interrupt (run resumed elsewhere** — Studio, another device, dcode, a queued double-text run**)**: on card open, re-hydrate the thread's state before enabling actions; if the `interrupt_id` is no longer in `tasks[].interrupts`, render the card as *Handled elsewhere* with a link to the thread, and drop the row. Any `respond()` failure triggers the same re-hydrate-and-reconcile path.
2. **Two devices decide the same interrupt concurrently**: exactly one resume can win — the interrupt resolves once. Expected behavior: first `respond()` wins; the second receives a server error for the no-longer-pending `interrupt_id` (exact status code unverified → §9-Q2; verified in the M0 Spike 3 golden-transcript harness, [04](../04-roadmap.md)). Error UX: never blind-retry a decision; re-hydrate, show "Already handled on another device" with the winning outcome if derivable from state, remove the row. Optimistic UI marks rows *Submitting…* but only removes them on confirmed success.
3. **Thread deleted under an open interrupt**: `getState`/`respond` returns 404 → toast "Task no longer exists", drop the row, no retry.
4. **Partial batch decisions**: the contract requires one decision per action **in a single resume** — there is no partial submit. Drafts accumulate client-side; *Submit N decisions* stays disabled until complete. If re-hydration replaces the payload (different `interrupt_id`), drafts are discarded with a notice.
5. **Source goes offline**: rows from that source stay listed, flagged *stale*, decisions disabled (a decision needs the live server anyway) with per-source retry; header shows the degraded banner. A decision that fails on network keeps its draft locally and offers retry.
6. **Malformed payload**: §3.4 fallback card; parse errors are per-item, never list-fatal.
7. **Expired sandbox under a pending interrupt**: irrelevant to validity — the interrupt is durable checkpoint state; thread-scoped sandboxes auto-recreate on resume ([02 §4](../02-architecture.md)). No special UI.
8. **Interrupt arrives for a thread already open in task detail**: one store, one `interrupt_id` — the in-thread card (F09) and inbox row appear/resolve together (§3.6 mechanics apply to all interrupts, not just plans).
9. **>100 interrupted threads on one source**: `threads.search` pages at 100 ([research 13](../../research/13-agent-inbox.md)); paginate per source, surface "showing oldest N" rather than silently truncating newest.

## 6. Security & privacy

- **Untrusted content boundary**: `args`, `description`, and tool names are agent/tool-derived text. Render as data — plain text or sanitized minimal markdown, inside the same untrusted-content boundary used for webhook/schedule payloads ([02 §10](../02-architecture.md)). Interrupt content must never be able to imitate chrome (e.g. a description containing "✓ Approved"); card chrome and payload areas are visually and structurally separated.
- **No tool-swap via edit**: the UI always submits `editedAction.name` copied verbatim from the `actionRequest`; only `args` are editable. Client-side `argsSchema` validation is a convenience — the deployment remains the authority.
- **Auth & transit**: decisions use the same credential path as all data-plane calls — server key-proxy (`apps/server`, P-005) or direct bearer; Deep Work stores no approvals data server-side (no DB in v1, [02 §1](../02-architecture.md)). Scoping is enforced by the platform: MDA identity stamps `metadata.owner` and fails closed ([research 20](../../research/20-gapfill-mda-api.md)) — the inbox can only ever show what the credential can read.
- **Destructive action friction**: *Mark resolved* requires an explicit confirm naming the task; it is visually distinct (red) from *Reject*.
- **Audit**: every decision is observable in the LangSmith trace — the trace is ground truth the UI never contradicts ([02 §10](../02-architecture.md)); cards carry the trace deep link.
- **Push payloads** carry ids, not `args` content — minimization is specified in [./19-notifications-and-push.md](./19-notifications-and-push.md).

## 7. Acceptance criteria

- **A1 Contract round-trip**: against `langgraph dev` golden transcripts (M0 Spike 3 harness), an `interrupt_on` interrupt renders a card and each decision type resumes via `respond()`; `reject` produces `ToolMessage status:'error'`, `respond` produces `status:'success'`; the legacy `submit(null,{command}})` pattern appears nowhere in the codebase (lint rule).
- **A2 Casing**: Python (snake_case) and JS (camelCase) fixture payloads render identically; `actionName/action_name`, `allowedDecisions/allowed_decisions`, `argsSchema/args_schema` all read in both casings.
- **A3 Batch**: a 3-action `HITLRequest` renders one card with 3 decision rows and progress dots; submit is disabled until 3 decisions exist; the wire payload preserves action order.
- **A4 Never-crash (test plan)**: fixture suite = all ~6 legacy/variant payload shapes from agent-inbox research + `null`/empty/deep-nested/oversized JSON + fast-check property-based random payloads → every input yields either a valid card or the raw-JSON fallback with copyable thread id; error-boundary tests prove a throwing card leaves siblings and list intact; CI-gated.
- **A5 Staleness/concurrency**: deciding an interrupt already resolved elsewhere sends no duplicate resume, shows *Handled elsewhere*, and removes the row (mock server returning the §9-Q2 error).
- **A6 Dismissal semantics**: *Reject* leaves the thread running with an error `ToolMessage`; *Mark resolved* ends the thread (status leaves `interrupted`, no `ToolMessage`); both verified against `langgraph dev`.
- **A7 Counts**: badge total equals visible interrupt count across sources; with an open stream, a new `input.requested` updates row + badge without refetch.
- **A8 Plan dedupe**: a plan interrupt yields exactly one inbox row and one in-thread card; approving in either resolves both.
- **A9 States & a11y**: loading/empty/error/degraded all render; keyboard-only completion of an approve and an edit flow; AA contrast both themes; `prefers-reduced-motion` honored.
- **A10 Scale**: 200 pending interrupts across 3 sources (one offline) renders virtualized with interactive list < 200 ms after data; offline source shows degraded chrome only.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `packages/sdk`: HITL normalizer + `InboxItem` types (dual-casing, `args??arguments`, malformed detection) | Phase B sdk seed | A2 fixtures pass; malformed inputs return `kind:'malformed'`, never throw |
| 2 | Cross-source hydration (`threads.search` status=interrupted → `getState().tasks[].interrupts`) | 1 | Items from 2 mock sources merge; one failing source yields partial results + error metadata |
| 3 | Live updates: `input.requested` wiring, focus/interval revalidation, headless-tool filtering | 2 | A7; client-tool interrupts never surface |
| 4 | Approvals store + `useApprovalsCount()` selector (F07 seam) | 2 | Badge parity test (A7); per-source breakdown exposed |
| 5 | List UI: rows, capability chips, ordering/grouping, nuqs facets, virtualization, four states | 4 | A9 states render; URL round-trips filters; skeletons on load |
| 6 | `InterruptCard`/`DecisionForm` single-action: prefilled fields, Edit⇄Accept, Reject-with-message, Respond | 1 | A1 for all four decision types; buttons follow `allowedDecisions` |
| 7 | `argsSchema`-driven field rendering + validation | 6 | Schema fixtures render typed fields; invalid input blocks submit with per-field errors |
| 8 | Batch card: per-call rows, progress dots, draft state, ordered single-resume submit, Approve-remaining | 6 | A3 |
| 9 | Mark-resolved path (`updateState asNode END`) + confirm dialog, distinct from Reject | 6 | A6 |
| 10 | Raw-JSON fallback card + error boundaries + fuzz suite in CI | 1, 6 | A4 |
| 11 | Staleness & concurrency handling (open-card re-hydrate, decision-failure reconcile) | 6, 3 | A5 |
| 12 | Plan-interrupt rows + F09 dedupe + deep link | 4, F09 store | A8 |
| 13 | Golden-transcript contract tests vs `langgraph dev` incl. dismissal semantics | 6–9 | A1/A6 in CI |
| 14 | Keyboard nav, hotkeys, a11y + reduced-motion pass | 5–9 | A9 |

## 9. Open questions

- **Q1** Is classic `threads.updateState(..., asNode: END)` the sanctioned force-end on every tier — specifically MDA with identity enforcement — or does protocol v2 define a command equivalent? (Verify in M0 Spike 2/3.)
- **Q2** Exact server response (status code/body) when `input.respond` targets a no-longer-pending `interrupt_id` — needed to distinguish "handled elsewhere" from transient failure; until verified, any respond failure takes the re-hydrate path.
- **Q3** Is a per-interrupt created-at timestamp available anywhere (task/checkpoint metadata), or is thread `updated_at` the best age proxy permanently?
- **Q4** Do run webhooks fire when a run ends in `interrupted` status? Determines whether F19 can push on new interrupts or the inbox is poll-only for closed streams. (F19 shares this question.)
- **Q5** `args` vs `arguments` on JS-emitted action requests — upstream bug or intent ([research 13](../../research/13-agent-inbox.md) open question); tolerant read stays until resolved.
- **Q6** The plan-gate action name convention `packages/agent` will publish (drives `kind:'plan'` detection; joint with F09/F17).
- **Q7** `respondAll()` exact semantics: batches across multiple pending interrupts in one thread vs across threads — typed in the SDK, unverified against a live server.
- **Q8** Fleet-sourced agents: are interrupt state reads and resumes fully available over the public invoke/read surface (PAT + owner-gating), matching v1 release criterion 3?

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `@langchain/react` 1.0.x weekly churn shifts HITL types | Med | Pins + renovate + A1/A2 contract tests as canary ([04 risk register](../04-roadmap.md)) |
| Upstream fixes the `reviewConfigs` casing gap or `args/arguments` — normalizer diverges silently | Low-Med | Casing fixtures are generated from both middleware sources' actual output; renovate PRs rerun A2 |
| Stale docs (legacy `submit(null,{command}})` still on the HITL page) mislead contributors | Med | Lint ban (A1) + CONTRIBUTING note; the contract is pinned here, not in upstream docs |
| MDA thread/run API remains design-partner-gated | Med | Same as project-wide: classic Deployment + `langgraph dev` are fully public and feature-equivalent for this spec ([02 §12](../02-architecture.md)) |
| Concurrency semantics (Q2) differ per tier | Med | Failure path is tier-agnostic (re-hydrate & reconcile); tier-specific codes only improve copy |
| Inbox scale: N sources × paged 100-thread searches on a 30 s poll hits gateway rate limits (e.g. 2000/10 s, [research 20](../../research/20-gapfill-mda-api.md)) | Low-Med | Per-source backoff, conditional refetch on `updated_at`, poll only while tab visible |
| Force-end leaves orphaned resources (sandbox TTL cleans up, but PR branches persist) | Low | Confirm dialog states consequences; task detail shows final state + trace for audit |
