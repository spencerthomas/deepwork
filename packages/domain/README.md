# @deepwork/domain

Pure, client-safe values shared by Deep Work clients and adapters.

The package currently exposes:

- source-qualified thread and run keys;
- evidence-bearing capability values and safe summaries; and
- task/presentation state types and guards.

Import only from `@deepwork/domain`. Provider payloads, HTTP DTOs, React, browser
and Node APIs, environment access, and side effects do not belong here.

The package scripts are declarations for the downstream lock and executable
verification cells. They have not been run by the authoring cell.
