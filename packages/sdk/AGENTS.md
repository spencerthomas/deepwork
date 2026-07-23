# SDK package agent instructions

`@deepwork/sdk` owns browser-safe client ports and reviewed mapping seams.

- Depend on `@deepwork/domain`, never UI, React, Next.js, app routes, provider
  packages, environment secrets, or server-only modules.
- Keep query, mutation, and stream contracts separate. Stream unsubscribe is not
  cancellation and a cache or React hook does not belong in this package.
- Add transport or wire mapping only from an accepted generated contract. Never
  guess endpoints, headers, cursors, fields, or success responses.
- Missing or gated behavior returns a typed unavailable result without making a
  request. Unknown/unverified support is not retryable; source unavailability is
  the recoverable unavailable case.
- Keep local ESM imports explicit with `.js` runtime extensions and test through
  named public entry points.
- Keep `check-architecture` and `package-check` distinct. The former proves green
  source plus intentional negative fixtures; the latter proves packed SDK/domain
  archives and an offline empty-consumer runtime and TypeScript import.
- SDK unit setup denies browser HTTP/stream primitives and Node HTTP/socket
  escape paths for the entire test process.
- Boundary diagnostics must name the legal destination,
  `ARCHITECTURE.md#package-graph`, and the local repair command.

After the shared lock exists, the verification cell may run the package scripts.
Until then, use only the static checks authorized by the active ExecPlan.
