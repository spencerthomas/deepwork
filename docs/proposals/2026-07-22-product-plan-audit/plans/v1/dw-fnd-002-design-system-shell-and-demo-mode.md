---
feature_id: DW-FND-002
title: Design system, application shell, and demo mode
release: v1
status: proposed
decision_status: proposed-for-review
implementation_readiness: not-ready
owners: [web, design-system, product]
surfaces: [web, pwa, desktop]
runtime_scopes: [fixture, any]
source_refs: [SRC-FE, SRC-DW, SRC-HE, SRC-NEXT]
evidence_pins:
  frontend: 8866d39
  canonical_plan: 06f0515
dependencies: [DW-FND-001]
contract_gates: []
last_reviewed: 2026-07-22
---

# Design system, application shell, and demo mode

## User outcome

A user encounters one coherent, accessible Deep Work product across responsive web, qualified installed-PWA cells, and qualified Tauri desktop. They can distinguish live, demo, offline, stale, and degraded-source state at a glance; navigate every permitted destination at any supported viewport; and explore synthetic workflows without authentication or accidental external side effects.

This plan is proposed and prepared for review, not implementation-ready. The final information architecture, token contract, browser support matrix, fixture disclosure, and command-palette permission model require design, product, accessibility, and security approval.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| The prototype at `8866d39` contains useful seams including `AppShell`, contextual rails, `Composer`, `StatusChip`, `ToolCard`, settings primitives, Inter, IBM Plex Mono, and semantic variables. | Direct prototype evidence | High | Preserve interaction intent and useful component boundaries, not generated implementation authority. |
| The prototype exposes seven top-level destinations while canonical planning variously describes five, six, or seven. | Direct contradiction | High | Adopt the reviewed five-primary-tab proposal pending IA approval. |
| The prototype has a token mismatch between RGB triplets and complete color values. | Direct code evidence | High | Normalize tokens before extracting or porting components. |
| Demo and live paths are visually similar in the prototype but demo/live isolation is not a proven contract. | Prototype evidence; simulated | High | Make mode visible and immutable per session, with separate repositories and no silent fallback. |
| Next.js 16/React 19, PWA, and Tauri v2 are the proposed clients over the same TypeScript domain contracts. | Proposed architecture | Medium until review | UI components stay transport-free and platform adaptations occur at application composition boundaries. |

No LangChain external contract is resolved here. Capability names and source health come from `DW-FND-004`; MDA and Fleet remain false unless `SPIKE-MDA-001` and `SPIKE-FLEET-001` pass.

## Scope, ownership, and non-goals

### In scope

- Semantic color, typography, space, radius, elevation, motion, focus, density, icon, and z-index tokens for light, dark, system, high-contrast, and reduced-motion behavior.
- Reusable primitives for text, buttons, inputs, menus, tabs, disclosure, dialogs, sheets, toasts, banners, status, skeletons, empty states, errors, and untrusted-content containers.
- Next.js application shell: header, five primary destinations, workspace/source context, account menu, Settings utility route, contextual sidebar, content region, optional right rail, global banners, and command palette.
- Proposed primary tabs: Tasks, Approvals, Agents, Schedules, and Activity. Settings is a utility route; Observability folds into Activity and agent detail.
- Responsive navigation: desktop tabs/rails, tablet sheets, and phone bottom navigation plus More/account navigation.
- Two explicit fixture levels: a browser-local developer UI harness for isolated component/route states and an API-backed user-facing product demo for end-to-end behavior. Demo entry, marker, synthetic identity, reset, and safe simulation are explicit.
- Consistent loading, empty, failure, offline, reconnect, stale, permission, degraded-source, unsupported-capability, and mobile patterns.
- Visual regression fixtures for every theme, density, state, and responsive breakpoint.

### Ownership

- Design System owns tokens, primitives, accessibility contracts, visual regression baselines, and deprecation policy.
- Web owns shell composition, Next.js routing, responsive placement, focus restoration, and fixture/live repository injection.
- Web/Design System own the UI harness. The application service owns the product-demo fixture adapter, persistence namespace, mutations, worker/object behavior, and reset contract. The shell must not blur their proof levels.
- Product owns IA labels, primary versus utility status, disclosure copy, and demo limitations.
- Security owns untrusted-content boundaries and confirms demo cannot resolve live credentials or endpoints.
- Desktop consumes the same shell and UI package; native chrome and capabilities remain owned by `DW-SURF-002`.

