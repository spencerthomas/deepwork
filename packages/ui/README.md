# @deepwork/ui

Accessible, presentational React primitives for Deep Work.

Public entry points:

- `@deepwork/ui` — named component exports;
- `@deepwork/ui/tokens.css` — the existing CSS token source;
- `@deepwork/ui/status-panel.css` — status primitive styles; and
- `@deepwork/ui/tailwind-preset` — the existing token-consuming Tailwind preset.

Consumers import `@deepwork/ui/tokens.css` and
`@deepwork/ui/status-panel.css` explicitly alongside the component entry point.
The JavaScript entry does not rely on a runtime CSS loader.

`StatusPanel` receives normalized domain values, display text, and callbacks
through props. It does not fetch, infer capabilities, authorize actions, or
render raw HTML. Its unavailable variant has no action prop, so an unknown
capability cannot look enabled. Its labelled title is deliberately non-heading
text so consumers retain control of document hierarchy.

The token and preset sources remain the single source for product color,
typography, spacing, measures, touch targets, radii, and layout. `StatusPanel`
uses those variables and intrinsic wrapping rather than a parallel component
scale or viewport breakpoint. Heading font ships as Inter (OFL); do not commit
commercial font files.

`check-architecture` scans shipped source and verifies intentional failing
fixtures for every enforced rule: SDK/self, Next.js, provider, raw network
package/API, Node API, environment access, local ESM extension,
computed/template dynamic import, and raw HTML.
The allowlist additionally rejects deep imports, package path escapes, and
server/Tauri/route/fixture/generated/database zones with repair diagnostics.
Shipped CSS is scanned separately: `@import` must use a contained relative CSS
path, and dynamic, package, external/scheme, absolute, encoded-traversal, or
escaping `url()` references fail closed.
`package-check` packs UI and domain output, inspects every JavaScript, CSS, token,
and preset export, rejects workspace-protocol leakage, installs the archives and
React offline into an empty temporary consumer, and imports or resolves every
public UI entry point. It also compiles a strict TSX consumer against packed UI
and domain declarations. Test typechecking resolves named public entries directly
to source without requiring `dist`.

These package scripts are reserved for the downstream lock and executable
verification cells and have not been run by the authoring cell.
