# Surfaces · Web + Desktop + Mobile split

*Feature deep-dive · 2026-07-23 · Milestone M4 (mobile/desktop shipping); web throughout · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Specs: [../application-architecture.md](../application-architecture.md), [../../plan/03-ui-spec.md](../../plan/03-ui-spec.md) §6*

> Develops the frontend split from [application-architecture.md](../application-architecture.md): **web + desktop share one Next.js app**; **mobile is a focused PWA (→ Expo later)**. All three consume `packages/sdk` and stream client-direct.

---

## The split, and why

| Surface | What it is | Scope | v1 |
|---|---|---|---|
| **Web** (`apps/web`) | Next.js operations room | **Full** — every screen | ✅ |
| **Desktop** (`apps/desktop`) | Tauri v2 wrapping the web build | **Full** (same UI) + native shell | ✅ |
| **Mobile** (`apps/mobile`) | PWA first, Expo/RN later | **Focused subset** | ✅ PWA |

**Web and desktop are the same app.** Desktop is not a re-implementation — it's the Next.js build in a Tauri webview plus native affordances (tray, notifications, deep links, device-flow sign-in, updater). One UI codebase, two delivery vehicles. This is the full operations room.

**Mobile is deliberately not the whole room.** On a phone the job is triage and unblock, not fleet configuration. Cramming 21 settings sections and a fleet matrix onto mobile would be worse than omitting them. So mobile ships a **focused subset** with its own navigation.

---

## Mobile v1 (PWA) — scope

**In:**
- **Inbox triage** — status-grouped task list, "needs you" banner, filters.
- **Task detail (watch + steer)** — live streaming narration, tool cards, todo tray; steering composer (queue vs interrupt); trace link.
- **Approvals** — the HITL inbox: approve / edit / reject / respond, batched interrupts, one-tap approve from a push notification.
- **Push** — Web Push/VAPID on run-completion and interrupt-raised; notification actions deep-link into the task or approval.
- **Offline shell** — installable, app-shell cached; last-fetched data visible offline; actions queue until reconnect.

**Out (v1 mobile — use web/desktop):**
- Agent builder / fleet config / connector permission matrix.
- Settings (21 sections).
- Observability (link out to LangSmith).
- Schedules CRUD (view only, maybe; create on web).
- Diff-review takeover (view diffs read-only; full review on web/desktop).

**Navigation:** bottom bar per [03-ui-spec §6](../../plan/03-ui-spec.md) — Inbox · Approvals · Activity, with task detail as a push view. No left sidebar / right rail (those are desktop-shape).

---

## Sharing model

```
packages/sdk   → consumed identically by web, desktop, mobile
packages/ui    → web/desktop use the full component set
               → mobile uses the RN-agnostic primitives (tokens, StatusChip,
                 ToolCard, approval cards); mobile-specific layout lives in apps/mobile
apps/api       → the same backend for all three surfaces
useStream      → all three stream client-direct against the deployment
```

- **`packages/sdk` is surface-agnostic** — no DOM/React-DOM assumptions in the client/stream layer, so Expo (React Native) can consume it unchanged later.
- **`packages/ui` splits** into framework-agnostic primitives (tokens, pure presentational components) usable by RN, and web-only composites. Mobile composes its own screens from the primitives.

---

## Desktop (Tauri v2) — native affordances

Wraps `apps/web`. Adds:
- **Tray** icon with quick status (running / needs-review counts).
- **Native notifications** on the same run-completion webhook event the PWA uses (via `apps/api` push fan-out → desktop channel).
- **Deep links** (`deepwork://task/:id`, `deepwork://approvals`) routing into the web UI.
- **Device-flow sign-in** (RFC 8628) — no embedded browser needed; uses `apps/api` `/v1/auth/device/*`.
- **Auto-updater** (Tauri updater) with signed artifacts.

Builds for macOS / Windows / Linux via a `desktop-build.yml` workflow; Mac/Win signing certs in CI secrets.

---

## Post-v1: Expo / React Native

Native mobile is deferred but designed-for:
- Reuses `packages/sdk` (already surface-agnostic) and the `packages/ui` primitives.
- Swaps Web Push for **APNs/FCM** (the `apps/api` push fan-out already abstracts the channel).
- Native deep links + secure token storage.
- Same focused scope as the PWA, upgraded to native feel.

The PWA-first choice means v1 mobile ships with the web pipeline (zero app-store friction), and the native app is an additive surface, not a rewrite.

---

## Test scenarios

- **PWA install:** installing on iOS/Android adds the icon; launch shows the inbox in standalone mode.
- **Push → approve:** a run raises an interrupt → push arrives → one-tap approve resolves it; the task detail reflects the resumed stream.
- **Offline:** with no network, the app-shell renders and last-fetched inbox is visible; a steering action queues and flushes on reconnect.
- **Shared SDK:** `packages/sdk` imported in a mobile context has no DOM dependency (build/lint enforces).
- **Desktop deep link:** `deepwork://task/:id` opens the desktop app to that task.
- **Desktop notification:** a run-completion event fires a native notification; clicking opens the task.

---

## Verification

- Lighthouse PWA audit passes (installable + offline).
- The full loop (dispatch → watch → steer → approve) completes from an installed PWA on a phone (v1 release criterion 2).
- Tauri CI produces signed macOS artifacts; tray + notifications + deep links work.
- `packages/sdk` builds for a non-DOM target without error.

---

## Open questions / deferred

- **Exact mobile screen-set line** (does Schedules view make the cut?) — decide at M4 entry.
- **Offline action queue semantics** (how long to hold a queued steer; conflict handling) — refine during U18.
- **Expo timing** — post-v1; revisit once PWA usage shows demand for native.

---

## Dependencies

- **Upstream:** U9 (inbox), U10 (task detail streaming), U11 (approvals), U7b (push endpoints), U18 (PWA/Tauri implementation).
- **Downstream:** informs U19 polish (mobile a11y, offline states).
