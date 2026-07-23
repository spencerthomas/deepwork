<!-- GENERATED: do not edit by hand. -->
<!-- Source: docs/product-specs/coverage-matrix.md; command: python3 tools/docs/generate.py --write -->

# Prototype route inventory

Accepted frontend evidence: `deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`.
This is interaction evidence only. Full controls and settings ownership remains in
the canonical coverage matrix.

- Routes: 13
- Desktop navigation destinations: 7
- Run-panel entries: 0
- Settings entries detected by `SETTINGS-*`: 22

| ID | Route and evidence | Observed state | Owner | Disposition | Planned resolution |
|---|---|---|---|---|---|
| ROUTE-01 | `/` - `app/page.tsx` | Functional redirect to `/tasks`; not session-aware | `DW-FND-002` | v1 | Resolve session/demo/onboarding state before the final landing redirect. |
| ROUTE-02 | `/login` - `app/login/page.tsx` | Simulated workspace, OAuth, device, and API-key UI; actions only navigate | `DW-ONB-001` | v1 | Ship application-session plus server-held API-key baseline; expose OAuth only after its spike passes. |
| ROUTE-03 | `/tasks` - `app/tasks/page.tsx` | Simulated fixture inbox with local filters/grouping | `DW-TASK-001` | v1 | Replace fixtures with authorized per-source aggregation, URL state, stable pagination, and recovery states. |
| ROUTE-04 | `/tasks/new` - `app/tasks/new/page.tsx` | Simulated composer; Dispatch always opens fixture `t-901` | `DW-TASK-002` | v1 | Add durable draft/preflight, idempotent creation, source capability gates, and real pending/failure outcomes. |
| ROUTE-05 | `/tasks/[id]` - `app/tasks/[id]/page.tsx` | Simulated fixture lookup and local-only run controls | `DW-TASK-003` | v1 | Hydrate durable source truth, stream through the accepted adapter, and add reconnect/stale/error behavior. |
| ROUTE-06 | `/approvals` - `app/approvals/page.tsx` | Contract-invalid flattened approvals and local success messages | `DW-HITL-001` | v1 | Rebuild around ordered action/review batches, allowed decisions, freshness, idempotency, and audit. |
| ROUTE-07 | `/agents` - `app/agents/page.tsx` | Simulated global fixture catalog; filters and Clone are inert | `DW-AGENT-002` | v1 | Aggregate registered sources, preserve source identity/authority, and show real health and capability state. |
| ROUTE-08 | `/agents/[id]`, including `id="new"` - `app/agents/[id]/page.tsx` | Simulated builder; chat send and Save do not publish; `new` clones a fixture | `DW-AGENT-003` | v1 | Use detail subroutes for versioned drafts, validation, explicit Deploy, revision history, and safe create/import. |
| ROUTE-09 | `/schedules` - `app/schedules/page.tsx` | Simulated static list; badges are not controls | `DW-OPS-001` | Flagged v1 | Show per-source ownership; enable mutations only for a verified schedule capability or project-deploy workflow. |
| ROUTE-10 | `/activity` - `app/activity/page.tsx` | Simulated static feed and fabricated trace identifiers; sidebar filters inert | `DW-OPS-001` | v1 | Combine authorized application audit events and source run events with safe filters and real trace/task links. |
| ROUTE-11 | `/observability` - `app/observability/page.tsx` | Simulated static metrics and charts | `DW-OPS-002` | Fold | Move slim summaries to Activity and agent detail; retain source-native trace deep links instead of a duplicate product. |
| ROUTE-12 | `/config` - `app/config/page.tsx` | Functional legacy redirect to `/settings` | `DW-FND-002` | Remove | Keep only a measured compatibility redirect, then remove the route. |
| ROUTE-13 | `/settings` and `/settings/:section` - catch-all page | Simulated 22-section local form library; scope and persistence are mixed | `DW-AGENT-004` | Fold | Move workspace controls to workspace Settings, agent controls to Agent detail, environment controls to Environment, and deploy facts to Deploy. |