### Non-goals

- Feature-specific data fetching, business mutation semantics, raw LangChain rendering, runtime deployment, or source authentication.
- A second desktop component library, native mobile UI, or one-off page tokens.
- Silent fixture fallback when live data fails, mixing demo and live entities, or presenting simulated controls as production proof.
- Retaining all seven prototype destinations merely because they exist, or hiding unowned settings in an overflow menu.

## Primary journeys

### Live desktop navigation

1. Session and source context load into a dimensionally stable shell.
2. The user switches among the five primary destinations without losing scoped sidebar state.
3. Settings opens as a utility route and preserves a safe return target.
4. Activity exposes slim operational context; source-specific observability links remain within the owning task/agent experience.
5. Keyboard users can reach navigation, content, contextual rail, command palette, and account actions in a predictable order.

### Phone dispatch and approval

1. The user lands on Tasks through bottom navigation.
2. Filters and contextual rail open as sheets; opening and closing restores focus.
3. Approvals is one tap away; Agents remains a direct bottom-nav destination.
4. Schedules, Activity, Settings, workspace, and account actions remain discoverable in More/account navigation.
5. No action is available only through hover, right-click, a wide table, or an unlabeled icon.

### Demo exploration and conversion

1. A signed-out visitor chooses Explore demo.
2. A persistent Demo data badge, synthetic workspace, and bounded fixture clock appear throughout the shell.
3. Mutations call the API-backed product-demo client, update its isolated deterministic server fixture state, and identify themselves as simulation. The developer-only UI harness may update browser-local state but is not the signed-out product demo or end-to-end proof.
4. External actions such as deployment, GitHub installation, push subscription, or live approval explain that sign-in is required and make no outbound call.
5. The visitor can reset fixtures or leave demo for sign-in without mixing identities or cached records.

## Complete state matrix

| State | Required shell behavior | Recovery or transition |
|---|---|---|
| Initial session loading | Render stable landmark skeletons; do not flash unauthorized navigation or guessed workspace identity. | Resolve to demo, signed-out, onboarding, or authenticated shell. |
| Signed out | Show authentication/demo entry only; retain permitted product documentation links. | Sign in or enter demo. |
| Demo active | Persistent text/icon badge, synthetic workspace, reset/exit actions, no live identifiers. | Reset fixtures or create a real session. |
| UI harness active | Developer-only banner states that services/persistence/recovery are not under test; no route may claim end-to-end product proof. | Start product demo for integrated acceptance. |
| Demo fixture empty | Purposeful empty state with reset/sample-generation action. | Generate deterministic sample or reset. |
| Authenticated, no source | Shell and Settings remain usable; primary content directs to source onboarding. | Connect source or enter demo separately. |
| Live healthy | Show real actor, workspace, selected source scope, and permitted navigation. | Normal route transitions. |
| Session refresh loading | Retain safe read-only shell; hold mutations; do not replace identity with fixtures. | Resume or show session-expired recovery. |
| Source loading | Use content skeleton with source identity retained; avoid full-shell reset. | Render data, empty state, or source-scoped error. |
| Source empty | Explain that the source is healthy but has no entities; show owning creation/onboarding action. | Create/connect or change source. |
| Source degraded / partial | Non-blocking warning identifies affected source and capabilities while healthy content remains usable. | Retry or open source settings. |
| Permission denied | Keep allowed destinations; explain required role for the specific control. | Request access, change source/workspace, or go back. |
| Unsupported capability | Omit or disable action according to discoverability policy with an explanation; never fake success. | Connect a capable source or follow gated setup. |
| Offline cold start | Show cached shell only when safe and a clear connectivity/sign-in explanation. | Retry when online. |
| Offline warm start | Show bounded last-known content with timestamp and read-only banner. | Reconnect; no sensitive queued mutation. |
| Reconnecting | Preserve content and focus; display bounded progress and manual retry. | Resume verified state or full hydrate. |
| Stale data | Label freshness and prevent stale destructive decisions. | Refresh before mutation. |
| Route not found | Render accessible error in shell with safe primary destination. | Return to Tasks or prior authorized route. |
| Mobile / narrow viewport | Move rail and secondary actions into labelled sheets/More; bottom navigation respects safe areas. | Preserve route, drafts, and focus across resize/orientation. |
| Reduced motion | Remove beam, pulse, parallax, and nonessential transitions without removing state information. | User preference persists. |
| High zoom or text expansion | Reflow without clipped controls or horizontal page scroll. | Preserve all actions in document order. |
| Untrusted content | Render inside bounded content surface with provenance and safe links. | Expand deliberately; never alter shell chrome. |

