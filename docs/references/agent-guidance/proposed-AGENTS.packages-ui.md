# UI package agent instructions

These instructions apply to `packages/ui` in addition to the repository root guidance.

## Package boundary

`packages/ui` owns shared design tokens, theme foundations, presentational React components, and stories. It must remain independent of applications and runtime clients. The private product fixture corpus belongs to `internal/fixtures`, not UI.

- It may import client-safe semantic types from `packages/domain`. Do not import `packages/sdk`, generated wire DTOs, app routes, Next.js server modules, Tauri APIs, LangChain clients, provider payloads, database models, or environment secrets.
- Components receive normalized data and callbacks through explicit props. They do not fetch, mutate, authenticate, select an agent source, or decide product authorization.
- Keep task and approval business reducers in the owning domain layer. Components may own transient presentation state such as an expanded panel or draft field.
- `tokens.css` and the shared preset are the canonical token source. Do not duplicate product colors, spacing, type, radius, elevation, or motion constants in app code.

## Component contracts

- Prefer semantic variants such as status, emphasis, density, and capability over route-specific or provider-specific props.
- Make loading, empty, error, offline, permission, stale, reconnecting, interrupted, disabled, partial, and success states explicit when a component renders them.
- Every action exposes pending, disabled reason, validation, success, and safe failure presentation as applicable. Inert controls are not acceptable substitutes for unimplemented behavior.
- Render source and capability provenance where ambiguity could make an action unsafe.
- Treat markdown, model text, tool output, terminal text, diffs, code, URLs, images, and artifact metadata as untrusted. Safe renderers must not expose raw HTML or executable content by default.

## Accessibility

- Build components to WCAG 2.2 AA. Use native elements first, accurate names and descriptions, visible focus, logical tab order, and predictable keyboard interaction.
- Do not encode state only with color, icon, animation, indentation, or spatial position. Status chips include readable text; charts and diffs provide equivalent textual access.
- Dialogs, sheets, menus, tabs, comboboxes, toasts, and virtualized lists must manage focus and announcements correctly.
- Streaming regions announce meaningful state changes at a controlled cadence. Do not place token-by-token text in an assertive live region.
- Support 200 percent zoom, narrow viewports, text expansion, high contrast where available, and `prefers-reduced-motion` without losing information.
- Interactive targets meet supported touch-size requirements, including approval actions on phones.

## Stories and fixture consumption

Fixture records are permanent private product infrastructure under
`internal/fixtures`. UI stories may consume schema-valid scenario records but
must not own, mutate, or publish the application fixture adapter.

- Consume deterministic, synthetic, redacted, source-identified, network-free records. Never add real users, repositories, credentials, signed URLs, or customer content to stories.
- Stories represent every normalized status and important edge state, including batch approvals, malformed safe fallback, multi-source partial failure, reconnect, offline, stale data, long content, missing permission, and mobile layouts as the feature set grows.
- Keep imported records immutable from component code. Simulated application mutations belong to an injected fixture client outside UI.
- Stories cover interaction, keyboard behavior, screen-reader labeling, responsive layouts, light/dark themes, reduced motion, and long or localized text.
- When live normalization changes, update fixtures, stories, and parity assertions in the same change.

## Verification

- Use strict TypeScript, Oxfmt/Oxlint, named package exports, explicit export maps, and `.js` extensions for framework-neutral relative imports. Default exports are not part of this package's public style.
- Test behavior and accessibility rather than snapshots alone. Include keyboard interaction, focus restoration, validation, error recovery, sanitized content, and responsive behavior.
- Run automated accessibility checks on stories and application-level critical journeys; manually verify complex widgets and screen-reader output before release.
- Keep components small enough to test independently. Avoid hidden module state, app-specific singletons, and global side effects.
- Do not accept a visual match that breaks semantic structure, focus behavior, contrast, reduced motion, or fixture/live parity.
