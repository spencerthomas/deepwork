---
feature_id: DW-SURF-002
title: Tauri desktop hosting, deep links, notifications, and updates
release: v1
status: proposed
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [desktop, web, api, security]
surfaces: [desktop]
runtime_scopes: [any]
source_refs: [SRC-DW, SRC-LC, SRC-LCJS, SRC-TAURI, SRC-RUST]
evidence_pins:
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  langchainjs: ee76ea0
dependencies: [DW-FND-002, DW-FND-003, DW-FND-004, DW-FND-005, DW-OPS-002, DW-SURF-001]
contract_gates: [SPIKE-DESKTOP-001]
optional_contract_gates: [SPIKE-AUTH-001, SPIKE-STREAM-001]
last_reviewed: 2026-07-23
---

# Tauri desktop hosting, deep links, notifications, and updates

## User outcome

A desktop user receives the same trusted Deep Work product, task state, and FastAPI `/api/v1` contract as web/PWA, with narrowly scoped native value: system-browser sign-in handoff, authorized deep links, native notifications, tray attention state, a permitted global shortcut, secure bootstrap storage, and signed updates. Desktop never turns arbitrary web content into privileged code or creates a second source of product truth.

This plan is proposed and blocked on `SPIKE-DESKTOP-001`. It is not implementation-ready until that spike proves hosted-origin navigation, cookie/session and system-browser authentication, service-worker interaction, stream foreground/background behavior, deep-link registration, notification delivery, signing/notarization, updater rollback, and native accessibility on each supported platform. If it fails, desktop is held while responsive web/PWA ships.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| The product vision requests a desktop experience with tray, deep links, notifications, and updater but does not define a host model. | Internal intent at `06f0515` | High | Resolve host/session/security behavior in a bounded spike before building native feature breadth. |
| Next.js 16 web/PWA, TypeScript SDK/UI, FastAPI/Postgres, and Tauri v2 are the proposed shared stack. | Proposed architecture | Medium until review | Tauri hosts/bridges; it does not fork React/domain/business logic or Python runtime ownership. |
| A trusted hosted Next.js origin minimizes duplicate delivery but webview cookies, external auth, service workers, navigation, offline state, and platform policies need live proof. | Architecture inference / external platform behavior | Medium | Make trusted hosted origin the proposal, gated entirely by `SPIKE-DESKTOP-001`. |
| Browser stream disconnect does not cancel a server-side run. | Audited LangChain contract | High | Window hide/sleep/close-to-tray manages client resources only; explicit cancel uses the normal mutation service. |
| Native notifications/deep links can be stale or arrive after permission/session changes. | Platform security fact | High | Payloads are hints with opaque application IDs and always reauthorize through FastAPI. |
| Tauri privileged commands and navigation expand the attack surface. | Security fact | High | Use least-privilege capabilities, exact origins/routes, typed commands, and no shell/arbitrary opener. |

## Scope, ownership, and non-goals

### In scope

- Tauri v2 applications for macOS, Windows, and Linux only where prerequisites, signing/distribution, and qualification pass.
- Pinned stable Rust toolchain, recorded edition/MSRV, rustfmt, Clippy, Cargo tests, dependency/license/advisory audit, generated bridge checks, and package-level commands consistent with the monorepo contract.
- Proposed host model: load one exact trusted hosted Next.js origin over TLS, using the same `packages/domain`, browser-safe `packages/sdk`, and FastAPI `/api/v1` as browsers.
- Development/fixture qualification loads an explicit loopback trusted origin backed by the isolated product-demo stack. “No network” means no external/provider traffic; loopback API/worker/object/telemetry traffic is expected.
- System-browser authentication and verified application callback/device binding; no credential entry into privileged native code beyond scoped session bootstrap.
- Deep links `deepwork://task/<application-task-id>` and `deepwork://approval/<application-task-id>` with strict grammar, opaque IDs, authorization, single-instance routing, and safe default behavior.
- Native notifications sourced from application notification events; tray icon/count plus open/hide/quit and needs-review navigation.
- Global command-palette shortcut only when the user enables it and the OS grants required permission.
- OS secure storage for device bootstrap/session material only; server-side provider credentials remain in FastAPI-managed secret storage.
- Signed updates, channels, release notes, minimum-supported-version policy, controlled restart, rollout/rollback telemetry, and kill switch.
- Secure external-link handoff to the system browser and platform accessibility alternatives in the main window.

