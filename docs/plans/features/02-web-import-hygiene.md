# U2 · Import `deep-work-frontend` as `apps/web` + hygiene

*Feature deep-dive · 2026-07-22 · Milestone M0 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Spec: [../../plan/06-frontend-implementation.md](../../plan/06-frontend-implementation.md) (§Phase A), [../../plan/03-ui-spec.md](../../plan/03-ui-spec.md)*

---

## Goal

Migrate the v0-built visual prototype into the monorepo as `apps/web` and pay down its hygiene debt so it is a CI-clean, strict-TypeScript foundation the data-wiring units can build on without inheriting mess. The import itself is mechanical; the value of this unit is in the **information-architecture consolidation** and the **strictness/tooling migration** that happen at the same time.

No data wiring here — `apps/web` still runs entirely on fixtures after U2. The point is that it runs *cleanly*, from `packages/ui/tokens.css`, under strict TS, with URL-encoded state, and with the tab structure the product actually ships.

---

## Decisions taken

### D1 — IA consolidates to 6 tabs (fold both Observability and Config)

Final top-level tabs: **Tasks · Approvals · Agents · Schedules · Activity · Settings**.

- **Config → Settings + Agent detail.** The prototype's `/config` (connectors, skills, plugins) is not a peer of Tasks; it's configuration. Connectors/plugins/skills move under Settings; agent-specific config lives in Agent detail (`/agents/[id]`). The `app/config/page.tsx` redirect is deleted.
- **Observability → slim + link out (see D3).** Not a top-level tab in v1. Its useful KPIs surface where they belong (Activity header / Agent detail) and the deep analysis links to LangSmith.

This matches frontend-eval decision 2. The 6 tabs map cleanly to the three product pillars (task loop, approvals, fleet) plus supporting surfaces.

### D2 — Strict TypeScript: fix-all, justified suppressions permitted

Removing `ignoreBuildErrors: true` will surface real errors (the prototype was never type-checked). Chosen posture:

