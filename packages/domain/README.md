# @deepwork/domain

Pure, client-safe values shared by Deep Work clients and adapters.

The package currently exposes:

- source-qualified thread and run keys;
- deeply snapshotted evidence-bearing capability values, canonical RFC3339
  observation instants, and safe summaries; and
- task/presentation state types and guards.

Import only from `@deepwork/domain`. Provider payloads, HTTP DTOs, React, browser
and Node APIs, environment access, and side effects do not belong here.

`check-architecture` scans shipped source and verifies intentional failing
fixtures for every enforced rule: internal-package, framework, provider, network
package/API, browser API, Node API, environment access, local ESM extension,
deep import, path escape, and server/Tauri/route/fixture/generated/database zone.
`package-check` packs built output, inspects its public files and exports, rejects
workspace-protocol leakage, installs it offline into an empty temporary consumer,
imports `@deepwork/domain`, and compiles a strict TypeScript consumer against the
packed declarations. Test typechecking resolves the named public entry directly
to source and does not require pre-existing `dist`.

These package scripts are declarations for the downstream lock and executable
verification cells. They have not been run by the authoring cell.