### Ownership

- Desktop owns Tauri configuration/capabilities, packaging, OS integration, deep-link parsing, single-instance behavior, secure native storage, updater, and platform qualification.
- Desktop also owns `rust-toolchain.toml`, Cargo dependency/feature policy, capability-oriented Rust modules, bridge generation/tests, and exact platform reproduction commands. Rust code does not own product-domain logic.
- Web owns hosted Next.js UI, routing, responsive layout, service-worker boundaries, and the shared command palette.
- FastAPI/Postgres own session/device binding, `/api/v1`, notification state, deep-link target authorization, and tray-count source data.
- `DW-OPS-002` owns notification categories/in-app records; desktop consumes them and must not become their source of truth.
- `DW-SURF-001` owns web/PWA fallback and responsive shell behavior; desktop depends on it one-way.
- Security approves trusted-origin policy, native capability list, auth handoff, signing keys, updater infrastructure, and hostile-content isolation.

### Non-goals

- Bundling Python/LangChain/deepagents inside the desktop client, running a local privileged agent daemon, or storing upstream API/GitHub credentials in Tauri.
- A desktop-specific REST API, forked domain model, forked React application, or native mobile behavior.
- Arbitrary navigation in the privileged webview, arbitrary URL/file/shell commands, generic filesystem access, localhost proxying, or plugin marketplace.
- Treating tray count or notification payload as authoritative task status.
- Shipping an unsigned/unnotarized updater, supporting a platform whose release prerequisites are unavailable, or blocking web/PWA v1 on desktop qualification.

## Primary journeys

### First launch and authentication

1. The signed application verifies bundled configuration and opens only the exact trusted hosted origin.
2. If signed out, Tauri opens the system browser to a FastAPI-created one-use authentication/device-binding transaction.
3. The verified `deepwork://auth/callback` carries only a short-lived one-use code/state, which native code validates and exchanges through FastAPI.
4. A scoped desktop session bootstrap is stored in the OS secure store; upstream credentials remain server-side.
5. The hosted app loads session/workspace/source context through the same `/api/v1` and SDK as web.

### Deep link or native notification

1. The OS delivers a task/approval deep link or the user selects a notification.
2. Tauri parses the strict scheme/path/opaque application ID and rejects extra host/query/fragment input.
3. If signed out, it retains a bounded opaque target and starts authentication; it never caches task content.
4. FastAPI authorizes the target against current actor/workspace/source state and returns a safe route.
5. The hosted app loads current durable state; stale notification copy is discarded.

### Tray attention and reconnect

1. Application notification state reports the actor's needs-review count.
2. Tauri displays a bounded count and accessible equivalent in the main window.
3. Resolving an approval on web/PWA updates server state; desktop refresh/realtime reconciliation converges.
4. Hiding or losing network releases client stream resources without cancelling active runs.
5. Reopening reauthenticates and resumes/hydrates through `DW-FND-004`.

### Signed update and rollback

1. The updater checks an exact HTTPS endpoint/channel using signed metadata and the installed platform/architecture/version.
2. The user sees version, release notes, restart impact, and minimum-version constraints.
3. Downloaded artifact signature/checksum/platform identity are verified before installation.
4. The app preserves safe navigation/draft state according to policy, installs, restarts, and reports success.
5. Failed health or staged rollout can pause the channel and direct users to the prior signed compatible release when platform policy supports rollback.

## Complete state matrix

