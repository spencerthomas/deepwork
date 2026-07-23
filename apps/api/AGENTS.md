# API package instructions

`apps/api` owns the Python application-service and worker distribution. In this
Wave 1 scaffold it exposes only credential-free process health, fixture demo
status, and an honest worker-unavailable smoke result.

- Keep dependencies inward: `transport/bootstrap -> application -> domain/ports`;
  adapters implement ports.
- Domain code imports no FastAPI, Pydantic, provider, persistence, environment, or
  network modules.
- Do not import `packages/agent`, TypeScript packages, sibling repositories, or
  private upstream internals.
- No credential, `authRef`, arbitrary endpoint/header, provider cursor, or copied
  production content may enter schemas, logs, fixtures, tests, or evidence.
- External dependency resolution is limited to explicit bootstrap. Every other uv
  command is offline and disables Python downloads; an unbootstrapped state fails
  closed. Runtime and tests make no provider/service calls; unit and contract tests
  deny IP sockets and allow only asyncio's local Unix socket pair.
- Run `make check` and `make package-check` from this directory before handoff.
