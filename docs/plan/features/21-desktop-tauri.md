# F21 · Desktop (Tauri v2)

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M4 · Depth: implementation-ready*

Sources: [../03-ui-spec.md](../03-ui-spec.md) (§5, §6) · [../04-roadmap.md](../04-roadmap.md) (M4) · [../../research/05-crossplatform-arch.md](../../research/05-crossplatform-arch.md) · [../02-architecture.md](../02-architecture.md) (§5, §7) · [../01-vision.md](../01-vision.md) · decisions: [../decisions.md](../decisions.md) (D-022, D-006, P-005) · neighbors: [F05](./05-auth-and-identity.md), [F07](./07-app-shell-and-navigation.md), [F10](./10-approvals-inbox.md), [F19](./19-notifications-and-push.md), [F01](./01-monorepo-and-oss-infra.md)

## 1. Scope

**In:** the `apps/desktop` Tauri v2 shell wrapping the same Next.js app (D-022; [03 §6](../03-ui-spec.md)): asset-loading architecture (§3.1), single-window/tray process model, tray icon + needs-review badge + menu, native notification raising, `deepwork://` deep-link registration and routing, the desktop **UX** of RFC 8628 device-flow sign-in (code display, polling states, expiry/retry), auto-updater + per-platform signing/notarization requirements, release artifact matrix and its CI job (extends F01's pipeline), global ⌘K, window-state persistence, launch-at-login, desktop settings, and the Tauri capability/CSP posture.

**Out (linked seams):** device-flow *protocol* mechanics, token refresh, keychain custody rules — [F05](./05-auth-and-identity.md) (§3.2, task 13); the run-completion push pipeline and event payloads — [F19](./19-notifications-and-push.md); everything rendered *inside* the webview — the web app specs ([F07](./07-app-shell-and-navigation.md) chrome, [F10](./10-approvals-inbox.md) approvals, [catalog](./README.md)); interrupt-count computation (`useApprovalsCount`) — [F10 §3.2](./10-approvals-inbox.md); monorepo scaffold, changesets, base CI — [F01](./01-monorepo-and-oss-infra.md) (which reserves `apps/desktop` as an M0 placeholder); PWA/mobile — [F20](./20-pwa-and-mobile.md).

## 2. Dependencies & seams

| Dependency | Direction | Seam |
|---|---|---|
| `apps/web` static export (D-022, P-005) | consumes | With no server routes in `apps/web`, Next satisfies Tauri's `output:'export'` requirement without a Node sidecar — constraint recorded by [F01 §3](./01-monorepo-and-oss-infra.md), inherited here ([research 05](../../research/05-crossplatform-arch.md)) |
| [F05](./05-auth-and-identity.md) | consumes | Device flow at `/oauth/device/code` (RFC 8628, endpoints via RFC 8414 metadata); tokens in OS keychain, never in webview storage (F05 acceptance 6); F05 task 13 = the shared implementation task |
| [F10](./10-approvals-inbox.md) → [F07](./07-app-shell-and-navigation.md) | consumes | `useApprovalsCount(): {total, bySource}` — the same selector feeding the tab badge feeds the tray count ([F10 §2](./10-approvals-inbox.md); F07 §9-7 wants one shared counter feed) |
| [F19](./19-notifications-and-push.md) | consumes | Normalized `NotificationEvent`s (run completed, input requested). Desktop raises them **locally** via the Tauri notification plugin — research 05 puts desktop on local notifications while Web Push/Expo serve PWA/mobile; transport to desktop in §3.4/§9-5 |
| [F04](./04-sdk-and-agent-sources.md) | consumes | `packages/sdk` is framework-agnostic TS explicitly "so it also serves Tauri" ([F04 §1](./04-sdk-and-agent-sources.md)); `DataProvider`/registry unchanged in the desktop build |
| [F01](./01-monorepo-and-oss-infra.md) | extends | Adds a `desktop-release` workflow to F01's CI (F01 scopes itself out of Tauri impl); artifacts attach to GitHub Releases, not npm |
| [F28](./28-backend-glue-service.md) (P-005) | optional | Reachability of a user-run `apps/server` decides proxy-vs-direct data path (§3.1, §9-1 = F05 §9-11) |
| Tauri v2 plugins | consumes | Confirmed by [research 05](../../research/05-crossplatform-arch.md): first-party **updater, notification, deep-link (`tauri-plugin-deep-link` 2.4.5), tray**; `@tauri-apps/api` 2.11.1; ~5 MB installers. Any plugin beyond these four is unverified → §9-3 |

## 3. Design

### 3.1 Asset architecture: bundled static export (recommended), not remote URL

Two options for what the webview loads:

| | A · Remote URL (deployed web app) | B · **Bundled static assets** (recommended) |
|---|---|---|
| Update cadence | UI updates on web deploy, no updater lag | UI rides desktop releases; mitigated by updater (§3.7) |
| Offline | White screen — nothing renders | Shell + fixtures/demo mode render; degraded states per F07 §3.8 |
| Auth | Reuses `apps/server` cookie session — but contradicts F05's desktop exception (keychain device-flow tokens) | Matches F05: device flow + keychain; no cookie dependency |
| OSS reality | There is **no canonical hosted URL** — Deep Work is self-hosted/OSS (D-003, [01](../01-vision.md)); every install would need URL config before first paint | Works out of the box; demo mode (P-004) with zero credentials |
| Security | Remote origin gets IPC reach; CSP must trust a mutable origin | IPC confined to the bundled origin; strict CSP (§6) |
| Feasibility | — | F01 already records static export as viable without a sidecar (P-005 side effect) |

**Decision: B.** Rationale: the OSS/no-canonical-URL point alone is dispositive; F05's desktop auth design assumes it; F01 pre-cleared the static-export path. Consequences: (a) `apps/web` must keep zero server routes (P-005 reversal would force the sidecar question back open — [F01 §5](./01-monorepo-and-oss-infra.md)); (b) OAuth *authorization-code* callbacks never target the desktop app — desktop uses device flow only, so no `http://localhost` redirect handling is needed; (c) a "connect to remote instance" mode is deliberately post-v1 (§9-10).

**Data path.** The webview talks to LangSmith control/data planes through one of two SDK modes ([F04 §3.3](./04-sdk-and-agent-sources.md)): **proxy** via a user-configured `apps/server` URL (team posture), or **direct** with the device-flow bearer (solo posture). Whether direct mode works from a Tauri origin (CORS on `api.smith.langchain.com` / `*.langgraph.app`) and whether a bundled `apps/server` sidecar is shipped instead is F05 §9-11 — mirrored here as §9-1, probed at M4 start.

### 3.2 Process model

- **Single window, single instance** (v1). A second launch or a deep link activates the existing instance (mechanism: §9-3). Multi-window is post-v1; the web app is designed as one shell (F07).
- **Close-to-tray**: closing the window hides it; the app keeps running in the tray, webview alive. This is load-bearing — the F10 approvals poll keeps running while hidden, so tray badge and notifications work without any background service. True quit only via tray menu / app menu.
- Default poll cadence while hidden: 60 s (vs F10's 30 s visible) to cut idle load; resumes 30 s + focus-revalidate on show.

### 3.3 Tray: badge + menu

- **Badge = needs-review count** from `useApprovalsCount().total` ([03 §6](../03-ui-spec.md); F10 counts *interrupts*, not threads). The webview pushes count changes over IPC (`set_badge`, §4.2); Rust renders it (macOS: tray title text; Windows/Linux: icon variant/tooltip — exact per-OS affordance at impl, §9-7). Count > 0 also swaps the tray icon to an attention variant.
- **Menu:** `Open Deep Work` · `N approvals waiting` (→ `/approvals`) · up to 5 most-recent pending items (tool name · agent — from `useApprovalsCount().bySource` detail feed; each → the item's deep link) · separator · `New task` (→ `/tasks/new`) · `Check for updates…` · `Settings` (→ `/settings`) · separator · `Quit`.
- Signed out or all sources unreachable: badge hidden, menu shows `Sign in…` / `Reconnect…` instead of counts (mirrors F07 degraded states).

### 3.4 Native notifications (F19 seam)

- **What desktop raises locally** (research 05: fan-out targets Expo/Web Push; "local notifications on desktop"): run completed / failed, new interrupt (`input.requested`), per F19's event taxonomy.
- **How events arrive on desktop, v1:** derived from data the webview already holds — open `useStream` subscriptions (root channels, [03 §5](../03-ui-spec.md)) and the F10 hidden-tab poll. No push transport, no OS push service. A server-push transport for desktop (e.g. subscribing to `apps/server`'s fan-out) is F19's call — §9-5; note 02 §7 *implies* desktop sits on the fan-out, research 05 says local — F19 owns reconciling this.
- Consequence: notification latency while hidden = poll cadence (≤60 s) except for threads with open streams (instant). F10 §9-Q4 (do webhooks fire on `interrupted`?) bounds how much F19 can improve this.
- Clicking a notification = its deep link (§3.5): show window, navigate. Per-category toggles in desktop settings (§4.4). Webview raises via the notification plugin through `@tauri-apps/api`; permission prompted on first use.

### 3.5 Deep links: `deepwork://`

Scheme registered at install via `tauri-plugin-deep-link` 2.4.5 (research 05); OS-level registration (Info.plist / registry / `.desktop`) is generated by Tauri config, not hand-rolled.

| Link | Route (F07 §4.1 map) |
|---|---|
| `deepwork://task/<source>/<threadId>` | `/tasks/[source]/[threadId]` |
| `deepwork://task/<source>/<threadId>/diff` | diff takeover sub-route (F07 §9-5 pending) |
| `deepwork://approval/<source>?item=<interruptKey>` | `/approvals?item=<key>` (F10's notification target) |
| `deepwork://agent/<agentId>` | `/agents/[agentId]` |
| anything else | `/` + toast "link not understood" |

- **Running instance:** plugin event → Rust forwards to webview (`deep-link` event, §4.2) → F07 router navigates; window shown + focused. **No bypass:** links resolve through the same route map and auth guards ([F07 §6](./07-app-shell-and-navigation.md)); signed out → link queued, `/login` shown, replayed after auth.
- **Cold start:** the launching URL is buffered Rust-side until the webview signals `router-ready`, then delivered — never dropped, never raced against hydration.
- URL params carry identifiers only, never secrets (F07 §6 rule). Wrong-org target → F07's 404-in-chrome with org-switch hint.

### 3.6 Device-flow sign-in (desktop UX; mechanics = F05)

Flow owner split: F05 owns endpoints, polling protocol, keychain writes; F21 owns the screen. All token traffic runs **Rust-side** — the webview only receives display state and a session handle; raw tokens never enter the JS context (§6).

States of the `/login` desktop variant:

1. **Start** — "Sign in with LangSmith" primary; API-key fallback link (F05 §3.3 flow, unchanged).
2. **Code display** — `user_code` in large mono with one-click copy; `verification_uri` as button (opens system browser via opener capability); QR optional (post-v1). Countdown ring showing device-code `expires_in`.
3. **Waiting** — polling per F05 (`authorization_pending`/`slow_down` honored Rust-side); passive spinner + "waiting for approval in your browser".
4. **Expired** — F05 edge row: poll until `expires_in` then stop; "Code expired" + `Get a new code` (fresh device code, back to 2). Never auto-loops silently.
5. **Denied / error** — distinct copy for `access_denied` vs network failure; retry.
6. **Success** — tokens → OS keychain (F05), org/workspace picker (F05 §3.2) inside the webview, then `/`.

Sign-out clears keychain entries + best-effort revocation (F05 §3.2); the tray immediately reflects signed-out state (§3.3).

### 3.7 Auto-updater & releases

- **Plugin:** first-party updater (research 05). Official behavior is full-artifact updates from a static JSON or dynamic server; differential updates are unconfirmed (research 05 open question) — plan for full artifacts.
- **Feed:** static `latest.json` attached to the GitHub Release (no update server to run — fits OSS/no-backend posture, D-003). **Channels:** `stable` only in v1; a `beta` channel is cheap later (separate manifest URL) — §9-4.
- **Updater signing:** Tauri updater artifacts are signed with the updater keypair per the plugin's requirements (research 05 sources); public key baked into `tauri.conf.json`, private key = GitHub Actions secret held by Tom. Key custody/rotation → §9-2.
- **Flow:** check on launch + every 24 h + tray `Check for updates…`; download in background; "Restart to update" toast + tray hint — never a forced restart mid-task (an agent may be streaming).

**Artifact matrix** (proposed; exact bundler target names verified at impl against Tauri docs — §9-6):

| OS | Arch | Artifacts | Signing requirement (OSS release) |
|---|---|---|---|
| macOS | aarch64 + x86_64 (or universal) | `.dmg` + updater archive | Developer ID cert + **notarization** — Apple Developer Program account (paid) → §9-2 |
| Windows | x64 | installer (`.exe`/`.msi`) + updater archive | Authenticode cert (OV vs Azure Trusted Signing undecided → §9-2); unsigned = SmartScreen wall |
| Linux | x64 | AppImage (updater-capable) + `.deb` | updater signature only |

**CI:** a `desktop-release` workflow in F01's pipeline (SHA-pinned actions per F01 conventions) — matrix build on macOS/Windows/Ubuntu runners, triggered by a `desktop-v*` tag; builds `apps/web` export → Tauri bundle → sign/notarize → attach artifacts + `latest.json` to the GitHub Release. Desktop versioning is tag-driven, independent of changesets (which covers npm packages only, [F01 §3](./01-monorepo-and-oss-infra.md)). PR CI adds a cheap `tauri build --debug` smoke job on one OS to catch export/config drift early.

### 3.8 Shortcuts, window state, launch-at-login

- **Global ⌘K / Ctrl+K** ([03 §6](../03-ui-spec.md)): registered OS-wide; fires show-window + open command palette (F07 §3.7 owns in-app behavior). If OS registration fails (conflict), degrade silently to the in-app-only binding and note it in settings. Registration mechanism is not among research 05's confirmed plugins → §9-3.
- **Window state:** size/position/maximized persisted across launches; restore validates against current monitor geometry (disconnected-display case → center on primary). Mechanism → §9-3.
- **Launch at login:** settings toggle, **default off**, with sub-option "start hidden in tray". Mechanism (autostart) → §9-3.

### 3.9 Degraded states

| State | Behavior |
|---|---|
| Offline | Bundled shell still renders (the §3.1 payoff); F07 degraded/error framework shows per-source unreachable states; tray badge freezes with stale indicator (tooltip "last updated HH:MM"); notifications pause |
| Webview drift (WebView2 / WKWebView / WebKitGTK versions vary per OS) | `apps/web` browserslist pinned to the minimum supported webview baseline (§9-8); CI smoke renders on all three OSes; no Chromium-only APIs without feature detection |
| Updater failure | Update check/download errors are non-blocking: log + settings badge, app keeps running current version; manual download link (GitHub Releases) always shown in Settings → About |
| Signed-out with pending deep link | Link queued and replayed post-auth (§3.5) |

## 4. Contracts

### 4.1 Workspace layout

```
apps/desktop/
  src-tauri/            # Rust: tray, deep-link buffer, device-flow driver, keychain, updater wiring
    tauri.conf.json     # frontendDist -> apps/web export output; updater pubkey; deep-link scheme
    capabilities/       # granted capability set (§6)
  package.json          # private: true (F01); scripts: dev, build (turbo-wired)
```

### 4.2 IPC surface (complete list — anything not here is not granted)

| Direction | Name | Payload | Notes |
|---|---|---|---|
| JS → Rust | `set_badge` | `{count: number}` | Tray badge/tooltip; 0 clears |
| JS → Rust | `set_recent_approvals` | `{items: {label, deepLink}[] ≤5}` | Tray menu section (§3.3) |
| JS → Rust | `auth_start_device_flow` | `{}` → stream of state events | Rust drives F05 polling; returns no tokens |
| JS → Rust | `auth_get_session` | `{}` → `{state: 'signedIn'\|'signedOut', workspace?}` | Plus short-lived bearer for direct mode **only if** §9-1 lands on webview-side calls |
| JS → Rust | `auth_sign_out` | `{}` | Keychain clear + revocation per F05 |
| JS → Rust | `router_ready` | `{}` | Unblocks cold-start deep-link delivery |
| JS → Rust | `open_external` | `{url}` | System browser; https-only allowlist |
| Rust → JS | `deep-link` | `{path, query}` | Normalized from `deepwork://` (§3.5 map) |
| Rust → JS | `auth-state` | device-flow state machine events (§3.6) | `codeReady{userCode, verificationUri, expiresAt}` · `waiting` · `expired` · `denied` · `success` |
| Rust → JS | `update-status` | `{state: 'available'\|'downloaded'\|'error', version?}` | Drives toast + settings badge |
| Rust → JS | `window-shown` / `window-hidden` | `{}` | Webview switches poll cadence (§3.2) |

### 4.3 Deep-link grammar

`deepwork://<kind>/<...>` with `kind ∈ {task, approval, agent}` per the §3.5 table. `<source>` uses the F04 registry source id/slug (stability caveat = F07 §9-2, shared).

### 4.4 Desktop settings (stored via Tauri, not webview localStorage)

```jsonc
{
  "connectionMode": "direct" | "proxy",   // §9-1; proxy requires serverUrl
  "serverUrl": "https://…",               // apps/server base (proxy mode)
  "launchAtLogin": false,
  "startHidden": false,
  "closeToTray": true,
  "notifications": { "runCompleted": true, "inputRequested": true, "runFailed": true },
  "updateChannel": "stable",
  "globalShortcut": "CmdOrCtrl+K"
}
```

### 4.5 Updater manifest

`latest.json` per the Tauri updater static-JSON format (version, platform → artifact URL + signature), attached to each `desktop-v*` GitHub Release; URL pinned in `tauri.conf.json`.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Deep link while signed out | Queue → login → replay (§3.5); queue survives the auth roundtrip, not app restart |
| Deep link to unknown/foreign-org entity | F07 404-in-chrome + org-switch hint; never a blank window |
| Two rapid deep links | Last-writer-wins navigation; earlier one dropped with a toast |
| Device code expires unwatched overnight | State 4 (§3.6); no infinite polling (F05 edge table) |
| Keychain locked/unavailable (e.g. Linux without a secret service) | Sign-in blocked with explicit remediation copy; API-key proxy mode remains usable → §9-3 |
| Update downloaded, user mid-stream | Restart deferred until user confirms; no auto-restart (§3.7) |
| Updater manifest unreachable / signature invalid | Fail closed: no install, current version keeps running, manual link surfaced (§3.9) |
| OS webview missing (Windows without WebView2 runtime) | Installer bootstraps/prompts per Tauri defaults; verified in the Windows QA pass (§8-12) |
| Tray unsupported (some Linux DEs) | App still opens as a normal window; badge features degrade; documented limitation |
| Global shortcut conflict | Silent degrade to in-app binding + settings notice (§3.8) |
| Laptop sleep/resume | Streams rejoin via resumable `Last-Event-ID` replay ([03 §5](../03-ui-spec.md)); badge poll fires immediately on resume |
| Multiple monitors / display removed | Window-state restore validates geometry (§3.8) |

## 6. Security & privacy

- **No secrets in the webview.** Device-flow tokens live in the OS keychain, written and read Rust-side (F05 acceptance 6); the JS context receives session *state*, and a raw bearer only if §9-1 resolves to webview-direct calls — in which case it is held in memory, never persisted to webview storage. There is no Node runtime in Tauri; there are no Node-side secrets by construction.
- **CSP (bundled assets):** `default-src 'self'`; `connect-src` limited to the configured `apps/server` origin + `api.smith.langchain.com` + `*.langgraph.app` (+ loopback in explicit local mode, mirroring F05's local-mode carve-out); no remote script/style/frame sources. Agent-generated content rendering rules are unchanged from web (untrusted-boundary principle, [02 §10](../02-architecture.md)).
- **IPC allowlist = §4.2, exactly.** Tauri capabilities granted: tray, notification, deep-link, updater (research 05's confirmed set) + the §4.2 custom commands + https-only opener; **no** shell-exec, no fs access, no arbitrary-URL webview navigation. Any plugin added via §9-3 extends this list explicitly in `capabilities/`.
- `open_external` validates `https:` and refuses `deepwork://` (no self-referral loops); deep-link input is parsed against the §4.3 grammar and route-guarded by F07 — malformed links cannot address IPC.
- Update integrity: updater signature verification (public key pinned in config) + platform code-signing/notarization (§3.7); fail-closed on mismatch.
- Notifications show task titles only (plain text, per F07's title-rendering rule) — no argument payloads or diff content in OS notification centers.
- Tray recent-items labels are plain text, length-capped; same untrusted-content treatment.

## 7. Acceptance criteria

1. `apps/desktop` builds from the `apps/web` static export on macOS, Windows, Linux; installers ship from the `desktop-v*` CI workflow with signed (and on macOS notarized) artifacts + `latest.json`.
2. Device flow signs in end-to-end on a Tauri build; tokens present in OS keychain, absent from webview storage — F05 acceptance 6 verified on all three OSes; expiry → state 4 → fresh-code retry works.
3. Tray badge equals `useApprovalsCount().total` within one poll interval, window visible or hidden; deciding an approval updates the badge without restart.
4. A run-completed and an input-requested event each raise exactly one native notification (per settings toggles); clicking it opens the correct screen via the §3.5 map.
5. `deepwork://task/...`, `deepwork://approval/...`, `deepwork://agent/...` resolve correctly from cold start *and* running instance; signed-out replay works; no auth-guard bypass (F07 §6).
6. Updater: an old version detects, downloads, and installs a new release only after user confirmation; a tampered signature is rejected and the app keeps running.
7. Global ⌘K/Ctrl+K summons the window + palette from any focused app; conflict degrades per §3.8.
8. Window state restores across restarts incl. the removed-monitor case; close-to-tray keeps polling (verified by badge change while hidden); launch-at-login + start-hidden honored.
9. Offline launch renders the shell with F07 degraded states — no white screen; updater failure is non-blocking with manual fallback visible.
10. Capability audit: granted Tauri capabilities and IPC commands match §4.2/§6 exactly (checked in review); CSP blocks a canary remote script in a test page.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Resolve §9-1 (data path: direct CORS probe vs bundled sidecar vs proxy-only) with F05/F28 — spike, memo, decision-log entry | — | Decision recorded; §4.4 `connectionMode` semantics fixed |
| 2 | Scaffold `apps/desktop` (Tauri v2, `frontendDist` → web export); wire `apps/web` `output:'export'` build into turbo | F01 placeholder | `tauri dev` renders the shell in fixtures/demo mode on all 3 OSes |
| 3 | PR-CI debug-build smoke job (one OS) | 2 | Export/config drift fails PRs |
| 4 | Process model: single instance, close-to-tray, show/hide events, hidden-cadence IPC | 2 | AC 8 (tray-poll half); §9-3 mechanisms chosen + capability list updated |
| 5 | Window-state persistence + monitor-geometry validation | 4 | AC 8 restore cases |
| 6 | Device-flow screen + Rust flow driver + keychain custody (joint with F05 task 13) | 2, 1 | AC 2; §3.6 states all reachable in a stub-server test |
| 7 | Tray icon, badge, menu (incl. recent approvals + signed-out variants) fed by `set_badge`/`set_recent_approvals` | 4, F10 selector | AC 3 |
| 8 | Native notifications: F19 event mapping, settings toggles, click-through to deep links | 7, F19 taxonomy | AC 4 |
| 9 | Deep links: scheme registration, cold-start buffer, running-instance forwarding, F07 router bridge, signed-out queue | 4, 6 | AC 5 |
| 10 | Global shortcut + launch-at-login + desktop settings surface (§4.4) | 4 | AC 7, AC 8 (launch half) |
| 11 | Updater integration: manifest, signature keys, check/download/confirm-restart UX | 2 | AC 6 against a staged release |
| 12 | `desktop-release` CI workflow: 3-OS matrix, signing + notarization secrets, artifact + `latest.json` publish | 11, §9-2 keys | AC 1; dry run produces installable artifacts |
| 13 | Cross-OS QA: webview drift matrix, offline, WebView2 bootstrap, tray-less Linux, sleep/resume | 2–11 | §5 table rows each have a test or documented manual check |
| 14 | Security review: capability/IPC audit, CSP canary, deep-link fuzz, token-absence check | 6–11 | AC 10; §6 rows verified |

## 9. Open questions

1. **Packaging/data path** (= F05 §9-11): bundled `apps/server` sidecar (Python packaging cost) vs user-pointed shared instance vs direct-from-desktop with device-flow bearer — direct mode hinges on unverified CORS/bearer acceptance from a Tauri origin on `api.smith.langchain.com` and `*.langgraph.app` (O-001/O-002 adjacent). Task 1 resolves before anything else lands.
2. **Signing costs & custody:** Apple Developer Program enrollment (paid, account owner TBD), Windows Authenticode route (OV cert vs Azure Trusted Signing), Tauri updater private-key custody/rotation policy — all unresolved; blocks task 12 only.
3. **Unverified Tauri mechanisms** (research 05 confirms only updater/notification/deep-link/tray): global-shortcut registration, window-state persistence, autostart, single-instance enforcement, and the exact keychain/secret-storage plugin (incl. Linux secret-service behavior). Verify against Tauri v2 plugin docs at M4 start; each addition extends the §6 capability list explicitly.
4. **Update channels:** is a `beta` channel wanted for v1.x dogfooding, and is differential updating real (research 05 open question) or are full ~5 MB-installer-class artifacts fine forever?
5. **Desktop event transport** (with F19): does desktop stay poll/stream-derived (§3.4) or subscribe to `apps/server` push fan-out? Depends on F10 §9-Q4 (webhooks on `interrupted`) and on 02 §7 vs research 05 wording (see contradictions note in review).
6. **Exact bundler targets** per OS (dmg/NSIS/MSI/AppImage/deb/rpm set) and macOS universal-vs-dual binaries — proposal in §3.7 pending verification.
7. **Per-OS tray badge affordance** (macOS title text vs Windows overlay vs Linux tooltip-only) — pick at impl, keep §3.3 semantics.
8. **Minimum OS / webview baselines** (WebView2 evergreen, macOS floor → WKWebView features, WebKitGTK version) → browserslist config for `apps/web`; is Linux a v1 release *blocker* or best-effort tier?
9. **⌘K double-duty:** same chord as the in-app palette (F07 §3.7) — when the window is already focused, does the global registration shadow the web listener? Needs a focus-aware suppression rule at impl.
10. **Remote-instance mode** (webview → self-hosted web deployment, option A of §3.1) as a post-v1 feature for teams already running `apps/web` — worth a backlog entry?

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| §9-1 lands on "bundle `apps/server`" — Python sidecar packaging balloons M4 scope | Med | High | Task 1 is first; proxy-to-user-run-server mode is a complete fallback that ships regardless; direct mode remains a fast-follow |
| Notarization/signing pipeline stalls first release (cert lead times, CI secrets) | Med | Med | Start §9-2 procurement at M3; unsigned dev builds unblock QA; Linux/updater signing has no external dependency |
| Webview drift breaks the app on one OS (esp. WebKitGTK) | Med | Med | Browserslist floor + 3-OS CI smoke (task 3) + QA matrix (task 13); Linux tier decision in §9-8 caps the blast radius |
| P-005 reversal reopens the static-export question (F01 §5) | Low-Med | High | Inherited constraint documented in both specs; if reversed pre-M0 the sidecar decision merges into §9-1 |
| Poll-derived notifications feel slow (≤60 s hidden) vs push-quality expectations | Med | Low-Med | Honest cadence copy in settings; F19 §9-5 transport upgrade path; open streams already deliver instantly |
| Tray/deep-link plugin behavior diverges across Linux DEs | Med | Low | Degrade-gracefully rules (§5); documented limitations; AppImage as the single supported Linux format initially |