| State | Required desktop behavior | Recovery or transition |
|---|---|---|
| First launch loading | Verify app/config/trusted origin before privileged webview navigation. | Open sign-in or authorized app; fail closed on invalid config. |
| Empty attention/notification state | Show an authorized zero state rather than an unresolved loading value; the main application remains usable. | Refresh from application notification state when an event occurs. |
| Hosted origin unavailable | Show native connectivity page without task content or arbitrary browse field. | Retry or open ordinary web app in system browser. |
| Hosted origin mismatch/redirect | Block in privileged webview, record sanitized security event. | Open allowlisted external URL in system browser only when explicitly safe. |
| Signed out | Main window offers system-browser sign-in; no protected tray count/content. | Complete verified handoff. |
| Auth handoff pending | Show expiry/cancel/restart without secrets. | Callback, timeout, or retry. |
| Auth callback invalid/stale/replayed | Reject and clear one-use transaction. | Start a new sign-in. |
| Session expired | Clear protected webview/native state and bootstrap as policy requires. | Reauthenticate; preserve only bounded opaque target. |
| Permission revoked | Hide cached protected detail/count and reject target. | Switch workspace/source or request access. |
| Offline cold launch | Native shell explains connectivity; hosted app is not presented as live. | Retry/open web later. |
| Offline warm launch | Cached web shell may show only `DW-SURF-001`-approved labelled read state. | Reconnect before mutations. |
| Window hidden/backgrounded | Pause/release client resources; do not cancel runs. | Restore and resume/hydrate. |
| Reconnecting | Preserve shell/focus, show bounded progress. | Reauthorize and use verified stream/full hydration. |
| Valid task deep link | Authorize current actor, source, and task before navigation. | Open current task route. |
| Invalid/malformed deep link | Reject payload and open default Tasks route without reflection. | Explain invalid link only if useful. |
| Signed-out deep link | Store opaque destination briefly, never content. | Authenticate then authorize. |
| Unauthorized/deleted target | Do not reveal existence/content beyond safe error. | Open Tasks or permitted workspace. |
| Duplicate deep link / second instance | Route once through single-instance handler. | Focus existing window; idempotent navigation. |
| Notification permission denied | Native notification stops; in-app inbox remains complete. | Enable in OS/app settings. |
| Notification stale | Ignore payload state and fetch current authorized entity. | Show resolved/current state. |
| Tray count loading | Show neutral state, not zero. | Converge after authorized query. |
| Tray source disconnected | Retain safe last count only if labelled; main app shows source/connectivity. | Reconnect and refresh. |
| Shortcut permission/conflict | Explain and leave command palette available inside app. | Choose another shortcut or enable OS permission. |
| Update check loading | Non-blocking status; current version stays usable unless minimum policy applies. | Continue/check later. |
| No update | Record safe check time. | Continue. |
| Update available | Show version, notes, channel, restart requirement. | Install/defer according to policy. |
| Download interrupted | Keep installed version intact and discard/validate partial artifact. | Retry. |
| Signature/checksum invalid | Reject artifact, retain installed version, raise security signal. | Pause channel/support; never bypass. |
| Update install/restart failure | Preserve/recover previous signed version where supported. | Rollback/support; do not corrupt user data. |
| Client/API incompatible | Block unsafe mutations and require compatible signed update or browser fallback. | Update or open supported web/PWA. |
| High zoom/small window | Hosted responsive shell reflows; native chrome remains operable. | Resize without losing route/draft. |

## Proposed interfaces

```ts
type DeepLinkTarget =
  | { kind: "task"; applicationTaskId: string }
  | { kind: "approval"; applicationTaskId: string }
  | { kind: "auth-callback"; transactionId: string; oneTimeCode: string };

interface DesktopCapabilityManifest {
  platform: "macos" | "windows" | "linux";
  appVersion: string;
  notifications: boolean;
  tray: boolean;
  globalShortcut: boolean;
  secureStorage: boolean;
  updater: boolean;
}

interface DesktopBridge {
  getCapabilities(): Promise<DesktopCapabilityManifest>;
  beginSystemBrowserAuth(transactionUrl: string): Promise<void>;
  showMainWindow(target?: DeepLinkTarget): Promise<void>;
  setTrayAttention(count: number): Promise<void>;
  openAllowlistedExternalUrl(url: string): Promise<void>;
  checkForSignedUpdate(): Promise<UpdateStatus>;
}
```

Native commands are separately allowlisted and validate typed inputs. There is no command for arbitrary shell, command execution, path read/write, HTTP fetch, provider credential, or unrestricted URL open.

