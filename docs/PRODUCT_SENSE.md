---
title: Deep Work product sense
status: canonical
last_reviewed: 2026-07-23
owners: [product]
---

# Deep Work product sense

Deep Work is an open-source control surface for delegating, supervising,
approving, and verifying long-running agent work from desktop and phone. V1 makes
one loop dependable: connect a supported agent source, start bounded work, follow
real progress, respond to ordered approvals, inspect evidence and artifacts, and
reach a useful result without confusing a fixture or UI state for runtime truth.

## Audience and promise

The primary v1 user is an individual technical operator working inside an
organization or workspace. Tenant and actor identity are present from the first
schema, but complete team administration and RBAC are later work. Coding targets a
reviewable draft pull request with tests and evidence; research and writing use the
same task loop with journey-specific outputs.

Deep Work complements rather than replaces LangGraph Agent Server, LangSmith
Deployment and traces, source-owned sandboxes, GitHub, and official deployment
tools. Classic LangSmith Deployment is the supported public baseline. Managed Deep
Agents and Fleet are capability-detected adapters and stay unavailable until their
named live-contract gates pass.

## Product beliefs

- Runtime truth outranks plausible UI. Unknown, denied, stale, or unsupported
  capabilities are explicit states.
- Human control is preserved through ordered decisions, visible consequences,
  idempotent mutations, cancellation, recovery, and durable audit.
- “No database” is replaced by data minimization: Deep Work stores the durable
  application state it owns and leaves runs, traces, and source state upstream.
- API-key authentication through the application service is the unconditional v1
  fallback; OAuth ships only after its contract spike passes.
- Responsive web owns the complete phone journey. PWA and Tauri are qualified
  enhancements; native mobile is deferred.
- The prototype is visual and interaction evidence only. Migration into `apps/web`
  is one-way.

## V1 information architecture

The five primary destinations are Tasks, Approvals, Agents, Schedules, and
Activity. Settings is an account/workspace utility. Agent configuration belongs
with agent detail, project/environment configuration with its owning environment,
and deployment state with an explicit versioned deploy experience.

## Boundaries and success

V1 does not promise global cross-provider thread search, public Fleet CRUD,
arbitrary MDA connector routes, force-resolve, automatic configuration deployment,
automatic merge, or native mobile. Every release claim must map to one of the 12
program acceptance scenarios in [PLANS.md](PLANS.md) and to executable feature
scenarios in [product-specs](product-specs/index.md).

Canonical vocabulary is defined in [the glossary](product-specs/glossary.md).
Decisions and unresolved contract gates are recorded in the
[decision register](design-docs/decisions/index.md).
