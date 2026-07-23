---
feature_id: DW-AGENT-002
title: Agent index, detail, and health
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [web, api, sdk]
surfaces: [web, pwa, desktop]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-FE, SRC-DW, SRC-LC]
dependencies: [DW-AGENT-001, DW-FND-005]
contract_gates: [SPIKE-SOURCE-001, SPIKE-FLEET-001]
last_reviewed: 2026-07-23
---

# Agent index, detail, and health

## User outcome

A user can find the right agent, understand who owns its configuration, judge whether it is healthy enough for the intended work, and start a task with the correct source and assistant identity. They do not need to open LangSmith for ordinary discovery, but Deep Work links to the authoritative source for unsupported administration and traces.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype contains an Agents destination, agent cards, health-like labels, configuration sections, and simulated actions. | `SRC-FE` | Interaction evidence | Preserve discovery and detail intent; do not treat controls as working scope. |
| The vision requires source-aware agents and a task-first workflow. | `SRC-DW` | Product intent | Agent identity must include its source; dispatch may never rely on display name alone. |
| Classic deployments can provide assistant/deployment information and run provenance. | `SRC-LC` | Documented with exact fields pending pinned contract fixtures | Use a classic adapter and normalize only verified fields. |
| MDA and Fleet expose equivalent enumerable agent catalogs and health. | Internal assumption | Unknown/gated | MDA is capability-detected; Fleet read/invoke is absent until its spike. |

Health is a Deep Work summary of dated evidence, not a claim that every runtime exposes a universal health endpoint. `SPIKE-SOURCE-001` and, for Fleet, `SPIKE-FLEET-001` must define each signal before this plan becomes implementation-ready.

## Scope, ownership, and non-goals

The web owner delivers the five-primary-tab Agents experience in Next.js/PWA and the same responsive UI in Tauri. The FastAPI service aggregates application registrations and verified source metadata. The TypeScript SDK provides cursor-safe queries and dispatch mutations; the Python agent package has no catalog ownership.

In scope:

- agent index with name, source/runtime, model label when verified, tool count when verified, schedule availability, last application task/run, normalized health, configuration authority, and access restriction;
- URL-backed search and filters for source, runtime, health, capability, and ownership;
- agent detail areas for Overview, Configuration, Schedules, Environment, and Deploy, with sections hidden or read-only by capability;
- probe history, current version/revision evidence, recent tasks, trace deep links, and limitation explanations;
- source-correct task dispatch with immutable source/assistant binding at submission.

Non-goals are Fleet CRUD, MDA deployment management, enterprise RBAC administration, arbitrary upstream search, a copied trace waterfall, billing analytics, chat-to-configure, and claiming a field exists across runtimes when it is only present in the prototype.

## Primary journeys

### Find and start an agent

1. The user opens Agents and immediately sees cached application records with freshness labels while sources refresh independently.
2. They filter by source and capability, search application-indexed names, and compare health and ownership.
3. They open an agent and review limitations, last verified source state, recent work, and environment/schedule availability.
4. They select Start task; Deep Work carries the immutable source ID and source-native assistant identity into the composer.
5. Dispatch rechecks authorization and invoke capability before creating the application task.

### Diagnose a degraded agent

1. A source or agent row shows the failing signal, observation time, and blast radius.
2. The user opens history, distinguishes stale metadata from authentication, permission, and upstream errors, then re-probes if authorized.
3. Safe source-native trace or configuration links remain available; unsupported mutations stay disabled.
4. Recovery updates the row without altering historical tasks.

### Inspect externally owned configuration

1. A user opens an MDA- or Fleet-bound agent.
2. The page states which system owns deployment and configuration.
3. It exposes only spike-verified read/invoke actions, otherwise offering export, official CLI guidance, or an allowlisted deep link.

## Complete state matrix

| State | Index behavior | Detail behavior |
|---|---|---|
| Initial loading | Preserve table/card geometry and filter controls; announce loading once. | Show titled skeleton with source placeholder. |
| Empty, no sources | Explain source connection and demo entry. | Not applicable; no invented row. |
| Empty, filters exclude all | Show active filter summary and one clear reset. | Existing detail remains addressable by URL if authorized. |
| Healthy/current | Show last verified time and supported primary action. | Show current capabilities, recent task evidence, and source authority. |
| Stale but cached | Keep record visible with stale label; do not imply current health. | Disable freshness-sensitive mutations until refresh/recheck policy passes. |
| Degraded | Identify source-scoped signal and unaffected actions. | Show history, correlation ID, and authorized recovery path. |
| Source unavailable | Keep cached rows, group one source warning, and keep other sources interactive. | Render cached facts with a prominent unavailable banner. |
| Authentication expired | Mark all affected rows without exposing credential detail. | Offer administrator reauthentication; preserve user navigation. |
| Permission denied | Hide or disable the prohibited action and state required role/scope. | Do not turn the detail page into a not-found response unless existence itself is restricted. |
| Agent missing upstream | Show tombstone only where history or registration requires it. | Offer remove registration; preserve related tasks and audit history. |
| Partial metadata | Use “Not reported” with provenance, not zero/none. | Omit unsupported sections or explain capability absence. |
| Search/query error | Retain prior result set as stale and allow retry. | Detail errors remain scoped to the failed panel. |
| Offline | Read cached non-sensitive records and filters; disable dispatch and re-probe. | Show cached snapshot time and offline-safe links only. |
| Reconnecting | Keep interaction stable and update source groups independently. | Revalidate before enabling dispatch or mutation. |
| Dispatch conflict | Keep composer context and explain changed capability/permission. | Refresh health/capability after failure; no duplicate task. |
| Mobile | Replace wide rows with ordered labelled cards; retain source, health, authority, and last run. | Use a select/menu or wrapped tabs, never horizontally clipped tab labels. |
| 1,000+ records | Paginate application results and use accessible virtualization only after semantic testing. | Load recent tasks and history independently. |

