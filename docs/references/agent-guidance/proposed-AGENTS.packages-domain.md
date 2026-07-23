# Domain package agent instructions

These instructions apply to `packages/domain` in addition to the repository
root guidance.

## Package boundary

`packages/domain` is the framework-neutral, browser-safe semantic core shared by
the TypeScript SDK, UI, web/PWA, fixtures, Tauri-hosted web application, and any
future native client. It owns opaque identities, source capability values,
normalized entities/events, stable safe error codes, status facts, pure reducers,
selectors, and application invariants that every client must interpret the same
way.

It owns no I/O. Do not import React, Next.js, Tauri, `packages/sdk`,
`packages/ui`, generated OpenAPI DTOs, provider SDKs/payloads, environment
variables, Node-only modules, storage, analytics, or credential types. A domain
type cannot contain `authRef`, provider token, forwarding header, signed URL, or
server-only endpoint configuration.

## Modeling rules

- Use source-qualified opaque identities for upstream-local records. Keep task,
  thread, run, checkpoint, agent, assistant, deployment, source, interrupt,
  decision, file, artifact, attachment, org, workspace, tenant, and actor
  meanings distinct.
- Model capabilities and unknown/unsupported/gated states explicitly. A source
  label never implies support and an unknown event never becomes success.
- Reducers are pure and deterministic. They derive presentation state from
  normalized facts; components cannot assign terminal status directly.
- Preserve ordered HITL `actionRequests[]`, `reviewConfigs[]`, and one decision
  per action. Do not flatten provider batches or accept incomplete decisions.
- Keep transport retryability, UI labels, provider exceptions, and persistence
  records outside semantic values. Define stable safe error codes and let SDK/UI
  map them to transport/presentation behavior.
- Prefer discriminated unions, readonly data, exhaustive checks with a bounded
  unknown variant, and constructors/type guards that make invalid states hard to
  represent.

## TypeScript method

- Use strict ES2022 ESM, Oxfmt/Oxlint, named exports, explicit export maps, and
  `.js` extensions for local relative imports. Set `allowJs: false`; do not hide
  contract problems with `any`, unsafe casts, non-null assertions, or blanket
  `skipLibCheck`.
- Validate truly untrusted/persisted domain inputs with Zod v4 where needed, but
  do not recreate FastAPI's wire schema. The SDK validates/maps wire DTOs before
  domain construction.
- Keep the default package export small. Add subpath exports such as events or
  errors only when they are coherent public surfaces with documentation and
  clean-consumer tests.
- Public exports require TSDoc describing invariants, unknown behavior, and
  compatibility. Public behavior changes require a Changeset or explicit
  no-release classification.

## Verification

- Unit/property tests cover identity collisions, allowed/forbidden transitions,
  status precedence, replay/deduplication facts, stale conflict, cancellation,
  ordered HITL, partial-source failure, unknown events, and serialization-safe
  values.
- Use the same synthetic golden scenarios as Python normalization and UI stories
  through `internal/fixtures`; domain never imports provider recordings or UI.
- Add `*.test-d.ts` coverage for public inference and consumer ergonomics. Pack
  and install the package in clean ESM/Next/Tauri consumers.
- Dependency-boundary CI must fail any framework, transport, provider,
  environment, generated DTO, or credential import.
- Tests are deterministic and network-disabled. A reducer test must fail when
  event order, identity, or decision alignment is broken; snapshots alone are
  insufficient.
