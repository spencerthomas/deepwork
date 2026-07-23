# @deepwork/sdk

Browser-safe, framework-neutral ports between Deep Work clients and reviewed
application contracts.

The initial surface separates query, mutation, and stream ports and provides
typed safe failures. It intentionally contains no React hooks, cache, provider
SDK, route, generated DTO, credential, cursor, or live transport. A missing
transport is represented by an explicit `capability-unavailable` result.

Import only from `@deepwork/sdk`; domain values come from `@deepwork/domain`.
The package scripts are reserved for the downstream lock and executable
verification cells and have not been run by the authoring cell.
