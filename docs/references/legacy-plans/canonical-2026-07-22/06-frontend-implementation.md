# 06 · Frontend concept evaluation & implementation plan

*Deep Work planning docs · 2026-07-22. Evaluates [`spencerthomas/deep-work-frontend`](https://github.com/spencerthomas/deep-work-frontend) @ `c46b994` (v0-built concept) against the [UI spec](03-ui-spec.md) and [architecture](02-architecture.md), then lays out the implementation plan that turns it into `apps/web`.*

## 1. What the concept is

A v0-generated Next.js app: Next 16.2.6 · React 19.2.4 · Tailwind v4 · shadcn 4.x on `@base-ui/react` · lucide-react · recharts. ~4.1k LOC across 53 files. Entirely client-rendered; **all data is mock** (`lib/data.ts`, 1,110 lines); no SDK, streaming, or auth wiring.

Screen coverage vs UI spec §3 — complete, plus extras:

| Spec screen | Concept | Notes |
|---|---|---|
| Task inbox | ✅ `/tasks` | rows, status chips, filters sidebar |
| Task detail | ✅ `/tasks/[id]` | thread events, composer, 558-line RunPanel (Status/Trace/Files/Git/Browser tabs), terminal pane, layout toggles |
| New task | ✅ `/tasks/new` | incl. composer attachments (tools/context/skills/subagents) |
| Approvals | ✅ `/approvals` | queue + per-kind/agent filters |
| Agents / builder | ✅ `/agents`, `/agents/[id]` | fleet cards + builder |
| Schedules · Activity | ✅ | |
| Onboarding/settings | ✅ `/login`, `/config` | sign-in already implements OAuth + device-flow + key-fallback copy; config has connectors (with per-permission **Auto/Ask**), skills, plugins |
| — beyond spec | ✅ | `/observability` (spend/latency/feedback/model charts), mini **trace-span viewer** in RunPanel, **browser/computer-use card**, decorative beam-field |

## 2. Evaluation

### Strengths — adopt these

1. **Screen and IA coverage is essentially v1-complete**, and the extras (trace viewer, connector permission matrix, composer attachments) anticipate roadmap items well.
2. **High token fidelity** to the design brief: `#006DDD`/`#161F34`/gray ramp/status-tint pattern, Inter + IBM Plex Mono, the 6/8/12/16 radius scale, dismissible brand banner, the 13.6px workspace-selector radius, dark mode via class — mapped through shadcn semantic variables, which is exactly the right integration seam.
3. **Clean decomposition**: `AppShell` with `sidebar`/`rail` slots, `StatusChip`, `ToolCard`, `Composer`, `RunPanel` tabs, `PageHeader` — maps ~1:1 onto the `packages/ui` inventory (UI spec §4).
4. **Centralized mock domain** (`lib/data.ts`): one seam to swap for the real data layer, and worth keeping permanently as the fixture set for Storybook/tests/demo mode.

### Gaps — the actual work

1. **No data layer.** The `ThreadEvent` union is an invention; the real contracts are `@langchain/react` v1 projections (content blocks, `AssembledToolCall`, `SubagentDiscoverySnapshot`, `values.todos`, `FileData` variants, checkpoints). Nothing streams.
2. **Approvals model is off-contract.** `Approval {kind: shell|write|network|commit, command}` with verbs approve/edit/respond/**ignore** is the *legacy agent-inbox* shape. The real contract is `HITLRequest` → `decisions` (approve/**edit**/**reject**/respond), capabilities derived from `reviewConfigs.allowedDecisions`, batched interrupts, `respond()/respondAll()`. The approvals UI must be re-grounded (UI spec §3.3).
3. **Missing spec pieces**: sub-agent cards, plan-approval card, todo tray in composer, diff-review takeover with batched line comments, branching/fork affordances, queue-vs-interrupt steering, interrupt-count badges, URL-as-state (uses `useState`; spec says nuqs), empty states, virtualization.
4. **No server side**: no OAuth/device-flow routes, no key proxy, no GitHub-token proxy callback, no push fan-out; sign-in is a visual.
5. **Hygiene**: `ignoreBuildErrors: true`, no tests/CI, package name `my-project`, lockfile pins a <24h-old `react-is` that trips pnpm `minimumReleaseAge` supply-chain policies (hit during this evaluation; ages out, but regenerate), all-client components (fine for v1 app-like surfaces, but drop the blanket pattern where server components are free wins).
6. **IA question**: 7 top-level tabs (adds Observability + Config). Recommendation: consolidate to 6 — fold Config into Settings + Agent detail; keep a slim Observability (or fold into Activity) that links out to LangSmith rather than re-implementing it.

