# @deepwork/ui

Accessible, presentational React primitives for Deep Work.

Public entry points:

- `@deepwork/ui` — named component exports;
- `@deepwork/ui/tokens.css` — the existing CSS token source;
- `@deepwork/ui/status-panel.css` — status primitive styles; and
- `@deepwork/ui/tailwind-preset` — the existing token-consuming Tailwind preset.

`StatusPanel` receives normalized domain values, display text, and callbacks
through props. It does not fetch, infer capabilities, authorize actions, or
render raw HTML. Its unavailable variant has no action prop, so an unknown
capability cannot look enabled.

The token and preset sources remain the single source for product color,
typography, radii, and layout. Heading font ships as Inter (OFL); do not commit
commercial font files.

The package scripts are reserved for the downstream lock and executable
verification cells and have not been run by the authoring cell.
