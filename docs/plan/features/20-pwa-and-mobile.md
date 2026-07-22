# F20 · PWA & mobile

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M4 (Expo: post-v1, design-complete) · Depth: implementation-ready*

Sources: [03 · UI spec](../03-ui-spec.md) (§2 responsive, §3.3, §5, §6, §7) · [04 · Roadmap](../04-roadmap.md) (M4, v1 release criteria) · [02 · Architecture](../02-architecture.md) (§7, §10, §11) · [01 · Vision](../01-vision.md) (success criterion 2, cut line) · [06 · Frontend implementation](../06-frontend-implementation.md) (Phase F) · [research 05 · Cross-platform arch](../../research/05-crossplatform-arch.md) · [research 21 · UI streaming contract](../../research/21-gapfill-ui-contract.md) · [research 13 · agent-inbox](../../research/13-agent-inbox.md)

Stack context: frontend is Next.js (D-022); mobile v1 is PWA-first, Expo post-v1 (D-006; [01](../01-vision.md) cut line; [research 05](../../research/05-crossplatform-arch.md): "v1 should ship web + Tauri desktop first with mobile as PWA"). Push fan-out lives on the `apps/server` FastAPI glue *(P-005)* and is owned end-to-end by [F19 · Notifications & push](./19-notifications-and-push.md). Shell/bottom-bar *foundations* are [F07 · App shell & navigation](./07-app-shell-and-navigation.md).

**Placement correction (flag for the decision log):** [05](../05-oss-setup.md), [02 §11](../02-architecture.md) and [F01](./01-monorepo-and-oss-infra.md) task 6 place "PWA assets/config" in `apps/mobile`. A web manifest and service worker must be served same-origin from the installable app and the SW's scope is bounded by where it is served — so PWA packaging lives **in `apps/web`**. `apps/mobile` stays reserved for the post-v1 Expo app (§3.7).

## 1. Scope

### In scope

- **PWA packaging** in `apps/web`: web app manifest (identity, icons, shortcuts, display), service worker with **offline-shell-only** caching (recommended v1 answer, matching [04](../04-roadmap.md) M4 "offline shell"), SW update flow (refresh prompt, guarded reload).
- **Install nudges**: iOS home-screen install nudge (prerequisite for Web Push on iOS ≥16.4, [research 05](../../research/05-crossplatform-arch.md)); Android/desktop `beforeinstallprompt` capture and settings entry. Placement inside onboarding is a seam to F06.
- **Mobile experience** (< lg / < xl breakpoints per [03 §2](../03-ui-spec.md)): bottom bar (Tasks/Approvals/Agents), rail-as-sheets in task detail, scrolling tab row with fade masks, composer voice input where available, touch targets and mobile a11y — behavior and acceptance here; shell primitives from F07.
- **Flagship flow**: push notification → one-tap approve screen ([03 §3.3](../03-ui-spec.md)), screen-by-screen, including cold start and stale interrupts.
- **Streaming lifecycle on mobile**: disconnect on background, resumable rejoin via `Last-Event-ID` ([02 §7](../02-architecture.md): load-bearing), reconnect tuning (seam to F04).
- **Release criterion 2** ([04](../04-roadmap.md)): full loop (dispatch/steer/approve/diff/merge) from an installed PWA — mobile walk-through plus the gaps it creates for neighbor specs.
- **Expo native app — DESIGN-COMPLETE section (§3.7)**: no tasks in §8; design only.

### Out of scope

- Push pipeline server side: webhook registration, VAPID keys, subscription storage, fan-out route, payload construction — [F19](./19-notifications-and-push.md). This spec owns only the SW-side handlers and the deep-link screens they open.
- Approvals contract, `InterruptCard`/`DecisionForm`, decision semantics and their edge cases — F10 (approvals inbox, see [catalog](./README.md)). This spec owns the mobile screen around them.
- `useStream` wiring, adapter layer, golden-transcript resume tests — F04 (streaming/data layer, see [catalog](./README.md)). This spec contributes mobile-specific config values and lifecycle triggers.
- Desktop (Tauri) surface; responsive shell foundations ([F07](./07-app-shell-and-navigation.md)); Expo implementation.

