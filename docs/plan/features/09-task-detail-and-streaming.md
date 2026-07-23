# F09 · Task detail & streaming

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1 · Depth: implementation-ready*

Sources: [UI spec §3.2/§5](../03-ui-spec.md) · [architecture §7](../02-architecture.md) · [frontend plan Phase B](../06-frontend-implementation.md) · [roadmap M1–M2](../04-roadmap.md) · [deepagents feature map](../08-deepagents-feature-map.md) (context-engineering, multimodality, fault-tolerance, rubrics rows) · [research 21 · UI contract](../../research/21-gapfill-ui-contract.md) · [research 04 · LangChain UIs](../../research/04-langchain-uis.md) · [research 22 · UI tokens](../../research/22-gapfill-ui-tokens.md) · [decision log](../decisions.md)

## 1. Scope

The task-detail **experience** at `/tasks/[source]/[threadId]` ([F07 route map](./07-app-shell-and-navigation.md)) — the watch/steer/review core of vision pillar 1 ([01](../01-vision.md)). This spec owns:

- **Thread rendering** from `useStream` projections: streaming narration, reasoning folds, `ToolCallCard` lifecycle, `SubagentCard`/`SubagentGroup`, `TodoTray`, summarized-history/context-compacted markers, inline interrupt cards incl. the **`PlanCard` UX**.
- **Steering composer**: always-live, queue-vs-interrupt, optimistic states, image attachments.
- **Run panel** (right rail): module composition, slot order, per-module data wiring, responsive sheet collapse.
- **Branching/time-travel** UX (edit-&-fork, branch switcher) and **resumability** behavior (disconnect/rejoin, cross-device).
- Scroll/perf policy (stick-to-bottom, virtualization) and the screen's loading/empty/error/**degraded** states.

**Phasing** ([04 roadmap](../04-roadmap.md)): narration + tool cards + todos + steering + trace links are the **M1** exit ("dispatch → watch → steer → done"); subagent cards, branching/fork, plan approval, and the coding-task rail modules (env/files/git) land **M2**. One surface, one spec.