## Interfaces and state ownership

The proposed `/api/v1` application contract returns an `AgentSummary` and `AgentDetail` keyed by application agent ID plus source ID and the source-native assistant identity. Fields include display metadata with provenance, configuration authority, normalized health signals with observation times, capability manifest reference, accessible actions, recent application task summaries, and allowlisted deep links. No source credential, raw upstream body, or secret-bearing trace URL is returned.

The service queries sources independently through `DW-AGENT-001`; it does not depend on global thread or agent search. Search indexes only application-owned metadata plus fields explicitly licensed and persisted by the adapter. The application pagination token records a stable sort boundary and per-source progress. Query clients, dispatch mutations, and React streaming hooks are separate modules.

PostgreSQL owns registered agent bindings, normalized display metadata, health observations, task associations, user-visible aliases, and audit events. Source runtimes remain authoritative for their agent configuration, deployment revision, source-native health, and runs. Deep Work stores provenance and freshness for every copied fact.

## Runtime capability and fallback rules

- Classic is the baseline and exposes only fields/actions verified by its pinned fixture.
- MDA catalog/detail fields are shown only when its detected adapter proves them. Configuration and deployment remain official-CLI/source-owned.
- Fleet rows appear only after `SPIKE-FLEET-001` proves discovery or an explicit read/invoke registration; all management remains read-only.
- Local development is marked non-production and is not advertised to hosted users.
- Missing model, tools, schedule, environment, trace, or version data is “Not reported,” not inferred from UI fixtures.
- A failure in one adapter yields a per-source warning and never blocks other rows or demo fixtures.

## Persistence, security, and privacy

Every query is tenant- and actor-authorized before aggregation. Source-native identifiers are treated as opaque and paired with source ID to avoid collisions. Health checks are safe, rate-limited, cached, and restricted to calls accepted in adapter fixtures. Deep links use allowlisted origins and no embedded credentials. Raw prompts, tool arguments, artifacts, and trace content are not indexed for agent search.

Aliases and filters may persist as application preferences; upstream metadata obeys freshness and retention policies. Removing a registration detaches future discovery but preserves tombstones needed by audit/task history. Logs and analytics use pseudonymous IDs and never source tokens.

## Responsive and accessible behavior

Desktop uses a semantic table with real headers, sortable-state announcements, visible focus, and a non-color health label. At narrow widths, cards retain the same information hierarchy and expose actions in a labelled menu. Detail tabs are keyboard reachable and become a select or wrapped list before overflow. Error summaries focus the affected source group without stealing focus during background refresh. Reduced motion applies to health changes and skeletons.

The first cached result should paint without waiting for all sources. Source refreshes are cancellable and bounded. Virtualization may ship only if screen-reader row position, keyboard traversal, and filter-result announcements pass acceptance tests.

## Metrics and guardrails

- Median time to identify the source and degradation reason is under ten seconds in task-based usability tests.
- 100% of visible actions agree with the current normalized capability and authorization decision.
- 100% of dispatches bind an application source ID and source-native assistant identity; zero display-name routing.
- Healthy sources remain interactive when another source fails in all contract scenarios.
- Search and filter remain responsive at 1,000 registered application records under the agreed performance budget.
- Guardrail: no field is rendered as an authoritative zero/false when its source value is absent or unverified.

## Dependencies and readiness gates

Depends on `DW-AGENT-001`, `DW-FND-005`, session/workspace selection, task composer/dispatch, and the tracing/deep-link policy in `DW-OPS-002`. MDA and Fleet sections inherit their adapter spikes. Readiness requires an accepted field-provenance schema, stable application pagination design, capability-to-action map, health-signal rubric, and accessible large-list test results.

## Rollout and rollback

1. Ship fixture/demo records and classic-only index/detail behind an Agents flag.
2. Add per-source degradation, tombstones, and large-list testing before general access.
3. Enable Start task only after identity binding and idempotent dispatch pass end-to-end tests.
4. Add MDA and Fleet rows independently when their adapters are accepted.

Rollback disables source-specific refresh or actions while preserving cached records, task provenance, and classic access. A bad health normalizer can be reverted to “Unknown” without deleting upstream or application data.

## Executable acceptance scenarios

1. **Mixed catalog:** Given two healthy classic sources and one failing fixture source, when Agents loads, then the healthy rows are usable and one scoped source warning is shown.
2. **Identity-safe dispatch:** Given duplicate agent display names on different sources, when the user starts from one detail page, then the created task contains that source ID and assistant identity and invokes only that adapter.
3. **Permission-limited detail:** Given an actor who can view but not deploy, when detail loads, then configuration facts remain visible and every deployment mutation is absent or disabled with an explanation.
4. **Stale/offline:** Given cached rows and lost connectivity, when the app restarts, then rows display their snapshot time and dispatch/re-probe are disabled until revalidation.
5. **Upstream deletion:** Given an agent with historical tasks that disappears upstream, when refreshed, then a tombstone preserves task links and allows authorized registration removal.
6. **Fleet gate:** Given an unaccepted Fleet spike, when the index loads, then no Fleet CRUD request or management action is issued.
7. **Accessible responsive use:** Given keyboard-only input, 200% zoom, and a 375 px viewport, when the user filters, opens detail, and selects Start task, then source, health, and authority remain perceivable and operable.
8. **Large list:** Given 1,000 application agent records and one source timeout, when a user filters and paginates, then results meet the performance budget and the timeout does not reset successful source progress.
