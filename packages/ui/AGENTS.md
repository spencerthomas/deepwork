# UI package agent instructions

These instructions apply to `packages/ui` in addition to root guidance. Wave 0
contains design tokens only; React package scaffolding belongs to the active Wave 1
ExecPlan.

## Boundary

This package owns shared tokens, theme foundations, presentational components, and
stories. It may consume client-safe semantic types from `packages/domain` once that
package exists. It must not import `packages/sdk`, network clients, generated DTOs,
app routes, Next.js server modules, Tauri APIs, provider payloads, database models,
fixtures, or environment secrets.

Components receive normalized data and callbacks through explicit props. They do
not fetch, authenticate, select sources, mutate durable state, or decide product
authorization. Business reducers stay in domain; components may own transient
presentation state.

Reusable status primitives do not choose a heading level. Use labelled
non-heading text or an explicit consumer-owned heading slot so composition does
not corrupt document hierarchy.

`tokens.css` and the shared preset are the token source. Do not duplicate
product color, spacing, type, radius, elevation, or motion constants in app code.

## Component and accessibility contract

- Prefer semantic variants such as status, emphasis, density, and capability over
  provider- or route-specific props.
- Make applicable loading, empty, partial, error, offline, permission, stale,
  reconnecting, interrupted, disabled, cancelled, and success states explicit.
- Treat markdown, model/tool/terminal/diff text, URLs, images, and artifact metadata
  as untrusted. Raw executable HTML/content is off by default.
- Meet WCAG 2.2 AA with native elements, accurate names, visible focus, logical
  keyboard order, non-color status, controlled live announcements, reduced motion,
  high contrast, 200% zoom, narrow reflow, and supported touch targets.

Stories use deterministic synthetic schema-valid records from
`internal/fixtures`; they never own the fixture adapter or contain real users,
repositories, credentials, signed URLs, or customer content. Test behavior,
keyboard/focus, accessibility, sanitization, long/localized content, and responsive
states rather than snapshots alone.

Import the component API only from `@deepwork/ui`, tokens from
`@deepwork/ui/tokens.css`, component styles from their named CSS entry point, and
domain values only from `@deepwork/domain`. Keep local ESM imports explicit with
`.js` runtime extensions.

Package scripts are declarations for the downstream lock and executable
verification cells. Until the shared lock exists, run only the install-free
static checks authorized by the active ExecPlan and report executable package
checks as unexecuted.

Keep `check-architecture` and `package-check` distinct. The former proves green
source plus intentional negative fixtures; the latter proves packed UI/domain
archives, CSS/token/preset exports, and an offline empty-consumer runtime and
TypeScript import. Boundary diagnostics must name the legal destination,
`ARCHITECTURE.md#package-graph`, and the local repair command.