**Not owned here** (link, don't duplicate): stream-option factories, normalization (D-011), `DataProvider`, banned-v0-pattern lint → [F04](./04-sdk-and-agent-sources.md); interrupt *mechanics* (`respond()`/decisions, `InterruptCard`/`DecisionForm`, inbox) → [F10](./10-approvals-inbox.md) (D-010); file browser, diff takeover, artifact viewers, read-only terminal pane (P-003) → [F13](./13-files-diff-and-review.md); env-chip internals/lifecycle → [F11](./11-execution-and-environments.md); branch/PR/CI data → [F12](./12-github-and-git-flow.md); verification-panel content → [F16](./16-verification-and-rubrics.md); new-task composer & inbox row cache → [F08](./08-task-inbox.md); component visual specs/tokens → [F03](./03-design-system-and-ui-package.md). The v0 concept's task-detail screen and 558-line RunPanel are the visual seed (D-012) but its invented `ThreadEvent` union is replaced wholesale by real projections ([06 §2 gap 1](../06-frontend-implementation.md)); its Browser tab ships flagged off (P-003).

## 2. Dependencies & seams

| Spec | Direction | What crosses the seam |
|---|---|---|
| [F04 · SDK](./04-sdk-and-agent-sources.md) | consumes | `buildStreamOptions(source, threadId)`, canonical normalized types, reconnection presets, `DataProvider` (fixtures P-004 + live); F09 never touches wire casing (D-011) |
| [F02 · M0 spikes](./02-m0-spikes.md) | gated by | Spike-3 golden transcripts (content blocks, tools channel, subagent namespaces, `Last-Event-ID` resume) are this screen's render-test fixtures |
| [F03 · design system](./03-design-system-and-ui-package.md) | consumes | `MessageStream`, `ToolCallCard`, `SubagentCard/Group`, `TodoTray`, `PlanCard`, `StatusChip`, `TracePill`, `EnvChip` component shells ([03 §4](../03-ui-spec.md)) |
| [F07 · app shell](./07-app-shell-and-navigation.md) | hosted by | Route `/tasks/[source]/[threadId]` (client component, D-022); content column + 19rem rail slots; `<xl` rail→sheet-tabs collapse; `--chat-max-width: 900px` var (F07 provides, F09 applies) |
| [F08 · task inbox](./08-task-inbox.md) | notifies | Opening detail marks the thread seen; this screen's `lifecycle` events patch the shared inbox row cache (no extra requests) |
| [F10 · approvals](./10-approvals-inbox.md) | shares | One interrupt store keyed by `interrupt_id`; F09 renders in-thread cards (generic + `PlanCard`), F10 owns decisions/resume; deciding in either surface resolves both (F10 §3.6) |
| [F11 · environments](./11-execution-and-environments.md) | renders | `EnvChip` contract F11 §4.4 (`state`, `idle_expires_at`, ids) in the rail; setup-failure diagnostics appear as a thread event |
| [F12 · GitHub](./12-github-and-git-flow.md) | renders | Branch name, draft-PR link, CI status for the rail's Git module |
| [F13 · files & review](./13-files-diff-and-review.md) | links to | Files-changed summary (counts + top paths) → F13 takeover; artifacts list; `execute` tool streams feed F13's read-only terminal (P-003) |
| [F16 · verification](./16-verification-and-rubrics.md) | provides slot | Verification panel renders below the Status module (F16 §3.3); grader subagent renders in-thread as a normal `SubagentCard` |
| [F14 · agent package](./14-agent-package.md) | upstream | Steering middleware (queued messages injected before each model call), reliability middleware events, plan-gate interrupt, summarization artifacts ([02 §3](../02-architecture.md)) |
| [F19 · notifications](./19-notifications-and-push.md) | entered from | Push deep-links land on this route (thread, optionally anchored to an interrupt) |
| [F28 · glue service](./28-backend-glue-service.md) | transit | Proxy-mode streams and data-plane calls transit `apps/server` (P-005); no F09 state is stored server-side (D-003) |

## 3. Design

### 3.1 Layout & screen states

Two-pane per [03 §3.2](../03-ui-spec.md): **thread** center, `max-width: var(--chat-max-width)` (900px — deep-agents-ui precedent, [research 22](../../research/22-gapfill-ui-tokens.md)); **run panel** in the 19rem rail. `<xl` the rail collapses to sheet tabs; mobile renders rail-as-sheets ([03 §6](../03-ui-spec.md), [F07 §3.5](./07-app-shell-and-navigation.md)).

| State | Treatment |
|---|---|
| Loading | Skeleton thread rows + skeleton rail modules while `isThreadLoading`/`hydrationPromise` pends — never spinners ([03 §7](../03-ui-spec.md)) |
| Empty | New thread, no messages: composer focused, template-appropriate sample prompts (teach-the-next-action, [03 §7](../03-ui-spec.md)) |
| Error | Thread fetch failed: full-pane error + retry + copyable thread id; typed errors from F04 (`GatedEndpointError` gets owner-gating copy) |
| Degraded | Stream broken, thread state stale: amber "Live updates unavailable — reconnect" banner; last-hydrated content stays rendered; **`TracePill` keeps working** — the trace is ground truth the UI never contradicts ([02 §10](../02-architecture.md)) |

### 3.2 Thread rendering (`MessageStream`)

Everything renders from the root subscription channels `values · checkpoints · lifecycle · input · messages · tools` at namespace `[]` ([research 21](../../research/21-gapfill-ui-contract.md)). Projection → row mapping:

| Projection | Row | Behavior |
|---|---|---|
| `text-delta` content blocks | Narration | Streaming markdown (Streamdown-style, [03 §3.2](../03-ui-spec.md)); pulsing ▌ cursor while the block is open (ui-patterns convention, [research 22](../../research/22-gapfill-ui-tokens.md)) |
| `reasoning-delta` blocks | Thinking fold | Collapsed by default ("Thinking…" + duration once finished); chevron-expand; content streams while open; no layout shift on finish |
| `data-delta` (base64) blocks | Media block | Rendered via F13's media renderers (images/PDF per the multimodality row, [08](../08-deepagents-feature-map.md)) |
| `block-delta` on `tool_call_chunk` | (feeds card) | Partial-JSON args accumulate; `content-block-finish` upgrades to `tool_call` with parsed args ([research 21](../../research/21-gapfill-ui-contract.md)) — cards may render with args still streaming |
| `AssembledToolCall` | `ToolCallCard` | See lifecycle below |
| `subagents` Map (`SubagentDiscoverySnapshot`) | `SubagentCard` / `SubagentGroup` | See below |
| `values.todos` | `TodoTray` (+ rail mirror) | See below |
| Summarization/compaction artifacts | Context marker | Non-message row: "Earlier history summarized" / "Context compacted" with expandable summary content where available ([08](../08-deepagents-feature-map.md) context-engineering row; detection §9-Q4) |
| Interrupts (`tasks[].interrupts` + `input.requested`) | Inline interrupt card | Generic HITL → F10's `InterruptCard` embedded in-thread; plan-gate interrupts → `PlanCard` (below). Headless client-tool interrupts are filtered, never shown (F10 §3.1) |

**`ToolCallCard` lifecycle.** `tool-started {tool_call_id, tool_name, input}` → card appears, status `running` (◉ pulse); optional `tool-output-delta` → **streams into the card's output pane while expanded** (mono, auto-scroll, tail-follow); `tool-finished {output}` → `finished` (✓); `tool-error {message}` → `error` (✕ red, message shown even when collapsed). Collapsed by default: name (mono) + one-line arg summary (≈65 chars) + status glyph; expanded: args/output JSON-pretty in the code frame ([03 §3.2/§1.3](../03-ui-spec.md)). `output` is `null` until success — the card never renders "null" as output. Special-casing: a `task` call whose `callId` matches a `SubagentDiscoverySnapshot.id` is **suppressed** in favor of the subagent card (deep-agents-ui precedent, [research 04](../../research/04-langchain-uis.md)); `write_todos` collapses to a one-line "Todos updated" marker (the tray owns todo state); `execute` renders as a normal card and additionally feeds F13's terminal pane.

**`SubagentCard`/`SubagentGroup`.** Snapshots are discovered eagerly from root `tools`/`values` events; **content is lazy**: `useMessages(stream, snapshot)` / `useToolCalls(stream, snapshot)` subscribe to the subagent's namespace only while the card is expanded, unsubscribing on collapse (ref-counted through `ChannelRegistry` — [research 21](../../research/21-gapfill-ui-contract.md); satisfies the lazy-mount perf bar, [03 §7](../03-ui-spec.md)). Card: bordered, ▶ caret header with name + `taskInput` preview, status glyphs ○ (discovered, no events yet) ◉ (running, pulse) ✓ (complete) ✕ (error), 12rem max-h auto-scrolling body ([03 §3.2](../03-ui-spec.md), [research 22](../../research/22-gapfill-ui-tokens.md)). Consecutive snapshots sharing a parent render as a `SubagentGroup` with an n/m progress bar and responsive 1/2/3-col grid. Nesting renders by `depth`/`parentId`; both `tools:<toolCallId>` and legacy `task:` namespaces are accepted ([research 21](../../research/21-gapfill-ui-contract.md)). The F16 grader subagent gets no special chrome here.

**`TodoTray`.** `values.todos: {content, status: pending|in_progress|completed}[]` → composer-attached tray: "Task N of M" summary row, expandable list (max-h-72), icons Circle / Clock (amber) / CheckCircle (green) — deep-agents-ui final revision ([03 §3.2](../03-ui-spec.md), [research 22](../../research/22-gapfill-ui-tokens.md)). The rail Todos module mirrors the same array; empty todos hide both (no empty tray).

**`PlanCard`.** When the plan-gate interrupt arrives (require-plan-approval toggle set in F08's composer), an inline card renders the proposed plan as **per-step markdown** with two actions: **Approve** and **Edit** (per-step text editing, resubmitted as an edited decision) — the first-class *cheap-verification* moment ([03 §3.2](../03-ui-spec.md), [01 pillar 1](../01-vision.md)). Decision transport is entirely F10's (`respond()`; approve/edit shapes per F10 §4); F09 owns only the card UX. Detection keys on the plan-gate action name published by `packages/agent` (joint question, F10 §9-Q6). While the plan interrupt is pending the composer shows "Waiting for plan review" and steering input queues.

### 3.3 Steering composer

Always-live ([03 §3.2](../03-ui-spec.md)). Behavior by run state:

- **Idle thread**: send → `submit(input)`; a run starts.
- **Running**: send defaults to **Queue** — `multitask_strategy: 'enqueue'` is the platform default ([02 §7](../02-architecture.md), [research 20](../../research/20-gapfill-mda-api.md)) and the agent's steering middleware injects queued user messages before each model call ([02 §3](../02-architecture.md)). Queued messages render as chips above the composer with cancel affordances (`useSubmissionQueue`, [research 04](../../research/04-langchain-uis.md)). A split-button secondary, **Interrupt & send**, calls `stream.stop()` then submits — because server-side honoring of the `interrupt` strategy is unverified (F04 §9-Q2), the client-side stop+submit path is the v1 implementation either way.
- **Optimistic states**: `optimistic: true` (default); rendered message carries `optimisticStatus: 'pending' | 'sent' | 'failed'` ([research 21](../../research/21-gapfill-ui-contract.md)) — pending = reduced opacity, failed = red outline + Retry/Discard, never silently dropped.
- **Attachments**: image attachments submitted as multimodal content blocks on the human message (agent-chat-ui precedent, [research 04](../../research/04-langchain-uis.md); multimodality row, [08](../08-deepagents-feature-map.md)). Paste + file-picker; previews before send; size/count limits §9-Q6.

### 3.4 Run panel (rail)

Module slot order (top→bottom); every module handles its own absent/loading state; modules marked M2 don't render for M1 templates:

| # | Module | Contents | Data | Seam |
|---|---|---|---|---|
| 1 | Status | `StatusChip` + elapsed timer; **reliability events** as amber rows: "Tool-call limit hit", "Model fallback engaged" ([08](../08-deepagents-feature-map.md) fault-tolerance row) | thread status + `lifecycle` channel (event vocabulary §9-Q3); reliability event transport §9-Q5 | F04 |
| 2 | Environment (M2) | `EnvChip`: env name, sandbox id, TTL countdown, state styling; popover diagnostics | F11 §4.4 contract (D-015) | F11 |
| 3 | Verification (M2) | Rubric verdicts, criterion rows, iteration count, per-pass trace links; ghost row when no rubric | F16 §3.3 `VerificationState` (D-017) | F16 |
| 4 | Todos | Mirror of `values.todos` with N-of-M header | `values.todos` | — |
| 5 | Files changed (M2) | Counts + top paths tree summary; click → F13 full-width takeover | `values.files` / F13 connector routes | F13 |
| 6 | Git (M2) | Branch name, draft-PR link, CI status once a PR exists | F12 | F12 |
| 7 | Artifacts | Non-code outputs (reports, documents) with open-in-viewer links | F13 artifact enumeration (source-of-truth §9-Q7) | F13 |
| 8 | Trace | **`TracePill` "View trace ↗" — always rendered, pinned as rail footer**, functional in every screen state including degraded ([02 §10](../02-architecture.md)) | run → LangSmith run URL | — |

`<xl`, modules become the rail-sheet's tabs (F07); the sheet trigger badge shows the most urgent module state (error > reliability event > running).

### 3.5 Branching & time-travel

Checkpoint-channel based — **the v0-era `getMessagesMetadata`/`setBranch` patterns do not apply and are lint-banned** (F04 §3.4; [research 21](../../research/21-gapfill-ui-contract.md)):

- Each rendered message exposes `useMessageMetadata(stream, messageId).parentCheckpointId`.
- **Edit & fork** (human messages): pencil affordance prefills the composer inline; submit calls `submit(editedInput, {forkFrom: parentCheckpointId})`, creating a sibling branch.
- **Regenerate** (AI messages, optional M2 polish): re-submit from the same parent checkpoint.
- **Branch switcher**: `‹ i/n ›` control on messages with sibling branches (agent-chat-ui `BranchSwitcher` chrome precedent, [research 22](../../research/22-gapfill-ui-tokens.md)). Sibling derivation is ours: group `checkpoints` envelopes `{id, parent_id, step, source}` by `parent_id`; >1 child = a fork point; `state.listCheckpoints` backfills history not seen live ([research 21](../../research/21-gapfill-ui-contract.md)). Switching re-renders the thread along the selected lineage.
- Forking while a run is active first routes through the same stop/queue choice as §3.3.

### 3.6 Resumability & lifecycle

- Runs are submitted with `stream_resumable`; reconnects replay via `Last-Event-ID`; thread-level join streams cover "opened mid-run" ([02 §7](../02-architecture.md), [research 20](../../research/20-gapfill-mda-api.md)).
- **Background**: on `document.hidden` → `stream.disconnect()` (run continues server-side); on focus → rejoin and replay ([03 §5](../03-ui-spec.md)). Reconnection knobs (`maxReconnectAttempts`, `streamIdleReconnect`, `reconnectDelayMs`, `onReconnect`) come from F04's per-surface presets.
- **Cross-device handoff**: any device opening the route hydrates thread state (`hydrationPromise`) and joins the live stream — no device owns a run. Optimistic-message reconciliation on rejoin is §9-Q8.
- **Scroll**: `use-stick-to-bottom` ([03 §4](../03-ui-spec.md) conventions); pinned while streaming; user scroll-up unpins and shows a "Jump to latest ↓" pill with unseen-count.
- **Perf**: long threads virtualized; subagent bodies lazy-mounted; `prefers-reduced-motion` disables pulses/cursor blink ([03 §7](../03-ui-spec.md)). Virtualization must coexist with stick-to-bottom and streaming row-height changes — approach criteria in task 12, risk table.

### 3.7 Failure surfacing

| Failure | UX |
|---|---|
| Stream drop | Auto-reconnect (presets); after attempts exhaust → degraded banner (§3.1) + manual "Rejoin" (re-hydrate + join); `TransportError{retryable}` from F04 |
| Run fails | Status module → Failed (red); terminal error block in-thread with message + `TracePill`; composer stays live (follow-up = new run on same thread) |
| Reliability middleware engages | Not a failure: limit-hit/fallback rows in Status module (§3.4) so the user sees *why* behavior changed ([08](../08-deepagents-feature-map.md)) |
| Tool error | `ToolCallCard` error state; the agent may self-recover via `ToolErrorMiddleware` ([02 §3](../02-architecture.md)) — the card stays, subsequent narration explains |
| Stream ends with dangling `running` tool calls (stop/abort) | Cards flip to a terminal `cancelled` style (gray ✕) — never left pulsing (dangling-tool-call hygiene precedent, [research 04](../../research/04-langchain-uis.md)) |
| Sandbox `setup_failed`/`unreachable` | Thread event + EnvChip diagnostics per F11 §5 |

## 4. Contracts

**Consumed (pinned upstream — `@langchain/react` ^1.0.28, `@langchain/langgraph-sdk` ^1.9.x; all facts [research 21](../../research/21-gapfill-ui-contract.md), reaching F09 already normalized per D-011):**

```ts
// transport: POST /threads/{id}/commands + POST /threads/{id}/stream/events (SSE; WS unverified — F04 Q1)
// root channels: values | checkpoints | lifecycle | input | messages | tools
// content blocks: message-start → content-block-start/delta/finish → message-finish
//   deltas: text-delta | reasoning-delta | data-delta (base64) | block-delta (tool_call_chunk args)
AssembledToolCall = { name, callId, id /*alias*/, namespace, input, args /*alias*/,
                      output /*null until success*/, status: 'running'|'finished'|'error', error }
SubagentDiscoverySnapshot = { id /*task tool_call_id*/, name /*subagent_type*/,
                              namespace /*'tools:<id>' | legacy 'task:'*/, parentId, depth,
                              status: 'running'|'complete'|'error', taskInput, output, error,
                              startedAt, completedAt }
values.todos: { content: string, status: 'pending'|'in_progress'|'completed' }[]
optimisticStatus: 'pending' | 'sent' | 'failed'
checkpoints envelope: { id, parent_id, step, source }
useMessageMetadata(stream, id).parentCheckpointId; submit(input, { forkFrom })
interrupt hydration: thread.getState().tasks[].interrupts + input.requested { interrupt_id, payload }
```

**Defined here (ours):**

```ts
type ThreadRow =            // derived render model — no invented wire fields
  | { kind: 'human'; message; optimisticStatus? }
  | { kind: 'narration'; blocks }                  // text/reasoning/data blocks of one AI message
  | { kind: 'tool'; call: AssembledToolCall }
  | { kind: 'subagents'; snapshots: SubagentDiscoverySnapshot[] }   // grouped
  | { kind: 'todo-marker' } | { kind: 'context-marker'; summary? }
  | { kind: 'interrupt'; interruptId; plan: boolean };

interface RunPanelModule { id: 'status'|'env'|'verification'|'todos'|'files'|'git'|'artifacts'|'trace';
  state: 'hidden'|'loading'|'ready'|'error'; urgent?: boolean }   // §3.4 order is normative

interface ComposerSubmit { text: string; attachments: ImageBlock[];
  mode: 'start' | 'queue' | 'interrupt'; forkFrom?: string }
```

URL contract: route `/tasks/[source]/[threadId]` (F07); nuqs params `?rail=<moduleId>` (sheet state `<xl`) and `?interrupt=<id>` (F10/F19 deep-link anchor). Rail module data contracts live with their owners: EnvChip → F11 §4.4, VerificationState → F16 §3.3, files/artifacts → F13, git → F12. Banned patterns (lint, F04): `onCustomEvent`, `streamMode`, `joinStream`, `submit(null,{command:{resume}})`, `getMessagesMetadata`, `setBranch`.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| `tool-output-delta` for a collapsed card | Buffered into the assembled call; no forced expand; collapsed row shows a subtle streaming glyph |
| `tool-error` before any output | Card error state renders `error` message; output pane omitted (output stays `null`) |
| Subagent snapshot arrives with legacy `task:` namespace | Rendered identically; namespace string only affects subscription key |
| Subagent expanded/collapsed rapidly | Ref-counted subscriptions guarantee no leak: unsubscribe only at refcount 0 |
| >10 parallel subagents | Group grid + n/m bar; bodies stay lazy; no namespace subscribed until expanded |
| `values.todos` shrinks or empties mid-run | Tray re-renders from the array as-is (write_todos owns truth); empty hides tray + module |
| Message with mixed text + reasoning + tool blocks | One narration row; blocks render in wire order; reasoning folds independently |
| Plan interrupt while queued steering messages exist | PlanCard renders; queue holds; on approve, queued messages deliver via steering middleware |
| Interrupt resolved elsewhere (inbox, other device) | Shared store (F10 §5.1): in-thread card flips to "Handled elsewhere" and collapses |
| Fork from a checkpoint that another device already forked | Both branches legitimate; switcher shows n siblings; no conflict semantics needed |
| Replay gap after long disconnect (`Last-Event-ID` expired server-side) | Full re-hydrate from thread state; banner "Reconnected — history refreshed"; no partial stitching |
| Duplicate rows after reconnect (optimistic + replayed) | Dedupe by message id at the ThreadRow builder; §9-Q8 tracks upstream behavior |
| Thread with 1,000+ messages | Virtualized; context markers make summarized spans cheap; branch switching re-derives visible lineage only |
| Malformed content block / unknown delta kind | Row degrades to a raw-JSON fold (schema-tolerant rule, [03 §3.3](../03-ui-spec.md)); never crashes the thread (error boundary per row) |
| `stop()` racing `tool-finished` | Last event wins; cancelled style only applies to calls still `running` at stream close |

## 6. Security & privacy

- **Untrusted-content boundary**: all agent-origin text (narration, tool args/output, subagent output, todos, plan steps) renders as data inside the same boundary used for webhook/schedule payloads ([02 §10](../02-architecture.md)). Markdown is sanitized: no raw HTML/scripts; links get `rel="noopener nofollow"` with external-link affordance; images render only from data/blob URLs (media blocks), not arbitrary remotes — no exfiltration-by-markdown-image.
- **Chrome separation**: payload areas are visually/structurally separated from chrome so agent text cannot imitate approval states or buttons (F10 §6 rule applied in-thread); every state-changing action (approve, steer, fork, stop) is an explicit user gesture — nothing in stream content can trigger one.
- **Credentials**: the screen holds none; streams and data-plane calls use F04's proxy/direct modes (P-005); trace links are plain URLs to smith.langchain.com — authorization happens there, no tokens in the URL.
- **Tool args/output may contain sensitive material** (env values, file contents): never logged client-side; copy-to-clipboard is explicit; F04 error scrubbing covers anything captured in errors.
- **Attachments**: client-side type/size validation before submit; image bytes go to the deployment (org-owned), never to Deep Work infrastructure (D-003).
- **Provenance everywhere**: sandbox id, branch, PR link, trace link surfaced in the rail ([02 §10](../02-architecture.md)) — verification UX is the product ([01 pillar 1](../01-vision.md)).

## 7. Acceptance criteria

1. Against the Spike-3 golden transcripts (F02), narration streams token-visible from `text-delta`; reasoning blocks render collapsed and expandable; final rendered thread deep-equals the fixture-derived `ThreadRow[]`.
2. `ToolCallCard`: running→finished and running→error lifecycles render with correct glyphs; `tool-output-delta` visibly streams into an expanded card; a `task`-call card is suppressed when its snapshot exists; `write_todos` renders as a marker.
3. Subagents: expanding a card subscribes its namespace and streams content; collapsing unsubscribes (asserted via ChannelRegistry refcounts); a 3-subagent group shows n/m progress; ○/◉/✓/✕ states all reachable from fixtures.
4. Todos: tray + rail mirror track `values.todos` updates live; "Task N of M" correct; both absent when no todos.
5. Composer: while running, default send enqueues (chip visible, cancellable) and the message is injected before the next model call (verified against `langgraph dev` + steering middleware); Interrupt & send stops the run and starts a new one; idle send starts a run.
6. Optimistic: pending→sent transition on ack; forced network failure yields failed + Retry; retry does not duplicate the message.
7. PlanCard renders per-step markdown from a plan-gate fixture; Approve and per-step Edit produce F10-contract decisions; deciding from the approvals inbox resolves the in-thread card (single store, F10 A8).
8. Branching: edit-&-fork on a human message calls `submit(input,{forkFrom: parentCheckpointId})` and yields a sibling branch; the switcher navigates between 2 branches; repo-wide lint proves no `setBranch`/`getMessagesMetadata` usage.
9. Resumability: killing the connection mid-run reconnects and replays with no lost or duplicated rows vs the transcript; backgrounding disconnects (0 open streams) and focus rejoins; a second client opening the thread mid-run converges to identical state.
10. A 500-message thread scrolls at 60fps target with virtualization on; stick-to-bottom holds during streaming; scroll-up unpins and the jump pill appears.
11. Degraded: with the stream forcibly broken, the banner shows, last-known content and rail persist, and `TracePill` resolves.
12. Loading/empty/error states render per §3.1; keyboard: composer submit, card expand/collapse, fold toggles all reachable; AA contrast both themes; `prefers-reduced-motion` disables pulse/cursor animations.
13. Rail: module order matches §3.4; each module renders loading/absent/ready; reliability-event fixtures produce Status-module rows; `<xl` modules become sheet tabs.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `ThreadRow` builder: messages + toolCalls + subagents + values → render model; per-row error boundaries; dedupe | F04 types | AC-1 fixture equality; malformed-block fixture degrades per §5 |
| 2 | `MessageStream` narration: streaming markdown, reasoning fold, data-block slot, sanitization pipeline (§6) | 1, F03 shells | AC-1, AC-12 (a11y on folds); sanitizer test suite |
| 3 | `ToolCallCard` wiring: lifecycle, streaming output, error/cancelled states, special-casing (`task`/`write_todos`/`execute`) | 1 | AC-2 |
| 4 | `TodoTray` + rail Todos mirror | 1 | AC-4 |
| 5 | Steering composer: submit modes, queue chips (`useSubmissionQueue`), stop+submit interrupt path, optimistic states | F04 stream options | AC-5, AC-6 |
| 6 | Run panel shell: module registry, §3.4 slot order, per-module states, `<xl` sheet collapse, `?rail=` param | F07 slots | AC-13 (M1 modules: status/todos/trace) |
| 7 | Status module: StatusChip + elapsed from lifecycle events; TracePill footer; degraded banner + rejoin | 6 | AC-11; elapsed source documented (or §9-Q3 fallback) |
| 8 | Resumability: visibility disconnect/rejoin, reconnect presets, replay-gap re-hydrate | 5 | AC-9 |
| 9 | Screen states (loading/empty/error) + inbox seen/patch seams (F08) | 1–7 | AC-12; F08 row patches observed |
| 10 | **M2** `SubagentCard`/`SubagentGroup` with lazy ref-counted subscriptions | 1 | AC-3 |
| 11 | **M2** Inline interrupts + `PlanCard` over the shared F10 store | 5, F10 tasks 1–6 | AC-7 |
| 12 | Virtualization + stick-to-bottom integration (approach chosen against AC-10 criteria) | 2, 3 | AC-10 |
| 13 | **M2** Branching: `parentCheckpointId` plumbing, edit-&-fork, sibling derivation, switcher | 1, 5 | AC-8 |
| 14 | **M2** Rail modules env/verification/files/git/artifacts against F11/F16/F13/F12 contracts; reliability-event rows | 6 + neighbor specs | AC-13 full; fixtures for every module state |
| 15 | Golden-transcript render suite in CI (Spike-3 fixtures → ThreadRow snapshots + interaction tests) | 1–8 | AC-1/2/9 gated in CI |

## 9. Open questions

1. **WebSocket availability per tier** — SSE is confirmed; WS unverified (F04 Q1). F09 assumes SSE; nothing here may require WS.
2. **`checkpoints` channel acceptance on deployed Agent Server** — the API-reference enum omits it while protocol 0.0.18 and the SDK root pump use it ([research 21](../../research/21-gapfill-ui-contract.md)). If unavailable on a tier, branching degrades to `state.listCheckpoints` on demand; verify in Spike 3.
3. **Lifecycle event vocabulary** — the `lifecycle` channel is pinned as a root channel, but run-start/end event shapes (and therefore the elapsed-timer source) are not documented in our sources. Pin from Spike-3 transcripts; fallback: thread `created_at`/`updated_at` deltas.
4. **Summarization/compaction detection** — what artifact does the harness leave in `messages`/`values` for the context-marker row ([08](../08-deepagents-feature-map.md) requires rendering it honestly)? Needs a recorded transcript with SummarizationMiddleware active.
5. **Reliability-event transport** — how `ModelCallLimit`/`ToolCallLimit`/`ModelFallback` engagements reach the client (custom channel? state key? synthetic message?). [08](../08-deepagents-feature-map.md) mandates rail surfacing; wire shape unknown. Joint with F14.
6. **Attachment limits** — max image size/count per message, and whether large media should be written to the backend and passed by path (the documented agent-side guidance) rather than inlined into the message. Joint with F14/F13.
7. **Artifacts enumeration** — is the rail's artifacts list derived from `values.files` (non-code MIME types) or a dedicated state key? [03 §3.2](../03-ui-spec.md) names the module without a source. Joint with F13/F14.
8. **Optimistic reconciliation on resume** — does `Last-Event-ID` replay reconcile client-side optimistic messages by id, or can duplicates surface (our builder dedupes defensively)? Not covered in [research 21](../../research/21-gapfill-ui-contract.md).
9. **Plan-gate action name convention** — shared with F10 §9-Q6 / F14; drives `PlanCard` detection.
10. **`stop()` semantics vs server-side `interrupt` strategy** — if server-side double-texting strategies land (F04 Q2), should Interrupt & send migrate from stop+submit to `multitask_strategy:'interrupt'`? Revisit when upstream ships.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `@langchain/react` 1.0.x weekly churn shifts projection shapes | High freq / med sev | All upstream contact via F04; Spike-3 render suite (task 15) is the tripwire ([04 risk register](../04-roadmap.md)) |
| Virtualization × stick-to-bottom × streaming heights is genuinely hard | Janky core surface | Task 12 isolated with explicit AC-10 criteria; fallback: virtualize only above a row-count threshold, keep tail unvirtualized |
| Client-side queue vs server enqueue double-delivery (steering middleware + `multitask_strategy` both queueing) | Duplicate steering messages | Single queue owner: client queues only while a run streams, submits one run's input at a time; verified in AC-5 against `langgraph dev` |
| Unknowns Q3–Q5 (lifecycle/markers/reliability events) force UI guesses | Rework in Status module & markers | Modules render from typed contracts with `hidden` states — absent data degrades to hidden, never wrong |
| Branching UX confuses more than it helps (checkpoint lineage is subtle) | Feature drag in M2 | Scope-boxed: edit-&-fork + switcher only; no checkpoint browser in v1; roadmap M2 gate can drop it without touching M1 scope |
| MDA invoke gating (O-003) blocks live testing on the primary tier | Schedule risk | Everything here is tier-agnostic; `langgraph dev` + classic Deployment cover all AC verification (D-004 fallback path) |
| Reasoning-delta availability varies by provider/profile | Fold renders inconsistently | Fold is data-driven: no reasoning blocks → no fold; never synthesized |
