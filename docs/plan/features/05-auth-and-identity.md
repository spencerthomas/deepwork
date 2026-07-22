# F05 · Auth & identity

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1 · Depth: implementation-ready*

Sources: [architecture §5](../02-architecture.md) · [UI spec §3.6](../03-ui-spec.md) · [roadmap (Spike 1, risks)](../04-roadmap.md) · [research 12 · lifecycle & auth](../../research/12-lifecycle-auth-followup.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [research 01 · MDA](../../research/01-managed-deep-agents.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [research 13 · agent-inbox](../../research/13-agent-inbox.md) · [decisions](../decisions.md)

## 1. Scope

This spec owns the **auth architecture** of Deep Work: the three auth planes and their flows, where credentials live, refresh/revocation, the MDA identity story per runtime tier, and the threat model. It defines *what* the glue service must enforce; the concrete FastAPI endpoint shapes (routes, payloads, cookie/env names) are owned by [F28 · backend glue service](./28-backend-glue-service.md). Agent Auth *configuration* UX (providers, MCP connector wiring) is owned by [F17 · fleet manager](./17-fleet-manager.md); here we cover only how connection state surfaces and why Deep Work never touches third-party tokens.

Stack facts that supersede older doc text: frontend is Next.js (D-022); the glue service is a Python FastAPI app at `apps/server` (P-005) — OAuth token exchange, key proxying, and `trusted_backend` forwarding are `apps/server` responsibilities, **not** Next.js server routes as [02-architecture §1/§11](../02-architecture.md) and [06-frontend-implementation Phase B](../06-frontend-implementation.md) still say.

In scope: operator sign-in (OAuth 2.1 + API-key fallback), org/workspace selection, token storage/refresh, sign-out/revocation, end-user→deployment identity (`trusted_backend` / `validated_token` / classic `langgraph_sdk.Auth`), Agent Auth surfacing, dual launch postures pending Spike 1 (O-001/O-002), threat model.

Out of scope: GitHub App sandbox token callback mechanics (F28 + execution spec), push notification auth, sandbox egress control, team RBAC surfaces (post-v1 per [roadmap backlog](../04-roadmap.md)).

## 2. Dependencies & seams

| Neighbor | Seam |
|---|---|
| [F28 · backend glue](./28-backend-glue-service.md) | Implements every server-side flow specified here: OAuth exchange/refresh/revoke endpoints, key proxy, `trusted_backend` header injection, session sealing. F05 pins the invariants (§4, §6); F28 pins routes/payloads/names. |
| [F17 · fleet manager](./17-fleet-manager.md) | Consumes plane-1 credentials for control-plane CRUD; owns Agent Auth provider config and MCP `auth-sessions` UI. F05 defines which credential each manager action uses (§3.1). |
| `packages/sdk` | `AgentSource` registry carries an auth mode per source; SDK attaches credentials via a header-provider callback and never persists secrets itself ([02-architecture §11](../02-architecture.md)). |
| `packages/agent` | Ships `identity.py` (`define_identity` presets) for MDA and the generated `langgraph_sdk.Auth` module for classic tiers ([02-architecture §3, §5](../02-architecture.md)). |
| M0 Spike 1 | O-001 (OAuth `scopes_supported` / DCR viability) and O-002 (bearer acceptance on control plane and `*.langgraph.app` data plane) gate the launch posture (§3.6; [roadmap M0](../04-roadmap.md)). |

Decisions cited: D-022 (Next.js frontend), P-005 (FastAPI `apps/server`), O-001/O-002 (Spike 1 outcomes, provisional).

## 3. Design

### 3.1 Three planes, never conflated

Per [02-architecture §5](../02-architecture.md):

| Plane | Question | Credential |
|---|---|---|
| **1 · Operator ↔ LangSmith** | Who are you to the org? | LangSmith OAuth 2.1 bearer, or API key (PAT / `lsv2_sk_` service key + `X-Tenant-Id`) |
| **2 · End user ↔ deployment** | Who are you to the agent? | MDA identity: `trusted_backend` headers or `validated_token` bearer; classic tiers: generated `langgraph_sdk.Auth` |
| **3 · Agent ↔ third-party services** | What may the agent touch? | Agent Auth (`langchain-auth`) brokered tokens; GitHub App installation tokens. Never held by Deep Work |

Action → plane map (normative for the UI and `apps/server`):

| UI / system action | Plane | Credential path |
|---|---|---|
| Sign in, org/workspace picker | 1 | OAuth bearer or API key → `api.smith.langchain.com` |
| Fleet manager: list/inspect deployments & agents (`/v2/deployments`, `/v1/deepagents/*`) | 1 | via `apps/server` proxy (default) |
| Deploy/update agent (tarball upload, revisions) | 1 | via `apps/server` proxy |
| Context Hub edits (`/v1/platform/hub/repos/`) | 1 | via `apps/server` proxy |
| Sandboxes REST (`/v2/sandboxes`) | 1 | `apps/server` proxy, workspace key |
| Fleet agent invoke/read | 1 (used on data plane) | PAT + `X-Auth-Scheme: langsmith-api-key`, owner-gated ([research 12 §1](../../research/12-lifecycle-auth-followup.md)) |
| Create task / stream thread / steer / approve / files & diff (connector routes) | 2 | solo: `trusted_backend` via `apps/server`; team: `validated_token` direct from client |
| Schedules CRUD (`/runs/crons` on the deployment) | 2* | same path as task traffic; base-credential question tracked in §9 |
| Connect a third-party provider (MCP/OAuth) | 3 | LangSmith-hosted flow; Deep Work only deep-links |
| Read connection state (`auth-sessions`) | 1 (reads about plane 3) | `apps/server` proxy |
| Sandbox GitHub credentials | 3 | GitHub App token minted by `apps/server`, injected by the sandbox auth proxy callback (spec: F28) |

Rule: a credential from one plane is never substituted for another. The one documented exception is Fleet invocation (plane-1 PAT on a deployment URL, owner-gated upstream).

### 3.2 Sign in with LangSmith (plane 1, OAuth)

LangSmith is a spec-complete OAuth 2.1 authorization server — RFC 8414 metadata at `/.well-known/oauth-authorization-server`, `/oauth/authorize` (code + PKCE S256 required), public DCR at `/oauth/register` (RFC 7591), device flow at `/oauth/device/code` (RFC 8628), token revocation. Cloud-only; self-hosted LangSmith must use keys ([research 12 §2](../../research/12-lifecycle-auth-followup.md)). Deep Work would be the first OSS consumer, so everything below is behind the Spike 1 gate (§3.6).

**Flows per surface**

- **Web (Next.js, D-022)**: authorization-code + PKCE, brokered by `apps/server` (P-005). `apps/server` bootstraps a client via public DCR on first run (registration persisted alongside its config), generates `state` + PKCE verifier, redirects the browser to `/oauth/authorize`, receives the callback, exchanges the code, and seals the tokens into an HttpOnly session cookie. The browser never sees an access or refresh token.
- **Mobile (PWA)**: same web flow — the PWA shares the web origin and `apps/server` session.
- **Desktop (Tauri v2)**: RFC 8628 device flow — app shows `user_code` + verification URI, polls the token endpoint, stores tokens in the OS keychain via Tauri. Ships in M4 per [roadmap](../04-roadmap.md).

**Token storage & refresh — recommendation**

Tokens live **server-side in the `apps/server` session** (sealed, encrypted HttpOnly cookie; no server DB in v1 per [02-architecture §1](../02-architecture.md)), not in the client. Rationale:

1. XSS in the web client cannot exfiltrate what the JS context never holds; agent-driven UIs render model output, which raises baseline XSS exposure.
2. `apps/server` is already mandatory for `trusted_backend` forwarding and key proxying — one place performs refresh (single-flight, on 401 or ahead of `expires_in`) and revocation.
3. The sealed-cookie pattern preserves the no-database constraint; if LangSmith tokens exceed cookie limits, fall back to a server-side session store (tracked in §9 — this is the one thing that could force a KV dependency into v1).

Desktop is the exception: device-flow tokens live in the OS keychain and the Tauri app talks to LangSmith directly or through its bundled `apps/server`, whichever the packaging lands on (§9).

**Org/workspace picker**: after sign-in, `apps/server` lists the operator's organizations/workspaces from the LangSmith API (orgs/workspaces reach is confirmed for the key family, [research 12 §2](../../research/12-lifecycle-auth-followup.md); exact endpoint + bearer acceptance verified in Spike 1, pinned in F28). The chosen workspace is stored in the session and drives `X-Tenant-Id` on every proxied call. The shell `OrgSwitcher` ([UI spec §2](../03-ui-spec.md)) mutates the session server-side — never a client-supplied per-request header.

**Sign-out**: destroy the session cookie, best-effort revoke refresh + access tokens at the revocation endpoint, clear client caches. Key-mode sign-out forgets the key (and tells the user Deep Work *cannot* revoke keys — link to LangSmith settings).

### 3.3 API-key fallback (plane 1, keys)

Always shipped; the only path on self-hosted LangSmith and the M1 default if Spike 1 is red ([roadmap M1](../04-roadmap.md)).

| Key type | Use | Notes |
|---|---|---|
| PAT (user-scoped) | Personal/solo use; Fleet invocation (owner-gated) | Discouraged upstream for apps ([research 12 §2](../../research/12-lifecycle-auth-followup.md)) |
| Service key `lsv2_sk_` (workspace-, multi-workspace-, or org-scoped) | Teams; control-plane ops | Org-scoped requires `X-Tenant-Id` on every request; Enterprise pins roles to keys |

**Entry UX** ([UI spec §3.6](../03-ui-spec.md)): paste key → detect service key by `lsv2_sk_` prefix (PAT prefix detection: §9) → `apps/server` validates with a read-only call → if the key is org-scoped, require a workspace selection before finishing (drives `X-Tenant-Id`) → show the workspace/org the key resolved to, so the operator confirms identity before any write.

**Storage**: by default the key is posted once to `apps/server` and held in the sealed session; all LangSmith/deployment calls go through the proxy (`langgraph-nextjs-api-passthrough` pattern, relocated to FastAPI per P-005). **Local mode only** (`langgraph dev` / explicitly self-hosted-without-server): key in browser `localStorage`, requests direct from client — the agent-chat-ui / agent-inbox status quo ([research 13](../../research/13-agent-inbox.md)).

**Trust-story copy (requirement)**: the key screen must state on-screen where the key is held for the active mode ("your key is held in an encrypted session on your Deep Work server; it is never written to a database" vs "local mode: your key stays in this browser's localStorage") and that all traffic goes to *your* LangSmith org — "your org, your data" ([UI spec §3.6](../03-ui-spec.md)). Mode is visible, not implied.

### 3.4 MDA identity (plane 2)

MDA identity is opt-in and **fail-closed**: with identity enabled, unauthenticated requests are rejected; thread/store access is stamped `metadata.owner` (actor|tenant|channel) and store reads outside the identity namespace 403 ([research 20](../../research/20-gapfill-mda-api.md)). `packages/agent` selects a preset via `define_identity` (`private-assistant`, `multi-tenant-saas`, `internal-tool`, … per [research 01](../../research/01-managed-deep-agents.md)).

| Path | Mechanism | When Deep Work uses it |
|---|---|---|
| **`trusted_backend`** | `apps/server` forwards `X-MDA-Ingress-Secret` (constant-time-checked against `MDA_INGRESS_SECRET`) + `X-MDA-Actor-Id` [+ `X-MDA-Tenant-Id`]; headers allowlisted via `configurable_headers` | **Solo / proxy default**: single operator or small team where all traffic already transits `apps/server`. Actor id derived from the server session, never from the client (§6) |
| **`validated_token`** | Bearer JWT validated in-deployment via JWKS/OIDC/introspection or Supabase; or HS256 guest tokens from public `POST /identity/guest` signed with `MDA_GUEST_SIGNING_KEY` | **Team / direct-from-client**: org has an IdP; clients call the deployment URL directly, removing `apps/server` from the data-plane hot path and removing its impersonation power. Guest tokens cover lightweight share/guest cases |

Public bypass routes (`POST /identity/guest`, `GET /identity/{provider}/callback`, `POST /channels/{name}/events` — Slack-signature verified) are the only unauthenticated surface ([research 20](../../research/20-gapfill-mda-api.md)).

**Classic tiers** (LangSmith Deployment): same semantics via the generated `langgraph_sdk.Auth` module referenced from `langgraph.json` `auth.path` — `@auth.authenticate` yields `config.configurable.langgraph_auth_user`, `@auth.on` handlers add owner filters; MDA auto-generates this (`_mda_auth`), and `packages/agent` ships the equivalent for classic deploys ([research 01](../../research/01-managed-deep-agents.md), [02-architecture §5](../02-architecture.md)). **`langgraph dev`**: no auth; `MDA_LOCAL_DEV=1` synthetic actor `mda:local-dev` — the UI labels the source "local, unauthenticated".

Solo→team migration: start on `trusted_backend` (zero IdP setup), move to `validated_token` when a team connects an IdP; whether both ingress modes can coexist on one deployment during migration is §9.

### 3.5 Agent Auth (plane 3) — surfacing only

Third-party OAuth is brokered by LangSmith Agent Auth (`langchain-auth`): providers registered via control-plane Auth Service v2, user consent through the LangSmith-hosted callback (`smith.langchain.com/host-oauth-callback/{provider_id}`), per-user tokens fetched by the agent at runtime — **never stored, proxied, or seen by Deep Work** ([research 12 §2](../../research/12-lifecycle-auth-followup.md); open-swe production pattern, [research 10](../../research/10-openswe-fleet.md)). The UI's whole job: show per-provider, per-user connection state (via the `/v1/deepagents/*` `oauth-provider` / `auth-sessions` surfaces, [research 20](../../research/20-gapfill-mda-api.md)), render "Connect" as a link-out to the hosted flow, and surface "connection required/expired" as an actionable task-detail state. Provider registration/config UX: [F17](./17-fleet-manager.md). GitHub repo access uses the GitHub App installation flow, not Agent Auth (F28 + execution spec).

### 3.6 Dual launch posture — Spike 1 switch points (O-001/O-002)

Both postures are specified and built behind one config flag; Spike 1's memo flips the default.

| | **OAuth-first** (O-001 green: scopes suffice, DCR allowed; O-002 green: bearer accepted) | **Key-first** (any red) |
|---|---|---|
| Sign-in screen | "Sign in with LangSmith" primary; key paste under "advanced" | Key paste primary; OAuth hidden or beta-flagged |
| Control plane | Session bearer via proxy | Session key via proxy |
| Deployment data plane | Bearer if O-002 green; else `trusted_backend` via `apps/server` regardless | `trusted_backend` via `apps/server` (key never used as end-user identity) |
| Self-hosted LangSmith | Keys (OAuth is cloud-only) | Keys |

Partial-green switch points: (a) bearer works on `api.smith.langchain.com` but not `*.langgraph.app` → OAuth for plane 1, `trusted_backend` for plane 2 — fully workable because plane 2 never needed LangSmith bearers; (b) DCR disallowed for consumer apps by ToS → attempt a pre-registered client with LangChain, else key-first; (c) scopes exist but exclude Context Hub writes → OAuth sign-in + key held server-side for Hub ops only, flagged in settings ([07-org-intelligence](../07-org-intelligence.md) dependency).

## 4. Contracts

Invariants this spec pins (concrete names/routes: [F28](./28-backend-glue-service.md)):

1. **Session**: browser ↔ `apps/server` uses an HttpOnly, Secure, SameSite=Lax sealed cookie containing (posture, tokens or key, org id, workspace/tenant id, actor id). No secret material in JS-readable storage except documented local mode.
2. **Header injection**: `apps/server` strips any inbound `X-MDA-*`, `X-Api-Key`, `X-Tenant-Id`, and `Authorization` headers from browser requests before injecting its own from the session. Client-supplied identity is never forwarded.
3. **Credential attach points** (wire facts, verified): `X-Api-Key` + `X-Tenant-Id` (control plane, org-scoped keys); `Authorization: Bearer` (OAuth, `validated_token`, guest tokens); `X-Auth-Scheme: langsmith-api-key` + PAT (Fleet invoke); `X-MDA-Ingress-Secret` / `X-MDA-Actor-Id` / `X-MDA-Tenant-Id` (`trusted_backend`).
4. **`AgentSource` auth modes** (`packages/sdk`): `oauth_session | key_proxy | key_local | validated_token | none_local` — every source declares exactly one; `useStream` and the control-plane client obtain headers from the source's provider callback, never from globals.
5. **OAuth endpoints** consumed (from RFC 8414 metadata, never hardcoded beyond the metadata URL): authorize, token, device authorization, registration, revocation.
6. **Fail-closed proxy**: no session → 401 with no upstream call; expired session → one refresh attempt (OAuth) then 401; unknown target host → 403 (proxy is an allowlist of the org's control-plane + registered deployment URLs, not an open relay).
7. **Actor mapping**: `X-MDA-Actor-Id` = stable operator identity from the session (LangSmith user identity in OAuth mode; configured actor id in key mode — exact field: §9). One session, one actor.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| OAuth refresh fails / token revoked upstream | Session marked invalid; UI returns to sign-in with reason; queued approvals preserved client-side (nuqs URL state survives) |
| Key revoked in LangSmith mid-session | Proxy surfaces upstream 401 as "credential invalid — re-enter key", distinct from network failure |
| Org-scoped key without workspace chosen | Setup cannot complete; every control-plane call would be ambiguous — block, don't default |
| Wrong-workspace confusion (multi-org operators) | Workspace pinned in session; switcher shows active org/workspace persistently in the navbar ([UI spec §2](../03-ui-spec.md)); switching invalidates cached thread lists |
| Device flow: user never completes | Poll until `expires_in` of the device code, then reset with a fresh code; show countdown |
| DCR registration lost/rotated server-side | `apps/server` re-registers on invalid-client errors; sessions survive (re-auth required only if refresh fails) |
| MDA identity off (bare deployment) but posture expects it | Source health check flags "unauthenticated deployment"; solo-mode traffic still flows; team features disabled for that source |
| Guest token expiry mid-stream | Stream drop → resumable rejoin with fresh token (`Last-Event-ID` replay, [02-architecture §7](../02-architecture.md)) |
| Sealed cookie exceeds browser limits | Detected at seal time; error instructs enabling the session-store option (§9) rather than silently truncating |
| `langgraph dev` source in proxy mode | Loopback URLs are exempt from the proxy allowlist only in explicit local mode; production `apps/server` refuses to proxy to private-network targets (SSRF, §6) |
| Sign-out with unreachable revocation endpoint | Session destroyed locally regardless; revocation retried best-effort; UI states which happened |

## 6. Security & privacy

Threat model (attack → control):

| Surface | Threat | Control |
|---|---|---|
| Browser JS context | Token/key exfiltration via XSS (model-rendered content) | Tokens server-side only (§3.2); HttpOnly sealed cookie; CSP; local-mode localStorage is opt-in, labeled, and confined to loopback/self-hosted targets |
| OAuth callback | CSRF / code injection / login-CSRF (binding victim session to attacker org) | `state` bound to session + PKCE S256 (mandatory in OAuth 2.1); callback rejects unknown `state`; SameSite=Lax |
| Device flow | Phishing — attacker initiates flow, lures victim into entering `user_code` | Desktop app displays code + URI itself, never in email/links; screen carries fixed copy: "only enter a code shown by *your* Deep Work app right now"; codes single-use, short TTL (server-enforced upstream) |
| `apps/server` proxy | Open-relay abuse / SSRF; identity header injection | Target allowlist (contract 6); strip-then-inject rule (contract 2); private-network targets refused outside local mode |
| `trusted_backend` | Actor spoofing = full impersonation of any user on the deployment | Actor id derived exclusively from session (contract 7); ingress secret only in `apps/server` env, never in client bundles, logs, or traces; rotate by redeploying both sides; prefer `validated_token` once a team exists (§3.4) |
| Multi-org keys | Acting in the wrong tenant | `X-Tenant-Id` from session only; workspace confirmation at key entry (§3.3); active workspace always visible |
| Logs & traces | Secrets in observability | `apps/server` redacts `Authorization`, `X-Api-Key`, `X-MDA-Ingress-Secret` in logs; run-metadata conventions ([02-architecture §10](../02-architecture.md)) carry actor/tenant *ids*, never credentials |
| Sandbox | Token theft from execution env | Zero-secrets rule: sandbox auth proxy callback injects headers, TTL-bound, fail-closed 502 ([research 20](../../research/20-gapfill-mda-api.md); enforced by [v1 release criterion 5](../04-roadmap.md)) |
| Third-party tokens | Deep Work as honeypot | Structurally impossible by design: Agent Auth tokens never transit Deep Work (§3.5) |

Privacy: Deep Work stores no user database in v1; identity data at rest is limited to sealed session contents and the desktop keychain entry. All data-plane traffic terminates in the operator's own LangSmith org ("your org, your data" — the trust story is a UI requirement, §3.3).

## 7. Acceptance criteria

1. OAuth web sign-in completes end-to-end with **no access/refresh token ever present in a client-readable context** (asserted by an integration test inspecting responses, cookies minus HttpOnly, and storage).
2. Key path: proxy mode by default — key absent from all browser storage; local mode stores in `localStorage` and renders the trust copy verbatim per mode. Org-scoped `lsv2_sk_` cannot finish setup without a workspace; subsequent proxied calls carry the session's `X-Tenant-Id`.
3. All solo-mode deployment traffic carries server-injected `X-MDA-*` headers; a request with forged client-side `X-MDA-Actor-Id` reaches the deployment with the session's actor instead (strip-then-inject test).
4. Proxy fail-closed: missing/expired session → 401 with zero upstream calls; unlisted target host → 403.
5. Sign-out destroys the session and (OAuth) calls revocation; the next proxied request 401s. Key-mode sign-out shows the "revoke in LangSmith" link.
6. Device flow signs in a Tauri build; tokens present in OS keychain, absent from web-view storage (M4).
7. Posture flag flips OAuth-first ⇄ key-first with no code change; both postures pass 1–5.
8. `validated_token` source: client attaches a bearer, deployment accepts, and a second actor's thread listing shows only their own threads (fail-closed scoping observed end-to-end).
9. Spike 1 memo recorded with O-001/O-002 outcomes and the chosen default posture, referenced from [decisions](../decisions.md).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Execute Spike 1: probe RFC 8414 metadata, DCR a public client, test bearer vs control plane and `*.langgraph.app` | — | Memo with O-001/O-002 resolved; default posture chosen (M0) |
| 2 | `packages/sdk`: `AgentSource` auth modes + header-provider seam | — | Modes of contract 4 typed; unit tests; no global credential state |
| 3 | `apps/server` sealed-session layer (cookie sealing, strip-then-inject middleware, target allowlist) | P-005 scaffold ([F28](./28-backend-glue-service.md)) | Contracts 1, 2, 6 pass integration tests |
| 4 | Key entry flow + proxy mode (validate key, workspace selection for org keys, trust copy) | 2, 3 | Acceptance 2; UI per [UI spec §3.6](../03-ui-spec.md) |
| 5 | Local mode: direct-from-client with `localStorage`, loopback-only default | 2 | Local `langgraph dev` source streams without `apps/server` running |
| 6 | OAuth web flow: DCR bootstrap, authorize redirect, callback, code exchange, sealing | 1, 3 | Acceptance 1; `state`+PKCE tests |
| 7 | Refresh, revocation, sign-out (both modes) | 6 | Acceptance 5; single-flight refresh under concurrent requests |
| 8 | Org/workspace picker fed from `apps/server`; session-side switcher | 4 or 6 | Switching tenant changes injected `X-Tenant-Id`; navbar shows active workspace |
| 9 | `trusted_backend` forwarding for deployment traffic | 3 | Acceptance 3 against an MDA deployment with `private-assistant` preset |
| 10 | `validated_token` client path + guest-token support | 2 | Acceptance 8; stream rejoin on token expiry |
| 11 | Classic-tier `langgraph_sdk.Auth` module in `packages/agent` mirroring MDA owner semantics | — | Same scoping test as 10 passes on a classic Deployment |
| 12 | Agent Auth connection-state UI (read `auth-sessions`, link-out connect, expired-state surfacing) | 8; [F17](./17-fleet-manager.md) provider config | State chips render from live API; zero third-party tokens in any Deep Work store (code audit) |
| 13 | Device flow + keychain on Tauri (M4) | 6 | Acceptance 6 |
| 14 | Threat-model test suite + security review (CSRF, header injection, SSRF allowlist, redaction, fail-closed) | 3–10 | §6 table has a test or documented manual check per row |

## 9. Open questions

1. **O-001**: OAuth `scopes_supported` reality; whether scopes cover control-plane CRUD and Context Hub writes ([research 12](../../research/12-lifecycle-auth-followup.md); [roadmap open questions](../04-roadmap.md)).
2. **O-002**: bearer acceptance on `api.smith.langchain.com` vs `*.langgraph.app` data planes; whether OAuth bearers work for Fleet invocation in place of PAT + `X-Auth-Scheme`.
3. DCR terms-of-service/allowlist posture for consumer apps (nothing forbids it in docs; unconfirmed).
4. Does the LangSmith OAuth server issue refresh tokens to public clients, and with what rotation policy? (Determines whether web sessions can outlive access-token TTL without re-auth.)
5. Sealed-cookie size vs actual LangSmith token sizes — does v1 need the optional server-side session store (breaking the no-DB constraint)?
6. Exact org/workspace listing endpoint + whether a key's scope (PAT vs workspace vs org) is introspectable, to drive entry UX; PAT prefix for client-side type detection (`lsv2_sk_` is confirmed; PAT prefix is not).
7. Which base credential MDA deployment URLs accept for *admin* data-plane ops (crons reconcile) when identity is enabled — API key, bearer, or `trusted_backend` only? ([research 20](../../research/20-gapfill-mda-api.md) shows `mda` CLI doing this; header set unpublished.)
8. Can `trusted_backend` and `validated_token` coexist on one deployment for solo→team migration, or is ingress mode exclusive per `define_identity`?
9. Revocation endpoint semantics (RFC 7009 conformance; does revoking the refresh token cascade to access tokens?).
10. `auth-sessions` / `oauth-provider` endpoint payloads for connection state (recoverable from deepagents-cli `api_client.py`, but response shapes unverified) — blocks task 12 detail work.
11. Desktop packaging: does Tauri bundle its own `apps/server` (device-flow tokens stay in keychain, loopback proxy) or talk to a shared deployment of it?
12. Actor-id field choice in OAuth mode (stable LangSmith user id vs email) — needs the userinfo/identity payload from Spike 1.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OAuth scopes/bearer coverage insufficient (O-001/O-002 red) | Med | Med | Key-first posture is fully specified and complete (§3.6); OAuth ships later behind the same flag ([roadmap risk register](../04-roadmap.md)) |
| First-OSS-consumer breakage: LangSmith changes DCR/device-flow behavior without notice | Med | Med | Endpoints discovered via RFC 8414 metadata at runtime, not hardcoded; contract tests against live metadata in CI; relationship with LangChain |
| Ingress secret is a single impersonation key for `trusted_backend` deployments | Low | High | Server-only custody + redaction (§6); documented rotation; team posture migrates to `validated_token` |
| Sealed-cookie approach fails on token size → v1 grows a session store | Med | Low-Med | §9-5 probed in M1 week 1; fallback is a small KV in `apps/server`, isolated behind the session interface |
| MDA identity churn on the `0.4.0-dev` channel (headers, presets, guest tokens) | High | Low-Med | Canary deployment in CI ([roadmap risk register](../04-roadmap.md)); identity code isolated in `apps/server` + `packages/agent/identity.py` |
| Self-hosted LangSmith users permanently key-only | Certain | Low | Key path is first-class forever, not a deprecation-tracked fallback |
| Multi-org operators acting in the wrong tenant despite controls | Low | Med | Session-pinned tenant + persistent workspace indicator + write-op confirmations in the fleet manager ([F17](./17-fleet-manager.md)) |
