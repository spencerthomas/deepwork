---
title: Deep Work frontend architecture and migration
status: canonical
last_reviewed: 2026-07-23
owners: [frontend, product-design]
---

# Deep Work frontend architecture and migration

V1 uses Next.js, React, and TypeScript for one responsive web application. The PWA
layer is capability-qualified. Tauri is a thin exact-origin host and does not own a
second UI. Expo/native mobile is deferred until its separate product and lifecycle
gates pass.

## Accepted prototype evidence

The current interaction reference is the sibling repository
`deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`. Do not modify it
from this repository and do not import it as a package. Port reviewed tokens,
layouts, and interactions one way into `apps/web`; reimplement behavior against
Deep Work domain and SDK contracts. The exact refresh evidence is recorded in
[the frontend refresh note](references/audits/2026-07-23-frontend-refresh.md).

The accepted refresh changes only `components/sidebar-nav.tsx` and
`components/task-detail.tsx`. The new Interrupt/Resume control is local component
state and therefore simulated. It is not evidence that an upstream run can be
interrupted, resumed, replayed, or recovered.

## Ownership

- `packages/domain`: pure client-safe identities, capability/status model, events,
  reducers, selectors, and safe errors.
- `packages/sdk`: browser-safe `/api/v1` queries/mutations, normalized application
  stream, mapping, recovery, and cancellation.
- `packages/ui`: tokens and presentational components only; no routes, fetches,
  fixtures, generated DTOs, or provider types.
- `apps/web`: routes, layouts, responsive composition, query/stream orchestration,
  accessibility, and fixture entry points.
- `apps/desktop`: a narrow native capability bridge around the hosted web origin.

React components never build provider URLs or handle reusable credentials. Ordinary
queries and mutations remain separate from the active stream reducer. FastAPI owns
source selection, headers, provider cursors, replay/deduplication, and per-source
aggregation.

## Shell and routes

The canonical primary navigation is Tasks, Approvals, Agents, Schedules, and
Activity. Settings is a utility route. The prototype’s seven destinations, eight
run-panel tabs, 22 settings sections, links, controls, and responsive gaps are
mapped to exactly one feature owner in the
[coverage matrix](product-specs/coverage-matrix.md). Prototype-only surfaces retain
their documented disposition and are never silently promoted.

## Migration rule

Each migration slice starts from an owning product spec and reviewed ExecPlan,
ports only the necessary presentation, replaces fixtures with typed domain/SDK
interfaces, implements the complete applicable state matrix, and proves both the
browser-local UI harness and API-backed product demo. Visual comparison alone is
not acceptance.
