# @deepwork/domain

Pure, client-safe values shared by Deep Work clients and adapters.

The package currently exposes:

- source-qualified thread, run, interrupt, evidence, and task-scoped application
  event keys;
- deeply snapshotted evidence-bearing capability values, canonical RFC3339
  observation instants, coherent state/reason pairs, and safe summaries; and
- bounded client-safe task, plan, evidence, decision, and receipt values; and
- a pure task projection reducer with canonical attention precedence,
  monotonic event-sequence and plan-revision guards, accepted local transition
  validation, replay deduplication, explicit quarantine/hydration recovery, and
  orthogonal reconnect/stale/source-health state.

Local `/api/v1` status spellings are not presentation vocabulary. SDK mapping
turns them into explicit underlying facts, and the domain derives `needs-review`,
`done`, and the other canonical presentation states. Disconnect, source outage,
missing/malformed events, and stream unsubscribe never infer a terminal outcome.
Evidence projection is capped at 256 records; overflow or an event-sequence gap
quarantines incremental reduction until authoritative hydration.
Opaque identity segments are capped at 200 Unicode code points. Plan revisions
and event sequences have distinct public constants, each currently capped at
`2_147_483_647`. The current API exposes no independent task resource revision,
so this package does not fabricate one.

Import only from `@deepwork/domain`. Provider payloads, HTTP DTOs, React, browser
and Node APIs, environment access, and side effects do not belong here.

`check-architecture` scans shipped source and verifies intentional failing
fixtures for every enforced rule: internal-package, framework, provider, network
package/API, browser API, Node API, environment access, local ESM extension,
deep import, path escape, computed/template dynamic import, and
server/Tauri/route/fixture/generated/database zone. Capability evidence accepts
only finite JSON-compatible data and rejects unsupported runtime values.
`package-check` packs built output, inspects its public files and exports, rejects
workspace-protocol leakage, installs it offline into an empty temporary consumer,
imports `@deepwork/domain`, and compiles a strict TypeScript consumer against the
packed declarations. Test typechecking resolves the named public entry directly
to source and does not require pre-existing `dist`.

The Outcome 3 living ExecPlan records the exact source, test, architecture, and
offline package-validation results for this contract.
