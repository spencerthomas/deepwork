# @deepwork/domain

Pure, client-safe values shared by Deep Work clients and adapters.

The package currently exposes:

- source-qualified thread and run keys;
- evidence-bearing capability values and safe summaries; and
- task/presentation state types and guards.

Import only from `@deepwork/domain`. Provider payloads, HTTP DTOs, React, browser
and Node APIs, environment access, and side effects do not belong here.

`check-architecture` scans shipped source and verifies intentional failing
fixtures for framework, browser/network, provider, Node, and internal-package
boundaries. `package-check` packs built output, inspects its public files and
exports, rejects workspace-protocol leakage, installs it offline into an empty
temporary consumer, and imports `@deepwork/domain`.

These package scripts are declarations for the downstream lock and executable
verification cells. They have not been run by the authoring cell.