Proposed application-service seams:

- `POST /api/v1/desktop/auth-transactions` creates one-use, device-bound system-browser handoff state after `SPIKE-DESKTOP-001`/`SPIKE-AUTH-001` acceptance.
- `POST /api/v1/desktop/auth-transactions/{id}/exchange` validates callback state and returns a scoped desktop session bootstrap.
- `POST /api/v1/deep-links/resolve` accepts parsed kind/opaque ID and returns only an authorized application route.
- Notification/tray state is read through `DW-OPS-002` `/api/v1` contracts, never directly from LangSmith.
- Next.js sees `DesktopCapabilityManifest` at composition time and keeps the same query/mutation/stream services as PWA.

## Runtime capability and fallback

- Classic LangSmith Deployment remains the public source baseline behind FastAPI/SDK; Tauri does not call provider endpoints directly.
- `SPIKE-STREAM-001` governs reconnect after window hide/sleep/offline. Native lifecycle signals can reconnect the application stream, but Tauri never owns an upstream protocol cursor or changes the server adapter's recovery semantics.
- MDA/Fleet remain capability-detected through their owning adapters; no privileged desktop route bypasses their gates.
- If hosted-origin cookie/session or auth handoff cannot be made safe and reliable, `SPIKE-DESKTOP-001` fails and desktop is not shipped; responsive web/PWA is the complete fallback.
- If native notification, tray, global shortcut, or updater is unavailable on a platform, its manifest value is false and the equivalent in-app/web route remains available.
- If a signed update is unavailable/incompatible, the app can direct the user to the supported browser origin; it never installs unsigned code.

## Persistence and security

- OS secure storage holds only a scoped, revocable desktop bootstrap/session token and device identifier; raw LangSmith/GitHub credentials remain encrypted behind FastAPI.
- Tauri capabilities are least privilege per platform/window. CSP, exact origin and navigation allowlists, TLS, certificate/host policy, permission scopes, and command allowlists are release-blocking.
- The privileged webview cannot navigate to provider docs, task links, tool URLs, OAuth pages, arbitrary redirects, `file:`, `data:`, custom schemes other than parsed app callbacks, or local network content. Approved external pages open in the system browser.
- Deep links use opaque application IDs, strict length/character limits, no task text/repository URL, one-use auth state, and current authorization on resolve.
- Native notification payloads follow PWA minimal-content policy; tray stores no protected list/content.
- Signing/notarization keys remain in protected release infrastructure with separation of duties, rotation, revocation, audit, and no pull-request availability.
- Updater metadata/artifacts are signed, version/architecture/channel constrained, replay/downgrade protected according to accepted policy, and checked before install.
- Logs redact session tokens, deep-link one-time codes, URLs/query strings, notification content, and webview payloads.

## Responsive and accessible behavior

- The hosted Next.js shell follows `DW-SURF-001` at small windows, high zoom, text expansion, reduced motion, keyboard-only use, and forced colors.
- Native menus/tray are supplementary. Every tray action, count, notification target, updater action, and shortcut setting has a labelled keyboard/screen-reader equivalent in the main window.
- Deep-link/auth/update errors move focus to a concise heading/action in the main window and do not rely on transient native toast alone.
- Window show/hide and update restart restore logical focus and safe navigation where authorized.
- Global shortcut is user-configurable, conflict-aware, and not required to access the command palette.
- Platform accessibility qualification includes VoiceOver, Narrator, and an accepted Linux screen-reader environment where that build is supported.

## Metrics and guardrails