## Proposed interfaces

Presentation components receive normalized domain props and events. They cannot import `/api/v1` clients, FastAPI-generated types directly, fixture repositories, authentication, Next.js server actions, Tauri commands, or raw LangChain types.

```ts
type ExperienceMode = "live" | "demo";

interface CapabilityEvidence {
  state: "available" | "unavailable" | "gated" | "permission-denied" | "unknown";
  value?: unknown;
  observedAt: string;
  adapterVersion: string;
  contractVersion: string;
  evidenceClass: "documented" | "live-contract" | "fixture";
  safeReason?: string;
}

interface ShellContext {
  mode: ExperienceMode;
  actorLabel?: string;
  workspaceLabel?: string;
  selectedSourceId?: string;
  connectivity: "online" | "offline" | "reconnecting";
  freshness?: { observedAt: string; stale: boolean };
  capabilities: Readonly<Record<string, CapabilityEvidence>>;
}

interface PrimaryDestination {
  id: "tasks" | "approvals" | "agents" | "schedules" | "activity";
  label: string;
  href: string;
  badge?: { value: number; accessibleLabel: string };
  availability: "available" | "permission-denied" | "capability-unavailable";
}
```

- Next.js owns route composition and obtains `ShellContext` through the TypeScript SDK backed by FastAPI `/api/v1`.
- Tauri loads the same trusted hosted shell and supplies only narrowly approved native capability signals.
- `packages/ui` exports tokens, primitives, and controlled slots; it never decides whether an upstream capability exists.
- Live/product-demo client selection occurs once at application composition and cannot change implicitly after a request fails. The separate UI harness is selected only by developer/test tooling and is visibly non-integrated.
- Command-palette entries are produced from authorized normalized actions, include availability reasons, and invoke the same query/mutation services as visible controls.

## Runtime capability and fallback

- Classic LangSmith Deployment is the live public baseline, but the shell never assumes deployment features merely because a session exists.
- MDA and Fleet destinations/actions appear only when the active `AgentSource` capability manifest is true after `SPIKE-MDA-001` or `SPIKE-FLEET-001` acceptance.
- Missing schedules, sandbox, deploy, configure, trace, or Context Hub capabilities resolve to a typed unavailable state owned by the relevant plan.
- A live repository error never triggers demo mode. The user must explicitly enter demo through a new isolated session.
- If the Tauri host is gated or unavailable, the same experience remains supported through responsive web/PWA.
- If command-palette search cannot query a source, it returns source-scoped partial state rather than claiming a global search contract.

## Persistence and security

- Theme, density, reduced-motion preference, last safe navigation destination, and non-sensitive layout preferences may persist per Deep Work actor in Postgres through `/api/v1/preferences`; early boot may mirror non-sensitive display preferences locally.
- Product-demo fixture state uses an isolated API/Postgres/object namespace with bounded expiry and never shares credential references, push subscriptions, source registrations, or live caches. UI-harness state is synthetic browser-local developer state and is never hydrated into the product demo.
- Route and command authorization is enforced by FastAPI and source adapters; hidden UI is not an authorization boundary.
- Untrusted markdown, tool output, filenames, links, and artifacts render through a sanitized, origin-aware boundary and cannot create shell controls.
- External links identify destination and open outside privileged Tauri context according to `DW-SURF-002`.
- Account, workspace, source, offline, demo, and stale banners cannot be dismissed when dismissal would hide a security-relevant state.

## Responsive and accessible behavior

- Semantic landmarks include banner/header, primary navigation, contextual navigation, main, complementary rail, and status region.
- Desktop primary destinations are reachable in one action; every destination is reachable in at most two actions on phone.
- Tab, sheet, menu, dialog, toast, command-palette, and navigation components follow native semantics or tested ARIA patterns, trap focus only when modal, and restore focus on close.
- All status combines text/icon with color; both themes meet WCAG 2.2 AA contrast and forced-colors retain boundaries and focus.
- Minimum touch targets follow the accepted accessibility baseline; pinch zoom is not disabled; virtual keyboard and safe-area insets do not cover composer or approval actions.
- Screen-reader announcements are reserved for meaningful state changes and do not replay streaming noise.
- Skeletons use `aria-busy` at the owning region; empty/error/offline content receives a real heading and actionable recovery.

