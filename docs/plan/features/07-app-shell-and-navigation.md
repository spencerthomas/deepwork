# F07 · App shell & navigation

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M0 · Depth: implementation-ready*

Sources: [../03-ui-spec.md](../03-ui-spec.md) (§2, §6, §7) · [../06-frontend-implementation.md](../06-frontend-implementation.md) · [../02-architecture.md](../02-architecture.md) · [../04-roadmap.md](../04-roadmap.md) · [../../research/11-docs-design-language.md](../../research/11-docs-design-language.md) · [../../research/22-gapfill-ui-tokens.md](../../research/22-gapfill-ui-tokens.md) · [../../../packages/ui/tokens.css](../../../packages/ui/tokens.css) · decisions: [../decisions.md](../decisions.md) (D-022, P-002, P-005)

## 1. Scope

**In:** the persistent chrome of `apps/web` — banner slot, navbar, tab row, contextual sidebar, content column, right rail; the Next.js App Router route map and server/client component split (D-022); the 6-tab IA under P-002; command palette (⌘K) v1 + SearchPill; responsive collapse rules; theme system; keyboard-nav map; the empty/loading/error/degraded-state *framework* the shell provides to every screen.

**Out (linked seams):** contents *inside* each screen (task rows, interrupt cards, agent tables — owned by their feature specs, see [catalog](./README.md)); sign-in, org/workspace membership, session handling ([./05-auth-and-identity.md](./05-auth-and-identity.md)); mobile-specific flows, PWA install, bottom-bar interaction detail, push ([./20-pwa-and-mobile.md](./20-pwa-and-mobile.md)); desktop tray/deep-link handling (Tauri, UI spec §6).

**P-002 dependency (provisional).** This spec is written against the consolidated **6-tab** IA: Tasks · Approvals · Agents · Schedules · Activity · Observability-slim, with the v0 concept's `Config` tab dissolved into Settings + Agent detail ([06 §2.6, §4.2](../06-frontend-implementation.md)). If P-002 is overturned, reverts are listed in §3.2.

## 2. Dependencies & seams

| Dependency | What this spec takes from it |
|---|---|
| D-022 — Next.js frontend | App Router, route groups, per-segment `layout/loading/error` files |
| P-002 (provisional) — 6 tabs | Tab set, `/config` → `/settings` relocation (§3.2) |
| P-005 (provisional) — Python FastAPI `apps/server` glue | Shell-level data (palette search, source health) reaches the browser via `apps/server` proxy routes, not Next.js API routes. Note: [02 §1/§11](../02-architecture.md) still describes Next.js server routes — P-005 supersedes |
| [../03-ui-spec.md](../03-ui-spec.md) §2 | All shell measurements, sidebar/rail semantics, scroll-fade masks, palette definition |
| [../06-frontend-implementation.md](../06-frontend-implementation.md) Phase A | v0 concept imported as `apps/web`; `AppShell` (sidebar/rail slots), `PageHeader`, `CommandBar` move to `packages/ui`; blanket client components called out as a smell (§2.5) |
| [../../../packages/ui/tokens.css](../../../packages/ui/tokens.css) | Layout CSS vars (§4.2) — single source of truth for measurements |
| [../04-roadmap.md](../04-roadmap.md) | M0: shell chrome against static data; M4: palette, keyboard nav, empty states, a11y pass |
| [../../research/11-docs-design-language.md](../../research/11-docs-design-language.md) | Live-verified anatomy (56px `h-14` navbar, 40px `h-10` tabs, 18rem sidebar, 19rem rail, 92rem shell), search pill recipe, fade masks, banner var |
| Upstream libs | shadcn/ui new-york re-themed (UI spec §4); nuqs URL state; sonner toasts (UI spec §4 conventions); Tailwind breakpoints `lg` 1024px / `xl` 1280px (v0 concept uses Tailwind v4 defaults, [06 §1](../06-frontend-implementation.md)) |

Seams held for neighbors: F05 owns everything behind the org/workspace switcher and route guarding; F20 owns bottom-bar flows, one-tap approval, installability; the per-screen specs own sidebar *filter definitions* and rail *panel contents* — F07 owns only the slots, dimensions, and collapse behavior.

## 3. Design

### 3.1 Shell anatomy (confirmed measurements)