## 2. Dependencies & seams

| Direction | Spec | What crosses the seam |
|---|---|---|
| needs ← | [F07 · App shell & navigation](./07-app-shell-and-navigation.md) | Responsive shell primitives: bottom-bar slot + badge API, tab-row with scroll fade masks, sheet primitive for rail-as-sheets, safe-area handling hooks |
| needs ← | [F19 · Notifications & push](./19-notifications-and-push.md) | Notification payload contract (thread id, agent-source id, best-effort **nullable** `interrupt_id`, deep-link path), Web Push subscription lifecycle, permission prompt UX; F20's SW hosts F19's `push`/`notificationclick` handler modules (one SW, split ownership — §4) |
| needs ← | F10 · Approvals inbox ([catalog](./README.md)) | `InterruptCard`/`DecisionForm` components, `respond()` semantics, stale/already-handled interrupt semantics; F20 defines the focused mobile screen and its states |
| needs ← | F04 · Streaming & data layer ([catalog](./README.md)) | `useStream` config surface (`maxReconnectAttempts`, `streamIdleReconnect`, `reconnectDelayMs`, `onReconnect` — [research 21](../../research/21-gapfill-ui-contract.md)); state-first hydration (`getThread`/`hydrationPromise`); ratifies §4 mobile values; Spike-3 resume tests cover the background→rejoin path ([04](../04-roadmap.md) M0) |
| needs ← | F06 · Onboarding ([catalog](./README.md)) | Slot for the install nudge in onboarding and in Settings → Notifications ([03 §3.6](../03-ui-spec.md): Web Push opt-in per device) |
| needs ← | [F01 · Monorepo](./01-monorepo-and-oss-infra.md) | `apps/web` workspace + CI; note the `apps/mobile` placement correction above |
| provides → | [F19](./19-notifications-and-push.md) | Registered root-scope SW (Web Push has no home without it); Expo Push slot design (§3.7) |
| provides → | Release process | Criterion-2 rehearsal checklist (§7-AC9) and the gap list it produces (§3.6) |
| depends on | D-022 · D-006 · P-005 | Next.js frontend; PWA-first mobile; push fan-out on FastAPI `apps/server` (provisional — a P-005 reversal moves the fan-out route, changes nothing here) |

## 3. Design

### 3.1 Packaging: manifest

Served from `apps/web` (Next.js metadata/manifest route). Fields:

| Field | Value | Grounding |
|---|---|---|
| `name` / `short_name` | `Deep Work` / `Deep Work` | product name, no `lang*` ([F01 §4](./01-monorepo-and-oss-infra.md) trademark contract) |
| `id` / `scope` / `start_url` | `/` / `/` / `/?surface=pwa` | `surface` feeds the run-metadata convention ([02 §10](../02-architecture.md)) so runs dispatched from the installed app are traceable |
| `display` | `standalone` | app-like; keep browser UI out of the flagship flow |
| `background_color` | `#FFFFFF` | page ground, light ([03 §1.1](../03-ui-spec.md)) |
| `theme_color` | `#FFFFFF`; dark handled by `<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#030710">` | token values from [03 §1.1](../03-ui-spec.md); manifest takes one static value |
| `icons` | 192/512 PNG + maskable variants; original mark only (no LangChain assets, [F01 §4](./01-monorepo-and-oss-infra.md)) | installability baseline |
| `shortcuts` | **New task** → `/tasks/new` · **Approvals** → `/approvals` | the two highest-intent entries ([01](../01-vision.md) pillars 1–2) |

### 3.2 Service worker: offline shell only (v1 recommendation)

**Recommendation: the SW precaches the app shell and nothing else.** [04](../04-roadmap.md) M4 says exactly "offline shell"; caching thread/approval data would present stale agent state as live — poisonous for an approvals product where the payload is the thing being verified ([01](../01-vision.md) pillar 1: verification UX *is* the product). Cached-inbox reading is explicitly rejected for v1 (revisit post-v1 with clear staleness labels).