## Metrics and guardrails

- Zero serious automated accessibility violations on shared primitives and shell fixtures; manual keyboard/screen-reader sign-off through `DW-QUAL-001`.
- Every primary destination reachable in one action on desktop and at most two on phone.
- Zero cumulative layout shift attributable to session/source capability hydration within the shell target budget.
- UI harness, product demo, and live views use the same component tree and normalized prop contract; only product demo/live exercise the application API.
- Demo-to-live outbound mutation count: zero before explicit sign-in and source authorization.
- Navigation task success, command-palette success, demo reset completion, and source-context errors are measured without recording user content.
- Guardrails: no feature-specific token, no silent fixture fallback, no hover-only action, no color-only status, and no hidden desktop control without mobile equivalent.

## Dependencies, contract gates, rollout, and rollback

### Dependencies and review gates

- `DW-FND-001` for package boundaries, named fixture modes, and worktree harness.
- The fixture shell and UI harness can land before `DW-FND-004/005`; live/product-demo integration cells consume their normalized capability, connectivity, status, and reducer contracts once stable. They are not reciprocal machine blockers for the presentation scaffold.
- Product/design approval of five-primary-tab IA and every prototype destination disposition.
- Accessibility approval of primitives, navigation patterns, state announcements, and supported browser/assistive-technology matrix.
- Runtime capabilities remain externally gated by `SPIKE-MDA-001`, `SPIKE-FLEET-001`, and `SPIKE-STREAM-001`; this shell does not promote them.

### Proposed rollout

1. Normalize tokens and publish visual fixtures without porting application pages.
2. Establish accessible primitives and state patterns, including untrusted content and demo disclosure.
3. Build the shell in the browser-local UI harness across desktop, tablet, phone, both themes, high zoom, and reduced motion.
4. Integrate the API-backed product demo, then live session/source context through SDK services backed by FastAPI `/api/v1`.
5. Port audited surfaces one owning plan at a time; compare prototype and canonical screenshots as evidence.
6. Enable Tauri hosting only after `SPIKE-DESKTOP-001`; web/PWA remains the fallback.

### Rollback

Each migrated route stays behind a route/capability flag until acceptance. Roll back a shell release by restoring the previous compatible token/UI package and Next.js bundle while retaining preferences. Never route failed live requests into demo; disable the affected live route and preserve an explicit recovery path.

## Executable acceptance scenarios

```gherkin
Scenario: Demo is visible and isolated
  Given a visitor has no credentials
  When they choose Explore demo
  Then every route shows the Demo data marker and synthetic workspace
  And fixture mutations remain deterministic inside the demo namespace
  And deployment, GitHub, push, and live approval attempts make no outbound request

Scenario: The UI harness cannot masquerade as product-demo proof
  Given a developer starts the browser-local UI harness
  When a fixture mutation, reconnect, worker, or persistence state is shown
  Then the developer banner states that application services are not under test
  And end-to-end acceptance requires the API-backed product demo

Scenario: A phone user can reach every destination and action
  Given the application is 375 CSS pixels wide with 200 percent text zoom
  When the user navigates using keyboard and touch equivalents
  Then Tasks, Approvals, and Agents are direct bottom-navigation destinations
  And Schedules, Activity, Settings, workspace, and account actions are reachable in More or account navigation
  And no action requires hover or horizontal page scrolling

Scenario: A failed live source never becomes demo data
  Given an authenticated live source returns an upstream error
  When the shell renders the failure
  Then it shows a source-scoped error and safe retry/settings actions
  And no fixture entity appears
  And the user must explicitly start a separate demo session to see demo data

Scenario: Responsive focus and state survive a layout change
  Given focus is inside an open contextual sidebar at tablet width
  When the viewport changes to phone width and the sidebar becomes a sheet
  Then focus remains on the equivalent control or owning trigger
  And closing the sheet restores focus
  And the current route and unsaved draft are preserved

Scenario: Unknown capabilities remain honest
  Given an MDA or Fleet capability has not passed its named spike
  When the source context loads
  Then the related action is absent or disabled with an explanatory reason
  And the shell does not infer support from the runtime label alone
```