```
┌ banner (optional · 40px min-h-10 · bg #006DDD · dismissible · --banner-height) ┐
├ navbar 56px h-14: logo h-6 · org/workspace ▾ · SearchPill (h-9 rounded-full ⌘K)│
│   · docs link · [New task] CTA (bg-primary-dark rounded-xl)                    │
├ tab row 40px h-10: Tasks·Approvals·Agents·Schedules·Activity·Observability     │
│   1px bottom indicator · active = accent + faux-bold        header Σ 96px      │
├──────────┬────────────────────────────────────────────┬────────────────────────┤
│ sidebar  │ content max-w 72rem · gap-x 48px            │ right rail 19rem       │
│ 288px    │ pad-l 88px (lg+) · pt 40px                  │ (incl 2.5rem gutter)   │
│ (18rem)  │ breadcrumb eyebrow → h1 → toolbar → body    │ hidden < xl            │
└──────────┴────────────────────────────────────────────┴────────────────────────┘
shell max-w 92rem · sidebar items text-sm py-1.5 rounded-xl · active bg-primary/10
```

All values from UI spec §2 / research 11, tokenized in `tokens.css` (§4.2 — navbar `var(--navbar-height)` 3.5rem/56px, tabs `var(--tabbar-height)` 2.5rem/40px). Signature details carried over verbatim: faux-bold active text-shadow (no layout shift), `bg-primary/10` active pills (dark: `primary-light` variants), scroll-fade masks top/bottom of sidebar and on the tab row when it scrolls, `--banner-height` var so content offset follows banner dismissal. Thread column inside task detail caps at `--chat-max-width` 900px (owned by the task-detail spec; the shell only provides the column).

### 3.2 Information architecture under P-002

| Tab | Sidebar (contextual) | Right rail | Notes |
|---|---|---|---|
| Tasks (home) | status/agent/repo filters (nuqs-backed) | inbox: metadata/help · task detail: **run panel** (status, env chip, todos, files, PR/CI, trace, artifacts — UI spec §3.2) | Inbox = `/`; filters owned by inbox spec |
| Approvals | filters derived from tool names / `reviewConfigs` — not hardcoded kinds ([06 Phase C](../06-frontend-implementation.md)) | decision context (owner: approvals spec) | |
| Agents | agent list (UI spec §2) | metadata/help | Detail hosts relocated per-agent Config (below) |
| Schedules | filter groups — *definition owned by schedules spec* | metadata/help | |
| Activity | filter groups — *owned by activity spec* | metadata/help | |
| Observability (slim) | none v1 | none v1 | Counts + LangSmith deep links; chart depth decided at M3 entry ([06 Phase E](../06-frontend-implementation.md)) |

**Config relocation** (P-002): app-level concerns → **Settings** (`/settings`: agent sources, GitHub App, notifications, theme, danger zone — UI spec §3.6); per-agent concerns → **Agent detail → Configuration** (instructions, tools/MCP, sub-agents, skills, memory, Auto/Ask matrix — UI spec §3.4). Settings is reachable from the navbar (avatar/gear menu), not a tab.

**If P-002 is overturned:** `Config` returns as a 7th top-level tab (route `/config` restored, redirect in §4.1 dropped); Settings shrinks back to the v0 split; the Agent-detail Configuration tab **stays** regardless — it is grounded in UI spec §3.4 independent of P-002. Tab-row overflow is already handled (scrolling row + fade masks), so no layout rework.

### 3.3 Server vs client components

Blanket `"use client"` is an explicitly flagged smell ([06 §2.5](../06-frontend-implementation.md)). Split:

| Segment | Server | Client (leaf islands) |
|---|---|---|
| Root layout | fonts, token CSS, html `class` bootstrap | `ThemeProvider`, toast portal (sonner) |
| Navbar | static frame, logo, docs link | `OrgSwitcher`, `SearchPill`→palette, New-task button (opens client modal) |
| Tab row | tab list markup | active-state highlighter (`usePathname`), badge counts |
| Banner | slot + server-decided content | dismiss button (persists to `localStorage`) |
| Sidebar | per-tab `layout.tsx` shells | filter widgets (nuqs), agent list (live data) |
| Content | settings pages, empty states, login/onboarding shells | anything on `useStream`/`threads.search`, composer, palette |
| Rail | slot | run panel and other live panels |
| Boundaries | `loading.tsx` skeletons | `error.tsx` (client per Next.js) per tab segment |

Palette and diff-heavy components load via `next/dynamic` so shell TTI stays independent of them.

