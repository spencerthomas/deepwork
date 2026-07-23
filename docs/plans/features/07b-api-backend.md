# U7b · `apps/api` — Python backend (FastAPI)

*Feature deep-dive · 2026-07-23 · Milestone M1 (foundational; spans M1–M3) · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Specs: [../application-architecture.md](../application-architecture.md), [../code-conventions.md](../code-conventions.md), [../../plan/02-architecture.md](../../plan/02-architecture.md) §5–§7*

> **New unit** introduced by the [application-architecture](../application-architecture.md) decision: the control-plane/auth/push/webhook glue moves out of Next.js route handlers into one **stateless Python backend** shared by web, desktop, and mobile. Follows LangChain Python conventions ([code-conventions.md](../code-conventions.md) §2).

---

## Goal

Build the single backend all Deep Work clients share: a **stateless FastAPI service** (no database in v1) that owns auth, the LangSmith control plane, push fan-out, webhook ingestion, and GitHub-token brokering — using the first-class Python `langsmith` / `langgraph-sdk` / `langchain-auth` SDKs. It is the "LangChain-native" server side. It is explicitly **not** in the run-stream byte path (clients stream `useStream` directly against the deployment).

---

## Boundaries (what it does / doesn't)

**Does**
- Terminate operator auth (OAuth 2.1 + device flow + API-key brokering); issue a signed client session; mint short-lived scoped tokens/identity headers for the direct stream.
- Wrap the LangSmith control plane: deployments, agents (`/v1/deepagents/*`), crons, Context Hub, sandboxes.
- Fan out run-completion webhooks to Web Push / APNs / FCM / desktop.
- Ingest external webhook/schedule payloads behind the untrusted-content boundary.
- Mint short-lived GitHub App installation tokens for the sandbox auth-proxy callback.
- Auth-enforced proxy in front of the agent's sandbox file/diff connector routes.

**Doesn't**
- Proxy the run stream (client-direct via `useStream`).
- Persist product data (no DB in v1; LangSmith is the system of record).
- Hold long-lived third-party tokens (LangSmith Agent Auth brokers per-user tokens at runtime; we never store them).

---

## Endpoint surface (v1)

Grouped by concern. All under `/v1`. Auth via the signed session (httpOnly cookie for web same-origin; `Authorization: Bearer <session>` for desktop/mobile).

### Auth (`/v1/auth/*`) — gated by M0 Spike 1 (U3)
| Method · path | Purpose |
|---|---|
| `GET /auth/login` | Begin OAuth 2.1 PKCE (redirect to LangSmith authorize). |
| `GET /auth/callback` | Exchange code→token; establish session; redirect. |
| `POST /auth/device/start` | Begin RFC 8628 device flow (desktop). |
| `POST /auth/device/poll` | Poll device-flow completion. |
| `POST /auth/api-key` | Key-paste fallback: validate + establish session (key held server-side, never returned). |
| `POST /auth/logout` | Revoke session. |
| `GET /auth/session` | Current operator/workspace identity for the client. |
| `POST /auth/stream-token` | Mint a short-lived scoped token/identity headers for a specific thread's direct stream. |

### Control plane (`/v1/agents`, `/v1/deployments`, `/v1/threads`, `/v1/crons`, `/v1/hub`, `/v1/sandboxes`)
| Area | Endpoints (representative) | Backed by |
|---|---|---|
| Deployments | `GET /deployments`, `POST /deployments`, `GET /deployments/:id` (+ tarball upload + revision poll) | `langgraph-sdk` / control-plane REST |
| Agents (fleet) | `GET /agents`, `GET /agents/:id`, `PATCH /agents/:id`, import/export | `/v1/deepagents/*` |
| Threads (inbox) | `GET /threads` (search/aggregate), `GET /threads/:id`, `POST /threads` (dispatch) | `langgraph-sdk` threads |
| HITL decisions | `POST /threads/:id/decisions` (approve/edit/reject/respond) | `respond()`/`respondAll()` |
| Crons (schedules) | `GET/POST/PATCH/DELETE /crons` | crons API |
| Context Hub | `GET/PUT /hub/repos/*` (instructions/skills/memories) | hub REST |
| Sandboxes | `GET /sandboxes/:threadId/{tree,file}` (auth-enforced proxy) | connector routes |

### Push & webhooks (`/v1/push`, `/webhooks`)
| Method · path | Purpose |
|---|---|
| `POST /push/subscribe` | Register a Web Push / APNs / FCM subscription for the operator. |
| `DELETE /push/subscribe` | Unregister. |
| `POST /webhooks/run` | Receive run-completion webhook from a deployment → fan out. |
| `POST /webhooks/github` | GitHub App events (installation, checks). |

### GitHub token broker (`/internal/gh-token`)
`POST /internal/gh-token` — called by the **sandbox auth proxy callback** (`{host,port}` → `{headers}`), mints a TTL-bound GitHub App installation token, fail-closed. Not client-facing.

---

## Auth flow detail (the crux of M1)

