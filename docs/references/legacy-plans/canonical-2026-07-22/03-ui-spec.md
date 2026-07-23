# 03 · UI specification

*Deep Work planning docs · 2026-07-21. Design tokens extracted from `langchain-ai/docs` (docs.json, style.css, brand-guidelines.md) and live docs.langchain.com CSS; component conventions from agent-chat-ui, deep-agents-ui (archived), ui-patterns.langchain.com, agent-inbox. Interactive companion: [design brief](../design/deepwork-design-brief.html).*

## 1. Design language

**North star: "feels like LangChain shipped it."** The app shell is a near-carbon copy of docs.langchain.com (Mintlify theme "aspen") — deliberately, since Deep Work is built for potential adoption. Two hygiene rules: no LangChain wordmark/logos/name in branding (registered trademarks), and no redistribution of their commercial fonts (TWK Lausanne, Aeonik Mono) — tokens make both swappable in one place if LangChain adopts the project.

### 1.1 Color

RGB-triplet custom properties composed with alpha (`rgb(var(--primary) / 0.10)`), exactly as the docs site does:

| Token | Light | Dark | Use |
|---|---|---|---|
| `--primary` | `#161F34` | — | light-mode accent/active, headings ink |
| `--primary-dark` | `#006DDD` | `#006DDD` | CTAs, banner, links, running state |
| `--primary-light` | — | `#7FC8FF` | dark-mode accent/active |
| background | `#FFFFFF` | `#030710` | page ground |
| surfaces (dark) | — | `#0D1322` raised · `#161F34` elevated | cards, popovers, inline code |
| borders | `#EEEEEF` (gray-100) | `white/10`, emphasis `#4f5d73` | rules, frames |
| gray ramp | `#F3F3F4 → #0A0B0B` (11 steps, machine-derived from primary) | | text hierarchy |

Semantic (from the LangChain extended palette + first-party UI conventions): success/approve green `#6E8900` (UI convention `#10b981` acceptable for chips), warning/in-progress amber `#f59e0b`, error/reject red `#ef4444`, running blue = primary-dark/light. Status colors are never the accent; the accent means *active/actionable*.

