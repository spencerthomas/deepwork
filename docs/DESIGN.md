---
title: Deep Work design principles
status: canonical
last_reviewed: 2026-07-23
owners: [product-design, accessibility]
---

# Deep Work design principles

The accepted visual and interaction baseline is
`deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`. It is evidence,
not an implementation dependency or runtime contract. The refresh from `8866d39`
adds a simulated Interrupt/Resume steering control and a sidebar adjustment; it
does not prove provider interruption, resume, streaming, persistence, or recovery.

## Experience rules

- Make task status, source, freshness, actor, and next safe action legible.
- Keep work inspectable: progress, approvals, artifacts, diffs, failures, and
  recovery live in one coherent task history.
- Never use animation, optimistic text, or a mock response to imply upstream
  success. Fixture mode is persistent and unmistakable.
- Preserve user control with explicit consequences, confirmation for destructive
  actions, focus recovery, and undo/retry where the domain permits it.
- Use shared tokens and presentational components; route and network ownership stay
  outside `packages/ui`.

## Required state model

Every supported surface considers loading, empty, partial, error, permission
denied, offline, stale, reconnecting, cancelled, success, and unsupported
capability states. A state that does not apply is documented in the owning product
spec rather than silently omitted.

## Responsive and accessible behavior

Supported flows target WCAG 2.2 AA, keyboard operation, visible focus, semantic
headings and landmarks, non-color status communication, reduced motion, 320 CSS px
reflow, and 200% zoom. On phone, context panels become deliberate sheets or routes;
approval order, evidence, and consequences remain visible. Desktop density never
justifies inaccessible controls or hidden state.

Detailed route and frontend ownership is in [FRONTEND.md](FRONTEND.md); the source
audit is preserved under [references](references/audits/2026-07-22-product-plan-audit/01-frontend.md).