- Privileged webview navigation outside the exact trusted origin: zero.
- Native bridge commands beyond reviewed manifest: zero; hostile-input contract suite passes 100%.
- Deep-link-to-authorized-current-target success: target above 99%; rejected/stale/unauthorized outcomes segmented safely.
- Tray needs-review convergence after reconnect/resolution within accepted p95, with zero protected count when signed out.
- Signed update success, deferral, download failure, signature rejection, restart health, and rollback by platform/channel.
- Credentials/provider tokens in native store/logs/notifications/deep links: zero.
- Guardrails: no unsigned update, no arbitrary opener/shell/filesystem/fetch, no background disconnect-as-cancel, no stale notification as authority, and no desktop launch blocking web/PWA release.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-002` for shared shell/UI and native capability composition.
- `DW-FND-003` for `/api/v1`, Postgres device/session binding, authorization, and credential boundary.
- `DW-FND-004`/`DW-FND-005` for resume, stable identity, status, and source capability.
- `DW-OPS-002` for application notification/tray event and preference semantics. Dependency is one-way from desktop to Operations.
- `DW-SURF-001` for responsive hosted app, offline cache policy, service-worker behavior, and web/PWA fallback.
- `SPIKE-AUTH-001` verifies provider/application authentication assumptions.
- `SPIKE-STREAM-001` verifies lifecycle reconnect/full hydration.
- `SPIKE-DESKTOP-001` must capture exact Tauri/WebView/platform versions and prove trusted hosted origin, cookie/session, system-browser auth callback, service worker, offline state, navigation blocking, deep links, notifications, tray/single instance, shortcut, signing/notarization, updater signature/rollback, and assistive-technology behavior on each proposed platform.
- Rust/Tauri review must accept stable toolchain, edition/MSRV, capability manifest, dependency/advisory policy, bridge schema, local qualification origin, and signing boundary before a platform build is release-eligible.

### Proposed rollout

1. Run threat model and `SPIKE-DESKTOP-001` in a non-production app identity against fixture `/api/v1`.
2. Ship internal macOS build with trusted-origin host and system-browser auth only; no notification/tray/updater privileges beyond development signing.
3. Add parsed deep links and native notifications/tray one capability at a time with hostile-input tests.
4. Add signed staged updater, kill switch, compatibility checks, and rollback rehearsal.
5. Qualify Windows, then Linux only when signing/distribution/accessibility prerequisites pass; unsupported platforms use web/PWA.
6. Invite a small cohort behind desktop release channel flags after web/PWA reaches acceptance.

### Rollback

- Server-side flags disable deep links, notifications, tray updates, shortcut, or update channel independently; hosted web remains available.
- A channel can be paused immediately. Users remain on the installed signed version or receive the prior compatible signed artifact where platform policy permits.
- If the desktop security boundary is uncertain, revoke desktop sessions/device bindings, stop update distribution, and direct users to browser/PWA. Preserve application data and audit evidence.

## Executable acceptance scenarios

```gherkin
Scenario: Clean desktop sign-in stores no provider credential
  Given a newly installed signed desktop build
  When the user signs in through the system browser and verified app callback
  Then Tauri stores only a scoped revocable desktop bootstrap in OS secure storage
  And LangSmith and GitHub credentials remain server-side
  And the hosted Next.js app loads the same /api/v1 SessionContext as web

Scenario: Hostile navigation remains outside privileged context
  Given the trusted hosted app renders an untrusted tool link and redirect
  When the user activates it or the page attempts top-level navigation
  Then the privileged webview does not navigate
  And only an explicitly allowlisted external URL may open in the system browser
  And no arbitrary URL, file, fetch, or shell native command exists

Scenario: Signed-out deep link is bounded and authorized
  Given the app is signed out and receives deepwork://task/<opaque-id>
  When authentication completes
  Then only the bounded opaque target survives the handoff
  And FastAPI authorizes it against the current actor/workspace/source
  And unauthorized task content is never displayed

Scenario: Tray converges without becoming authoritative
  Given desktop shows two needs-review items
  When one approval is resolved in the web app
  Then application notification state updates
  And desktop tray converges to one after reconnect/refresh
  And opening the tray always loads current authorized task state

Scenario: A tampered update cannot install
  Given an update artifact or metadata has an invalid signature or checksum
  When the updater validates it
  Then installation is rejected
  And the current signed version remains intact
  And the channel raises a security signal without offering a bypass

Scenario: Failed desktop qualification does not block v1 web
  Given SPIKE-DESKTOP-001 cannot prove safe hosted-origin authentication on one platform
  When release scope is reviewed
  Then that desktop platform remains disabled
  And responsive web/PWA retains the complete product journey
  And no weaker desktop auth or credential storage fallback is introduced
```