Never pure black; darkest ink `#030710`/`#0A0B0B`. If the primary hue ever changes, regenerate the gray ramp (it's derived, not independent).

### 1.2 Typography

- **Headings**: Inter 600/700 (OFL stand-in for TWK Lausanne; token `--font-heading` for drop-in swap). h1 30→36px/600/tracking-tight; h2 24/700; h3 20/600.
- **Body**: Inter 400, 16px, lh ~1.65. **UI workhorse is 14px** (`text-sm`); micro-labels 12px/600/uppercase/+5% tracking.
- **Mono**: IBM Plex Mono — code, diffs, paths, tool args, tokens. 14px / lh 24px.
- **Signature detail**: active nav/tab items use faux-bold via `text-shadow: -0.2px 0 0 currentColor, 0.2px 0 0 currentColor` (no layout shift), plus `bg-primary/10 text-primary` pills (dark: primary-light variants).

### 1.3 Radii, icons, code

- Radii: 8px tiles · **12px interactive (workhorse)** · 14px code inner · 16px frames/cards · pill for search/chips.
- Icons: **Tabler outline**, 16px, 1.5px stroke (docs-site parity; lucide acceptable in shadcn internals).
- Code/diff: catppuccin-latte `#eff1f5` / mocha `#1e1e2e`, framed (16px outer + 2px gutter + 14px inner); diffs via `@pierre/diffs` (ui-patterns' choice) or Shiki, unified view default.

## 2. App shell (docs-site anatomy, re-labeled)

Measurements confirmed from live CSS:

```
┌ banner (optional, 40px, #006DDD, dismissible, --banner-height) ──────────────┐
├ navbar h-56: logo · org/workspace ▾ · search pill (⌘K, rounded-full) ·      │
│   docs link · [New task] CTA (bg-primary-dark, rounded-xl)                   │
├ tab row h-40: Tasks · Approvals · Agents · Schedules · Activity              │
│   (1px bottom indicator, active = accent + faux-bold)      header Σ 96px    │
├──────────┬───────────────────────────────────────────┬──────────────────────┤
│ sidebar  │ content                                    │ right rail           │
│ 288px    │ max-w 72rem, gap 48px, pad-l 88px, pt 40px │ 19rem (2.5rem gutter)│
│ context  │ breadcrumb eyebrow → h1 → toolbar → body   │ contextual panel     │
│ nav      │                                            │                      │
└──────────┴───────────────────────────────────────────┴──────────────────────┘
shell max-w 92rem · sidebar items text-sm py-1.5 rounded-xl, active bg-primary/10
```

- **Sidebar** is contextual per tab (Tasks → status/agent/repo filters; Agents → agent list; Settings groups). Scroll-fade masks top/bottom (docs-site detail).
- **Right rail** replaces "On this page": in task detail it's the **run panel** (status, todos, files, trace); elsewhere it's metadata/help. Hidden < xl.
- **Command palette** (⌘K): search tasks/agents/actions; the search pill is its trigger.
- **Responsive**: < lg sidebar goes off-canvas; < xl rail collapses into tabs/sheets; mobile gets a bottom bar (Tasks / Approvals / Agents) and the tab row scrolls with fade masks.

## 3. Screens

### 3.1 Task inbox (home)

- Rows (agent-inbox-derived, fixed-height ~72px, 12-col grid): unread dot · task title (bold) + one-line preview (last narration/todo, truncated) · context chip (repo/agent) · **status chip** · relative time. Hover `bg-gray-50/90`; URL-as-state for filters/pagination (nuqs).
- Status chips (pill + 6px dot): Running (blue, subtle pulse) · **Needs review** (amber) · Done (green) · Failed (red) · Queued (gray). Grouping: *Needs you* → *Running* → *Recent*; deep-agents-ui's time-bucket grouping (Today/Yesterday/This Week) within *Recent*.
- Thread listing = `threads.search({metadata: {assistant_id | graph_id}, sortBy: 'updated_at', status?})`, aggregated across configured agent sources; interrupt-count badges per thread.
- **New task** composer: modal from CTA — prompt, agent picker, environment picker (coding), repo/branch, "require plan approval" toggle (Jules' `requirePlanApproval` pattern).

### 3.2 Task detail

Two-pane: **thread** (center, max-w ~900px) + **run panel** (rail).

Thread renders from `useStream` projections:
- **Narration**: streaming markdown (Streamdown-style), content-block deltas (`text-delta`; `reasoning-delta` in a collapsed "thinking" affordance).
- **Tool calls**: chevron-collapsible cards from `AssembledToolCall {name, callId, namespace, input/args, output, status: running|finished|error, error}` — collapsed by default showing name + one-line arg summary + status glyph; expanded shows args/output (mono, JSON-pretty). `tool-output-delta` streams into the open card.
- **Sub-agents**: cards from the `subagents` Map (`SubagentDiscoverySnapshot {id, name, namespace, status, taskInput, output}`) — ui-patterns styling: bordered card, ▶ caret header, status glyphs ○ ◉(pulse) ✓ ✕, 12rem max-h auto-scrolling body; content lazy-loaded via `useMessages/useToolCalls(stream, snapshot)` (ref-counted namespace subscriptions). Group header shows n/m progress bar.
- **Todos** (`values.todos: {content, status: pending|in_progress|completed}[]`): compact tray above the composer (deep-agents-ui final revision) — "Task N of M" summary row, expandable; icons Circle/Clock(amber)/CheckCircle(green).
- **Composer**: always-live steering input. While running, send = queue (enqueue default) with explicit "queue vs interrupt" affordance; optimistic messages show pending/sent/failed.
- **Plan approval**: when the plan interrupt arrives, an inline plan card with per-step markdown + Approve/Edit — the first-class *cheap verification* moment.

Run panel (rail): status + elapsed; environment/sandbox chip (id, TTL); todos mirror; **Files changed** (tree + counts, from `values.files` or sandbox connector routes; FileData both variants: py `{content, encoding}` / js v1 lines / v2 `{content, mimeType}`); branch + **draft PR link** + CI status once open; **View trace ↗** (always); artifacts list.

- **Diff review**: full-width takeover from "Files changed" — unified diff, per-line comments batched into one steering message (the Codex/Claude convention), Approve-and-PR action.
- **Branching/time-travel**: checkpoint-channel based — `useMessageMetadata(...).parentCheckpointId`, `submit(input, {forkFrom})`; UI = per-message "edit & fork" affordance with a branch switcher (v0 `setBranch` patterns do not apply).

### 3.3 Approvals inbox

Built **natively on the v1 HITL contract** (agent-inbox is UX reference only — its resume path predates the contract):

- Interrupt payload: `{actionRequests: [{name, args, description?}], reviewConfigs: [{actionName|action_name, allowedDecisions|allowed_decisions: [approve|edit|reject|respond], argsSchema?|args_schema?}]}` (SDK normalizes casing, camelCase canonical — **except** reviewConfigs' inner keys: read both).
- Resume: `stream.respond({decisions: [{type:'approve'} | {type:'edit', editedAction:{name,args}} | {type:'reject', message?} | {type:'respond', message}]})` — one decision per action request, in order; `respondAll()` for batches. **Never** the legacy `submit(null, {command:{resume}})`.
- List: cross-agent, rows show tool name + arg preview + capability chip derived from `allowedDecisions` ("Requires action" vs informational); batched interrupts render as one card with per-call decision rows + progress dots (green/red/amber by decision — agent-chat-ui pattern).
- Card: per-arg editable fields prefilled from args (Edit⇄Accept auto-switch: accept becomes edit when dirtied); Reject-with-message and Respond textarea; two dismissal semantics kept distinct — *Reject* (agent continues, ToolMessage error) vs *Mark resolved* (force-end, `updateState asNode: END` equivalent).
- Schema-tolerant rendering: malformed interrupts degrade to a raw-JSON card with copyable thread id — never crash the inbox.
- Mobile: push notification → one-tap approve screen. This is the flagship mobile flow.

### 3.4 Agents (fleet manager)

- **Index**: table (LangSmith is table-heavy; cards optional toggle) — name, runtime tier badge (MDA / Deployment / Fleet / local), model, tools count, channels, schedules, last run, health. Fleet-sourced agents show owner-gating state (invoke-only).
- **Agent detail** tabs: *Overview* (recent runs, health, trace links) · *Configuration* — file-first editor over the canonical deepagents project layout: `instructions.md` (markdown editor), tools + MCP connectors (list + `/v1/deepagents/mcp-servers` wiring), sub-agents, skills (`SKILL.md` browser), memory (`/memories/AGENTS.md`, per-user on dev channel), **per-tool Auto/Ask matrix** (renders to `interrupt_on`) · *Schedules* (cron editor with timezone + prompt|input, `deliver_to` when channels exist) · *Environment* (sandbox snapshot picker, `setup.sh` editor, egress allow-list) · *Deploy* (revision history, deploy button → tarball/gh-source flow, deep link to smith.langchain.com).
- **Create**: template gallery (Deep Work SWE · Research · Writing · blank) → form flow. Import/export = Fleet-export deepagents ZIP format both ways.

### 3.5 Schedules & Activity

- Schedules: org-wide cron list (crons search API) with per-schedule prompt, next-run, enable/disable, run history linking into task detail. Fired-run payloads render in untrusted-content boundaries.
- Activity: recent runs across agents (compact audit feed), filterable; each row → task detail + trace.

### 3.6 Onboarding & settings

- **Sign in with LangSmith** (OAuth PKCE; device-code screen on desktop) → org/workspace picker → "deploy the Deep Work agent" wizard (detects beta MDA availability; falls back to Deployment flow; or "connect an existing agent" by URL + assistant id).
- API-key path (self-hosted orgs / no-OAuth): paste key → stored via server proxy by default (`langgraph-nextjs-api-passthrough` pattern), client-side localStorage only in local mode — with the trust story ("your org, your data") stated on-screen.
- Settings: agent sources (multi-deployment registry, OAP's `NEXT_PUBLIC_DEPLOYMENTS`-style but user-editable), GitHub App install/repos, notifications (Web Push opt-in per device), theme (system/light/dark), danger zone.

## 4. Component inventory (`packages/ui`)

Foundations: tokens.css (committed as seed) · Tailwind preset · shadcn/ui (new-york) re-themed to the token set.

| Component | Notes |
|---|---|
| `StatusChip` | 5 task states + thread statuses; pill + dot; pulse on running |
| `TaskRow` / `TaskList` | fixed-height grid rows, unread dot, URL-state filters, virtualized |
| `MessageStream` | content-block renderer: markdown, reasoning fold, stick-to-bottom |
| `ToolCallCard` | collapsible; streaming output; error state |
| `SubagentCard` / `SubagentGroup` | lazy namespace subscription; n/m progress |
| `TodoTray` | composer-attached tray + rail mirror |
| `InterruptCard` / `DecisionForm` | v1 HITL contract; batch; Edit⇄Accept; schema-tolerant fallback |
| `FileTree` / `FileViewer` / `DiffViewer` | Prism/Shiki + @pierre/diffs; 60vw dialog or takeover; line comments; FileViewer renders multimodal content blocks (image/PDF/audio/video) — `read_file` returns media, and the composer accepts image attachments |
| `PlanCard` | plan approval with per-step edit |
| `AgentCard` / `AgentTable` | tier badges, health |
| `CronEditor` | 5-field cron + timezone + prompt/input |
| `TracePill` | canonical "View trace ↗" |
| `CommandPalette`, `SearchPill`, `OrgSwitcher`, `EnvChip`, `Banner`, `EmptyState`s | shell chrome |

Conventions (shared across all LangChain first-party UIs — keep them): sonner toasts, nuqs URL state, use-stick-to-bottom, uppercase micro-labels, chevron-collapsible cards, amber = in-progress/interrupted, green = success/approve, red = error/reject.

## 5. Data-layer contract (pins)

- `@langchain/react` ^1.0.28 + `@langchain/langgraph-sdk` ^1.9.x; **do not** copy agent-chat-ui's legacy v0 hook patterns (`onCustomEvent`, `streamMode`, `joinStream`, `submit(null,{command}})` — all gone in v1).
- `useStream` per active thread: SSE default, WebSocket where beneficial (desktop), custom `AgentServerAdapter` reserved for the post-v1 OSS tier; `maxReconnectAttempts`/`streamIdleReconnect` tuned for mobile; `stream.disconnect()` on background, rejoin via resumable streams (`Last-Event-ID`).
- Root subscription channels (`values, checkpoints, lifecycle, input, messages, tools`) drive everything above; interrupts hydrate from thread state and live-update from `input.requested`.
- Wire is snake_case; render layer normalizes once at the SDK boundary — components never see casing variants except the documented reviewConfigs exception.

## 6. Platform adaptations

- **Web**: the spec above; PWA manifest + Web Push (iOS ≥16.4 requires home-screen install — onboarding nudges this).
- **Desktop (Tauri v2)**: same web app; tray with needs-review count, native notifications, deep links (`deepwork://task/...`), auto-updater; global ⌘K.
- **Mobile (PWA v1)**: bottom bar (Tasks/Approvals/Agents), thread with rail-as-sheets, approval one-tap flow, composer voice input where available. Native Expo app post-v1 reuses `packages/sdk` + tokens; `useStream` is RN-compatible (documented with expo/fetch).

## 7. Accessibility & quality bars

- WCAG AA contrast in both themes (dark borders already bumped to `#4f5d73` for 1.4.11 — keep); visible focus states; full keyboard nav (inbox j/k, ⌘K, approval hotkeys); `prefers-reduced-motion` honored (pulse/motion off).
- Virtualize inbox and long threads; lazy-mount subagent bodies (the ref-counting exists for this); skeletons, not spinners, in list views.
- Every screen has a real empty state that teaches the next action (no blank tables).