### 3.4 Command palette (⌘K) v1

Trigger: `SearchPill` (navbar center, h-9 max-w-sm rounded-full, ⌘K hint — research 11) or ⌘K / Ctrl+K anywhere; desktop app adds a global OS shortcut (UI spec §6, owned by the desktop work). Built on the concept's `CommandBar` promoted into `packages/ui` ([06 Phase A](../06-frontend-implementation.md)); implementation default is shadcn `Command` (cmdk).

| Section | Source | Notes |
|---|---|---|
| Actions | static client registry: New task, go-to-tab ×6, Settings, theme cycle, Copy trace link (context-dependent) | always available, offline-safe |
| Tasks | `threads.search` across configured agent sources (UI spec §3.1), via `apps/server` proxy (P-005) | debounced ~200 ms; per-source results merged; a failing source degrades silently to a footer notice (§5) |
| Agents | agent-source registry + `/v2/deployments` + `/v1/deepagents/*` ([02 §6](../02-architecture.md)) | cached client-side per session |

Ranking (proposed, client-side): exact-prefix > substring on title/name; within a section, tasks by `updated_at` desc (the sort the inbox already uses, UI spec §3.1), agents alphabetical, actions in fixed order; sections capped (8 items) with "see all in tab" overflow rows. No server-side text search assumed — whether `threads.search` supports text queries is unverified (§9). Keyboard model: type-to-filter, ↑/↓ move, Enter opens, Esc closes, focus trapped; selection restores to the invoking element on close.

### 3.5 Responsive behavior