```
web:     browser → /v1/auth/login → LangSmith authorize (PKCE)
              → /v1/auth/callback (code→token) → set httpOnly session cookie → /tasks
desktop: Tauri → /v1/auth/device/start → show code → poll → session (secure storage)
mobile:  PWA → same PKCE web flow; native (Expo) → device or PKCE + secure storage
fallback: any → /v1/auth/api-key (paste) → validate → session

streaming: client → /v1/auth/stream-token (per thread)
              → client opens useStream(deploymentUrl, {token, identityHeaders}) DIRECTLY
```

The backend is the **auth authority**; it never sits in the stream. Whether OAuth or key-paste ships as the default is decided by **U3 (Spike 1)** — the endpoint set above supports both; the client just shows different buttons.

**Session/cookie topology (open):** serve `apps/web` and `apps/api` under one parent domain (`app.` / `api.` with cookie domain `.deepwork.dev`) so the httpOnly cookie is same-site; desktop/mobile use bearer tokens. Finalized during implementation.

---

## Streaming stays client-direct (restated, because it's load-bearing)

The backend issues a per-thread stream token and identity headers, then steps out. Clients use `@langchain/react` `useStream` straight against the deployment URL. Rationale in [application-architecture.md](../application-architecture.md) §"Why streaming stays client-direct": proxying would break `stream_resumable` + `Last-Event-ID` and add token-path latency. The `packages/sdk` streaming adapters (U7) consume the token from `/v1/auth/stream-token`.

---

## Untrusted-payload boundary

Webhook and schedule-sourced content is wrapped in the untrusted-content boundary before it ever reaches an agent prompt or a client render (adopting Claude Routines' `<routine-fire-payload>` prompt-injection defense, per 02-architecture §10). The backend sanitizes/labels; clients render via a text-safe path (never raw-HTML injection of untrusted content — see U16).

---

## Structure (LangChain Python conventions)

```
apps/api/
  pyproject.toml            # uv; requires-python >=3.11; groups test/lint/typing/integration
  Makefile                  # test/lint/format/type targets
  deepwork_api/
    __init__.py
    _version.py             # __version__
    py.typed
    main.py                 # FastAPI app factory
    auth/                   # oauth.py, device.py, api_key.py, session.py, stream_token.py
    control_plane/          # deployments.py, agents.py, threads.py, crons.py, hub.py, sandboxes.py
    push/                   # subscribe.py, fanout.py (web_push/apns/fcm adapters)
    webhooks/               # run.py, github.py, untrusted.py
    github/                 # app_tokens.py (installation-token minting)
    clients/                # langsmith_client.py, langgraph_client.py (SDK wrappers)
    errors.py               # typed errors + codes
  tests/
    unit_tests/             # no network (socket-disabled), SDK calls mocked
    integration_tests/      # against langgraph dev / a test deployment
```

- `from __future__ import annotations`, `X | None`, `collections.abc`, keyword-only new params, Google docstrings, return types everywhere.
- FastAPI + `uvicorn`; Pydantic models for request/response (mypy `pydantic.mypy` plugin).
- No dynamic-eval / unsafe deserialization of request bodies; `msg` variable for errors; no bare `except`.

---

## Test scenarios

- **Happy path (auth):** valid API key via `/v1/auth/api-key` establishes a session; `/v1/auth/session` returns the operator identity.
- **Happy path (control plane):** `GET /v1/threads` returns the aggregated inbox from a mocked `langgraph-sdk` (unit) and a real `langgraph dev` (integration).
- **Happy path (stream token):** `POST /v1/auth/stream-token` returns a short-lived token the client uses to open `useStream` directly.
- **Happy path (HITL):** `POST /v1/threads/:id/decisions` with approve resolves the interrupt via `respond()`.
- **Security:** the LangSmith key / GitHub token never appears in any client-facing response body (unit assertion).
- **Security:** a webhook payload with embedded markup passes through the untrusted boundary and is labeled/sanitized.
- **Error path:** invalid API key → 401 with a typed error code, not a stack trace.
- **Error path:** `/internal/gh-token` fails closed (returns no headers) when the installation token can't be minted.
- **Edge case:** expired session → 401; client re-auths.

---

## Verification

- `make -C apps/api test` (unit, socket-disabled) and integration tests against `langgraph dev` pass.
- `ruff check` + `ruff format --check` + `mypy` clean.
- A signed-in client drives the full loop (dispatch via `/v1/threads`, stream direct, approve via `/v1/threads/:id/decisions`).
- No secret leaks in responses (test-enforced).

---

## Open questions / deferred

- **Session/cookie topology** (shared parent domain vs proxy) — finalize in implementation.
- **Deploy target** for the stateless service (self-host container vs managed) — document a reference deploy in U19.
- **How much sandbox file browsing is proxied vs client-direct** — decide with U13.
- **Rate limiting / abuse controls** on public webhook endpoints — add before public launch (M4).

---

## Dependencies

- **Upstream:** U1 (uv workspace, `apps/api` stub), U3 (auth posture), U4 (control-plane/deploy shapes), U5/U7 (stream-token consumed by SDK adapters).
- **Downstream:** U8 (sign-in wires to these auth endpoints; Next keeps only a thin callback), U9/U10 (inbox/detail call control-plane + stream-token), U11 (decisions endpoint), U13 (gh-token + sandbox proxy), U15/U16 (agents/crons/push endpoints), U18 (push fan-out to PWA/desktop).
