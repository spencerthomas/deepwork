# Desktop application agent instructions

These instructions apply to `apps/desktop` in addition to the repository root guidance.

## Host-only boundary

`apps/desktop` is a Tauri host for one exact trusted hosted origin of the canonical web application. It owns desktop integration, not a second product implementation.

- Load the reviewed trusted web origin and reuse its SDK contracts, UI tokens, routes, normalized state, and fixture/live application behavior. Do not ship a separate bundled product UI in v1.
- Keep business rules, Agent Server clients, HITL normalization, task reducers, and product components out of Rust commands and desktop-only TypeScript.
- Expose desktop behavior through small, typed host adapters that the web application can capability-detect.
- A web fallback or explicit unavailable state is required for every desktop adapter used by shared product code.

Desktop-only ownership includes window lifecycle, deep-link registration, system-browser auth handoff, tray and dock behavior, native notifications, secure storage for a scoped revocable Deep Work bootstrap/device key, updater integration, OS file-picker mediation, and platform packaging.

## Security boundary

- Use the narrowest Tauri capability and command allowlists. Disable unused plugins and shell capabilities.
- Set a restrictive content security policy. Do not allow arbitrary remote navigation, script injection, shell arguments, file paths, or deep-link payloads.
- Store only a scoped, revocable Deep Work session bootstrap/device key in approved OS secure storage. Never store LangSmith, LangGraph, GitHub, sandbox, model-provider, source, or other reusable provider credentials in Tauri or the webview.
- Validate and normalize every deep link, notification action, file path, URL, and command payload on both sides of the IPC boundary.
- Restrict updater signing keys to release infrastructure. Verify signatures and channel before applying an update; expose recoverable failure behavior.
- Redact secrets and user content from crash reports, native logs, window titles, notifications, and tray previews.

## Lifecycle and parity

- Treat suspend, resume, backgrounding, window close, network handoff, and sleep/wake as normal states. Disconnect streams intentionally and recover through the application API's advertised contract; Tauri never owns or constructs an upstream protocol-v2 cursor.
- Tray counts and notifications derive from the same normalized task and approval state as the web UI. Do not maintain a parallel authoritative store.
- Deep links resolve through normal route authorization and source selection. If the target source, task, or permission is unavailable, show a recoverable landing state.
- Fixture qualification uses an explicit local trusted origin and must work without credentials or external/provider traffic. Local loopback calls to the fixture API/worker/object stack are expected. Native actions in fixture mode must be labeled and must not contact external services.
- Use mutually exclusive host profiles. Release builds allow exactly one reviewed
  HTTPS scheme/host/port and reject loopback, development, wildcard, and arbitrary
  navigation. Fixture qualification allows exactly one issue-derived loopback
  origin, is visibly non-production, and cannot be packaged or signed with the
  release profile. Test redirects, new-window requests, top-level navigation,
  custom schemes, and system-browser handoff in both profiles.
- A desktop-only enhancement must not change the meaning of a shared action or make the browser flow invalid.

## Accessibility and platform behavior

- Preserve web keyboard order, focus visibility, zoom, contrast, reduced motion, and screen-reader semantics inside the host.
- Native notifications and tray menus must have clear labels and must not be the only way to reach a task or approval.
- Support keyboard navigation and platform conventions for menus, window controls, deep links, and global shortcuts. Make global shortcuts configurable and avoid collisions with OS or assistive-technology shortcuts.
- Test minimum supported window dimensions, high DPI, multiple displays, system theme changes, reduced motion, and offline resume.

## Verification and release

- Pin stable Rust with `rust-toolchain.toml`; document edition and minimum supported Rust version. Run rustfmt, Clippy with warnings denied in CI, Cargo tests, and the accepted dependency/license/security audit. Keep Tauri Rust modules organized by typed host capability rather than product feature logic.
- Contract-test each host adapter with success, denial, unavailable, malformed-input, and OS-error results.
- Exercise signed development or staging packages on every supported OS; a browser build is not desktop verification.
- Test notification click-through, deep-link cold and warm start, expired session, locked keychain, denied notification permission, offline launch, sleep/wake reconnect, tray count recovery, and updater rollback behavior.
- Keep OS-specific code isolated behind adapters and document any platform exception in the owning feature plan.
