# @deepwork/sdk

Browser-safe, framework-neutral ports between Deep Work clients and reviewed
application contracts.

The initial surface separates query, mutation, and stream ports and provides
typed safe failures. It intentionally contains no React hooks, cache, provider
SDK, route, generated DTO, credential, cursor, or live transport. A missing
transport is represented by an explicit `capability-unavailable` result.

Import only from `@deepwork/sdk`; domain values come from `@deepwork/domain`.
`check-architecture` scans shipped source and verifies intentional failing
fixtures for every enforced rule: UI/self, framework, provider, raw network
package/API, Node API, environment access, local ESM extension, and
computed/template dynamic import.
The allowlist additionally rejects deep imports, package path escapes, and
server/Tauri/route/fixture/generated/database zones with repair diagnostics.
`package-check` packs SDK and domain output, inspects SDK public files and exports,
rejects workspace-protocol leakage, installs both archives offline into an empty
temporary consumer, imports `@deepwork/sdk`, and compiles a strict TypeScript
consumer against both packed declaration surfaces. Test typechecking resolves
named public entries directly to source without requiring `dist`.

The Vitest setup denies browser and Node network primitives for every SDK unit
test. Unknown/unverified capability failures are non-retryable; only
the coherent `unavailable` + `source-unavailable` pair is marked recoverable.

These package scripts are reserved for the downstream lock and executable
verification cells and have not been run by the authoring cell.