- Turn on full strict mode from `tsconfig.base.json` (U1), including `noUncheckedIndexedAccess`.
- **Fix every error properly** wherever the fix is real (missing null checks, loose props, `any` leaks).
- **Allow `// @ts-expect-error` only with an inline justification** and a tracked follow-up, reserved for genuine upstream typing gaps — most likely in `@base-ui/react` (the prototype uses base-ui, not Radix, so shadcn's typings are less battle-tested here).

Rationale: zero-suppressions is a nice ideal but risks burning hours fighting third-party type holes on a prototype we're about to heavily rewire anyway. A justified, tracked suppression is honest debt; a silent `any` is hidden debt. This keeps the foundation clean without letting upstream gaps block the import.

### D3 — Observability: keep the code, ship link-out for v1

Per user direction ("langsmith link can do for now"):

- **Keep** the recharts-based observability components in the tree — they're good work and anticipate a real need.
- For v1, the primary observability affordance is a **deep link to LangSmith** for the connected workspace/deployment. Charts that can be cheaply populated from a bearer-readable stats endpoint may stay live (decided at M3 entry per master plan); the rest render behind a flag or as "View in LangSmith."
- No top-level tab (D1). A compact stats strip can live in Activity and Agent detail.

### D4 — Browser / computer-use = open-source **plugin**, not a built-in

Per user direction ("browseruse as a open source plugin for browser"). This is a **product divergence** from the roadmap's "browser card ships flagged-off (Fleet-only)":

- The browser/computer-use **card component stays** in `apps/web`.
- Browser capability is delivered as an **installable open-source plugin** (the `browser-use` OSS project family), surfaced through the existing **Plugins** screen (now under Settings per D1).
- For v1: the card renders only when the browser-use plugin is present/installed on the connected agent; default is not-installed, so most users never see it. No bespoke Fleet-only coupling.
- This makes browser use a first-class extension point rather than a hidden flag — consistent with the OSS positioning.

**Cross-unit impact:** U13 (coding-task surfaces) should treat the browser card as plugin-gated rather than hard feature-flagged. The plugins system (currently mock in `components/config/`) becomes the install surface — this raises the priority of wiring the plugin registry, tracked as a note in U15 (Fleet/config) and the master plan's Deferred list should move "browser card" from "flagged off" to "plugin-gated." Captured here; will reconcile the master plan when we reach U13.

---

## Import mechanics

1. **Copy, don't move.** `deep-work-frontend/` stays as the external v0 design sandbox. `apps/web` is a curated copy. Sync is one-way and manual thereafter (frontend-eval decision 1).
2. **Regenerate the lockfile.** Do not carry over the v0 `pnpm-lock.yaml`; install fresh at workspace root so versions resolve through the U1 catalog. (Also sidesteps the <24h `react-is` supply-chain trip noted in the eval — `minimum-release-age` from U1 guards it.)
3. **Rename the package.** `"my-project"` → `"@deepwork/web"` (or chosen scope).
4. **Single token source.** Delete the inline `@theme` / `:root` block in the prototype; import `packages/ui/tokens.css` + the tailwind preset. Any duplicated color/radius/font declarations in `apps/web` are removed — `packages/ui` is authoritative.
5. **Extract shared primitives to `packages/ui`.** Move `StatusChip`, `ToolCard`, `PageHeader`, the `AppShell` primitives, and `CommandBar` into `packages/ui/components/` with Storybook stories. App-specific composites stay in `apps/web`.
6. **Fixtures move.** `deep-work-frontend/lib/data.ts` → `packages/ui/fixtures/index.ts`. This becomes the permanent demo-mode + test-fixture source (frontend-eval decision 4). It must keep `apps/web` runnable with zero credentials — the CI fixtures-smoke job (U1) enforces this.

---

## Tab consolidation — what moves where

| Prototype surface | v1 home |
|---|---|
| `/tasks`, `/tasks/[id]`, `/tasks/new` | **Tasks** tab (unchanged) |
| `/approvals` | **Approvals** tab (rebuilt in U11) |
| `/agents`, `/agents/[id]` | **Agents** tab; agent config lives in `[id]` detail |
| `/schedules` | **Schedules** tab |
| `/activity` | **Activity** tab (+ optional slim stats strip) |
| `/settings/[[...section]]` | **Settings** tab (absorbs connectors/plugins/skills) |
| `/config` | **deleted** → content relocated to Settings + Agent detail |
| `/observability` | no tab; link-out to LangSmith (D3); components retained |
| `/login` | route stays; not a tab |

---

## URL-as-state (nuqs)

Replace `useState`-driven view state with nuqs URL params where the state is shareable/bookmarkable:

- **Inbox** (`task-inbox.tsx`): `?status=running|needs-review|done|failed`, `?agent=<id>`, `?view=by-status|recent`.
- **Task detail** (`task-detail.tsx` / `run-panel.tsx`): `?tab=stream|agents|context|trace|browser|status|files|git`, layout toggle.
- **Approvals** (`approvals-view.tsx`): `?kind=<toolName>`, `?agent=<id>` — note filters become tool-name-derived in U11, so keep this generic.

Ephemeral UI state (open menus, hover) stays in `useState`.

---

## File-by-file plan (high level)

- **Create** `apps/web/` — copied tree, minus `lib/data.ts` (moved) and `app/config/page.tsx` (deleted).
- **Create** `apps/web/package.json` — renamed, deps via catalog.
- **Create** `apps/web/tsconfig.json` — extends `tsconfig.base.json`.
- **Modify** `apps/web/next.config.mjs` — remove `ignoreBuildErrors: true` and `images.unoptimized: true`.
- **Modify** `apps/web/app/layout.tsx` — import `packages/ui/tokens.css`; drop inline theme block.
- **Modify** `apps/web/components/app-shell.tsx` — 6-tab nav (D1); remove Config + Observability tabs.
- **Create** `packages/ui/components/{status-chip,tool-card,page-header,app-shell,command-bar}.tsx` + stories.
- **Move** `packages/ui/fixtures/index.ts` — from prototype `lib/data.ts`.
- **Create** `apps/web/vitest.config.ts` + `apps/web/tests/setup.ts` — vitest + React Testing Library.
- **Modify** `apps/web/components/{task-inbox,task-detail,approvals-view}.tsx` — nuqs URL state.
- **Delete** `apps/web/app/config/page.tsx`.

---

## Test scenarios

- **Happy path:** `pnpm turbo build --filter=@deepwork/web` exits 0 with no TS errors and no `ignoreBuildErrors`.
- **Happy path:** booting `apps/web` with **no env vars** renders the full inbox on fixture data (all 6 tabs reachable).
- **Happy path:** each extracted `packages/ui` primitive renders in Storybook and is imported by `apps/web`.
- **Edge case:** navigating to `/tasks?status=running` renders the inbox pre-filtered (nuqs hydration from URL).
- **Edge case:** deep-linking a task-detail tab (`/tasks/t-1?tab=files`) opens that tab directly.
- **Edge case:** removing `ignoreBuildErrors` surfaces prior type errors — each is fixed, or carries a justified `@ts-expect-error` + tracked follow-up (D2); count of suppressions is recorded in the PR.
- **Integration:** `packages/ui/fixtures` imports cleanly from both `apps/web` and a `packages/ui` test.
- **IA:** Config and Observability are absent from top-level nav; their content is reachable under Settings / Agent detail / LangSmith link.

---

## Verification

- `pnpm turbo typecheck --filter=@deepwork/web` exits 0.
- All (now 10, minus deleted `/config`) pages load in a Vercel preview with fixture data, zero console errors.
- Nav shows exactly 6 tabs.
- `grep` for inline `#006DDD` / theme literals in `apps/web` returns nothing (tokens are the only source).
- Suppression audit: every `@ts-expect-error` in `apps/web` has a justification comment.

---

## Open questions / deferred

- **npm scope for `@deepwork/web`** — depends on the trademark-safe scope chosen at first publish; placeholder until then.
- **Storybook hosting** — build stories in U2; whether to publish a static Storybook (Chromatic/Vercel) is a polish-era call (U19).
- **Observability chart depth** — final decision at M3 entry (which stats a bearer token can read cheaply); U2 only ensures the components survive the import and the tab is removed.
- **Plugin registry wiring for browser-use (D4)** — the install surface is mock today; real wiring is scheduled around U13/U15. U2 only preserves the card and relocates the Plugins screen under Settings.

---

## Dependencies

- **Upstream:** U1 (workspace, `tsconfig.base.json`, biome, CI, catalog).
- **Downstream:** all UI-wiring units (U8–U16) build on this `apps/web`. U11 rebuilds the approvals surface imported here. U13 revisits the browser card as plugin-gated (D4).