| Breakpoint | Behavior (UI spec §2, §6) |
|---|---|
| ≥ xl (1280px) | full three-column shell |
| < xl | rail collapses into tabs/sheets within content (task detail: run panel becomes sheet tabs) |
| < lg (1024px) | sidebar goes off-canvas (Sheet pattern, matching agent-chat-ui's <1024px behavior — research 22); hamburger in navbar |
| mobile | bottom bar **Tasks / Approvals / Agents**; tab row scrolls horizontally with fade masks; SearchPill collapses to an icon (proposed) |

The shell renders the bottom bar and defines its three destinations; everything else mobile (thresholds for "installed PWA" behavior, one-tap approve, safe-area insets, offline shell) lives in [./20-pwa-and-mobile.md](./20-pwa-and-mobile.md).

### 3.6 Theme system & banner slot

- **Theme:** system/light/dark tri-state (UI spec §3.6), class strategy on `<html>` (v0 concept already does dark-via-class — [06 §2.2](../06-frontend-implementation.md)). Implementation default `next-themes` with `attribute="class"` + pre-hydration inline script to prevent flash; `suppressHydrationWarning` on `<html>`. Tokens carry both palettes (`tokens.css`); status colors never become the accent (UI spec §1.1).
- **Banner slot semantics:** one slot, one banner at a time, priority-ordered: (1) **degraded** — a configured agent source is unreachable (amber treatment, §5); (2) **product notice** — release/announcement (brand blue `#006DDD`, the docs-site default). Dismissal persists per banner-id in `localStorage`; degraded banners re-arm when the condition recurs. Height feeds `--banner-height` so header offsets track presence (research 11).
- **Org/workspace switcher:** navbar, left cluster next to the logo (UI spec §2 anatomy). F07 owns placement, trigger styling (h-8 rounded-xl product-dropdown recipe — research 11) and the "switching clears client caches" rule (§6); the picker's contents and auth flow are [./05-auth-and-identity.md](./05-auth-and-identity.md).

### 3.7 Keyboard map & accessibility

| Scope | Keys | Action |
|---|---|---|
| Global | ⌘K / Ctrl+K | command palette (UI spec §2) |
| Global | Esc | close palette/sheet/modal (topmost) |
| Inbox lists (Tasks, Approvals) | j / k | move selection down/up (UI spec §7) |
| Inbox lists | Enter | open selected |
| Approvals card | approve/edit/reject/respond hotkeys | bindings proposed by the approvals spec; F07 reserves single-letter keys outside inputs (§9) |

Rules: single-letter hotkeys are suppressed while focus is in an input/textarea/contenteditable; palette and sheets trap focus; a skip-to-content link precedes the navbar. A11y bars carried from UI spec §7: WCAG AA contrast in both themes (dark border emphasis `#4f5d73` kept), visible focus states, `prefers-reduced-motion` disables pulses/masks-transitions, `aria-current="page"` on the active tab, landmarks `banner`/`navigation`/`main`/`complementary` for banner+navbar/tabs+sidebar/content/rail.

### 3.8 Shell state framework

- **Loading:** per-segment `loading.tsx` renders skeletons, never spinners, in list views (UI spec §7); chrome (navbar/tabs) renders immediately from the layout.
- **Empty:** every screen ships a real `EmptyState` (component in UI spec §4) that teaches the next action (UI spec §7). Owned per screen; F07 supplies the component and the rule. Canonical examples: Tasks → "New task" CTA; Agents → connect a source; Settings-sources empty → onboarding wizard.
- **Error:** per-tab `error.tsx` boundaries — a crash in one tab never takes down chrome or other tabs; boundary UI offers retry + "copy details".
- **Degraded:** one agent source unreachable → amber banner ("n of m sources unreachable · Retry") + inline per-source notice inside affected lists; other sources keep rendering (aggregation is per-source, UI spec §3.1). *All* sources unreachable → full-tab error state with retry + link to Settings→Agent sources. Anything not readable via API links out to smith.langchain.com rather than erroring ([02 §6](../02-architecture.md) degradation rule).

## 4. Contracts

### 4.1 Route map (Next.js App Router, D-022)

| Route | Screen | Rendering |
|---|---|---|
| `/` | redirect → `/tasks` | — |
| `/tasks` | task inbox (home) | server shell + client list |
| `/tasks/new` | new-task composer (route-addressable modal) | client |
| `/tasks/[source]/[threadId]` | task detail | client (useStream) |
| `/tasks/[source]/[threadId]/diff` | diff-review takeover (proposed as sub-route for deep-linking; §9) | client |
| `/approvals` | approvals inbox; selection via nuqs query state, no detail route | client list |
| `/agents` | fleet index | server shell + client table |
| `/agents/new` | template gallery → create flow | client |
| `/agents/[agentId]/(overview\|configuration\|schedules\|environment\|deploy)` | agent detail tabs (UI spec §3.4) | mixed |
| `/schedules` · `/activity` · `/observability` | per tab | server shell + client lists |
| `/settings/(sources\|github\|notifications\|appearance\|danger)` | settings groups (UI spec §3.6) | mostly server |
| `/login`, `/onboarding` | auth + first-run (F05 owns internals) | server shells |
| `/config/*` | **redirect → `/settings/*`** (P-002; removed if P-002 overturned) | — |

Conventions: filter/pagination/selection state is URL-as-state via nuqs, never `useState` ([06 §2.3](../06-frontend-implementation.md)); `[source]` is a stable slug for the agent source from the registry — scheme unresolved (§9); unknown routes render a 404 inside chrome.

### 4.2 Layout variables (single source: `packages/ui/tokens.css`)

`--shell-max-width: 92rem` · `--content-max-width: 72rem` · `--navbar-height: 3.5rem` · `--tabbar-height: 2.5rem` · `--banner-height: 2.5rem` · `--sidebar-width: 18rem` · `--rail-width: 19rem` (incl. 2.5rem gutter) · `--content-gap: 3rem` · `--content-pad-left: 5.5rem` · `--chat-max-width: 900px`. Components must consume vars, not hardcode pixels.

### 4.3 Component contracts (`packages/ui`)

- `AppShell` — props: `sidebar?: ReactNode`, `rail?: ReactNode`, `banner?: BannerSpec`, `bottomBar?: boolean`; renders chrome + slots; owns collapse behavior (§3.5). Ported from the concept ([06 §2.3](../06-frontend-implementation.md)).
- `BannerSpec` — `{ id: string; severity: 'notice' | 'degraded'; content: ReactNode; dismissible: boolean }`; one visible at a time, `degraded` outranks `notice`.
- `CommandPalette` — `sources: PaletteSource[]` where `PaletteSource = { id; section: 'actions'|'tasks'|'agents'; query(q, signal): Promise<PaletteItem[]> }`; `PaletteItem = { id; title; subtitle?; href | run(); icon? }`.
- `SearchPill`, `OrgSwitcher`, `EmptyState { icon; title; body; action }`, `PageHeader { eyebrow; title; toolbar? }` — per UI spec §4 inventory.
- Shell-level data calls (palette task search, source health) go through `apps/server` (P-005); components take fetchers as props so fixtures mode ([06 §4.4](../06-frontend-implementation.md)) works with zero credentials.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| One agent source down | Amber degraded banner + per-source inline notice; palette task section shows footer "1 source unavailable"; other sources unaffected (§3.8) |
| All sources down | Tab-level error state, retry + Settings link; chrome and Actions palette section still work |
| Zero sources configured | Every data tab renders its EmptyState pointing to onboarding/Settings→sources; no error styling |
| Deep link to `/config/*` | 301-style redirect to `/settings/*` while P-002 holds |
| Deep link to thread not found / wrong org | 404-in-chrome with "check org/workspace" hint (switcher may hold the wrong org) |
| Org/workspace switch mid-view | client caches cleared, current route re-resolved; if the entity doesn't exist in the new org → 404-in-chrome |
| Banner + mobile safe areas | banner stacks above navbar; safe-area handling deferred to F20 |
| Theme flash on first paint | pre-hydration script sets class before CSS applies; `system` tracks OS changes live |
| Palette with thousands of threads | per-source result caps + debounce; no full-corpus client index in v1 |
| Reduced motion | status pulse, fade-mask transitions, sheet animations disabled (UI spec §7); decorative beam-field already flagged for audit ([06 Phase F](../06-frontend-implementation.md)) |
| Tab crash | segment `error.tsx` catches; other tabs and chrome unaffected |

## 6. Security & privacy

- **Route guarding:** all routes except `/login`, `/onboarding` require a session; enforcement mechanics (middleware vs server-side check) are F05's contract — F07 only guarantees no org data renders in chrome before auth resolves.
- **No secrets in URLs:** route params carry thread/agent/source *identifiers* only; API keys/tokens never appear in URL state, `localStorage` shell keys (`theme`, `banner:<id>:dismissed`, sidebar collapse) hold no org data. Key storage rules are F05's ([02 §5](../02-architecture.md)).
- **Cross-org bleed:** palette caches, list caches, and badge counts are keyed by org/workspace and dropped on switch — the palette must never surface another org's threads after switching.
- **Proxy discipline (P-005):** browser talks to `apps/server`; data-plane credentials stay server-side per the passthrough pattern (UI spec §3.6). Client-side key mode is local-dev only.
- **Untrusted content:** shell chrome renders no agent-generated content except task *titles* in palette/lists — rendered as plain text, never HTML/markdown (untrusted-boundary principle, [02 §10](../02-architecture.md)).
- **Desktop deep links** (`deepwork://task/...`) resolve through the same route map + guards; no bypass.

## 7. Acceptance criteria

1. Shell renders with confirmed measurements (banner 40px, navbar 56px, tab row 40px, sidebar 288px, rail 19rem, content 72rem, shell 92rem) sourced from `tokens.css` vars — verified by visual regression against the [design brief](../../design/deepwork-design-brief.html).
2. Six tabs exactly (P-002); `/config/*` redirects to `/settings/*`; every route in §4.1 resolves inside chrome; unknown routes 404 inside chrome.
3. `apps/web` builds with server components for layouts/static chrome; `"use client"` only on the islands in §3.3 (checked in review; no blanket client root).
4. ⌘K opens the palette from any screen; searching returns actions + tasks + agents per §3.4; Esc restores focus to the trigger; palette works in fixtures mode with no credentials.
5. At `<xl` the rail collapses to tabs/sheets; at `<lg` the sidebar is off-canvas; mobile shows the Tasks/Approvals/Agents bottom bar and a scrolling tab row with fade masks.
6. Theme tri-state persists, no flash-of-wrong-theme on hard reload, both palettes pass WCAG AA spot checks (UI spec §7).
7. Killing one agent source in a two-source setup yields the amber banner + intact rendering of the healthy source; killing both yields tab-level error with retry.
8. j/k + Enter drive the task inbox with visible focus; single-letter keys are inert while typing in any input; skip-link and landmarks present (axe clean on shell chrome).
9. Every tab shows a teaching EmptyState with zero data; list loading shows skeletons, not spinners.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Import v0 concept as `apps/web`; hygiene pass (rename, strict TS, drop `ignoreBuildErrors`, regenerate lockfile) | — | CI green per [06 Phase A](../06-frontend-implementation.md) |
| 2 | Wire `packages/ui` tokens + Tailwind preset as sole style source; delete inline `@theme` block | 1 | all shell dimensions come from §4.2 vars |
| 3 | Promote `AppShell`/`PageHeader`/`SearchPill`/`CommandBar`/`EmptyState` into `packages/ui` with stories | 2 | fixtures-driven stories render |
| 4 | Route scaffolding per §4.1 incl. `/config→/settings` redirects, 404-in-chrome, `/` redirect | 1 | route tests pass |
| 5 | Server/client split refactor: server layouts, client islands per §3.3 | 4 | no blanket `"use client"`; build output verified |
| 6 | Per-tab sidebar layouts + nuqs filter slots; scroll-fade masks | 3, 4 | tabs render contextual sidebars against fixtures |
| 7 | Rail slot + `<xl` sheet collapse; `<lg` off-canvas sidebar; mobile bottom bar + scrolling tab row | 6 | AC 5 |
| 8 | Theme system (class strategy, tri-state, pre-hydration script) | 2 | AC 6 |
| 9 | Banner slot (severity, dismissal persistence, `--banner-height` coupling) | 3 | AC 7 banner behavior |
| 10 | Command palette v1: actions registry + tasks/agents sources via `apps/server` fetchers, fixtures impl | 3, 5 | AC 4 |
| 11 | Keyboard framework: global hotkey manager, j/k list navigation, input-focus suppression | 5 | AC 8 |
| 12 | State framework: `loading.tsx` skeletons, per-tab `error.tsx`, degraded-source banner wiring, EmptyStates | 6, 9 | AC 7, 9 |
| 13 | A11y pass on chrome (landmarks, skip-link, focus, reduced motion) + visual regression baseline | 7–12 | AC 1, 8; axe clean |

Tasks 1–7 are M0 ("shell chrome against static data", [04 M0](../04-roadmap.md)); 8–9 straddle M0/M1; 10–13 land by M4 polish but the contracts above are frozen now.

## 9. Open questions

1. **Observability tab survival** — slim tab vs fold into Activity is explicitly deferred to M3 entry ([06 Phase E](../06-frontend-implementation.md)); if folded, the shell drops to 5 tabs and P-002 needs amending.
2. **`[source]` slug scheme** for task URLs — user-defined name vs derived deployment id; must be stable across renames or task links break. Owner: SDK agent-source registry design.
3. **`threads.search` text-query support** — unverified; determines whether palette task search is server-filtered or client-side over recent threads only.
4. **Approval hotkey bindings** — final letters and conflict policy belong to the approvals spec; F07 needs the reserved-key list before task 11.
5. **Diff takeover as route vs overlay** — §4.1 proposes a sub-route for deep-linking from PR/notification contexts; task-detail spec should confirm.
6. **Plugins screen placement** under P-002 — [02 §9](../02-architecture.md) names a plugins screen (M3 in [04](../04-roadmap.md)); Settings vs Agent detail is undecided.
7. **Tab badge counts** (e.g. Approvals pending count) — desired but polling/streaming source and cost unresolved; desktop tray already wants a needs-review count (UI spec §6), so one shared counter feed is preferable.
8. **`/tasks/new` modal-vs-page** — route-addressable modal (parallel/intercepting route) or plain page; UI spec §3.1 says "modal from CTA", deep-linkability suggests intercepting route.
9. **Decision-register cross-check** — D-022/P-002/P-005 cited from the briefing; verify IDs and any adjacent O- items when [../decisions.md](../decisions.md) lands in-repo (absent at time of writing).

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| P-002 overturned → 7-tab revert | Med | Low-Med | Reverts pre-enumerated (§3.2); tab row already overflow-safe; redirects isolated in one file |
| P-005 churn (FastAPI glue vs doc 02's Next.js routes) | Med | Med | Shell components take fetchers as props (§4.3) — transport swap touches only the fetcher layer |
| v0 concept refactor cost (all-client → split) exceeds estimate | Med | Med | Split is per-segment (task 5) and can land tab-by-tab; blanket-client is functional in the interim ([06 §2.5](../06-frontend-implementation.md)) |
| Palette scope creep toward full search product | Med | Low | v1 sections/caps pinned in §3.4; anything more is a new spec |
| Theme flash / hydration mismatch regressions | Low | Low | Pre-hydration script + visual regression in task 13 |
| Keyboard conflicts (browser/OS/screen readers) | Low | Med | Reserved-key list (§9.4), input-focus suppression, no chords in v1 |
| Measurement drift from docs-site updates | Low | Low | Values frozen in `tokens.css`, not re-scraped; changes are deliberate token PRs |
