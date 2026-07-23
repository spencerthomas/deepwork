---
feature_id: DW-ONB-001
title: Authentication, session, workspace, and demo entry
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [application-platform, web, desktop, security]
surfaces: [web, pwa, desktop, api]
runtime_scopes: [classic, mda, fleet, local, fixture]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
evidence_pins:
  frontend: 8866d39
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
dependencies: [DW-FND-002, DW-FND-003, DW-FND-005]
contract_gates:
  - SPIKE-AUTH-001
  - SPIKE-AUTH-002
last_reviewed: 2026-07-22
---

# Authentication, session, workspace, and demo entry

## User outcome

A person can enter Deep Work safely through a real LangSmith-backed session or a clearly labelled fixture-only demo, select the organization and workspace they intend to use, and return without repeating setup. The interface never suggests that OAuth, team access, or a connected runtime is available until that capability has been verified for the active account and source.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype sign-in screen offers OAuth, API key, workspace selection, and a desktop-device-flow message, but all paths only navigate to `/tasks`. | Prototype evidence at `8866d39`; simulated | Preserve the interaction intent, not its implied contracts. |
| The vision promises LangSmith OAuth with API-key fallback and org/workspace choice. | Internal intent at `06f0515`; unverified externally | OAuth remains gated by `SPIKE-AUTH-001`; API key is the deterministic launch fallback. |
| Different LangSmith control-plane and deployment calls can require different endpoints and headers. | Documented in parts at `7b9215d`; exact cross-plane matrix unknown | Centralize credentials and header selection in the Python application service. Do not let UI code invent headers. |
| v1 needs durable identity, source registry, onboarding progress, and revocation state. | Product requirement; inferred | Use Postgres for Deep Work application state even though LangSmith remains authoritative for runtime data. |

This plan cannot become implementation-ready until the two authentication spikes produce accepted fixtures and a reviewed credential matrix.

## Scope and ownership

### In scope

- Web OAuth authorization-code flow with PKCE if the live LangSmith flow supports the required scopes and audiences.
- Desktop device authorization only if verified; otherwise open the web sign-in flow in the system browser.
- API-key entry as the complete v1 fallback.
- Organization and workspace discovery, selection, switching, and revoked-access handling.
- A server-managed Deep Work session shared by the Next.js web/PWA and the Tauri shell.
- A fixture-only demo session with no outbound runtime, control-plane, GitHub, or notification mutations.
- Session expiry, sign-out, credential replacement, and device/session visibility sufficient for v1.

### Out of scope

- Deep Work-owned passwords, social login, SCIM, or enterprise RBAC administration.
- Native mobile authentication; mobile v1 is responsive web, with installation
  only on `SPIKE-PWA-001`-qualified browser cells.
- Treating one LangSmith API key as proof of access to every deployment.
- Persisting raw credentials in browser local storage, URLs, logs, traces, analytics, or sandbox state.

### Ownership

- The Python 3.12 FastAPI application service owns OAuth callbacks, API-key validation, encrypted credential references, session issuance, org/workspace discovery, CSRF protections, and audit events.
- Postgres owns users, actors, sessions, selected workspace, onboarding progress, encrypted-secret references, and revocation metadata.
- Next.js owns the sign-in, workspace picker, session-expired recovery, and demo disclosures.
- Tauri owns secure native storage for its session token and system-browser handoff; it calls the same FastAPI API as the web client.
- LangSmith owns operator identity, organizations, workspaces, permissions, and the validity of its credentials.

## Primary journey

