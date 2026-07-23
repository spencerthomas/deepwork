# SDK package agent instructions

These instructions apply to `packages/sdk` in addition to the repository root guidance.

## Package responsibility

`packages/sdk` is the browser-safe client for the Deep Work application API and application stream. It owns generated OpenAPI transport, deliberate query and mutation services, application-stream transport, request cancellation, DTO-to-domain mapping, safe error translation, public package exports, and client contract tests.

It does not own React presentation, Next.js routes, desktop APIs, provider credentials or credential references, source capability probing, direct LangGraph/LangSmith clients, provider pagination/cursors, cross-source fan-out, server persistence, or Python agent implementation. Those runtime concerns belong to `apps/api`. V1 must remain browser-safe and framework-neutral below its optional React leaf. A future native client may reuse only generated/schema and client-core pieces separately proven platform-neutral; native auth, secure storage, connectivity, stream, and notification transports remain native-owned. React-specific bindings belong in an explicit leaf subpath and depend on framework-neutral services, never the reverse.

## Public interfaces

Import client-safe source identities, capabilities, statuses, normalized events,
and reducers from `packages/domain`. A public source view may carry safe display
origin/assistant metadata and credential state, but never `authRef`, a provider
token, forwarding headers, or a reusable signed URL.

- Separate application query services, mutation services, stream services, and DTO normalization functions. A hook may compose them but must not become the only usable interface.
- Require a source identity for every entity whose upstream identifier is source-local. Use composite identities where collisions are possible.
- Request aggregate lists from FastAPI through one opaque Deep Work cursor. Preserve source identity, partial failures, freshness, and provenance in the normalized result; never call configured providers or expose their cursors.
- Capability checks gate client APIs and UI affordances from the server-supplied manifest. The SDK does not infer runtime support from a source label.
- Return typed unavailable, permission, stale, partial, rate-limit, conflict, and retryable errors. Do not erase upstream distinctions into a generic exception.

## External contract verification

Before changing an application API/event adapter:

1. Start from committed FastAPI OpenAPI/event JSON Schema; generated files are never edited by hand.
2. Regenerate deterministically and review the source schema plus generated diff.
3. Map wire DTOs into `packages/domain` explicitly; do not use generated transport types as UI models.
4. Add runtime, type, malformed-input, cancellation, and compatibility tests.
5. Keep provider-contract classification and live fixtures in `apps/api`; consume only the normalized server result.
6. If the application schema, generated code, and recorded application transcript disagree, fail contract CI rather than adding a cast.

Do not expose guessed Fleet CRUD, `/v1/deepagents/*`, arbitrary Managed Deep Agents connector routes, global thread search, or a reimplementation of `mda deploy`.

## Streaming and HITL invariants

- Preserve the opaque Deep Work application cursor without parsing or regenerating it. FastAPI owns upstream protocol-v2/legacy cursors. Test application disconnect, replay, duplicate event, cursor expiry, full hydration, and terminal completion.
- Keep checkpoint, thread, run, assistant, and source identities distinct.
- Normalize application wire casing once at the DTO-to-domain boundary. Raw provider payloads never enter this package.
- The normalized HITL model preserves `actionRequests[]`, `reviewConfigs[]`, their order, the allowed decisions for each action, and one ordered decision per action.
- Validate batch lengths and action pairing. A malformed batch becomes an explicit recoverable contract error with a redacted raw representation; it must not crash consumers or silently approve anything.
- Model `submit` and multitask strategies only from the normalized application contract. Do not expose provider resume or join signatures behind similarly named wrappers.

## State, credentials, and persistence

- Define explicit ownership for query cache, preferences, task projections, opaque application cursors, pending mutations, and optimistic state. Consumers must distinguish local, cached, and server-confirmed state.
- Do not define, accept, log, serialize, or persist an `authRef` or provider credential type. Public source models expose credential status only.
- Apply tenant, actor, workspace, source, and assistant context deliberately. Do not infer one identity plane from another.
- Design mutations for retries and duplicate submission. Carry upstream idempotency, conflict, and version tokens when available.

## Fixture and test policy

- Consume injected fixture application clients/transcripts from `internal/fixtures`; do not own fixture records or import `packages/ui`.
- Run the same normalization and reducer assertions for fixtures and recorded live payloads wherever possible.
- Golden transcripts must cover streaming messages, tool calls, subagents, todos, files, interrupts, ordered decisions, checkpoints, reconnect, completion, cancellation, malformed events, and version skew as those capabilities are introduced.
- Contract fixtures include their source version and provenance and contain no credentials or customer data.
- Public type changes require compile-time consumer tests and a migration note. Do not use broad `any`, unsafe casts, or UI-specific aliases to hide an upstream change.

## TypeScript package method

- Use the pinned pnpm/Turbo workspace, strict ES2022 ESM, Oxfmt/Oxlint, named exports, explicit export maps, and `.js` extensions for local relative imports.
- Keep `allowJs: false` and contract/type CI free of blanket `skipLibCheck`. Validate untrusted persisted/native/application data with Zod v4 without redefining the FastAPI wire schema.
- Unit tests are `*.test.ts`, integration tests `*.int.test.ts`, public type tests `*.test-d.ts`, and wire tests `*.contract.test.ts`. Unit tests deny external network access.
- Every request/stream accepts `AbortSignal`; normalize timeouts into one cancellation path and release streams/resources deterministically.
- Validate packed tarballs in clean ESM/Next/Tauri consumers. Public behavior changes require a Changeset or explicit no-release classification.
