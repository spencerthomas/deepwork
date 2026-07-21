# @deepwork/ui (seed)

Design tokens and (eventually) the shared component library for Deep Work.

Currently contains the **token seed** extracted from the LangChain docs design system
(see [docs/plan/03-ui-spec.md](../../docs/plan/03-ui-spec.md) and the
[design brief](../../docs/design/deepwork-design-brief.html)):

- `tokens.css` — CSS custom properties (colors, type, radii, layout)
- `tailwind.preset.mjs` — Tailwind preset consuming those tokens

Component build-out lands in roadmap M0–M1 (shadcn/ui new-york re-themed to these
tokens; component inventory in the UI spec §4).

Notes:

- Heading font ships as Inter (OFL). The docs site uses commercial TWK Lausanne —
  swap `--font-heading` to rebrand; do not commit commercial font files.
- Grays are machine-derived from the primary; regenerate the ramp if the primary
  hue ever changes.