- **Precache**: build-hashed static assets, the shell route skeleton, an `/offline` fallback document, fonts, icons.
- **Runtime**: `cache-first` for hashed static assets only. **Network-only, never intercepted**: everything under the agent-source URLs (`/threads/*`, `/commands`, `/stream/events`, connector routes), control-plane calls, auth routes. SSE/fetch streams pass through untouched.
- **Offline UX**: opening the app offline renders the shell + an explicit offline state (last-connected timestamp, retry button) — a real empty state per [03 §7](../03-ui-spec.md), not a spinner. Going offline while open: banner + disabled submit affordances; decisions are never queued offline (§5).
- **Update flow**: new deploy → new SW installs and waits → app surfaces a sonner toast ([03 §4](../03-ui-spec.md) conventions) "Update available — Refresh" → on consent, `postMessage(SKIP_WAITING)` → `controllerchange` → reload. Reload is **guarded**: never while a decision or composer submit is in-flight (§4). No auto-`skipWaiting`.
- **Tooling**: minimal hand-rolled SW vs Serwist-class generator — §9-Q1. The caching contract in §4 holds either way.

### 3.3 Install nudges

- **iOS ≥16.4**: Web Push works only for home-screen-installed PWAs ([research 05](../../research/05-crossplatform-arch.md)); there is no programmatic install prompt on iOS — the nudge is an instruction sheet (Share → Add to Home Screen, with visuals). Trigger points: (a) onboarding step after first task dispatch — "get notified when it needs you" (slot owned by F06); (b) Settings → Notifications when Web Push opt-in is attempted in a Safari tab ([03 §6](../03-ui-spec.md): "onboarding nudges this"). Detection: `display-mode: standalone` media query + iOS UA → show/hide nudge and gate the push toggle (F19 owns the toggle).
- **Android/desktop**: capture `beforeinstallprompt`, defer, surface as (a) a dismissible one-time nudge after first completed task, (b) a permanent "Install app" entry in Settings. If the event never fires (already installed / unsupported browser), the entry hides.
- Nudges are dismissible and never modal — install is required for iOS push, not for using the app (§5).

### 3.4 Mobile experience

Breakpoint behavior inherited from [03 §2](../03-ui-spec.md): < lg sidebar off-canvas; < xl rail collapses; mobile adds the bottom bar.

- **Bottom bar**: Tasks · Approvals · Agents ([03 §6](../03-ui-spec.md)); Approvals carries the needs-review badge count (interrupt-count aggregation from [03 §3.1](../03-ui-spec.md)); respects `env(safe-area-inset-bottom)`; active state = accent + faux-bold per [03 §1.2](../03-ui-spec.md). Schedules/Activity/Settings reachable via the tab row and ⌘K-equivalent search. Optional: mirror the badge to the OS icon via the Badging API where supported (§9-Q6).
- **Tab row**: horizontal scroll with fade masks at both edges ([03 §2](../03-ui-spec.md)) — masks match the sidebar scroll-fade detail.
- **Task detail, rail-as-sheets** ([03 §6](../03-ui-spec.md)): the run panel's content (status/elapsed, todos, files changed, branch/PR/CI, trace, artifacts — [03 §3.2](../03-ui-spec.md)) becomes bottom sheets opened from a compact status strip under the header. Diff review — already a full-width takeover on desktop — becomes a full-screen route on mobile.
- **Composer**: full-width docked above the bottom bar; queue-vs-interrupt affordance preserved ([03 §3.2](../03-ui-spec.md)); todo tray collapses to the "Task N of M" summary row. **Voice input where available** ([03 §6](../03-ui-spec.md)): baseline is OS keyboard dictation (zero code, works everywhere); an explicit mic button ships only behind capability detection — Web Speech API reliability across mobile browsers is unverified, §9-Q3.
- **Touch & a11y**: interactive targets ≥ 44×44 CSS px; hover-only affordances (row hover, chevron cards) get tap equivalents (whole row tappable, chevron always visible); keyboard-centric features (j/k, hotkeys — [03 §7](../03-ui-spec.md)) are additive, never the only path; AA contrast both themes; `prefers-reduced-motion` disables the running-status pulse.

### 3.5 The flagship flow: push → one-tap approve

