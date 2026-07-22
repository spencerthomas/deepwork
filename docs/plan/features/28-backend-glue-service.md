# F28 · Backend glue service (`apps/server`)

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M0–M2 (grows with features) · Depth: implementation-ready*

Sources: [decisions (P-005, D-003, D-015, D-022)](../decisions.md) · [02 · Architecture §1/§4/§5/§7](../02-architecture.md) · [03 · UI spec §3.6](../03-ui-spec.md) · [05 · OSS setup](../05-oss-setup.md) · [04 · Roadmap](../04-roadmap.md) · [research 12 · lifecycle & auth](../../research/12-lifecycle-auth-followup.md) · [research 20 · MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [research 06 · sandboxes](../../research/06-execution-sandboxes.md) · [research 05 · cross-platform arch](../../research/05-crossplatform-arch.md) · [feature catalog](./README.md)

## 1. Scope

**This spec exists because of [P-005](../decisions.md)**: the server-side glue is a **Python FastAPI service at `apps/server`**, a member of the uv workspace shared with `packages/agent` — not Next.js server routes as [02 §1/§11](../02-architecture.md), [05](../05-oss-setup.md), and [04 M1](../04-roadmap.md) ("key-proxy server route") still say. Those docs are amended when P-005 is ratified; until then every spec citing the glue marks the dependency, and `apps/web` keeps only browser-flow pages.

**Owns:** the service itself — FastAPI app layout, the consolidated endpoint inventory (routes/paths/exposure classes), auth/session middleware plumbing, streaming passthrough mechanics, configuration & secret handling, boot validation, deployment story (docker-compose, hosted, CORS, health), local-dev composition, testing strategy, and the service-level hardening checklist.

**Does not own (semantics live with neighbors; F28 hosts):** auth flows/planes/threat model → [F05](./05-auth-and-identity.md); GitHub App design, token minting semantics, callback payloads → [F12](./12-github-and-git-flow.md); environment/sandbox route semantics → [F11](./11-execution-and-environments.md); onboarding/deploy orchestration semantics → [F06](./06-onboarding-and-deploy.md); notification product behavior & payloads → [F19](./19-notifications-and-push.md); Insights provisioning logic → [F22](./22-org-intelligence-v1.md); L2 review-loop webhook semantics → [F23](./23-org-intelligence-v1x-consolidation.md); SDK-side proxy-vs-direct routing → [F04](./04-sdk-and-agent-sources.md); scaffold/CI mechanics → [F01](./01-monorepo-and-oss-infra.md).

**Statelessness (D-003):** Deep Work stores essentially nothing — the service is **stateless by default**: no database, no user records; the user's LangSmith org is the source of truth ([01 · vision](../01-vision.md), [02 §1](../02-architecture.md)). §3.4 enumerates the three unavoidable state candidates honestly.

## 2. Dependencies & seams

| Neighbor | Direction | Seam |
|---|---|---|
| [F05 · auth](./05-auth-and-identity.md) | F05 defines, F28 implements | Sealed-session cookie, strip-then-inject, target allowlist, OAuth exchange/refresh/revoke, `trusted_backend` header injection — F05 §4 invariants are binding; F28 pins routes/names (§4 here) |
| [F04 · SDK](./04-sdk-and-agent-sources.md) | F04 calls F28 | Plane router `resolveAuth(source, plane) → {headers, via: proxy\|direct}`; proxy mode rewrites base URL to F28's passthrough routes |
| [F12 · GitHub](./12-github-and-git-flow.md) | F12 defines, F28 hosts | `github/` module: app JWT, mint + down-scope + cache, install/setup/listing routes, the sandbox auth-proxy **callback** (F12 §4.2–4.3) |
| [F11 · execution](./11-execution-and-environments.md) | F11 defines, F28 hosts | Environment registry CRUD, snapshot build + SSE logs, thread-sandbox status (F11 §4.3); workspace key custody |
| [F06 · onboarding](./06-onboarding-and-deploy.md) | F06 defines, F28 hosts | Capabilities probe, deploy orchestration + SSE progress, source validation (F06 §4 internal table) |
| [F19 · notifications](./19-notifications-and-push.md) | F19 defines, F28 hosts | Run-completion webhook receiver → push fan-out (Web Push/VAPID; Tauri/Expo per surface) ([02 §7](../02-architecture.md)); subscription-storage question shared (§9-3) |
| [F23](./23-org-intelligence-v1x-consolidation.md) / [F22](./22-org-intelligence-v1.md) | define, F28 hosts (v1.x / M3) | Context Hub commit webhook consumer (`context_hub.commit.created.v1`, HMAC-signed — [07 §Layer 2](../07-org-intelligence.md)); Insights config provisioning glue (O-007) |
| [F01 · monorepo](./01-monorepo-and-oss-infra.md) | F01 scaffolds | uv workspace member, ruff/pytest/CI wiring, wrapper `package.json`, FastAPI skeleton + boot smoke test (F01 task 3); F28 fills routes in |
| [F02 · spikes](./02-m0-spikes.md) | informs | Spike 1 fixes OAuth posture (O-001/O-002); Spike 3 golden transcripts feed the passthrough contract tests |

Decisions cited: P-005 (this service, provisional), D-003 (no backend/DB), D-015 (zero secrets in sandbox), D-022 (Next.js frontend), P-003/P-004 (demo mode fixtures — zero-credential path bypasses this service), D-007 (GitHub only). Open questions inherited: O-001/O-002 (posture), O-007 (Insights API), O-008 (Hub write scopes).

## 3. Design

### 3.1 Role & shape

One FastAPI app, three exposure classes (proposal — names pinned here, first use of a class elsewhere must match):

| Class | Prefix | Caller | Auth |
|---|---|---|---|
| **session** | `/api/*` | browser (`apps/web`, PWA) | sealed HttpOnly session cookie (F05 contract 1); CSRF via SameSite=Lax + Origin check |
| **hooks** | `/hooks/*` | machines: LangSmith sandbox auth proxy, Agent Server run webhooks, Context Hub webhooks, GitHub post-install redirect | per-route: unguessable grant URL (F12 §4.2), HMAC signature ([07](../07-org-intelligence.md)), or provider redirect state; **never** the session cookie |
| **infra** | `/healthz`, `/readyz` | orchestrator / compose | none (no data returned beyond status) |

The service concentrates everything that must hold a secret: LangSmith keys/bearers (sealed sessions), `MDA_INGRESS_SECRET`, the GitHub App private key, VAPID private key, session-sealing key. Nothing else in the system holds any of these ([02 §5](../02-architecture.md); F12 §6).

### 3.2 Streaming passthrough (the hot path)

When a source's auth mode is `proxy` (solo/`trusted_backend` default — F05 §3.4), every data-plane call including `POST /threads/{id}/stream/events` transits `apps/server`. Design:

- **SSE relay**: async httpx upstream request streamed into a `StreamingResponse`; events forwarded unparsed (byte-range chunks, no re-framing) so protocol-v2 content is untouched. Backpressure is natural: the relay awaits the client write before pulling the next upstream chunk; a slow client slows its own upstream read, nothing buffers unboundedly (bounded in-flight buffer, proposed 64 KiB).
- **Header passthrough**: `Last-Event-ID` (resume/replay — [02 §7](../02-architecture.md)) and `Accept` forwarded upstream verbatim; auth headers stripped-then-injected per F05 contract 2. Response `Content-Type: text/event-stream`, `Cache-Control: no-store`, compression disabled on stream routes (SSE + gzip buffering interact badly — proposal grounded in ecosystem norm, not a source doc).
- **Timeouts**: short connect timeout (proposed 10 s); **no read timeout** on established streams — idle handling belongs to the client (`streamIdleReconnect`, [03 §5](../03-ui-spec.md)) and the platform. Client disconnect cancels the upstream request (httpx client closed on task cancellation) so abandoned streams don't leak upstream connections.
- **Reconnects** are client-driven (`useStream` `maxReconnectAttempts` + `Last-Event-ID` replay against `stream_resumable` runs); the relay never retries a broken upstream mid-stream — it terminates the SSE cleanly and lets the client rejoin.
- **WebSocket stance**: v1 relay is **SSE-only**. WebSocket transport ([02 §7](../02-architecture.md)) is only used where the client talks to the deployment **directly** (`validated_token` team posture, local mode); proxying WS through FastAPI is deferred (§9-6).
- **Performance envelope / when to bypass**: the relay adds one hop on every token. This is acceptable for the solo posture it serves; the designed escape valves are F05 §3.6's postures — `validated_token` direct-from-client for teams (removes F28 from the data plane entirely), O-002-green OAuth bearers direct-from-client, and local mode. F28 must not become load-bearing for scale it wasn't designed for; the spec target is "a handful of concurrent operators per instance" (solo/small-team self-host), asserted by a soak test (§7-6), not by invented throughput numbers.

Server-*originated* SSE (deploy progress F06, build logs F11) uses the same response plumbing minus the upstream leg.

### 3.3 Configuration

All config via environment variables, validated at boot (fail fast, refuse to start on invalid/missing required config; pydantic-settings proposed — flag: recommendation, not sourced). No config file is required beyond `.env` for local dev.

| Variable (proposed names) | Secret? | Used by | Required when |
|---|---|---|---|
| `DW_SESSION_SEALING_KEY` | yes | session cookie sealing (F05 contract 1) | always |
| `DW_ALLOWED_ORIGINS` | no | CORS allowlist (§3.5) | always |
| `DW_PUBLIC_URL` | no | callback/webhook URL construction (OAuth redirect, proxy-callback, run webhooks) | always |
| `DW_PROXY_TARGET_ALLOWLIST` | no | proxy allowlist seed: control-plane hosts + registered deployment URLs (F05 contract 6) | always |
| `MDA_INGRESS_SECRET` | yes | `trusted_backend` injection (F05 §3.4; [research 20](../../research/20-gapfill-mda-api.md)) | proxy posture w/ MDA identity |
| `GITHUB_APP_ID` / `GITHUB_APP_PRIVATE_KEY` / `GITHUB_APP_CLIENT_ID` / `GITHUB_APP_CLIENT_SECRET` | key/secret: yes | `github/` module (F12 §3.1–3.2; open-swe env precedent, [research 06](../../research/06-execution-sandboxes.md)) | M2+, GitHub features on |
| `DW_VAPID_PUBLIC_KEY` / `DW_VAPID_PRIVATE_KEY` / `DW_VAPID_SUBJECT` | private: yes | Web Push fan-out (F19; [02 §7](../02-architecture.md)) | M4+, push on |
| `DW_OAUTH_*` (issuer URL only; client credentials from DCR) | no | OAuth flows (F05 §3.2) | OAuth posture |
| `DW_HUB_WEBHOOK_SECRET` | yes | Context Hub webhook HMAC verification (F23; [07](../07-org-intelligence.md)) | v1.x |

Secret-handling rules: secrets are read once at boot into a config object whose `repr`/serialization masks them; never logged, never returned by any endpoint, never included in error responses or traces (F05 §6 redaction row); private keys accepted as PEM content or file path. LangSmith API keys and OAuth tokens are **not** env config — they arrive per-session from the operator and live only in sealed sessions (F05 §3.2–3.3).

### 3.4 Where unavoidable state lives (D-003 pressure points)

| State | v1 answer | Notes |
|---|---|---|
| OAuth DCR client registration | Persisted "alongside its config" (F05 §3.2): a small JSON file at a configurable path (default: container volume) | Re-registers on invalid-client (F05 §5); losing it costs a re-registration, not user data |
| GitHub token / installations cache | **In-process memory only**, expiry-aware (F12 §3.1) | Restart = cold cache; correctness unaffected |
| Proxy-callback grants (F12 §4.2 binds grant → `{installation_id, owner, repo}`) | **Proposal: stateless sealed grant** — the grant id embedded in each sandbox's callback URL is an HMAC-sealed, TTL-bound token encoding the binding, verified on POST; satisfies F12's "opaque server-generated grant id" with zero storage | Needs F12 sign-off; fallback is an in-memory map (breaks on restart mid-task) |
| Push subscriptions | **Open — shared with F19 (§9-3)**. Web Push requires the sender to hold per-device subscription objects; a stateless service cannot. Options: (a) LangGraph Store on the user's deployment via connector routes (keeps D-003: state lives in *their* org; open-swe stores prefs in Store — F12 §9-Q10 precedent); (b) small local file/SQLite on the `apps/server` volume (honest, self-host-friendly, breaks "no DB" letter but not spirit — device endpoints, not user content); (c) Context Hub repo (diffable but wrong tool) | Decide with F19 before M4 |
| Session store fallback (if sealed cookie exceeds size limits) | Not built unless F05 §9-5 forces it | Isolated behind the session interface (F05 risk table) |
| Rate-limit counters, SSE fan-in state | In-process memory | Per-instance is acceptable at the §3.2 scale target |

### 3.5 Deployment, CORS, health

- **Self-host (primary)**: `docker-compose.yml` runs `apps/web` (Next.js) + `apps/server` (uvicorn) — the P-005 trade-off mitigation, verbatim. Compose is the reference topology in the self-deploy guide ([04 M4](../04-roadmap.md) docs exit).
- **Hosted guidance**: `apps/server` needs a long-lived container host (SSE relays + webhook receivers rule out serverless-per-request platforms); no deploy target is pinned by any source doc — F01 §9-Q4, carried here as §9-2. `apps/web` deploys to Vercel (F01 previews).
- **Vercel-only / demo mode (P-004)**: `apps/web` alone, fixtures-powered demo mode, **zero credentials, zero `apps/server`** — the service is not deployed at all in this mode ([06 §4](../06-frontend-implementation.md)). The web app must render its full demo surface with the server absent, not erroring toward it.
- **CORS**: browser calls to `/api/*` carry the session cookie → `Access-Control-Allow-Origin` exactly the configured `apps/web` origin(s) (`DW_ALLOWED_ORIGINS`, no wildcard — wildcard + credentials is invalid anyway), `Allow-Credentials: true`. Recommendation: same-site deployment (one parent domain, e.g. `app.example.com` + `api.example.com`) so SameSite=Lax cookies flow without third-party-cookie trouble; a Next.js rewrite fronting `/api → apps/server` is a supported convenience for single-domain setups (flag: proposal). `hooks/*` and `infra` routes send no CORS headers (not browser surfaces).
- **Health**: `GET /healthz` (process live) and `GET /readyz` (config validated + sealing key usable); readiness does **not** probe LangSmith upstream (an upstream outage should not knock a proxy that can still serve session/demo pages out of rotation).

### 3.6 Project shape, local dev, testing

- **Workspace member** per F01: root `pyproject.toml` `[tool.uv.workspace] members = ["packages/agent", "apps/server"]`, single `uv.lock`, shared ruff/pytest config, Python ≥3.11, wrapper `package.json` so `turbo run lint|test|dev` spans it.
- **Stack**: FastAPI + uvicorn (uvicorn is the ecosystem-default ASGI server — flag: norm-based recommendation; FastAPI itself is P-005). App assembled from per-domain routers (`auth/`, `proxy/`, `github/`, `environments/`, `onboarding/`, `push/`, `hooks/`) matching the owner-spec seams so neighbor specs map 1:1 to modules (F12 §3.6's single-module rule generalized).
- **`pnpm dev`**: turbo `dev` runs `apps/web` (`next dev`) and `apps/server` (`uv run uvicorn --reload` via the wrapper) concurrently; `.env` at `apps/server` supplies dev config; `DW_ALLOWED_ORIGINS=http://localhost:3000`. Demo mode (`apps/web` fixtures) requires neither process beyond `next dev`.
- **Testing** (runs in F01's `python` CI job): pytest + FastAPI's ASGI test client for unit/route tests; recorded-fixture tests for GitHub interactions (F12 task 2); **contract tests against `langgraph dev`** for the passthrough — relay a Spike-3 golden-transcript run through the proxy and byte-compare the SSE event stream against the direct connection (same fixtures as [F02](./02-m0-spikes.md) Spike 3); the F05 threat-model suite (strip-then-inject, fail-closed, SSRF allowlist) and F12's `test_zero_secrets_in_sandbox` both execute against this service. Fork-PR safety: all F28 CI tests run secret-free (mocks/`langgraph dev`); live-platform tests are nightly-only (F01 §6).

## 4. Contracts

### 4.1 Endpoint inventory (consolidated; semantics owned per rightmost column)

Paths are pinned here (F28-owned); payload semantics stay with the owner spec. Milestone = when the route ships.

| Route | Class | M | Semantics |
|---|---|---|---|
| `GET /healthz` · `GET /readyz` | infra | M0 | §3.5 (F28) |
| `POST /api/auth/oauth/login` → redirect · `GET /api/auth/oauth/callback` | session | M1 | OAuth code+PKCE, DCR bootstrap, sealing ([F05 §3.2](./05-auth-and-identity.md)) |
| `POST /api/auth/key` | session | M1 | key validate + seal + workspace requirement ([F05 §3.3](./05-auth-and-identity.md)) |
| `GET /api/auth/session` · `POST /api/auth/logout` | session | M1 | session introspection (non-secret fields only); sign-out + revocation ([F05 §3.2](./05-auth-and-identity.md)) |
| `GET /api/auth/workspaces` · `POST /api/auth/workspace` | session | M1 | org/workspace listing + session-side switch ([F05 §3.2](./05-auth-and-identity.md); exact upstream endpoint F05 §9-6) |
| `ANY /api/proxy/control/{path:path}` | session | M1 | control-plane passthrough (`api.host.langchain.com` → `api.smith.langchain.com` fallback per [research 20](../../research/20-gapfill-mda-api.md)); strip-then-inject `X-Api-Key`/bearer + `X-Tenant-Id` ([F05 §4](./05-auth-and-identity.md), [F04 §auth matrix](./04-sdk-and-agent-sources.md)) |
| `ANY /api/proxy/source/{sourceId}/{path:path}` | session | M1 | data-plane passthrough to a registered source URL incl. SSE relay (§3.2); injects `trusted_backend` headers `X-MDA-Ingress-Secret` + `X-MDA-Actor-Id` [+ `X-MDA-Tenant-Id`] from session ([F05 §3.4](./05-auth-and-identity.md)) |
| `GET /api/onboarding/capabilities` · `POST /api/onboarding/deploy` · `GET /api/onboarding/deploy/{id}/events` (SSE) · `POST /api/sources/validate` | session | M1 | [F06 §4](./06-onboarding-and-deploy.md) internal table, adopted verbatim |
| `GET /api/github/install-url` · `GET /api/github/installations` · `GET /api/github/installations/{id}/repos` · `GET /api/github/checks` | session | M2 | [F12 §4.3](./12-github-and-git-flow.md) |
| `GET /hooks/github/setup` | hooks | M2 | GitHub post-install redirect ([F12 §4.3](./12-github-and-git-flow.md)) |
| `POST /hooks/github/proxy-callback/{grant}` | hooks | M2 | sandbox auth-proxy callback: proxy POSTs `{host, port}` → `200 {headers}`, TTL-bound (60–3600 s platform bounds), any failure ⇒ non-200 ⇒ proxy fail-closed 502 ([F12 §4.2](./12-github-and-git-flow.md); [research 20](../../research/20-gapfill-mda-api.md) fact 12); grant per §3.4 |
| `GET/POST /api/environments` · `GET/PUT/DELETE /api/environments/{name}` · `POST /api/environments/{name}/build` · `GET /api/environments/{name}/build/logs` (SSE) · `GET /api/threads/{thread_id}/sandbox` | session | M2 | [F11 §4.3](./11-execution-and-environments.md), adopted verbatim |
| `POST /api/push/subscriptions` · `DELETE /api/push/subscriptions` | session | M4 | device subscription register/remove ([F19](./19-notifications-and-push.md); storage §9-3) |
| `POST /hooks/runs/{grant}` | hooks | M4 | run-completion webhook receiver (`webhook` param on run create, [02 §7](../02-architecture.md)) → push fan-out; payload treated as untrusted ([04 criterion 5](../04-roadmap.md)) |
| `POST /hooks/context-hub` | hooks | v1.x | `context_hub.commit.created.v1`, HMAC-verified → L2 review loop ([F23](./23-org-intelligence-v1x-consolidation.md); [07](../07-org-intelligence.md)) |
| Insights provisioning glue | session | M3 | via `/api/proxy/control` unless F22 needs orchestration routes — placeholder, shapes owned by [F22](./22-org-intelligence-v1.md) (O-007) |

### 4.2 Service-level invariants

1. **F05 contracts 1–7 are binding** on every `session` route: sealed cookie; strip-then-inject (`Authorization`, `X-Api-Key`, `X-Tenant-Id`, `X-MDA-*` never accepted from clients); target allowlist (control-plane hosts + registered deployment URLs only — no open relay, private-network targets refused outside local mode); fail-closed 401/403 with zero upstream calls.
2. **Hooks routes authenticate independently** (grant URL / HMAC / provider state) and are rate-limited (§6); they never read the session cookie.
3. **SSE relay is content-transparent**: no parsing, reordering, or re-framing of protocol-v2 events; `Last-Event-ID` passes through; golden-transcript byte-equivalence is the regression gate (§3.6).
4. **Boot validation**: missing/invalid required config (per enabled feature set, §3.3 table) aborts startup with a named error; `readyz` stays red until valid.
5. **Route stability**: paths in §4.1 are the contract for `apps/web`/`packages/sdk`; changes require updating this table and the F04 passthrough stub in the same PR.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Upstream SSE drops mid-relay | Terminate client SSE cleanly (connection close, no synthetic events); client rejoins with `Last-Event-ID` ([02 §7](../02-architecture.md)) |
| Client disconnects mid-relay | Upstream request cancelled immediately; no orphaned upstream streams (asserted by test) |
| Slow client on a fast stream | Bounded buffer + backpressure (§3.2); memory flat under the soak test (§7-6) |
| Upstream 429 (gateway limits, e.g. 2000/10 s — [research 20](../../research/20-gapfill-mda-api.md)) | Status relayed as-is; no server-side retry (retry policy belongs to SDK/agent middleware) |
| LangSmith upstream down | Proxied routes 502/504 with typed error body; `readyz` unaffected (§3.5); demo mode unaffected (no server) |
| Proxy-callback grant expired / sandbox outlives TTL | Verification fails → non-200 → proxy 502 in sandbox → tool error + retry ([F12 §5](./12-github-and-git-flow.md)); never fail-open |
| Server restart mid-task (stateless) | Sessions survive (cookie-sealed); token caches cold; sealed grants (§3.4) still verify; in-flight SSE relays drop and clients rejoin |
| Run webhook arrives for unknown/expired grant | 404, logged, counted; no fan-out — prevents blind-POST probing |
| Context Hub webhook bad HMAC | 401, constant-time compare, rate-limit bucket |
| Two `apps/server` instances behind an LB | Supported only if all state is per §3.4 stateless options; in-memory-grant fallback and in-memory rate limits are documented as single-instance-only |
| `apps/web` served from an origin not in `DW_ALLOWED_ORIGINS` | CORS-blocked; startup log prints configured origins to make this diagnosable |
| Demo mode with server accidentally configured | Fixtures never mix with live sources ([F06 §5](./06-onboarding-and-deploy.md)); demo pages make zero `/api` calls |

## 6. Security & privacy

This service holds the org's most sensitive material (ingress secret, GitHub App private key, sealed operator credentials). F05 §6 is the governing threat model; F12 §6 governs the GitHub surface. Service-level hardening checklist (each row lands as a test or a documented manual check, §7-7):

- **Fail-closed defaults everywhere**: no session → 401 before any upstream call; unknown proxy target → 403; callback/webhook verification failure → non-200; missing feature config → feature disabled at boot, routes 404, never a degraded-auth fallback.
- **No secret ever logged or traced**: structured logging with a denylist redactor (`Authorization`, `X-Api-Key`, `X-MDA-Ingress-Secret`, cookies, minted tokens, VAPID/private keys); config `repr` masked (§3.3); audit logs carry ids, never values (F12 §6 mint-log rule).
- **Constant-time comparison** for all secret/HMAC checks (ingress secret upstream precedent: MDA compares constant-time — [research 20](../../research/20-gapfill-mda-api.md)).
- **SSRF/open-relay**: allowlist enforcement on every proxied request incl. redirect targets; loopback/private ranges only in explicit local mode (F05 §5).
- **Rate limiting on public (`hooks/`) endpoints** and auth endpoints (`/api/auth/*`): per-IP + per-grant token buckets, in-memory v1 (§3.4); 429 with no detail leakage. Proxy-callback additionally bounded by grant TTL.
- **Untrusted-payload boundaries**: run-webhook and Hub-webhook bodies are data, never rendered as markup or fed to prompts without the `<...payload>` boundary convention ([02 §10](../02-architecture.md); [04 criterion 5](../04-roadmap.md)).
- **Container posture**: non-root user, read-only filesystem except the declared volume (DCR file, optional push store), no shell in image (distroless/slim — proposal); TLS terminates at the operator's proxy/host — compose ships an HTTPS-required note since cookies are `Secure`.
- **Dependency hygiene**: rides F01's supply-chain rules (pinned deps, weekly grouped updates, SHA-pinned actions); `uv.lock` covered by the update bot (F01 §9-Q2).
- **Privacy**: no user database; nothing persisted beyond §3.4; all user data flows terminate in the operator's LangSmith org or GitHub — "your org, your data" ([F05 §6](./05-auth-and-identity.md)).

## 7. Acceptance criteria

1. Fresh clone: `uv sync && turbo run test --filter=server` green; boot with valid minimal config serves `healthz`/`readyz`; boot with a missing required var exits non-zero naming the variable.
2. Passthrough: a golden-transcript run relayed via `/api/proxy/source/...` is byte-identical (SSE payload) to the direct connection, including a `Last-Event-ID` resume mid-run (contract test vs `langgraph dev`).
3. F05 acceptance 1–5 (sealing, strip-then-inject, fail-closed, sign-out) pass against this implementation; forged client `X-MDA-Actor-Id` arrives upstream as the session's actor.
4. F12 §4.2 callback behaviors pass here: valid grant → `{headers}` within TTL bounds; expired/unknown grant, unknown host, mint failure → non-200; `test_zero_secrets_in_sandbox` wired per F12 task 13.
5. `docker compose up` brings up web + server; sign-in → task stream works cross-container with cookies + CORS per §3.5; killing and restarting `apps/server` mid-session requires no re-auth (stateless restart, §5).
6. Soak: N concurrent relayed streams (N per the §3.2 scale target, pinned in the test) for 30 min with one deliberately slow client — flat memory, no upstream connection leak.
7. Hardening checklist (§6) fully covered: log-capture test proves redaction; rate-limit 429s observed on `hooks/` flood; every row has a test or a checked runbook item.
8. Demo mode: `apps/web` with no server deployed renders the full fixture surface with zero requests to `/api/*` (network-capture assertion).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Adopt F01's skeleton: router layout (§3.6), config loader + boot validation + masked repr, `healthz`/`readyz`, structured logging w/ redactor | F01 task 3 | AC-1; redaction test green |
| 2 | Session layer: cookie sealing, strip-then-inject middleware, target allowlist (implements F05 tasks 3) | 1 | F05 contracts 1/2/6 integration-tested (AC-3) |
| 3 | Control-plane passthrough (`/api/proxy/control`) incl. host fallback + `X-Tenant-Id` injection | 2 | F04 plane-router matrix rows pass against it |
| 4 | SSE relay (`/api/proxy/source/...`): streaming, backpressure, cancellation, `Last-Event-ID`, `trusted_backend` injection | 2 | AC-2; disconnect-cancellation test |
| 5 | Auth routes (key entry M1; OAuth login/callback/logout per Spike-1 posture) | 2, F05 tasks 4/6 | F05 AC-1/2/5 (AC-3 here) |
| 6 | Onboarding routes hosting F06 orchestration (incl. server-originated SSE) | 3 | F06 task 4/8 DoD met on these paths |
| 7 | CORS + compose file (web+server) + self-host deploy doc section; local-dev wiring in turbo `dev` | 1 | AC-5; `pnpm dev` runs both, demo mode runs neither (AC-8) |
| 8 | `github/` module hosting: mint/cache (F12 task 2), session routes (F12 task 3), sealed-grant proxy-callback (F12 task 5 + §3.4 proposal) | 2 | AC-4; sealed-grant design reviewed with F12 |
| 9 | Environment routes hosting F11 §4.3 (registry, build + SSE logs, sandbox status) | 3 | F11 task 2 DoD on these paths |
| 10 | Rate limiting on `hooks/` + auth routes; hardening pass + threat-model test suite (with F05 task 14) | 2–9 | AC-7 |
| 11 | Push: subscription routes + run-webhook receiver + VAPID fan-out (storage per §9-3 resolution) | F19 design, §9-3 | F19 pipeline demo: run completes → device notification (M4) |
| 12 | Soak/perf harness for the relay | 4 | AC-6 automated (nightly) |
| 13 | v1.x: Context Hub webhook consumer (HMAC verify → F23 handoff) | F23 design | Signed fixture verified; bad-HMAC 401 test |

## 9. Open questions

1. **P-005 ratification** — this entire spec is written against a provisional decision; reversal is cheap only before M0 ([decisions](../decisions.md)).
2. **Hosted deploy target** for `apps/server` (long-lived container host; which one to document?) and whether CI gets any preview deploy — no source doc answers (F01 §9-Q4 shared).
3. **Push-subscription storage** (shared with [F19](./19-notifications-and-push.md)): deployment Store vs local volume file vs Context Hub — §3.4 options; blocks task 11. Related: how run-completion webhooks are authenticated (the `webhook` run param is a bare URL — is any signature provided upstream, or is the per-run grant URL the only control?).
4. **Sealed stateless grant** for the proxy callback (§3.4) — acceptable to F12, or does callback-caller authentication (F12 §9-Q1) demand server-held state?
5. **Run-webhook payload shape** — what exactly does Agent Server POST at run completion? Needed for F19's payload contract and the untrusted-boundary handling ([02 §7](../02-architecture.md) confirms the param, not the body).
6. WebSocket passthrough: ever needed, or does the direct-from-client posture permanently cover WS use cases (desktop)? ([03 §5](../03-ui-spec.md) marks WS "where beneficial".)
7. Does `langgraph dev` behind the proxy need special-casing beyond the loopback allowlist exemption (F05 §5) — e.g. no-auth header set?
8. Multi-instance story: is single-instance a documented v1 constraint, or do we require the stateless-grant + external-store options from day one (§5 two-instances row)?
9. Session-scoped vs env-scoped control-plane credentials for *unattended* work (M3 schedules glue, F22 provisioning): sessions expire with cookies — does M3 force an optional server-held service-key mode? (Touches F05 §9-7.)

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| P-005 reversed after code exists | Low (per decision note: cheap pre-M0 only) | High rework | Ratify at M0 exit; F01 keeps the skeleton thin until then |
| Relay becomes a perf/reliability bottleneck on the hot path | Med | Med | §3.2 escape valves (direct-from-client postures); soak test AC-6; scale target stated honestly in docs |
| Two-deployable friction hurts self-host adoption (the P-005 trade-off) | Med | Med | Compose as the blessed path; demo mode needs zero server; single-container option (server serving built web assets) evaluated post-v1 |
| Secret concentration makes `apps/server` the highest-value target | Certain | High | §6 checklist, fail-closed defaults, minimal state, container posture; blast-radius notes per secret (F12 §6 down-scoping) |
| Statelessness erodes feature-by-feature (push subs, session store, grants) | Med | Med | §3.4 is the single ledger of state; any addition requires updating it + a decision-log entry |
| SSE proxying subtleties (buffering proxies, compression, LB idle timeouts) break streams in real deployments | Med | Med | Deploy docs pin required proxy settings; golden-transcript relay test catches framing regressions; client resume is the safety net |
| FastAPI/uvicorn choices drift from ecosystem norms we claimed | Low | Low | Both flagged as norm-based recommendations (§3.6); swap is contained to the app entrypoint |
