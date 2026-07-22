# F03 · Design system & `packages/ui`

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M0 · Depth: implementation-ready*

Sources: [UI spec](../03-ui-spec.md) · [frontend plan](../06-frontend-implementation.md) · [docs design language](../../research/11-docs-design-language.md) · [UI tokens gap-fill](../../research/22-gapfill-ui-tokens.md) · [UI contract gap-fill](../../research/21-gapfill-ui-contract.md) · [OSS setup](../05-oss-setup.md) · [roadmap](../04-roadmap.md) · seed files [tokens.css](../../../packages/ui/tokens.css), [tailwind.preset.mjs](../../../packages/ui/tailwind.preset.mjs), [README](../../../packages/ui/README.md) · [design brief](../../design/deepwork-design-brief.html) · [decisions](../decisions.md)

## 1. Scope

**In:** the `@deepwork/ui` workspace package — design tokens (CSS custom properties + Tailwind preset), shadcn/ui (new-york) re-themed onto those tokens, the Tabler icon layer, typography/radii/color system incl. signature details, catppuccin code theming, the full presentational component inventory from [UI spec §4](../03-ui-spec.md#4-component-inventory-packagesui), the fixtures dataset (P-004), Storybook + visual-regression + a11y bars, and package build/export mechanics.

**Out (neighbors, see [catalog](README.md)):** monorepo/CI scaffold that this package builds on (F01); `apps/web` screens, routing, and server routes (the app consumes this package); `packages/sdk` data layer — stream normalization, `DataProvider`, HITL casing (per [05 §repo structure](../05-oss-setup.md#repo-structure), casing lives in sdk, "nowhere else"); agent (`packages/agent`); desktop/mobile shells. Components here are **presentational**: no `@langchain/*` dependencies, no fetching — live wiring is Phase B of the [frontend plan](../06-frontend-implementation.md#phase-b--data-layer-under-the-paint-m1).

## 2. Dependencies & seams

| Dependency | ID | Nature |
|---|---|---|
| Next.js frontend | D-022 | Primary consumer (`apps/web`). Package must be importable by a Next.js App Router app (client components marked `"use client"`). |
| v0 concept import as `apps/web` | P-001 / D-012 (provisional) | Extraction source for Phase A components ([06 §3-A](../06-frontend-implementation.md#phase-a--adopt--consolidate-m0)). **Not imported yet** — tasks 9–10 below block on it; everything else proceeds without it. |
| Fixtures package | P-004 (provisional) | v0's `lib/data.ts` (1,110 lines) becomes `packages/ui/fixtures`; also blocked on the import. |
| Brand/font swappability | D-009 | Token layer must keep font + brand hue swappable in one place (no commercial fonts committed; regenerate gray ramp on hue change — [tokens.css](../../../packages/ui/tokens.css) comment, [research 11](../../research/11-docs-design-language.md)). |
| FastAPI glue (`apps/server`) | P-005 (provisional) | No seam: `packages/ui` is server-agnostic and is not consumed by Python glue. Noted only because older doc text ([02 §1](../02-architecture.md#1-system-overview), [05](../05-oss-setup.md)) places glue routes in Next.js — superseded. |
| Monorepo toolchain | F01 | pnpm + Turborepo + changesets + biome + CI ([05 §toolchain](../05-oss-setup.md#toolchain)). F03 task 1 assumes the workspace exists. |
| Upstream UI deps | — | shadcn/ui new-york style (per [UI spec §4](../03-ui-spec.md#4-component-inventory-packagesui); agent-chat-ui precedent, [research 22](../../research/22-gapfill-ui-tokens.md)); Tabler outline icons (docs site pins v3.44.0 — [research 11](../../research/11-docs-design-language.md)); sonner/nuqs/use-stick-to-bottom conventions (spec §4). Exact npm pins land at scaffold (§9). |

**Type seam (design decision):** `packages/ui` defines its own prop interfaces that *mirror* the normalized v1 contract shapes (`AssembledToolCall`, `SubagentDiscoverySnapshot`, todo items, HITL decisions, `FileData` — [research 21](../../research/21-gapfill-ui-contract.md)); `packages/sdk` maps live projections onto them. Components never see wire casing ([UI spec §5](../03-ui-spec.md#5-data-layer-contract-pins)); the documented `reviewConfigs` casing exception is absorbed in sdk and never reaches ui props.

## 3. Design

### 3.1 Token seed — what exists vs what [UI spec §1](../03-ui-spec.md#1-design-language) requires

| Spec §1 requirement | In seed? | Gap → task |
|---|---|---|
| RGB-triplet vars composed with alpha (`rgb(var(--primary) / 0.10)`) | ✅ tokens.css | Preset hardcodes hex for `gray`/`surface`/`background` — converge on var-driven so themes flip (T2) |
| Brand core (`--primary` #161F34 / `-light` #7FC8FF / `-dark` #006DDD), bg pair #FFFFFF/#030710, never-pure-black ink | ✅ | — |
| Dark theme *applied* (bg #030710, `white/10` borders, accent → primary-light, surfaces #0D1322/#161F34) | ⚠️ values present as standalone tokens; no `.dark` remap block | Semantic alias layer + `.dark` overrides (T2) |
| Gray ramp, 11 steps, machine-derived | ✅ both files | Regeneration procedure is a comment only → document/script under D-009 (T2) |
| Semantic status set: success #6E8900, warning #f59e0b, error #ef4444, running = primary-dark/light, queued gray | ⚠️ green/warning/error only | Named `--status-*` tokens for running/queued/needs-review/done/failed; chip-green variant #10b981 undecided (§9) (T2) |
| Typography scale: h1 30→36/600 tight, h2 24/700, h3 20/600, body 16/lh 1.65, **UI 14px**, micro-label 12/600/caps/+5% tracking, mono 14/24 | ❌ fonts only | fontSize/lineHeight/letterSpacing tokens + preset entries (T6) |
| Faux-bold active state `text-shadow: -0.2px 0 0 currentColor, 0.2px 0 0 currentColor` | ⚠️ documented as comment | Real utility class/plugin (T6) |
| Radii scale 8/12/13.6/14/16/pill | ✅ tokens.css | Preset misses `selector`; add (T2) |
| Tabler outline 16px/1.5px | ❌ | Icon wrapper + dependency pin (T5, §9) |
| Catppuccin code: latte #eff1f5 / mocha #1e1e2e, 16px frame + 2px gutter + 14px inner | ⚠️ bg colors only | Full syntax themes + frame recipe; diffs via `@pierre/diffs` or Shiki per spec §1.3 (T7) |
| Layout vars (shell 92rem, content 72rem, header 96px, sidebar 18rem, rail 19rem, chat 900px…) | ✅ tokens.css | Preset misses banner/content-gap/pad-left/chat-max-width (T2) |
| shadcn semantic variables (`--card`, `--muted`, `--ring`, `--destructive`…) | ❌ | Bridge layer mapping shadcn vars onto brand tokens (T4) |
| Motion: running-pulse, scroll-fade masks, focus rings, prose-link style (600 + 1px primary border-bottom) | ❌ (links/pills as comments) | Keyframes + utilities, `prefers-reduced-motion` guards (T6) |

### 3.2 Theming & dark mode

- **Strategy: `class` dark mode** (already in the preset; matches the v0 concept — [06 §2](../06-frontend-implementation.md#2-evaluation)). Raw brand tokens stay theme-invariant; a semantic alias layer (`--accent`, `--surface-1/2`, `--ink`, `--border-*`) remaps per theme in `:root` / `.dark`. Active/accent means *actionable*; status colors are never the accent (spec §1.1).
- **Token-swap story (D-009):** rebrand = swap `--font-heading` + the three primary triplets + regenerate the gray ramp (derived, not independent). No LangChain wordmarks; no TWK Lausanne/Aeonik Mono files ever committed ([05 §naming](../05-oss-setup.md#naming--trademark-hygiene)). Fonts load in the consuming app (e.g. `next/font`); the package only references family names with system fallbacks.

### 3.3 shadcn/ui re-theme (new-york)

Generate shadcn primitives inside `packages/ui` with the semantic-var bridge so every primitive picks up the aspen look: 12px interactive radius, gray ramp, `bg-primary/10 text-primary` active states (dark: primary-light), `#4f5d73` dark border emphasis. Lucide is acceptable *inside shadcn internals* only; product iconography is Tabler (spec §1.3). Note the v0 concept runs shadcn 4.x on `@base-ui/react` while the reference first-party UIs use classic radix-based shadcn — base library must be standardized before Phase A extraction (§9, R3).

### 3.4 Component inventory

All components ship with stories against fixtures, and loading/empty/error states where listed. "Consumed by" links are the screen specs; conventions shared by all (spec §4): sonner toasts, nuqs URL state handled by the app (components accept values/callbacks), use-stick-to-bottom, uppercase micro-labels, chevron-collapsible cards, amber=in-progress, green=success, red=error.

| Component | Purpose | Key props (sketch) | States | Consumed by |
|---|---|---|---|---|
| `StatusChip` | Pill + 6px dot for 5 task states + thread statuses | `{status: running\|needs_review\|done\|failed\|queued, label?, pulse?}` | per-status; pulse on running (off under reduced motion) | [Inbox §3.1](../03-ui-spec.md#31-task-inbox-home) |
| `TaskRow` / `TaskList` | Fixed-height ~72px 12-col rows; grouped, virtualized list | row `{title, preview, contextChips, status, unread, interruptCount, updatedAt, href}`; list `{groups, onSelect}` | skeleton loading; teaching empty state; hover `bg-gray-50/90` | [Inbox §3.1](../03-ui-spec.md#31-task-inbox-home) |
| `MessageStream` | Content-block renderer: streaming markdown + reasoning fold | `{blocks, streaming?, onRetry?}` | streaming cursor; empty; render-error per block | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `ToolCallCard` | Chevron-collapsible tool call | mirrors `AssembledToolCall`: `{name, callId, input, output, status: running\|finished\|error, error}` | collapsed default (name + arg summary + glyph); streaming output into open card; error | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `SubagentCard` / `SubagentGroup` | Bordered card, ▶ caret, glyphs ○ ◉ ✓ ✕, 12rem max-h body; group n/m progress bar | mirrors `SubagentDiscoverySnapshot`: `{id, name, namespace, status, taskInput, output}` + `onExpand` (lazy body mount) | pending/running(pulse)/complete/error; lazy-loading body | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `TodoTray` | Composer-attached "Task N of M" tray + rail mirror | `{todos: {content, status: pending\|in_progress\|completed}[], expanded?}` | collapsed summary; expanded; empty (hidden) | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `InterruptCard` / `DecisionForm` | v1 HITL card: per-arg edit (Edit⇄Accept auto-switch), reject/respond, batch rows + progress dots | `{actionRequests, reviewConfigs (normalized), onDecisions(decisions[])}` | capability chips from `allowedDecisions`; batch progress; **malformed → raw-JSON fallback card, never crash** | [Approvals §3.3](../03-ui-spec.md#33-approvals-inbox) |
| `FileTree` / `FileViewer` / `DiffViewer` | Changed-files tree; viewer incl. multimodal blocks (image/PDF/audio/video); unified diff w/ batched line comments | tree `{nodes, modified}`; viewer `{path, content (normalized FileData), mimeType}`; diff `{diff, comments, onComment, onApprove}` | loading; binary/unsupported; oversized-file truncation; diff empty | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `PlanCard` | Plan-approval interrupt: per-step markdown + Approve/Edit | `{steps, onApprove, onEdit}` | pending/editing/submitted | [Task detail §3.2](../03-ui-spec.md#32-task-detail) |
| `AgentCard` / `AgentTable` | Fleet index: tier badge (MDA/Deployment/Fleet/local), health | `{name, tier, model, toolsCount, channels, schedules, lastRun, health, ownerGated?}` | loading skeleton; empty gallery CTA; degraded health | [Agents §3.4](../03-ui-spec.md#34-agents-fleet-manager) |
| `CronEditor` | 5-field cron + timezone + prompt\|input payload | `{value, timezone, payloadMode, deliverTo?, onChange}` | invalid-expression error; next-run preview | [Schedules §3.5](../03-ui-spec.md#35-schedules--activity) |
| `TracePill` | Canonical "View trace ↗" | `{traceUrl}` | disabled when URL absent (should be never — [02 §10](../02-architecture.md#10-observability--provenance)) | all screens |
| `AppShell` / `PageHeader` | Navbar + tab row + sidebar/rail slots; breadcrumb eyebrow → h1 → toolbar | `{banner?, sidebar, rail?, children}` | responsive collapse (<lg off-canvas, <xl rail sheets) | [Shell §2](../03-ui-spec.md#2-app-shell-docs-site-anatomy-re-labeled) |
| `CommandPalette`, `SearchPill`, `OrgSwitcher`, `EnvChip`, `Banner`, `EmptyState` | Shell chrome: ⌘K palette + trigger pill; org/workspace ▾; sandbox id+TTL chip; dismissible 40px banner; teaching empty states | per spec §2/§4 | palette empty-results; banner dismissed (`--banner-height` collapses); EnvChip expired-TTL | [Shell §2](../03-ui-spec.md#2-app-shell-docs-site-anatomy-re-labeled), [§3.6](../03-ui-spec.md#36-onboarding--settings) |

### 3.5 Extraction plan from the v0 concept (blocked on P-001/D-012)

Per [06 Phase A](../06-frontend-implementation.md#phase-a--adopt--consolidate-m0): once the concept is imported as `apps/web`, move `StatusChip`, `ToolCard` (→ `ToolCallCard`), `PageHeader`, `AppShell` primitives, and `CommandBar` (→ `CommandPalette`) into `packages/ui` *with stories*; replace the app's inline `@theme`/`:root` block with `tokens.css` + preset (single token source). Extraction is a port, not a merge: renamed props to the §3.4 sketches, re-typed off the invented `ThreadEvent` union, `@base-ui/react` vs radix resolved first (§9). The v0 repo stays a design sandbox; monorepo is canonical (06 §4).

### 3.6 Fixtures (`packages/ui/fixtures`, P-004)

v0's `lib/data.ts` (1,110 lines, centralized mock domain) is kept permanently as the fixture set for Storybook, vitest, and demo mode — the app stays runnable with zero credentials (06 §4). Work: re-type fixtures against the §2 prop interfaces (the v0 shapes are off-contract: legacy approvals model, invented event union — [06 §2 gaps](../06-frontend-implementation.md#2-evaluation)), add fixture cases the concept lacks (batched interrupts, malformed interrupt, subagent trees, multimodal file blocks, all five chip states). Exported as `@deepwork/ui/fixtures`; `packages/sdk`'s fixtures `DataProvider` (Phase B) consumes the same data.

### 3.7 Storybook, visual regression, a11y

- **Recommendation: Storybook** — it is the direction already named in [06 §2/§3-A](../06-frontend-implementation.md) ("stories", "Storybook/tests/demo mode"); alternatives (e.g. lighter story runners) rejected to keep addon a11y/interaction testing and the largest ecosystem. Version unpinned in docs (§9). Static build published from CI as the living component catalog.
- **Visual regression (option):** story snapshots in CI via Storybook's test runner, both themes per story. A hosted diff service is a later opt-in — nothing pinned in docs (§9). Baseline gate: T16.
- **A11y bars ([spec §7](../03-ui-spec.md#7-accessibility--quality-bars)):** WCAG AA contrast in *both* themes (dark borders already bumped to #4f5d73 for 1.4.11 — keep); visible focus states; keyboard operability per component; `prefers-reduced-motion` disables pulse/motion; axe checks wired into stories; virtualization + lazy subagent mounts are component-level responsibilities.

### 3.8 Build & publish mechanics (what F01 needs)

- **Recommendation (docs pin no bundler):** v1 ships `@deepwork/ui` as an **internal source package** — TS + CSS exported as-is, consumed via pnpm workspace + Next.js transpilation; no build step, Turborepo caches typecheck/test/storybook tasks. Rationale: single consumer (D-022), fastest iteration, zero dual-format surface. Introduce a bundler (tsup is the conventional choice; **not pinned in any doc**) only if/when the package publishes to npm externally — decision deferred (§9).
- **Exports map:** `.` (components barrel), `./tokens.css`, `./styles.css` (utilities: faux-bold, prose links, scroll-fade, motion), `./tailwind-preset`, `./fixtures`. `sideEffects: ["*.css"]`. React 19 peer (v0 concept + agent-chat-ui are React 19 — [06 §1](../06-frontend-implementation.md#1-what-the-concept-is), [research 22](../../research/22-gapfill-ui-tokens.md)).
- **Versioning:** changesets per [05 §toolchain](../05-oss-setup.md#toolchain); package stays `private: true` until an external-publish decision.

## 4. Contracts

- **CSS contract:** colors are RGB triplets composed with alpha at point of use (`rgb(var(--primary) / 0.10)`) — the docs-site convention; consumers must not hardcode brand hexes. Dark mode = `.dark` class on the root element. Semantic aliases are the only vars components reference; raw brand tokens are reserved to the alias layer.
- **Tailwind contract:** apps consume the preset (or its v4 `@theme` equivalent — §9) and `tokens.css`; utility names (`rounded-interactive`, `bg-surface-raised`, `text-primary-light`, spacing `navbar/tabbar/sidebar/rail`) are the stable API, current names per [tailwind.preset.mjs](../../../packages/ui/tailwind.preset.mjs).
- **Prop-type contract:** camelCase, normalized, defined in `packages/ui` and mirrored (not imported) from the v1 SDK shapes documented in [research 21](../../research/21-gapfill-ui-contract.md); `packages/sdk` owns all wire normalization incl. the `reviewConfigs` casing exception. Breaking prop changes require a changeset major.
- **Component contract:** presentational + controlled; no data fetching, no router coupling, no `@langchain/*` imports; interactive components are client components (`"use client"`); every stateful component exposes loading/empty/error variants renderable from fixtures alone.
- **Fixture contract:** `@deepwork/ui/fixtures` typechecks against the prop interfaces; any prop change must update fixtures in the same PR (CI-enforced via typecheck).

## 5. Edge cases & failure modes

- **Malformed HITL interrupt** → `InterruptCard` degrades to raw-JSON card with copyable thread id; never crashes the inbox (spec §3.3).
- **`FileData` divergence** (py `{content, encoding}` vs js v1 lines / v2 `{content, mimeType}` — research 21): normalization happens in sdk; `FileViewer` receives one shape but must still handle base64/binary, unknown mime, and oversized content (truncate + "open raw").
- **Streaming pathologies:** `tool-output-delta` into a card the user collapsed (buffer, don't reopen); interleaved subagent output (namespace-scoped bodies); markdown blocks that never `finish` (render partial, no spinner lock).
- **Reduced motion:** running pulse, banner slide, scroll-fade animation all gated on `prefers-reduced-motion` (spec §7); status remains distinguishable without motion (dot + label, not color/pulse alone).
- **Theme edge cases:** components rendered before `.dark` is stamped (no flash of wrong theme — semantic aliases defined in both blocks); WCAG 1.4.11 on dark borders (#4f5d73 emphasis tier, tokens.css).
- **Font fallback:** Inter/IBM Plex Mono unavailable (offline, licensing swap per D-009) → system stacks already in tokens; layout must tolerate metric shift (no px-tuned truncation).
- **Brand hue swap (D-009):** gray ramp is *derived* — swapping `--primary` without regenerating grays is a documented failure mode (tokens.css comment); provide the regeneration procedure with the tokens.
- **Long lists:** `TaskList` and thread views virtualize; `SubagentCard` bodies lazy-mount (ref-counted subscriptions exist for this — spec §7). Fixed-height rows keep virtualization honest.
- **Tailwind major mismatch:** v0 concept is Tailwind v4 (`@theme`), the seed preset is classic `theme.extend` — shipping both unreconciled silently forks the token source (task T3; §9).

## 6. Security & privacy

- **No commercial assets:** TWK Lausanne / Aeonik Mono never committed; no LangChain wordmark/logo in the package or Storybook chrome ([05 §naming](../05-oss-setup.md#naming--trademark-hygiene)). Storybook, if publicly hosted, carries the non-affiliation disclaimer.
- **Untrusted content rendering:** `MessageStream`, `ToolCallCard` output, and schedule/webhook-fired payloads render agent/external-controlled text — markdown rendering must not execute HTML/scripts, and untrusted-payload boundaries per [02 §10](../02-architecture.md#10-observability--provenance) apply where these components display webhook/schedule content.
- **Fixtures hygiene:** fixture data is fabricated only — no real org names, keys, repo URLs, or trace ids; demo mode must not imply real credentials.
- **Supply chain:** dependency adds respect the pnpm `minimumReleaseAge` posture that already caught a <24h `react-is` pin during the v0 evaluation ([06 §2 hygiene](../06-frontend-implementation.md#2-evaluation)); renovate weekly per [05](../05-oss-setup.md#toolchain). No telemetry of any kind in the package.

## 7. Acceptance criteria

1. `apps/web` (once scaffolded) imports tokens, preset, and components exclusively from `@deepwork/ui`; no inline token blocks remain (06 Phase A).
2. Every §3.1 gap row is closed: `.dark` remap, semantic status tokens, typography scale, faux-bold utility, preset/var convergence, layout vars complete.
3. shadcn (new-york) primitives render docs-aspen styling in both themes with no per-component color overrides.
4. All §3.4 components exist with stories covering default + loading/empty/error + both themes, driven only by `@deepwork/ui/fixtures`.
5. Malformed-interrupt story renders the raw-JSON fallback; batched-interrupt story shows per-call decision rows + progress dots.
6. Icons: product surfaces use Tabler outline at 16px/1.5px stroke; a lint/review convention prevents lucide leakage outside shadcn internals.
7. Code blocks render catppuccin latte/mocha inside the 16px frame + 2px gutter + 14px inner-radius recipe; unified diff view renders with line-comment affordances.
8. a11y: axe passes on all stories; AA contrast verified in both themes; pulse/motion disabled under `prefers-reduced-motion`; interactive components keyboard-operable.
9. CI (F01) runs typecheck, tests, Storybook build, and story snapshots for `packages/ui`; fixtures typecheck against prop interfaces.
10. Storybook static build publishes from CI as the component catalog.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| T1 | Package scaffold: `package.json` (`@deepwork/ui`, private), exports map (§3.8), tsconfig, `"use client"` conventions | F01 scaffold | Package resolves from a workspace consumer; CI typechecks it |
| T2 | Token gap-fill: semantic alias layer + `.dark` remap; `--status-*` set; preset↔var convergence (grays/surfaces/background); missing preset radii + layout vars; gray-ramp regeneration doc (D-009) | T1 | §3.1 rows 1–5, 8, 11 closed; both themes render a token sheet story |
| T3 | Tailwind integration decision (v4 `@theme` vs JS preset — §9 O2) implemented as the single token source | T2 | One mechanism documented; sample consumer builds; the other path deleted or generated |
| T4 | shadcn/ui (new-york) init in-package + semantic-var bridge; base primitives generated & re-themed | T3 | AC 3; primitives story in both themes |
| T5 | Icon layer: Tabler outline wrapper (16px/1.5px default), dependency pinned (§9 O3), lucide-leakage convention | T1 | AC 6 |
| T6 | Typography & signature utilities: type scale, micro-labels, faux-bold active utility, prose links, scroll-fade masks, focus rings, motion + reduced-motion guards | T2 | §3.1 typography/motion rows closed; utilities story |
| T7 | Code/diff theming: catppuccin latte/mocha syntax themes + frame recipe; diff rendering choice (`@pierre/diffs` vs Shiki, spec §1.3) exercised in a story | T3 | AC 7 |
| T8 | Storybook setup (recommended tool, §3.7) + CI static build + axe checks | T1 | AC 10; a11y checks run in CI |
| T9 | Fixtures port: v0 `lib/data.ts` → `@deepwork/ui/fixtures`, re-typed to §2 prop interfaces, missing cases added (§3.6) | P-001/D-012 import; T1 | Fixtures typecheck; every §3.4 component has fixture coverage |
| T10 | Phase A extraction: `StatusChip`, `ToolCard`→`ToolCallCard`, `PageHeader`, `AppShell`, `CommandBar`→`CommandPalette` moved in with stories; app's inline theme block replaced | T4, T8, T9; base-library decision (§9 O4) | AC 1; extracted components pass stories in both themes |
| T11 | Thread components: `MessageStream`, `TodoTray`, `SubagentCard`/`Group` | T4, T9 | Stories incl. streaming/lazy/error states |
| T12 | HITL components: `InterruptCard`/`DecisionForm`, `PlanCard` | T9 | AC 5 |
| T13 | Files components: `FileTree`/`FileViewer`/`DiffViewer` incl. multimodal blocks | T7, T9 | Stories incl. binary/oversized/empty-diff |
| T14 | Fleet/schedule components: `AgentCard`/`AgentTable`, `CronEditor`, `TracePill`, `EnvChip`, `Banner`, `EmptyState`, `SearchPill`, `OrgSwitcher` | T4, T9 | Stories incl. invalid-cron, expired-TTL, dismissed banner |
| T15 | a11y pass: AA both themes, keyboard nav, reduced-motion audit | T10–T14 | AC 8 |
| T16 | Visual-regression baseline: per-story snapshots, both themes, in CI | T8, T10–T14 | AC 9 snapshot leg green; diffs block merge |
| T17 | Release wiring: changesets config, package README, contribution notes | T1 | Version bumps flow through changesets; README documents exports + theming |

M0 = T1–T10 (matches [roadmap M0](../04-roadmap.md): tokens seeded, shadcn re-theme, shell chrome); T11–T14 land with their consuming milestones (M1–M3); T15–T16 harden through M4.

## 9. Open questions

| # | Question | Blocking? |
|---|---|---|
| O1 | `docs/plan/decisions.md` and the features catalog were absent from the working tree at drafting time — the D-/P- glosses here (D-009, D-012, D-022, P-001, P-004, P-005) come from the planning brief and must be verified against the ledger once present | No (verify) |
| O2 | Tailwind major: v0 concept is v4 (`@theme`), the seed preset is a classic JS preset; agent-chat-ui is also v4. Which mechanism is canonical, and is the preset kept, generated, or replaced? Docs don't pin the monorepo's Tailwind version | T3 |
| O3 | Tabler icon delivery: docs site uses CSS `mask-image` (v3.44.0); package + version for React usage is not pinned in any doc | T5 |
| O4 | shadcn base library: v0 uses shadcn 4.x on `@base-ui/react`; reference UIs use radix-based shadcn. Standardize before extraction | T10 |
| O5 | Storybook major version, a11y/test tooling pins, and whether a hosted visual-diff service is adopted — no doc pins any | T8/T16 |
| O6 | Bundler: source-only internal package recommended (§3.8); confirm with F01, and revisit tsup/dual-format only on an external npm-publish decision (scope name also unpinned — `@deepwork/ui` is the seed README's title only) | No |
| O7 | StatusChip green: brand success #6E8900 vs "UI convention #10b981 acceptable for chips" (spec §1.1) — pick one token value for `--status-done` | T2 |
| O8 | Full catppuccin latte/mocha syntax palettes: seed carries only the two background hexes; source of the complete theme (Shiki built-ins vs vendored palette) unconfirmed | T7 |
| O9 | Font loading ownership: recommendation is app-side (`next/font`) with the package referencing family names only — confirm against D-022 app scaffold | No |
| O10 | Where does the demo-mode toggle live (app concern) vs fixtures export (this package)? P-004 covers the data; the mode itself belongs to `apps/web`/`packages/sdk` — confirm in those specs | No |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Extraction blocked: v0 import (P-001/D-012) slips, stalling T9–T10 and fixtures | Med | Med | T1–T8 are import-independent; hand-write minimal fixtures for early stories if the import slips past M0 |
| Tailwind v4/preset fork: two token sources drift (app `@theme` vs package preset) | Med | High | T3 forces a single mechanism before any component work; AC 1 audits for inline token blocks |
| shadcn base-library mismatch (`@base-ui/react` vs radix) makes extracted components carry a second primitive stack | Med | Med | Decide O4 before T10; extraction is a port, not a copy |
| Visual parity drift from docs-aspen without regression tooling | High | Low-Med | T16 snapshots both themes; design brief + token sheet story as reference |
| Fixture drift from real v1 contracts (fixtures re-typed by hand, contracts churn weekly — [04 risk register](../04-roadmap.md#risk-register)) | High | Low-Med | Prop types mirror research-21 shapes; sdk golden-transcript tests (M0 Spike 3) are the ground truth; fixture updates ride prop-change PRs |
| Trademark/font slip: a commercial font file or wordmark lands in the package or Storybook | Low | Med | §6 rules; review checklist item; repo-wide font-file denylist in CI |
| Dark-theme AA regressions as components accumulate | Med | Med | axe in stories (T8) + contrast checks in the a11y pass (T15); #4f5d73 emphasis tier kept |
