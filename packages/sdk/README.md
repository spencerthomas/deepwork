# @deepwork/sdk

Browser-safe, framework-neutral ports between Deep Work clients and reviewed
application contracts.

The public surface separates `TaskQueryService`, `TaskMutationService`, and
`TaskStreamService` and provides typed safe failures. Strict mappers accept only
the reviewed current Deep Work `/api/v1` task, plan, decision, result, evidence,
and named application-event shapes. Unknown fields, enum values, malformed
receipts, missing source/thread bindings, and mismatched task/run/interrupt/
revision correlation fail closed.

Transport implementations are injected. The package intentionally contains no
React hooks, cache, raw fetch/EventSource use, endpoint construction, provider
SDK, credential/reference, environment read, server secret, or custom upstream
protocol. Stream unsubscribe is idempotent and is not cancellation. A malformed
event or sequence gap quarantines the subscription so a later terminal event
cannot bypass missing evidence; consumers must hydrate and subscribe again.
The stream observer exposes explicit bounded connection boundaries. `connected`
is never authoritative recovery; only validated `recovered` or `hydrated`
boundaries can establish replay completeness. Events already covered by an
asserted replay cursor are suppressed, while forward gaps fail closed.
A missing or gated transport is represented by an explicit
`capability-unavailable` result.

Mutation binding resolves the current full pending interrupt. Decision inputs
carry an application-side expected plan revision and must use an allowed current
choice; this concurrency guard is intentionally omitted from the unchanged
local HTTP payload. Accepted application Problems require exact HTTP status/code
pairs and always use SDK-owned safe messages.

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

The Outcome 3 living ExecPlan records the exact source, network-denied test,
architecture, and offline package-validation results for this contract.