1. A signed-out visitor sees three honest entries: **Continue with LangSmith** when live capability discovery says it is supported, **Use an API key**, and **Explore demo**.
2. The application service creates a short-lived, one-use authentication transaction containing PKCE, state, nonce where applicable, return target, client surface, and expiry.
3. After authorization, the service validates the response and probes only the documented identity/workspace endpoint set established by `SPIKE-AUTH-001`.
4. If more than one organization or workspace is available, the user chooses one; inaccessible choices explain the required LangSmith role rather than failing silently.
5. The service creates a Deep Work session and persists only the selected identity context and an encrypted credential reference.
6. The user proceeds to `DW-ONB-002` to connect or deploy an agent source. A returning user with a healthy source may proceed directly to the inbox.
7. If OAuth is unsupported for the account or any required plane, the same screen offers API-key setup without losing the selected return target.
8. If **Explore demo** is chosen, a synthetic actor and workspace are created with an expiry. Every surface carries a persistent **Demo data** marker and destructive or external actions are disabled.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| Signed out | Show only currently supported entry methods and privacy copy. | Start OAuth, API-key entry, or demo. |
| Starting OAuth | Disable duplicate submits and expose cancel. | Return to signed out on timeout or cancel. |
| Awaiting browser/device action | Show verification location, expiry, and polling status without exposing secrets. | Complete, restart after expiry, or use API key. |
| OAuth callback validating | Keep return target server-side and show progress. | Continue to workspace selection or a specific error. |
| OAuth unavailable | Explain that the capability is unavailable, not that the account is invalid. | Use API key; retain onboarding context. |
| API key validating | Mask the value, prevent logging, and probe the minimum safe endpoint. | Accept, retry, replace, or cancel. |
| Key valid but insufficient | List the failed capability/plane without revealing sensitive response bodies. | Replace key, choose a permitted workspace, or enter demo. |
| Workspaces loading | Skeleton rows with retry; no default selection before authorization is known. | Populate choices or show a scoped error. |
| No accessible workspace | Explain the LangSmith-side prerequisite. | Refresh after access is granted, switch credential, or demo. |
| Multiple workspaces | Require an explicit selection and display org/workspace together. | Persist selection; allow later switch. |
| Session active | Show actor, org, workspace, auth method, and expiry/refresh health in settings. | Continue to sources or inbox. |
| Session refresh in progress | Existing read-only content may remain visible; mutations wait. | Resume automatically or enter expired state. |
| Session expired/revoked | Freeze mutations, clear sensitive in-memory data, and preserve a safe return path. | Reauthenticate, replace key, or sign out. |
| Offline with prior session | Show cached shell and identity label; never claim credential validity. | Retry when online; external mutations remain disabled. |
| Demo active | Use fixtures only, show expiry and reset action, prevent external side effects. | Reset demo, sign in, or expire and clear. |
| Permission changed while active | Surface which workspace capability was lost and invalidate affected source access. | Switch workspace or reauthenticate. |
| Unexpected provider response | Render a support code and sanitized details. | Retry or choose API key; raw payload stays server-side. |

## Proposed interfaces and runtime fallback

The browser and Tauri shell consume application-service contracts; neither calls the LangSmith control plane with a raw credential.

```ts
type AuthMethod = "langsmith_oauth" | "langsmith_api_key" | "demo";

interface SessionContext {
  sessionId: string;
  actor: { id: string; displayName?: string };
  organization?: { id: string; name: string };
  workspace?: { id: string; name: string };
  authMethod: AuthMethod;
  capabilities: string[];
  expiresAt: string;
  demo: boolean;
}
```

Proposed application-service operations:

- `POST /api/v1/auth/oauth/transactions` and `GET /api/v1/auth/oauth/callback` create and complete verified transactions.
- `POST /api/v1/auth/api-key/sessions` validates a submitted key and converts it to an encrypted server-side credential reference.
- `GET /api/v1/auth/workspaces` returns normalized organization/workspace choices with capability diagnostics.
- `POST /api/v1/session/workspace` changes context after re-authorizing all registered sources.
- `POST /api/v1/demo/sessions` creates a bounded fixture session.
- `DELETE /api/v1/session` revokes the Deep Work session and deletes or revokes associated local secret material as policy requires.

`SPIKE-AUTH-001` must pin a package/client version and record OAuth metadata, scopes, token audience, refresh behavior, desktop feasibility, and bearer acceptance separately for identity, control-plane, and deployment calls. If any required result fails, OAuth is hidden or labelled experimental and API-key sign-in is the supported path.