### Verdict

**Adopt as the seed of `apps/web`.** This is a strong visual/IA foundation that compresses M0–M1 chrome work by weeks. It is a *rendering layer waiting for a data layer* — the plan below wires the architecture underneath it without repainting it.

## 3. Implementation plan

Phases map onto the existing [roadmap](04-roadmap.md) milestones.

### Phase A — Adopt & consolidate (M0)

- Import the concept into the monorepo as `apps/web` (one-way: **the monorepo becomes canonical**; the v0 repo stays a design sandbox — v0 pushes there, curated changes get ported over, never merged blind).
- Single token source: replace the inline `@theme`/`:root` block with `packages/ui/tokens.css` + preset; move `StatusChip`, `ToolCard`, `PageHeader`, `AppShell` primitives, `CommandBar` into `packages/ui` with stories.
- Hygiene: rename package, strict TS + remove `ignoreBuildErrors`, biome, vitest + RTL scaffold, regenerate lockfile, nuqs for inbox/task URL state, CI wiring per [05](05-oss-setup.md).
- Keep `lib/data.ts` as `packages/ui/fixtures` — it becomes demo mode + test fixtures.

### Phase B — Data layer under the paint (M1)

- `packages/sdk`: `AgentSource` registry (MDA deployment / any deployment URL / `langgraph dev`), control-plane client, normalized types. UI components consume a `DataProvider` interface with two implementations: **fixtures** (Phase A) and **live**.
- Live inbox: `threads.search` aggregation → existing `TaskRow`; status chips from thread status + interrupt counts.
- Live task detail: `useStream` per thread → map real projections onto existing renderers — content blocks → narration; `AssembledToolCall` → `ToolCard` (incl. streaming output into the open card); `values.todos` → RunPanel Status tab + new composer todo tray; `FileData` → Files tab; **new** `SubagentCard`; trace pill → real run URL.
- Server routes in `apps/web`: key proxy (passthrough pattern), OAuth/device-flow per M0 spike outcome; sign-in screen goes live.
- Composer: real submit + double-texting (queue vs interrupt affordance), optimistic states.

### Phase C — HITL correctness (M2)

- Rebuild `ApprovalActions`/`approvals-view` on the v1 contract: decisions approve/edit/reject/respond; per-arg edit forms (Edit⇄Accept auto-switch); batched interrupts as one card with per-call decision rows; capability chips from `allowedDecisions`; casing-tolerant `reviewConfigs` reads; schema-tolerant raw-JSON fallback; *Reject* vs *Mark resolved* kept distinct. Sidebar filters derive from tool names/`reviewConfigs`, not hardcoded kinds.
- Plan-approval card in task detail; approvals hydrate from thread state + `input.requested` live updates.

### Phase D — Coding-task surfaces (M2)

- Files/diff: wire Files/Git tabs to sandbox connector routes; promote the diff view to the full-width takeover with per-line comments batched into a steering message; PR/CI status in Git tab.
- Terminal pane fed by `execute` tool streams (read-only v1).
- Browser/computer-use card: keep the component, feature-flag it off for v1 (no default browser tool in the deepagents harness; Fleet-only capability today).

### Phase E — Fleet manager & config (M3)

- Wire agents/builder/config to `/v1/deepagents/*`, Context Hub (instructions/skills/memories), crons (schedules), and the connector permission matrix → `interrupt_on` config. Import/export via Fleet-export format.
- Observability: keep the charts bound to whatever LangSmith stats the key can read cheaply; otherwise slim to counts + deep links (decision at M3 entry).

### Phase F — Platform & polish (M4)

- PWA (manifest, Web Push from run webhooks, bottom bar per spec §6), Tauri wrap (tray, notifications, deep links, device-flow), keyboard/a11y/virtualization/empty states, reduced-motion audit of beam-field + status pulses.

## 4. Decisions taken (flag if you disagree)

1. **Monorepo is canonical; v0 repo is a sandbox.** Two-way sync with v0 invites drift and lockfile surprises.
2. **IA consolidates to 6 tabs** (Config → Settings/Agent detail; Observability slimmed).
3. **Browser card ships flagged-off**; terminal ships read-only.
4. **Fixtures stay forever** (demo mode + tests), so the app remains runnable with zero credentials — good for OSS contributors.
