# Application API agent instructions

These instructions apply to `apps/api` in addition to the repository root guidance.

## Service role

`apps/api` is one independently locked Python 3.12 distribution with separate API and worker entry points for the Next.js web/PWA and Tauri desktop clients. It owns application sessions, durable Postgres state, source configuration, server-only credential references, application-level authorization, capability detection, per-source aggregation, upstream streaming, durable background work, inbound webhooks, push fan-out, object-store metadata, and secret-bearing integration mediation.

It is not the Deep Work agent runtime. Keep `packages/agent` independently deployable and invoke agents, LangSmith, Agent Server, sandboxes, GitHub, and other providers through explicit verified adapters. Do not import the agent graph as application business logic.

## API boundary

- Define the public application API with versioned FastAPI request/response models and generated OpenAPI. Treat that schema as the client boundary consumed by `packages/sdk`.
- Keep transport models, persistence models, external provider payloads, and domain models distinct. Normalize provider-specific casing and errors at adapters.
- Require stable source identity on source-local task, thread, run, approval, schedule, agent, and artifact operations.
- Cross-source lists fan out per source, preserve provenance and per-source cursors, and return explicit partial failures. Do not model a nonexistent global provider search endpoint.
- Use typed error envelopes for authentication, authorization, validation, unavailable capability, conflict, stale version, rate limit, retryable upstream failure, and terminal upstream failure.
- Mutations must be idempotent where retries are possible. Require idempotency keys or optimistic concurrency tokens for duplicate-sensitive actions such as task creation, approval submission, cancel, archive, deployment changes, and webhook processing.
- Use capability manifests. Classic LangSmith Deployment is the baseline; Managed Deep Agents and Fleet-specific operations stay disabled or link out until verified for the current tenant and access tier.
- Public source responses expose credential health and safe display metadata, never `authRef`, provider tokens, forwarding headers, or reusable signed URLs.
- All first-party clients use the versioned application stream in v1. Compose the pinned public async LangGraph SDK behind a source adapter and keep provider cursor/recovery state server-side. Do not import private SDK stream-controller modules.

## Python structure and commands

- Keep `pyproject.toml`, `uv.lock`, `Makefile`, README, `deepwork_api/`, and tests package-local. Use `uv`; do not document pip/Poetry/Conda or depend on an implicit root Python environment.
- Use Ruff for formatting/linting and strict `mypy` with `pydantic.mypy`, deprecated-code reporting, and unreachable-code warnings. Production functions have full annotations and public functions use concise Google-style docstrings.
- Use absolute imports. Prefer an exact inline `# noqa: RULE` with a reason over broad per-file ignores; categorical test/script policies are the exception.
- Export deliberate public symbols explicitly and ship `py.typed` if the package becomes importable outside its process entry points. Add public parameters keyword-only and review compatibility before changing signatures.
- The package `Makefile` must provide truthful `format`, `lint`, `typecheck`, `test`, `contract`, `integration`, and `build` targets. Unit tests disable external sockets; integration tests are explicit.

## Layering and process boundary

- `transport/` owns FastAPI routes, SSE envelopes, auth middleware, and webhooks; `application/` owns use cases and transaction/authorization orchestration; `domain/` owns pure entities, policies, errors, and transitions; `ports/` owns implementation-neutral protocols; `adapters/` owns source, persistence, object, secret, GitHub, and notification implementations; `contracts/` owns Pydantic wire models; `bootstrap/` owns validated settings and process composition; `workers/` owns durable handlers.
- Dependencies point inward. Routers do not call SQLAlchemy or provider SDKs directly. Domain/application code does not read environment variables or import FastAPI/provider implementations.
- API and worker run from the same immutable distribution initially but as separate processes. The API never acknowledges accepted durable work that exists only in process memory or FastAPI `BackgroundTasks`.

## Durable state and Postgres

Postgres is authoritative for application-owned durable state. This includes user and session records, org/workspace membership cache, configured sources, opaque credential references, preferences, device registrations, notification subscriptions, idempotency records, webhook receipts, and application metadata that is not authoritative in an upstream platform.

