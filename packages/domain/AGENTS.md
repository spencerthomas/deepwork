# Domain package agent instructions

`@deepwork/domain` owns deterministic, framework-neutral client semantics.

- Keep every external identity source-qualified. Never expose an unqualified
  provider ID as a complete key.
- Capability support requires evidence. Unknown or unverified support remains
  unavailable and carries only an enumerated safe reason.
- Do not import SDK, UI, React, Next.js, browser or Node APIs, generated DTOs,
  provider packages, environment state, or network clients.
- Keep local ESM imports explicit with `.js` runtime extensions.
- Test public entry points and source-collision behavior. Test records must be
  synthetic and contain no credentials or raw customer content.
- Keep `check-architecture` and `package-check` distinct. The former proves green
  source plus intentional negative fixtures; the latter proves the built archive
  and an offline empty-consumer import.

After the shared lock exists, the verification cell may run the package scripts.
Until then, use only the static checks authorized by the active ExecPlan.
