# Binding visual reference

These screenshots are the product baseline for Deep Work. They were rendered from the
original front end at commit `26c698b30ff08d5122cfaeedbd4a95296a7884f4` and captured
with Chromium in light mode on 2026-08-03.

The reference is intentionally binding on hierarchy, density, navigation, interaction
placement, and product story. A real API limitation may change copy or disable a control;
it may not silently collapse the designed experience. Any intentional divergence needs a
documented product decision in the release scorecard.

## Viewports

- Desktop: `1440 x 1000` CSS pixels.
- Phone: `390 x 844` CSS pixels.
- Full-page images retain horizontal overflow. Several original phone captures are therefore
  562 pixels wide; that is evidence of the prototype's known narrow-screen overflow, not an
  accepted responsive target. The recovered application must fit 390 pixels and pass a
  separate 320-pixel reflow check.

## Route contract

| Reference | Route | Product obligation |
| --- | --- | --- |
| `login.png` | `/login` | Brand story and trustworthy connection flow |
| `tasks.png` | `/tasks` | Scannable grouped inbox and status access |
| `tasks-new.png` | `/tasks/new` | Choose agent, compose outcome, review approval policy |
| `task-detail.png` | `/tasks/t-901` | Dense task workbench, live run and inspection surfaces |
| `approvals.png` | `/approvals` | Context-rich review and explicit decision |
| `agents.png` | `/agents` | Fleet identity, capability and state |
| `agent-detail.png` | `/agents/swe` | Agent context and configuration hierarchy |
| `schedules.png` | `/schedules` | Recurring work visibility |
| `activity.png` | `/activity` | Inspectable provenance timeline |
| `settings.png` | `/settings` | Contained settings shell |
| `config.png` | `/config` | Original configuration surface retained as design evidence |
| `observability.png` | `/observability` | Original run/trace density retained as design evidence |

The last two routes are reference evidence, not permission to fabricate unsupported API
contracts. Their useful interaction patterns should be carried into truthful task, trace,
agent, and settings surfaces.

## Mechanical enforcement

`reference-contract.spec.ts` verifies the SHA-256 of every immutable prototype capture,
maps every prototype route to a current canonical route screenshot, and applies a bounded
64-by-64 grayscale perceptual delta. `product-journey.spec.ts` separately blocks on the
full-resolution current screenshots. The two checks make the source design binding while
allowing documented copy and truthful contract differences. Intentional visual changes must
update the current screenshot, the manifest threshold only when justified, and the release
scorecard in the same review.