`SPIKE-AUTH-002` must produce an endpoint/header matrix for personal and workspace-scoped keys, including whether tenant/workspace headers are required. Until accepted, only the exact validated combinations are enabled; no guessed `X-*` header is emitted.

## Persistence and security

- Store session records, actor/workspace mapping, auth transactions, and audit metadata in Postgres with explicit tenant keys and row-level authorization in application code and database policy where available.
- Encrypt provider credentials with envelope encryption. Persist a key reference in ordinary tables, never the plaintext value.
- Use secure, HTTP-only, same-site cookies for web sessions and a short-lived bound token in the Tauri secure store. Rotate on privilege or workspace change.
- Enforce CSRF protection, PKCE, exact callback allow-lists, one-use state, transaction expiry, rate limits, and sign-in abuse monitoring.
- Redact authorization headers, API keys, OAuth codes, device codes, workspace secrets, and provider error bodies from logs and traces.
- Demo sessions use an isolated fixture tenant and cannot resolve credential references or enqueue provider jobs.
- Workspace switching invalidates cached authorization and forces every source capability to be re-probed.

## Responsive and accessible behavior

- The flow is single-column and usable at 320 CSS pixels without horizontal scrolling.
- The workspace picker is a labelled listbox or radio group with full keyboard operation, visible focus, org/workspace names announced together, and no color-only state.
- Status changes use a polite live region; errors move focus to a concise summary and remain adjacent to the responsible field.
- API keys support paste and password-manager interaction, remain masked by default, and expose a deliberate press-and-hold or toggle to reveal.
- Device-flow codes, if shipped, are large, copyable, and never announced repeatedly while polling.
- Reduced-motion mode removes progress animation. Demo and offline banners remain visible to screen magnification and do not obscure controls.

## Metrics and guardrails

- Sign-in completion rate by method, with provider error categories but no credential material.
- Median and p95 time from sign-in start to selected workspace.
- OAuth-to-key fallback rate and explicit reason.
- Session refresh success rate and unexpected sign-out rate.
- Percentage of demo users who later create a real session.
- Security guardrail: zero credentials in client telemetry, logs, traces, URLs, screenshots generated by tests, or fixture exports.

## Dependencies and rollout

- Depends on the foundation identity model, encrypted secret storage, audit logging, and fixture mode.
- Phase 0: run both authentication spikes against pinned clients and a test org; security review the matrix.
- Phase 1: ship API-key sessions and demo behind an internal flag.
- Phase 2: enable OAuth only for validated account/surface combinations; retain API key as fallback.
- Phase 3: enable workspace switching after cross-source invalidation tests pass.
- Roll back by disabling the OAuth capability flag; existing API-key and demo sessions remain usable.

## Executable acceptance scenarios

```gherkin
Scenario: API-key user selects a workspace without exposing the key
  Given a valid test key with access to two fixture workspaces
  When the user submits the key and selects "Engineering / Agents"
  Then the browser receives a SessionContext without the raw key
  And the database stores only an encrypted credential reference
  And captured browser logs, application logs, and traces do not contain the key

Scenario: OAuth is unavailable and degrades deterministically
  Given SPIKE-AUTH-001 marks OAuth unsupported for the required deployment audience
  When a signed-out user opens Deep Work
  Then "Continue with LangSmith" is absent or explicitly experimental
  And "Use an API key" remains available
  And no guessed OAuth request is sent

Scenario: Workspace access is revoked during a session
  Given an authenticated user has an active source in workspace A
  And the provider test fixture revokes access to workspace A
  When the next session refresh runs
  Then mutations are blocked
  And the user sees a workspace-access error with switch and reauthenticate actions
  And cached source authorization is invalidated

Scenario: Demo cannot cause external side effects
  Given a user enters the demo without credentials
  When they attempt to deploy an agent, install GitHub, or approve a write
  Then Deep Work performs no outbound mutation
  And the control explains that the action requires a real workspace
```
