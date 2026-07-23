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
package/API, Node API, environment access, and local ESM extension.
`package-check` packs SDK and domain output, inspects SDK public files and exports,
rejects workspace-protocol leakage, installs both archives offline into an empty
temporary consumer, and imports `@deepwork/sdk`.

These package scripts are reserved for the downstream lock and executable
verification cells and have not been run by the authoring cell.