- Write forward and rollback migration notes for every schema change. Review locking, indexes, backfill cost, nullability transitions, and deploy ordering.
- Put transaction boundaries around multi-row invariants. Do not hold a database transaction open while waiting on a provider network call.
- Scope every tenant-owned query by tenant and actor authorization. Prefer repository or query helpers that make unscoped access difficult; test cross-tenant denial explicitly.
- Store upstream identity and cursor fields without conflating task, thread, run, checkpoint, source, assistant, deployment, org, workspace, tenant, or actor.
- Keep browser and desktop caches non-authoritative. Reconcile stale client mutations with explicit versions or conflicts rather than last-write-wins by accident.
- Define retention and deletion behavior for sessions, webhook bodies, notification endpoints, artifacts, audit events, and redacted diagnostics.
- Commit application state and its outbox/job record atomically. Workers use expiring leases, bounded retry/backoff, idempotent handlers, dead-letter visibility, and reconciliation for ambiguous external outcomes.
- Put Deep Work-owned attachment/import/export bytes in private S3-compatible object storage, not database bodies. Persist tenant-scoped metadata, hash/size/type, quarantine/scan state, authorization, retention, and deletion evidence.

## Credentials and integration security

- Store only encrypted credentials or provider-managed secret references. Keep encryption keys outside Postgres and application logs. Plan rotation and revocation before accepting a new credential type.
- Treat operator-to-platform, end-user-to-deployment, and agent-to-service credentials as separate planes. Do not reuse a token across planes because scopes appear compatible.
- Use short-lived, least-privilege tokens for sandboxes and GitHub. Fail closed on tenant, actor, repository, callback host, path, or scope mismatch.
- Validate OAuth state, PKCE, issuer, audience, redirect URI, webhook signatures, replay windows, source URLs, and outbound destinations.
- Apply SSRF protections to user-configurable endpoints: approved schemes, DNS/IP checks, redirect limits, timeouts, response limits, and network policy.
- Redact authorization headers, cookies, tokens, source secrets, user content, artifact bodies, and signed URLs from exceptions, structured logs, traces, metrics, and API responses.
- Render no provider exception directly to clients. Return a stable error code, safe message, source identity, and correlation ID.

## Runtime contract verification

- Keep provider clients behind interfaces with recorded contract fixtures and explicit capability probes.
- Pin SDK and API versions and classify every external behavior as documented, gated/beta, inferred, contradicted, or unknown.
- Preserve protocol-v2 stream event IDs and resume cursors exactly inside the source adapter. Emit a distinct opaque application cursor to clients and test reconnect/full hydration through the application stream.
- Preserve ordered HITL `actionRequests[]`, `reviewConfigs[]`, allowed decisions, and one decision per action. Validate stale or already-resolved interrupts before mutation.
- When official prose, generated clients, and live responses differ, keep the adapter capability off and create a live-contract spike. Never patch around uncertainty with a guessed endpoint.

## Background work, webhooks, and delivery

- Acknowledge verified webhooks only after durable receipt. Process asynchronously with idempotency, bounded retries, dead-letter visibility, and tenant-scoped audit events.
- Make notification fan-out derive from confirmed application or upstream state. Do not treat push delivery as task completion.
- Record job state transitions, attempt count, next retry, terminal reason, and safe correlation identifiers. Avoid queues encoded only in process memory.
- Handle startup, shutdown, cancellation, connection pool exhaustion, provider timeouts, and deployment overlap without losing accepted work.

## Testing and operations

- Unit-test domain and authorization rules; integration-test repositories and migrations against Postgres; contract-test providers from redacted recordings; and end-to-end test authenticated API journeys.
- Test cross-tenant access, expired sessions, revoked credentials, duplicate mutations, webhook replay, partial multi-source failure, provider throttling, reconnect cursor behavior, stale approval races, and migration rollback or forward recovery.
- Fixture/demo support must use isolated deterministic data and must never share production credentials or tenant records.
- Expose health separately for process liveness, database readiness, and dependency degradation. Keep metrics low-cardinality and free of secrets or user content.
- Do not run schema creation implicitly at request time or silently auto-migrate production on application startup.