[03 §3.3](../03-ui-spec.md): "push notification → one-tap approve screen. This is the flagship mobile flow." Screen-by-screen:

| # | Step | Behavior |
|---|---|---|
| 1 | **Notification arrives** | F19 payload gives thread id, agent-source id, deep-link path, and a **best-effort, nullable** `interrupt_id` (extracted by F19 from the webhook's interrupt marker when present; the id originates in `input.requested {interrupt_id, payload}`, [research 21](../../research/21-gapfill-ui-contract.md)). SW `notificationclick`: focus an existing client and in-app-navigate, else open the deep link. No decision buttons on the notification itself (§6) |
| 2 | **Auth check** | Session valid → continue. Expired → sign-in (OAuth PKCE / key unlock per [02 §5](../02-architecture.md)) with `returnTo` preserving the full deep link, including `interrupt_id` when present |
| 3 | **Focused approval card** | Route renders a single F10 `InterruptCard` for that interrupt. **Hydrate from thread state first** (interrupts hydrate from `thread.getState().tasks[].interrupts`, [research 21](../../research/21-gapfill-ui-contract.md)) — one fetch, no stream attach required to render. Thread-state resolution is **authoritative**: when the payload's `interrupt_id` is null, the screen targets the thread's current pending interrupt from state — never assume the payload supplies the id. Card shows tool name, args, capability chips from `allowedDecisions` |
| 4 | **Decision** | Primary: one-tap **Approve** (≥44px, thumb zone). Secondary: expand to edit/reject/respond (full F10 form). Submit via `respond()` |
| 5 | **Confirmation** | Optimistic pending → confirmed. Then: "Watch run" (attach `useStream`, land in task detail) or back to Approvals |

**Cold start**: precached shell (§3.2) gets first paint fast; step 3's state-first hydration avoids waiting on SSE attach. Budget: tap → actionable card **≤ 3 s warm, ≤ 5 s cold** on a mid-tier device over 4G (§7-AC5). The approval route stays out of heavy chunks (diff viewer, charts) via code-splitting.

**Stale interrupt** (opened minutes/hours later; another device may have answered — multi-device handoff is a designed-for case, [02 §7](../02-architecture.md)): if hydration finds no interrupt matching a non-null `interrupt_id` — or no pending interrupt at all when it was null — render an explicit **"Already handled"** state — current run status chip + link into task detail — and never submit a decision against a missing interrupt. If the race is lost between render and submit, surface the `respond()` error the same way. Canonical semantics (and what the server returns for an already-resolved `interrupt_id` — §9-Q5) belong to F10's edge-case section; this spec owns the screen.

### 3.6 Release criterion 2: the full loop from a phone

[04](../04-roadmap.md) criterion 2 / [01](../01-vision.md) success criterion 2: dispatch → steer → approve → diff → merge from an installed PWA.

| Stage | Mobile screen | Gap / note for neighbors |
|---|---|---|
| Dispatch | New-task composer ([03 §3.1](../03-ui-spec.md) modal) as full-screen sheet: prompt, agent/environment/repo pickers, plan-approval toggle | Composer spec must keep picker UIs touch-viable (no hover dropdown chains) |
| Steer | Task detail thread + docked composer; queue/interrupt affordance | Streaming lifecycle per §3.7 while the screen is foregrounded |
| Approve | §3.5 flagship flow, or in-app Approvals tab | F10: batched-interrupt card must fit narrow viewports (per-call decision rows stack) |
| Diff | Full-screen diff takeover; unified view default ([03 §1.3](../03-ui-spec.md)) with horizontal scroll inside the code frame | **Gap → diff-review spec**: per-line comment gesture needs a touch affordance (tap line gutter → comment sheet); batching UX unchanged |
| Merge | v1 flow ends at a **draft PR** ([02 §4](../02-architecture.md) git flow); rail exposes PR link + CI status ([03 §3.2](../03-ui-spec.md)) | **Gap**: no in-app merge exists in any source doc. Options: (a) deep link to the GitHub PR and merge there — satisfies "from a phone" literally, weakest story; (b) in-app merge action via GitHub App (Contents/PRs RW, [02 §4](../02-architecture.md)) through the server glue. Recommend (b) as a small addition to the diff/PR spec; decide §9-Q4 |

### 3.7 Streaming on mobile

- **Background**: on `visibilitychange: hidden` (the reliable signal on mobile; `beforeunload` is not), call `stream.disconnect()` ([03 §5](../03-ui-spec.md)). PWAs get no background execution — awareness while backgrounded comes from push (F19), never from a held-open stream. This is also the battery/data story: no radio held for SSE in the background.
- **Foreground**: rejoin via resumable streams — `stream_resumable` runs replayed with `Last-Event-ID`; thread-level join streams cover multi-run threads ([02 §7](../02-architecture.md); [research 05](../../research/05-crossplatform-arch.md): "designed for mobile backgrounding and multi-device handoff"). If replay can't bridge the gap (buffer expiry, server restart), fall back to fresh state hydration (`getThread`) then re-attach live — the UI reconciles from state, never shows a spliced-wrong transcript.
- **Reconnect tuning** (options exist on `UseStreamOptions`: `maxReconnectAttempts`, `streamIdleReconnect`, `reconnectDelayMs`, `onReconnect` — [research 21](../../research/21-gapfill-ui-contract.md)). Proposed mobile profile, to be ratified by F04 against Spike-3 tests and real networks: `maxReconnectAttempts: 5` with exponential backoff + jitter via `reconnectDelayMs`, then a manual "Reconnect" banner (don't spin the radio forever on a dead hotel network); `streamIdleReconnect` enabled so an idle-killed SSE (mobile networks kill quiet connections) self-heals while foregrounded.

### 3.8 Expo native app — POST-v1 · DESIGN-COMPLETE (no §8 tasks)

Explicitly cut from v1 ([01](../01-vision.md); [04](../04-roadmap.md) post-v1 backlog); the architecture keeps the door open. Design is settled as follows:

- **What carries over**: `packages/sdk` unchanged (agent-source registry, control-plane client, normalization — pure TS); `packages/ui` **token values** as the theme source of truth (tokens.css → RN theme object; Tailwind preset and DOM components do not carry); fixtures for demo/tests. Screens are rebuilt on RN primitives mirroring the §3.4 IA (bottom bar = native tabs via expo-router).
- **Streaming**: `useStream`/langgraph-sdk work in React Native/Expo today — documented with `expo/fetch` (WinterCG-compliant; RN 0.74+ fetch streams; assistant-ui ships RN bindings on exactly this stack) ([research 05](../../research/05-crossplatform-arch.md)). Open item carried from research: whether Hermes needs any polyfill beyond streaming fetch (e.g. `TextDecoderStream`) — verify at build start (§9-Q7).
- **Push**: slots into the existing F19 pipeline — the run-completion webhook fan-out gains an Expo Push channel (server → Expo Push API for native, alongside Web Push/VAPID; [research 05](../../research/05-crossplatform-arch.md), [02 §7](../02-architecture.md) "Expo Push later"). Device registers an Expo push token with the same subscription store; notification payload contract (§4) is transport-agnostic by design.
- **Platform baseline at design time**: Expo SDK 56 (RN 0.85, React 19.2, Hermes V1, New Architecture mandatory since SDK 55; expo-router independent of React Navigation) ([research 05](../../research/05-crossplatform-arch.md)) — re-pin at build start.
- **When to trigger the build (demand signals)**: (a) measured iOS install-nudge conversion so low that push never reaches most iOS users; (b) iOS EU Web Push confirmed unavailable (§9-Q2) for a meaningful user segment; (c) repeated App-Store-presence asks from teams; (d) needs beyond PWA reach (reliable background behavior, native share targets). Any one signal opens a roadmap PR; none is scheduled work today.

## 4. Contracts

**SW caching contract** (v1, offline shell only):

| Class | Strategy | Examples |
|---|---|---|
| Build-hashed static assets | cache-first (precached) | JS/CSS chunks, fonts, icons |
| Shell + offline fallback | precached document(s) | shell skeleton, `/offline` |
| Agent-source APIs | **never intercepted** | `/threads/*`, `/commands`, `/stream/events`, connector routes ([02 §4](../02-architecture.md)) |
| Control plane / auth / push subscription | **never intercepted** | api.smith.langchain.com calls via proxy, OAuth routes, F19 endpoints |

**SW update contract**: versioned precache manifest; waiting SW emits `dw:sw-update-available` to the app; user consent → `SKIP_WAITING` message → `controllerchange` → reload **only if** no decision/composer submit is in-flight (deferred until settled). One SW file at root scope; F19's `push`/`notificationclick` handlers are imported modules inside it — F20 owns registration/lifecycle/caching, F19 owns handler behavior and payload parsing.

**Deep-link contract** (consumed from the F19 payload; canonical shape defined there): path `/approvals/t/{sourceId}/{threadId}?interrupt={interrupt_id}` — `sourceId` is required because threads span multiple agent sources ([03 §3.6](../03-ui-spec.md) registry); the `interrupt` param is **optional**: F19's `interrupt_id` is best-effort nullable (originating in `input.requested`, [research 21](../../research/21-gapfill-ui-contract.md)) and omitted when null — thread-state resolution (§3.5 step 3) is authoritative then. Auth redirects must round-trip the full URL. Notification tap with the app open focuses and client-side-navigates (no second window).

**Mobile stream profile** (proposed values; F04 ratifies): `transport: 'sse'`; `disconnect()` on `visibilitychange: hidden` / `pagehide`; rejoin with last event id on foreground; `maxReconnectAttempts: 5`; backoff with jitter via `reconnectDelayMs`; `streamIdleReconnect: true`; `onReconnect` → state re-hydration fallback per §3.7.

**Layout constants**: touch targets ≥ 44×44 CSS px; bottom bar height + `env(safe-area-inset-bottom)`; `display-mode: standalone` media query is the installed-state detector; runs dispatched from the installed app carry `surface: 'pwa'` metadata ([02 §10](../02-architecture.md) convention).

## 5. Edge cases & failure modes

- **Stale interrupt on open** (§3.5): "Already handled" state; never submit against a missing `interrupt_id`; lost race surfaces the same state. Semantics owned by F10.
- **Offline decision attempt**: submit affordances disable with an explicit offline notice; approvals are **never queued for later send** — a queued approve against state that has since moved is a correctness and safety bug, not a convenience.
- **Notification tap with expired session**: full deep link survives the auth round-trip; a failed `returnTo` lands on Approvals (degraded, not lost).
- **SW update mid-flow**: reload deferred until in-flight submits settle (§4); a broken SW ships with a kill-switch path — deploy a no-op SW that clears caches and unregisters (§8 task 3).
- **`Last-Event-ID` replay gap** (buffer expiry/restart): fall back to `getThread` hydration + live re-attach; no duplicate or missing messages rendered (Spike-3 resume transcripts are the test bed, [04](../04-roadmap.md) M0).
- **iOS never installs**: no push, but the app remains fully usable in-browser — badge counts on open, Approvals tab as the discovery surface. Push is an enhancement, not a dependency.
- **`beforeinstallprompt` never fires** (installed already / unsupported): settings entry hides; nudge suppressed.
- **Multi-device double-answer**: second device gets the stale-interrupt state; no double-resume is ever sent.
- **Sandbox expired by open time** (thread sandbox `idle_ttl` 600s default, [02 §4](../02-architecture.md)): approval screen still renders from thread state; follow-up work auto-recreates the sandbox — no special mobile handling, just no assumption that the sandbox is live.
- **Safari storage eviction** (browser-tab usage): nothing critical lives in SW caches or local storage beyond re-fetchable shell + re-authable session; eviction degrades to a normal cold sign-in.

## 6. Security & privacy

- **SW caches hold zero user data**: static shell only (§4) — consistent with "Deep Work stores essentially nothing" ([01](../01-vision.md) non-goals; [02 §1](../02-architecture.md)). No API responses, no tokens, no thread content in Cache Storage (§7-AC10 verifies).
- **No decisions from the lock screen**: notifications carry no approve/reject action buttons in v1 — approving without seeing current args would gut the verification pillar ([01](../01-vision.md) pillar 1). Tap always lands on the authenticated, freshly-hydrated card. Revisit only with F10/F19 jointly (§9-Q8).
- **Deep links carry identifiers, never authority**: thread/interrupt ids only — no tokens, no pre-signed actions; the session is the sole authority and expired sessions re-authenticate (§3.5 step 2).
- **Lock-screen exposure**: notification text can leak org data (tool names, task titles) to a locked screen; payload minimization and a "generic notifications" option are F19's contract, flagged here as a mobile-surfaced requirement.
- **Untrusted-content boundaries** for webhook/schedule payloads ([02 §10](../02-architecture.md)) apply unchanged on mobile screens, including the focused approval card's description fields.
- **Transport**: PWA installability requires HTTPS; VAPID/push key custody is server-side (F19, on `apps/server` per P-005).

## 7. Acceptance criteria

1. Installability: Android Chrome and desktop Chrome/Edge offer install; manifest validates (id, scope, icons incl. maskable, `standalone`); both shortcuts open their routes in the installed app.
2. On an iPhone (iOS ≥16.4, home-screen-installed): Web Push permission grantable; a run-completion push arrives; tapping it opens the focused approval screen deep-linked to the right interrupt.
3. Offline: airplane-mode launch renders the shell with the explicit offline state (no stale data presented as live, no blank screen); regaining network shows a reconnect affordance that recovers without full reload.
4. Update flow: deploying a new build surfaces the refresh toast in an open installed app; accepting activates the new SW; a decision in-flight defers the reload until settled.
5. Flagship latency: notification tap → actionable approval card ≤ 3 s warm / ≤ 5 s cold on a mid-tier phone over throttled 4G (measured in the criterion-2 rehearsal).
6. Stale interrupt: an interrupt resolved elsewhere renders "Already handled" with run status + task link; no resume payload is sent.
7. Background/foreground: backgrounding disconnects the stream (verified: no open SSE while hidden); foregrounding rejoins with no missing or duplicated messages against the Spike-3 resume transcripts.
8. Mobile experience: bottom bar with live Approvals badge + safe-area padding; run-panel sheets expose status/todos/files/PR/trace; tab row scrolls with fade masks; all targets ≥ 44px; AA contrast both themes; reduced-motion honored.
9. Criterion-2 rehearsal passes on a real phone (installed PWA): dispatch → steer → approve (via push) → diff review with a line comment → merge path per §9-Q4 resolution; gaps filed on neighbor specs.
10. Cache audit: after a full session, Cache Storage contains only build assets + shell/offline documents — no API responses, tokens, or thread content.

## 8. Task breakdown

PWA/M4 items only — the Expo section (§3.7 · §3.8) generates **no tasks**.

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Manifest + icon set (192/512 + maskable) + shortcuts + theme-color meta in `apps/web`; `surface=pwa` start-url metadata plumbed to run dispatch | F01 (`apps/web`) | AC-1; metadata visible on traces per [02 §10](../02-architecture.md) |
| 2 | SW toolchain decision (§9-Q1) + root-scope SW: precache shell/offline fallback, §4 caching contract, F19 handler module slots | 1 | AC-3; AC-10; F19 can register handlers without touching lifecycle code |
| 3 | SW update flow: waiting→toast→SKIP_WAITING→guarded reload; kill-switch SW documented and rehearsed | 2 | AC-4 |
| 4 | Install nudges: `beforeinstallprompt` capture + settings entry; iOS instruction sheet + standalone detection gating the push toggle | 1; F06 slot; F19 toggle | AC-1; iOS nudge shows only where install is absent + required |
| 5 | Bottom bar (Tasks/Approvals/Agents) on F07 primitives: badge wiring, safe-area, active states; tab-row fade masks verified on touch | F07 | AC-8 (bar + tab row) |
| 6 | Task detail rail-as-sheets: status strip + sheets for todos/files/PR/trace; diff takeover as full-screen mobile route | F07 sheets; diff spec | AC-8 (sheets); §3.6 diff gap filed |
| 7 | Composer mobile pass: docked layout, queue/interrupt on touch, todo tray collapse, dictation-friendly input (+ mic button iff §9-Q3 lands) | 5 | AC-8; voice baseline documented |
| 8 | Notification deep-link route + auth `returnTo` round-trip (contract §4, payload from F19) | 2; F19 payload | Tap-through lands correctly authed and unauthed |
| 9 | Focused approval screen: state-first hydration, one-tap approve, expand-to-edit/reject/respond, stale/"already handled" states | 8; F10 components | AC-2; AC-5; AC-6 |
| 10 | Stream lifecycle wiring: visibility disconnect, foreground rejoin, reconnect profile handed to F04 for ratification; hydration fallback | F04 | AC-7 |
| 11 | Mobile perf pass: code-split approval route, cold-start budget measurement rig (throttled 4G, mid-tier device) | 9 | AC-5 measured and recorded |
| 12 | Criterion-2 rehearsal on hardware; file gaps (diff touch comments, merge affordance §9-Q4) on neighbor specs | 1–11 | AC-9; gap issues opened |

## 9. Open questions

1. **SW toolchain**: hand-rolled minimal SW vs a generator (Serwist-class) for the Next.js build — the §4 contract is small enough to hand-roll; ratify at task 2.
2. **iOS EU Web Push**: research flags a conflicting secondary claim that iOS 17.4+ EU devices lack PWA push ([research 05](../../research/05-crossplatform-arch.md) open question). Verify on hardware before marketing push as universal; feeds Expo demand signal (b).
3. **Voice input**: is Web Speech API reliable enough on target mobile browsers to ship a mic button, or is OS keyboard dictation the whole v1 story? ([03 §6](../03-ui-spec.md) says "where available" — define available.)
4. **Merge from phone**: in-app merge via GitHub App vs deep link to the GitHub PR (§3.6). Decides how release criterion 2's "merge" is satisfied; lands in the diff/PR spec's scope.
5. **Already-resolved `interrupt_id` behavior**: what exactly does `input.respond` return when the interrupt was already answered? Needed for precise error UX; F10/F04 to pin via Spike-3-style transcript.
6. **Badging API**: adopt `navigator.setAppBadge` for the approvals count where supported? Support matrix unverified.
7. **Hermes polyfills for `useStream`** (Expo, post-v1): confirm whether anything beyond streaming fetch is needed ([research 05](../../research/05-crossplatform-arch.md) open question) at Expo build start.
8. **Notification action buttons**: keep "no approve from the lock screen" permanent, or allow a constrained variant (e.g. reject-only) post-v1? Joint call with F10 + F19.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| iOS install friction throttles the flagship flow (push requires install; no programmatic prompt) | Flagship demo weak on the most common phone | Nudges at high-intent moments (§3.3); app fully usable uninstalled; measured conversion is Expo demand signal (a) |
| iOS EU push gap materializes (§9-Q2) | Flagship flow dead for EU iOS users | Verify early on hardware; Expo demand signal (b); in-app Approvals tab remains the fallback surface |
| SW caching bug serves a stale shell | Users stuck on broken builds — worst PWA failure class | Offline-shell-only scope (tiny cache surface), versioned precache, kill-switch SW rehearsed (task 3) |
| Resume-replay gaps on flaky mobile networks | Missing/duplicated transcript content | State-first hydration fallback (§3.7); Spike-3 golden transcripts as regression net (AC-7) |
| Cold-start latency blows the ≤5 s budget | One-tap approve stops feeling one-tap | Precached shell, state-first hydration, code-split approval route, measured rig (task 11) |
| "PWA is not a real app" perception vs native competitors (Cowork shipped mobile in July 2026, [research 05](../../research/05-crossplatform-arch.md)) | Adoption drag | Design-complete Expo path (§3.8) with explicit trigger signals; PWA quality bar in §7 |
| `useStream` reconnect knobs churn under weekly `@langchain/react` releases ([04](../04-roadmap.md) risk register) | Mobile profile breaks silently | Values live in F04's adapter layer, not scattered; contract tests catch renames |
| Manifest/SW placement confusion from the `apps/mobile` doc drift | Wasted scaffold work | Placement correction stated up front; decision-log entry filed |
