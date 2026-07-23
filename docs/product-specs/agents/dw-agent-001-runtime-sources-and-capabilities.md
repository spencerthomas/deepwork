---
feature_id: DW-AGENT-001
title: Runtime sources and capability negotiation
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [api, sdk, platform]
surfaces: [api, web, settings]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-LC, SRC-DW]
dependencies: [DW-FND-003, DW-FND-004]
contract_gates: [SPIKE-SOURCE-001, SPIKE-MDA-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Runtime sources and capability negotiation

## User outcome

A workspace administrator can connect a supported agent runtime once, verify the exact actions Deep Work may perform, and make that source available without exposing credentials or implying capabilities the runtime does not have. A task author sees an actionable fallback whenever a source cannot support an experience.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype expects users to switch among agents and environments. | `SRC-FE` at the pinned frontend commit | Interaction evidence, not contract authority | Preserve the source-switching intent, but replace simulated rows with registered sources. |
| Deep Work needs multiple runtime sources and per-source aggregation. | `SRC-DW` at the pinned plan commit | Product intent | The application service owns a normalized source registry. |
| Classic LangSmith Deployment exposes the public assistant/thread/run baseline. | `SRC-LC` at the pinned docs commit | Documented, subject to pinned-package verification | Classic is the first supported live adapter. |
| Managed Deep Agents access and management are beta- and CLI-shaped. | `SRC-LC` plus `SPIKE-MDA-001` | Gated/beta; exact contract unverified | Detect access and connect an already deployed agent; keep deployment CLI-owned. |
| Fleet supports a stable public read/invoke integration suitable for Deep Work. | Internal plans plus `SPIKE-FLEET-001` | Unknown until spike | No Fleet adapter ships until the spike proves the minimum read/invoke contract. |

The FastAPI/PostgreSQL application-service boundary and normalized capability model are approved product architecture for this proposal. Exact upstream routes, headers, generated client versions, and probe calls remain outputs of `SPIKE-SOURCE-001`, `SPIKE-MDA-001`, and `SPIKE-FLEET-001`; this plan is not implementation-ready until those fixtures are accepted.

## Scope, ownership, and non-goals

The API/platform owners deliver source registration, authorization, safe contract probing, capability normalization, source health, and credential-reference handling. The TypeScript SDK exposes application-service query and mutation clients to Next.js and Tauri. The separate Python agent package does not own source registration or browser sessions.

Supported dispositions are:

| Source | v1 disposition | Registration path |
|---|---|---|
| Classic LangSmith Deployment | Public baseline | Select an authorized deployment or enter a validated API URL and assistant identity. |
| Managed Deep Agents | Private-beta feature flag | Detect beta eligibility, then connect an agent that was deployed with the official CLI. |
| Fleet | Feature flag after `SPIKE-FLEET-001` | Read/invoke connection only when a pinned live contract proves it. |
| Local `langgraph dev` | Development mode only | Explicit loopback endpoint and assistant identity; never enabled in hosted production. |

Non-goals are Fleet CRUD, invented `/v1/deepagents/*` endpoints, arbitrary MDA connector routes, reimplementation of `mda deploy`, a global runtime thread-search endpoint, runtime credential storage in the browser, and capability equivalence across sources.

## Primary journeys

### Connect a classic deployment

1. An administrator opens Workspace Settings > Sources and chooses Classic Deployment.
2. Deep Work obtains or accepts the endpoint, assistant identity, workspace context, and an application-service credential reference.
3. The service validates the host and authorization without returning the secret to the client.
4. A non-destructive probe produces a dated capability manifest and separates unsupported from permission-denied and unknown states.
5. The administrator reviews limitations and confirms registration.
6. The source appears in agent and task selectors; each later action is guarded by the stored capability state.

### Connect a gated source

1. The service checks the MDA or Fleet adapter gate before presenting setup.
2. MDA users connect an already deployed identity and receive official CLI guidance for lifecycle changes.
3. Fleet users may continue only after the accepted spike enables a read/invoke adapter.
4. If access or the minimum contract is absent, Deep Work returns to the classic path without creating a nominal source.

### Recover a degraded source

1. A background or user-triggered safe check marks a source stale, unauthorized, or degraded.
2. Existing application metadata remains visible while unsafe mutations are disabled.
3. An administrator reauthenticates or re-probes.
4. Capabilities change only after a complete, auditable result; other sources remain usable throughout.

## Complete state matrix

| State | Required behavior |
|---|---|
| Loading registrations | Stable skeleton and source count placeholder; no blank settings panel. |
| Empty workspace | Explain classic deployment, local development, and demo choices; identify administrator permission required. |
| Probe running | Show stages, elapsed time, cancel-safe navigation, and that no source is active yet. |
| Valid full source | Enable only capabilities reported by the accepted adapter and show probe time/version. |
| Valid limited source | Register with explicit limitation badges and contextual fallbacks. |
| Unknown capability | Treat as unsupported for mutation; offer a contract/probe explanation, never optimistic enablement. |
| Permission denied | Distinguish from unsupported; name the missing scope without exposing upstream response content. |
| Authentication failed or expired | Do not activate a new source; preserve a degraded existing registration and offer reauthentication. |
| Probe validation error | Keep form values except secrets, focus the first error, and provide a correlation ID. |
| Probe timeout/upstream error | Hosted v1 requires retry before activation; local development may retain an explicitly unverified draft only. |
| Offline before save | Preserve non-secret form state locally, do not claim registration, and retry only with user confirmation. |
| Offline after registration | Show cached metadata as stale, disable network mutations, and retain other cached sources. |
| Reconnecting | Back off with a visible retry state; never run concurrent destructive probes. |
| Stale manifest | Continue safe reads, block newly risky operations, and request re-probe based on policy or upstream version change. |
| Source removed upstream | Show a tombstone and remove-registration action; preserve task/audit references. |
| Mixed-source partial failure | Return successful source results plus per-source errors; never collapse to a global failure. |
| MDA gate absent | Hide beta setup and offer classic deployment; do not show an inert wizard. |
| Fleet spike/gate absent | No Fleet connect action; existing imported evidence remains documentary only. |
| Mobile | Use a step flow with the same warnings and capability detail; never request raw secrets through an unsafe custom keyboard. |

## Interfaces and state ownership

The application has two deliberately different models. Server-only
`AgentSourceRecord` contains operational connection details and is never
serialized. `/api/v1` returns credential-free `AgentSourceView`. Exact resource
names may change during API review, but ownership is fixed:

- both models carry application source ID, source kind, display name, lifecycle state, owner workspace, and source-qualified assistant identity;
- only `AgentSourceRecord` carries validated operational endpoint, source workspace context required for calls, and server-only `authRef`—never an access token or API key;
- `AgentSourceView` carries only a sanitized endpoint label or separately validated authorized deep link, credential health, and no generic proxy target;
- every public capability entry carries state (`available`, `unavailable`, `gated`, `permission-denied`, or `unknown`), observation time, adapter version, contract version, evidence class, and safe reason;
- the public view carries last successful check, stale-after policy, degradation reason, and safe source-native metadata without exposing secret-manager identity.

Queries and mutations remain separate from the React streaming hook. Task/thread aggregation fans out through one source adapter at a time and records source-native cursors; it never calls a nonexistent global search API. The service may return an application pagination token that encapsulates per-source progress without claiming an upstream global cursor.

PostgreSQL owns registrations, workspace bindings, manifests, probe history, audit events, and idempotency records. The approved credential broker owns secrets. The browser may cache non-sensitive labels and stale indicators, but never authentication material or a capability override.

## Runtime capability and fallback rules

- Classic uses only calls verified against the pinned official package/live fixture.
- MDA is capability-detected and CLI-first. Deep Work may read/invoke only what `SPIKE-MDA-001` proves and never manages deployment behind the CLI.
- Fleet read/invoke remains absent until `SPIKE-FLEET-001` resolves authentication, identity, lifecycle, and minimum methods.
- A missing schedule, sandbox, file, HITL, or stream capability folds to a read-only explanation, source deep link, or disabled experience owned by the consuming plan.
- Permission denial never becomes a permanent unsupported result; unknown never becomes supported because a UI control exists.
- Adapter failure is source-scoped and cannot disable classic or demo mode.

## Persistence, security, and privacy

Only HTTPS origins are accepted outside explicit loopback development. Validation rejects credentials in URLs, redirects to unapproved origins, DNS rebinding, private/link-local/metadata ranges, wildcard hosts, and mixed-scheme redirects. Probe calls have strict method, path, timeout, redirect, response-size, and content-type allowlists. Upstream bodies are untrusted, redacted, and never rendered as raw HTML.

All registrations are tenant-scoped, actor-authorized, idempotent, and audited. Credential references are encrypted at rest through the approved broker and are redacted from logs, telemetry, exports, and client errors. Removal revokes the binding without deleting task history. Retention and erasure apply independently to source metadata, credentials, and historical provenance.

## Responsive and accessible behavior

Connection steps have semantic headings, persistent labels, error summaries, keyboard focus recovery, and text equivalents for every status icon. Capability tables collapse into labelled groups below 640 px without hiding evidence or restrictions. Progress and re-probe completion use polite live announcements. Reduced motion disables decorative progress transitions. All actions remain usable at 320 CSS px and 200% zoom.

## Metrics and guardrails

- 100% of runtime actions are guarded by a current normalized capability decision.
- Zero source credentials or raw upstream error bodies reach browser storage, analytics, or notifications.
- Zero probe false positives in accepted contract fixtures; unknown and permission-denied are measured separately.
- At least 95% of successful classic registrations reach a verified manifest without support intervention.
- Partial-source failure never makes a healthy source unavailable in contract and end-to-end tests.
- Guardrail: no adapter is enabled in production without an accepted pinned-package/live-contract fixture and rollback flag.

## Dependencies and readiness gates

Depends on `DW-FND-003`, `DW-FND-004`, workspace/session authorization, the credential broker, and the canonical identity/status model. `SPIKE-MDA-001` and `SPIKE-FLEET-001` block their respective adapters. The classic adapter also needs an accepted pinned-package/live-contract fixture for auth headers, assistant identity, streaming/resume, and safe health calls.

Readiness requires approved source and credential ownership matrices, SSRF threat-model tests, source-adapter fixture tests, and signed-off copy for unknown/unsupported/permission-denied states. Until then, this remains a proposed plan.

## Rollout and rollback

1. Ship demo/local fixtures and classic registration to internal workspaces behind adapter flags.
2. Exercise source degradation, credential revocation, and mixed-source aggregation against pinned fixtures.
3. Enable classic for selected workspaces, then general v1 after security and reliability gates.
4. Enable MDA and Fleet independently only after their spikes and beta eligibility checks.

Rollback disables the affected adapter, blocks new registrations and mutations, retains registrations and historical provenance, and guides users to classic or source-native tools. Database records are not destructively rewritten during adapter rollback.

## Executable acceptance scenarios

1. **Classic happy path:** Given an authorized pinned classic deployment fixture, when an administrator registers it, then `/api/v1` returns a credential-free `AgentSourceView` and dated evidence manifest, the SDK sends a normalized task request to FastAPI, and FastAPI invokes the verified adapter.
2. **Capability fallback:** Given a source fixture without schedules, when a user opens schedule creation, then the action is absent or disabled with a source-specific reason and deep-link fallback.
3. **SSRF rejection:** Given a URL resolving to loopback, link-local, private, or metadata space in hosted mode, when validation runs, then no outbound probe reaches that target and an audited safe error is returned.
4. **Permission classification:** Given valid authentication without invoke scope, when probed, then invoke is `permission-denied`, not `unsupported`, and dispatch remains blocked.
5. **Credential revocation:** Given an active source whose secret is revoked, when a check fails, then the source becomes degraded, its mutations stop, its history remains, and another source still works.
6. **No-beta fallback:** Given a workspace without MDA entitlement or an absent MDA adapter flag, when onboarding reaches runtime selection, then classic deployment is offered and no MDA management route is called.
7. **Fleet gate:** Given `SPIKE-FLEET-001` is unaccepted, when a production client loads source types, then no Fleet connect or CRUD control is present.
8. **Offline recovery:** Given a completed non-secret form and a network loss before confirmation, when connectivity returns, then the form is restored and registration occurs only after explicit retry with one idempotent record.
9. **Fleet read/invoke path:** Given `SPIKE-FLEET-001` has accepted exact read,
   invoke, HITL, identity, auth, and error cells for the current account, when an
   administrator connects Fleet and a user lists an agent, dispatches through the
   inbox, and completes an approval, then every call flows through FastAPI with
   source-qualified identity, only accepted capabilities appear, and no Fleet CRUD
   or inferred route is requested.
