# Web application agent instructions

These instructions apply to `apps/web` in addition to the repository root guidance.

## Ownership

`apps/web` owns the Next.js product surface: routes, layouts, product composition, browser session behavior, minimal same-origin request mediation, and fixture/live application composition through the same client contracts. It does not own durable product state, application business APIs, upstream LangChain wire contracts, reusable design primitives, desktop host behavior, or Python agent behavior.

- Import semantic identities, capabilities, statuses, and reducer types from `packages/domain`; import Deep Work query/mutation/stream services from `packages/sdk`.
- Import shared tokens and components from `packages/ui`; consume deterministic application scenarios from `internal/fixtures` through the injected fixture client, never as UI-owned records.
- Keep route-specific orchestration in the app. Move reusable presentation to `packages/ui`, pure semantics to `packages/domain`, application-client logic to `packages/sdk`, and provider contracts to `apps/api`.
- Do not import from `deep-work-frontend`; port reviewed code and then maintain it here.

## Data and streaming boundaries

- Components must not call LangSmith, Agent Server, Fleet, Managed Deep Agents, sandbox, GitHub, or Postgres directly. Live product operations go through the shared FastAPI service and SDK client.
- Keep ordinary queries and mutations in SDK services over the application API. Keep the React streaming hook as a thin composition layer over the SDK application-stream client; do not turn it into a general data client or provider transport.
- Select an `AgentSource` explicitly and scope all thread, run, approval, schedule, and agent actions to that source. Cross-source views aggregate per-source results and retain source identity.
- Render capabilities from the source manifest. If a source lacks a feature, show an unavailable, alternative, or documented link-out state. Never make an inert control look live.
- Preserve the opaque Deep Work application cursor and checkpoint identity across background, reconnect, and route transitions. Upstream protocol-v2/legacy cursors remain server-side.

For HITL, render the normalized ordered batch. Maintain the index relationship between `actionRequests[]`, `reviewConfigs[]`, and decisions. Support only decisions allowed for that action. Reject is an ordered source decision. There is no user-visible force-resolve action in v1; stale projections disappear through refresh/reconciliation, and cancellation remains a separate verified action.

## Server and client separation

- Default to server components for static composition and non-interactive reads when that improves security or payload size. Add `use client` only at the smallest interactive boundary.
- The FastAPI service owns OAuth callbacks, API-key mediation, GitHub App token mediation, push fan-out, durable sessions, and other secret-bearing exchanges. Next.js server routes may provide a narrow same-origin facade but must not duplicate those workflows or stores.
- Never serialize server secrets, provider tokens, secure cookie values, or secret-bearing upstream errors into client props, browser storage, URLs, analytics, or logs.
- Use secure, `HttpOnly`, `SameSite` cookies for web sessions where applicable. Provider/API keys and server credential references are forbidden in browser storage even in local development; supply local credentials to FastAPI through approved environment/secret tooling.
- Validate redirect targets, source endpoints, uploaded files, attachment metadata, webhook payloads, and deep links before use.

## Fixture and live modes

- Use the browser-local UI harness for isolated visual/state work and the API-backed product demo for end-to-end behavior. Only the product demo proves application-service, persistence, worker, object, recovery, and telemetry integration.
- Both modes use the same routes, components, normalized domain types, state reducer, responsive behavior, and action affordances.
- Compose the injected fixture application client in the app from `internal/fixtures`. SDK, domain, and UI packages must not depend on one another in reverse to obtain fixtures.
- Make the UI harness deterministic, network-free, and visibly identified. The
  product demo may call only its isolated loopback/internal API, stream, object,
  and telemetry services; it denies external/provider traffic and uses no real
  credentials. Destructive-looking fixture actions update only fixture state and
  announce that no external system changed.
- A live feature is incomplete until the equivalent fixture state and parity test exist. A fixture feature is not proof that the live contract works.

## Experience states

Every route and major panel must deliberately handle the applicable states: initial loading, incremental streaming, empty, no search results, permission denied, unauthenticated, source unavailable, offline, stale cache, reconnecting, retryable error, terminal error, partial multi-source result, interrupted, cancelled, and success.

- Do not replace existing data with an empty screen while refreshing.
- Identify stale and partial data visibly and preserve safe read access when possible.
- Cancellation, retry, rename, archive, delete, approval, and deploy controls must have pending, duplicate-submit, success, and failure behavior.
- Restore focus after dialogs, sheets, route changes, and approval submissions. Announce streaming and mutation outcomes without reading every token to assistive technology.

## React state model

- Use App Router URL/segments for shareable navigation, search, filter, and selection state where privacy permits.
- Use the SDK plus the reviewed, exactly pinned TanStack Query v5 integration for ordinary server state, invalidation, cancellation, and mutation status. Record its boundary in the frontend ADR; it never owns active stream truth or offline mutation replay.
- Use the pure `packages/domain` reducer plus the SDK application-stream client for active task state. Do not mirror token/event state into a global everything store.
- Use local component/feature reducers for transient interaction and an explicit draft service for retained composer state. React context is for stable composition dependencies, not high-frequency stream data.
- Server Components own stable/public shell and safe initial reads; Client Component islands own task stream, composer, approvals, virtualized activity, terminal/diff, offline, and other interactive behavior.

## Responsive and accessible UI

- Build mobile layouts from the same information architecture and actions, not a reduced mock. The approved bottom navigation and rail-to-sheet behavior must preserve task source and pending-review context.
- All critical flows must work with keyboard and screen reader: sign-in, source selection, create task, follow a run, steer, cancel, approve or reject, inspect an artifact, and recover from disconnect.
- Use semantic controls, visible focus, adequate targets, AA contrast, reduced-motion fallbacks, and status text in addition to color or iconography.
- Virtualize large task and event lists without breaking focus, reading order, anchor links, or live updates.
- Treat model markdown, tool output, terminal text, diffs, artifacts, and fetched content as untrusted. Sanitize rendering and protect against executable links and unsafe HTML.

## Verification

- Test route and reducer behavior with deterministic fixtures first, then add adapter and authenticated end-to-end coverage for live behavior.
- Include keyboard-only and narrow viewport coverage for release-critical journeys.
- Test offline/reconnect with an opaque application cursor, server-side full hydration fallback, duplicate mutation protection, expired sessions, permission failures, and a partial failure from one of multiple sources.
- Keep type checking strict. Do not use `ignoreBuildErrors`, broad `any`, or duplicated wire types to bypass an SDK mismatch.
