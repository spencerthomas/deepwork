# Frontend Prototype Audit

Status: staged audit; not canonical product scope
Frontend evidence pin: `deep-work-frontend@8866d39a2888e358091208063693f260cff6d261`
Plan comparison pin: `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`
Audit date: 2026-07-22

## Purpose and authority

This audit treats the frontend prototype as interaction and visual evidence, not as product, runtime, or API authority. It inventories the committed prototype at the pinned revision, identifies what actually works, and proposes a release disposition for every visible product surface. Nothing in this document promotes a simulated interaction into v1 scope.

The prototype contains 77 tracked files. Product data is centralized in the 1,784-line `lib/data.ts`; the 683-line `components/run-panel.tsx` is the largest interactive surface. There are no application API routes, server actions, authentication SDKs, data-fetching clients, or network calls in the source. The only persisted user preference is theme selection in browser `localStorage` under `dw-theme`.

The existing frontend implementation plan is stale evidence: `docs/plan/06-frontend-implementation.md` describes frontend revision `c46b994`, 53 files, a 1,110-line data file, and a 558-line run panel. It must not be used as the inventory for revision `8866d39`.

## Classification and disposition

Current-state classifications:

- **Functional**: completes its stated prototype-local outcome and survives navigation or reload where persistence is part of that outcome.
- **Simulated**: changes local UI state or navigates, but does not invoke or persist the represented product operation.
- **Inert**: visible affordance has no meaningful handler or uses a placeholder such as `href="#"`.
- **Missing**: required experience or state has no surface.
- **Contract-invalid**: the UI encodes an external runtime model contradicted by the pinned primary contract evidence.

Proposed dispositions:

- **v1**: required for the release acceptance boundary.
- **Flagged v1**: only visible when a connected source advertises and passes the required capability.
- **Later**: retain as a product brief, not a v1 promise.
- **Fold**: move the useful behavior into another owning experience.
- **Remove**: do not migrate the prototype surface.

## Executive verdict

The prototype demonstrates a coherent visual language and useful interaction hypotheses, but it is not an application slice. Its routes render fixture data, its mutations are local or inert, and several runtime/configuration surfaces imply capabilities that are either source-specific or unsupported. The safest migration is one-way: preserve selected presentation patterns, rebuild behavior against normalized domain contracts, and never copy fixture assumptions into the application service or SDK.

The release-significant frontend gaps are:

1. no authenticated or durable application state;
2. no source-aware task/run/approval contracts;
3. no loading, network error, permission, offline, reconnect, or stale-data experiences;
4. no usable mobile navigation to the run panel or its eight tabs;
5. no accessible, idempotent approval or cancellation workflow;
6. no distinction among workspace settings, agent configuration, project environment, and deployment status;
7. no capability fallback when a source cannot provide files, Git, browser, trace, schedule, checkpoint, or HITL features.

## Route inventory

The route inventory below counts the 13 committed page modules, including redirects and dynamic/catch-all modules. The dynamic `/agents/[id]` module also renders the `id="new"` creation hypothesis; `/agents/new` is therefore a user-visible variant, not a fourteenth page module.

| ID | Route | Evidence | Current state | Proposed owner and disposition |
|---|---|---|---|---|
| FE-R01 | `/` | `app/page.tsx` | Functional redirect to `/tasks`; no session-aware landing | `DW-SURF`: v1 redirect after session/bootstrap resolution |
| FE-R02 | `/login` | `app/login/page.tsx`, `components/sign-in.tsx` | Simulated workspace and API-key entry; both actions only navigate | `DW-ONB`: v1, rebuilt as a real session and source-connection journey |
| FE-R03 | `/tasks` | `app/tasks/page.tsx`, `components/task-inbox.tsx` | Simulated fixture inbox with local status/group controls | `DW-TASK`: v1 |
| FE-R04 | `/tasks/new` | `app/tasks/new/page.tsx`, `components/new-task.tsx` | Simulated composer; dispatch always opens fixture `t-901` | `DW-TASK`: v1, with source capability and attachment gates |
| FE-R05 | `/tasks/[id]` | `app/tasks/[id]/page.tsx`, `components/task-detail.tsx` | Simulated fixture lookup and local panel controls | `DW-TASK`: v1 |
| FE-R06 | `/approvals` | `app/approvals/page.tsx`, `components/approvals-view.tsx`, `components/approval-actions.tsx` | Contract-invalid fixture HITL and local success message | `DW-HITL`: v1, rebuilt around ordered batches |
| FE-R07 | `/agents` | `app/agents/page.tsx`, `components/agent-fleet.tsx` | Simulated fixture catalog; filters and clone are inert | `DW-AGENT`: v1 source-aware index; remove implied global CRUD |
| FE-R08 | `/agents/[id]`, including `id="new"` | `app/agents/[id]/page.tsx`, `components/agent-builder.tsx` | Simulated builder; `new` is a fixture variant; Save and chat send do not publish changes | `DW-AGENT`: v1 read/detail; creation and versioned edit/deploy only where supported |
| FE-R09 | `/schedules` | `app/schedules/page.tsx` | Simulated static list and inert controls | `DW-OPS`: flagged v1 per source schedule capability |
| FE-R10 | `/activity` | `app/activity/page.tsx` | Simulated static activity feed and inert filtering | `DW-OPS`: v1, app event projection plus source links |
| FE-R11 | `/observability` | `app/observability/page.tsx`, `components/observability-charts.tsx` | Simulated static charts | `DW-OPS`: fold into Activity summary and external trace links |
| FE-R12 | `/config` | `app/config/page.tsx` | Functional redirect to `/settings` | `DW-SURF`: remove legacy route after a compatibility redirect window |
| FE-R13 | `/settings` and `/settings/:section` | catch-all settings page and shell | Simulated 22-section local form library | `DW-SURF` plus relevant domain plans: restructure before migration |

The inventory uses FE-R13 for the optional settings segment because the same catch-all implementation owns both URLs. No 404/not-found, unauthorized, source-disconnected, or route-level error boundary is defined for these experiences.

## Primary navigation inventory

`components/app-shell.tsx` exposes exactly seven desktop destinations.

| ID | Label | Current state | v1 disposition |
|---|---|---|---|
| FE-N01 | Tasks | Functional navigation to a simulated page | Primary navigation, `DW-TASK` |
| FE-N02 | Approvals | Functional navigation to a contract-invalid page | Primary navigation, rebuilt under `DW-HITL` |
| FE-N03 | Agents | Functional navigation to a simulated page | Primary navigation, `DW-AGENT` |
| FE-N04 | Schedules | Functional navigation to a simulated page | Primary navigation when at least one source supports schedules; otherwise discoverable disabled/empty state |
| FE-N05 | Activity | Functional navigation to a simulated page | Primary navigation, `DW-OPS` |
| FE-N06 | Observability | Functional navigation to simulated charts | Fold into Activity; deep-link to source-native traces |
| FE-N07 | Settings | Functional navigation to simulated forms | Move to workspace menu and command palette; not a primary tab |

Canonical v1 desktop information architecture is five primary destinations: Tasks, Approvals, Agents, Schedules, and Activity. Settings is contextual administration. Observability is a slim Activity view, not a second observability product.

Canonical mobile navigation is Tasks, Approvals, Agents, and More. More contains Schedules, Activity, Settings, connection status, and account/workspace actions. Capability-dependent destinations must remain predictable: hide only before first connection, then show an explanatory unavailable state rather than silently disappearing.

## Application shell and global controls

| ID | Surface/control | Current state | Proposed disposition |
|---|---|---|---|
| FE-S01 | Workspace selector | Inert visual control | v1 real workspace/source context selector backed by the application session |
| FE-S02 | Left navigation | Functional links on desktop; hidden below `lg` without replacement | v1 desktop sidebar plus mobile bottom bar/drawer |
| FE-S03 | “Design brief” link | Inert `href="#"` | Remove from product shell; documentation belongs in Help/Docs |
| FE-S04 | Dismissible prototype banner | Functional local dismissal only | Remove for production; use versioned announcements if required |
| FE-S05 | Command palette | Functional local modal with six static navigation commands | v1 navigation/actions; task search only after indexed source aggregation exists |
| FE-S06 | Docs link | Functional external link | v1, point to versioned user documentation |
| FE-S07 | Theme toggle | Functional and persisted in localStorage | v1; synchronize to account preference only if justified |
| FE-S08 | New task action | Functional route link | v1; disable with reason when no invokable source exists |
| FE-S09 | Session/account menu | Missing | v1 under `DW-ONB`/`DW-SURF` |
| FE-S10 | Source health/reconnect indicator | Missing | v1 under `DW-ONB`/`DW-OPS` |
| FE-S11 | Notification center | Missing | v1 compact notification entry, preferences, and deep links under `DW-OPS-002`; push requires durable backend ownership, while email may remain later |

## Task inbox and composer controls

| ID | Surface/control | Current state | Proposed disposition |
|---|---|---|---|
| FE-T01 | Fixture task rows and detail links | Simulated | v1 normalized task index, per-source pagination and stable IDs |
| FE-T02 | Status selector | Simulated local filter | v1, URL-addressable and source-aware |
| FE-T03 | Group selector | Simulated local grouping | v1 if supported by usability evidence; default to status/date |
| FE-T04 | Repository filter | Inert menu item | v1 only after repository identity is normalized |
| FE-T05 | Research filter | Inert menu item | Fold into task/template/type filter; avoid hard-coded work modes |
| FE-T06 | “Last 7 days” filter | Inert menu item | v1 date filter with timezone semantics |
| FE-T07 | Inbox search | Missing | v1 per-source aggregation; never imply nonexistent global runtime search |
| FE-T08 | Agent selector | Simulated fixture selection | v1 with source identity and invoke capability |
| FE-T09 | Task template selector | Simulated | v1 basic templates; authoring/marketplace later |
| FE-T10 | Autonomy selector | Simulated | v1 only as a normalized policy mapped to source-supported controls |
| FE-T11 | Attachment affordance | Simulated filename UI only | flagged v1 after upload, provenance, limits, retention, and source handoff contracts exist |
| FE-T12 | Dispatch | Contract-invalid outcome: always routes to fixture task | v1 idempotent create/start with pending and failure recovery states |
| FE-T13 | Draft persistence | Missing | v1 local draft; server draft only if cross-device continuation is required |
| FE-T14 | No-source/demo entry | Missing on composer | v1 guided fixture/demo entry plus explicit “demo” labeling |

## Task detail and run controls

| ID | Surface/control | Current state | Proposed disposition |
|---|---|---|---|
| FE-D01 | Stream transcript | Simulated fixture timeline | v1 event reducer with reconnect/dedupe and untrusted-content rendering |
| FE-D02 | Main Fullscreen button | Inert | Remove duplicate or wire to the single panel fullscreen behavior |
| FE-D03 | Run-panel fullscreen | Functional local UI, Escape and scroll lock | v1 desktop behavior; mobile uses a full-screen sheet |
| FE-D04 | Run panel toggle | Functional local UI | v1 and persisted per device |
| FE-D05 | Terminal toggle | Functional local UI | flagged v1 for coding-capable sources |
| FE-D06 | Sidebar Todos | Simulated fixture | v1 if derived from stream/state; show provenance and freshness |
| FE-D07 | “Files changed” | Simulated fixture | flagged v1; link to Files/Diff state |
| FE-D08 | Steering composer | Simulated: clears text only | v1 as a new input or supported multitask action, never an invented stream method |
| FE-D09 | Cancellation | Missing | v1 explicit cancel-current-run semantics |
| FE-D10 | Retry/branch/checkpoint | Missing | v1 retry; checkpoint branch flagged by capability |
| FE-D11 | Artifact list/download | Missing as a first-class experience | v1 artifact metadata and safe download path |
| FE-D12 | Verification/verdict history | Missing | v1 under `DW-HITL` when a task declares a rubric/goal |

## Eight run-panel tabs

The panel in `components/run-panel.tsx` exposes eight tabs. All eight are hidden below the `lg` breakpoint because the containing aside is hidden and there is no mobile sheet or alternate route.

| ID | Tab | Current state | Contract/capability issue | Disposition |
|---|---|---|---|---|
| FE-P01 | Stream | Simulated fixture events | No event protocol, cursor, dedupe, or malformed-event path | v1, `DW-TASK` |
| FE-P02 | Agents | Simulated subagent tree | No source capability or stable parent/child run identity | flagged v1, `DW-TASK`/`DW-AGENT` |
| FE-P03 | Context | Simulated static context | Ownership, redaction, token accounting, and source fidelity undefined | v1 read-only summary; editing later |
| FE-P04 | Trace | Simulated timeline | Risks reimplementing source-native observability | fold to compact summary plus LangSmith trace deep-link |
| FE-P05 | Browser | Simulated screenshot card | Browser availability is source/sandbox dependent | flagged v1, `DW-CODE` |
| FE-P06 | Status | Simulated metadata | No normalized status reducer or freshness semantics | v1, fold core status into task header and diagnostics |
| FE-P07 | Files | Simulated file tree | No artifact/filesystem boundary or safe rendering | flagged v1, `DW-CODE` |
| FE-P08 | Git | Simulated branch/commit state | No GitHub authorization or repository lifecycle | flagged v1, `DW-CODE` |

The panel is also missing two distinct experiences: **Artifacts** (durable outputs and attachments, not the sandbox filesystem) and **Verification** (goals, rubric checks, verdicts, and evidence). They may be tabs, contextual drawers, or task sections, but each requires an owning plan and mobile equivalent before UI selection.

## Approval experience

| ID | Surface/control | Current state | Proposed disposition |
|---|---|---|---|
| FE-A01 | Approval queue | Simulated fixture list | v1 normalized pending-interrupt projection with source freshness |
| FE-A02 | Queue filters | Inert | v1 status/source/risk filters if supported by real fields |
| FE-A03 | “Approve all safe” | Inert and unsafe as an unexplained bulk action | Remove from v1; later only with explicit policy, preview, and audit |
| FE-A04 | Approve | Simulated local success | v1 ordered decision submission with idempotency |
| FE-A05 | Edit | Simulated local form | v1 only when `review_config` permits edit; preserve exact arguments/schema |
| FE-A06 | Respond | Simulated local response | v1 only for response-type requests |
| FE-A07 | Ignore | Contract-invalid decision | Replace with reject where allowed; stale dismissal is a separate verified action |
| FE-A08 | Reject | Missing | v1 when permitted by the request config |
| FE-A09 | Batch ordering | Missing | v1; one ordered decision per action request |
| FE-A10 | Stale interrupt resolution | Missing | v1 refetch-before-submit and safe dismissal rules |
| FE-A11 | Mobile one-tap review | Missing | v1 approve/reject for simple requests, full sheet for edit/respond |
| FE-A12 | Approval audit trail | Missing | v1 durable app audit plus source result/reference |

## Agent and operational surfaces

| ID | Surface/control | Current state | Proposed disposition |
|---|---|---|---|
| FE-G01 | Agent index | Simulated global fixture catalog | v1 per-source index with identity collision handling |
| FE-G02 | Agent filters | Inert | v1 source/status/capability filters |
| FE-G03 | Clone | Inert and assumes create authority | Later or flagged v1; export/import is safer baseline |
| FE-G04 | Agent detail | Simulated | v1 read/invoke details |
| FE-G05 | Builder chat send | Inert | Remove until chat-to-configure has a future brief and contract |
| FE-G06 | Builder tabs/tool modes | Simulated local state | v1 versioned form editor where supported; no implied live mutation |
| FE-G07 | Save changes | Inert | v1 Save Draft only; Deploy is separate asynchronous action |
| FE-G08 | New agent | Simulated fixture clone | flagged v1 for classic/local supported sources; MDA beta adapter cannot assume CRUD |
| FE-O01 | Schedule list/sidebar/actions | Simulated/static and inert | flagged v1 per source; creation semantics source-specific |
| FE-O02 | Activity list/sidebar/actions | Simulated/static and inert | v1 app audit/activity projection with source deep-links |
| FE-O03 | Observability charts | Simulated/static | fold into Activity; do not recreate trace analytics |

## Settings inventory and ownership correction

The prototype exposes 22 sections from `components/settings/settings-shell.tsx`. They currently mix four ownership domains that must be separated:

1. **Workspace settings**: identity/session, Agent Sources, GitHub installation and repository access, notification preferences, security, theme, and destructive account/workspace actions.
2. **Agent configuration**: model, tools, permissions/HITL policy, subagents, skills, memory policy, goals/rubrics, and connector bindings.
3. **Project/environment configuration**: repository/branch, sandbox lifecycle, setup/cleanup scripts, egress, environment variables, worktree policy, and artifact boundaries.
4. **Deployment status**: source/runtime identity, immutable revision, build/health state, capability manifest, last deploy result, and diagnostics.

| ID | Prototype section | Current state | Correct owner | Proposed disposition |
|---|---|---|---|---|
| FE-C01 | Models | Simulated local controls | Agent configuration | Fold into Agent detail; v1 actual model, advanced model routing later/capability-gated |
| FE-C02 | Configuration | Simulated; Open config uses `#`; Diagnose/Reinstall inert | Agent or project, depending field | Remove generic Codex/config-file assumptions; fold normalized fields into Agent/Environment |
| FE-C03 | Profiles | Simulated local selection | Agent configuration | Later/v1.x unless a real reusable-profile contract is accepted |
| FE-C04 | Goals & rubrics | Simulated local edit/add/remove | Agent configuration and verification | Flagged v1 when goal/rubric middleware is installed and verified |
| FE-C05 | Sandboxes | Simulated; wording assumes task/worktree equivalence | Project/environment | v1 capability-aware lifecycle; correct to per-thread where MDA is used |
| FE-C06 | Interpreters | Simulated local controls | Project/environment | Later/capability-gated |
| FE-C07 | Backends | Simulated local controls | Source diagnostics/platform-owned | Remove from normal user settings; expose read-only source/runtime diagnostics |
| FE-C08 | Tools | Simulated local controls | Agent configuration | v1 in Agent detail with source schema fidelity |
| FE-C09 | Permissions | Simulated local controls | Agent configuration/HITL | v1 policy editor only where enforceable; otherwise read-only |
| FE-C10 | Multimodality | Simulated local controls | Agent configuration/source capability | Flagged v1 |
| FE-C11 | Memory | Simulated local controls | Agent configuration and organizational review | v1 policy/read view; publication requires explicit review |
| FE-C12 | Subagents | Simulated local controls | Agent configuration | v1 where graph/runtime supports it |
| FE-C13 | Streaming | Simulated local controls | Source diagnostics | Fold into diagnostics; not a general user preference |
| FE-C14 | Hooks | Simulated enable; remaining actions inert | Project/environment | Later/v1.x after execution/security model |
| FE-C15 | Environments | Simulated local edit; Add Project inert, Save only navigates | Project/environment | v1 with versioned, secret-safe persistence |
| FE-C16 | Worktrees | Simulated local controls | Project/environment | Later/v1.x; multi-worktree is not v1 baseline |
| FE-C17 | Git | Simulated local controls | Project/environment | v1 basic repository/branch policy |
| FE-C18 | Connectors | Simulated filters/modal; connect/add/per-tool actions inert | Workspace credentials plus Agent bindings | v1 split ownership; use official project/SDK paths only |
| FE-C19 | Plugins | Simulated detail; install/build inert | Agent/project extension | Later/v1.x |
| FE-C20 | Skills | Simulated search/preview; toolbar inert, no editor/save | Agent configuration/versioned source | v1 read/versioned edit where supported |
| FE-C21 | Protocols | Simulated static claims; connect actions inert | Source integration architecture | Remove top-level section; fold MCP into Connectors, ACP/A2A later |
| FE-C22 | Deployment | Simulated static state; Open inert | Deployment status | v1 read/health/deploy status, classic baseline; MDA private beta behind capability detection |

## Component inventory

All product components at the pin are accounted for below. Primitive UI components are implementation assets, not product features.

| Group | Components | Audit result |
|---|---|---|
| Shell/navigation | `app-shell`, `sidebar-nav`, `command-bar`, `page-header`, `theme-toggle`, `status-chip` | Visual patterns reusable; workspace, search, health, and mobile behavior require rebuild |
| Onboarding | `sign-in` | Simulated; no auth/session/source contract |
| Tasks | `task-inbox`, `new-task`, `composer`, `task-detail`, `run-stream`, `run-panel`, `run-context`, `run-subagents`, `terminal-pane`, `tool-card`, `browser-card` | Fixture presentation; state, streaming, mutation, security, and responsive paths missing |
| Approvals | `approvals-view`, `approval-actions` | Contract-invalid decision model; rebuild |
| Agents | `agent-fleet`, `agent-builder` | Fixture catalog/builder; retain visual concepts only |
| Operations | `observability-charts` plus route-local schedule/activity components | Static evidence; consolidate around Activity and source links |
| Settings | `settings-shell`, `settings-ui`, 19 section files under `components/settings`, and Connectors/Plugins/Skills under `components/config` | All local-only; split by ownership before migration |
| Shared primitives | `beam-field`, `ui/button`, `ui/card`, `ui/chart` | Candidate design-system inputs after accessibility and token review |

## Required state matrix

Every owning feature plan must describe the following states and the transition that exits each state. The prototype only covers nominal fixture-loaded states and a few local empty selections.

| State | Current coverage | v1 requirement |
|---|---|---|
| Initial loading | Missing | Skeleton or progress appropriate to expected latency; never show false empty state |
| Empty workspace/source | Missing | Guided connect or explicit demo path |
| Empty result/filter | Partial local examples only | Explain filter state and provide clear reset |
| Recoverable request error | Missing | Preserve user input, offer retry, include correlation/reference |
| Fatal configuration error | Missing | Block unsafe actions and route to source diagnostics |
| Offline | Missing | Persistent status, read-only cached data where safe, queued draft semantics explicit |
| Permission denied | Missing | Distinguish app authorization, source authorization, and resource authorization |
| Authentication expired | Missing | Preserve route/draft and reauthenticate without exposing credentials |
| Source disconnected | Missing | Scoped degraded state and reconnect action; other sources continue |
| Stream reconnecting | Missing | Last confirmed event, attempt count/backoff, safe cancel, cursor-based resume |
| Stream resumed | Missing | Deduplicate events and disclose gap if continuity cannot be proven |
| Stale data/interrupt | Missing | Timestamp/freshness, refetch, conflict-safe resolution |
| Partial/malformed response | Missing | Render safe subset, quarantine untrusted fields, provide diagnostic reference |
| Capability unavailable | Missing | Explain source limitation and offer supported alternative; do not render dead controls |
| Mutation pending | Missing | Idempotency key, disable duplicate submit, cancellability semantics |
| Mutation succeeded | Local-only toast/message in places | Reconcile authoritative state rather than optimistic fiction |
| Mutation failed/ambiguous | Missing | Refetch before retry; never duplicate runs or approval decisions |
| Destructive confirmation | Missing | Exact target/scope, recoverability, source-vs-app deletion distinction |
| Archived/deleted | Missing | Stable recovery/retention rules and deep-link behavior |

## Responsive and accessibility audit

- The primary sidebar disappears below `lg` with no drawer or bottom navigation.
- The contextual rail disappears below `xl`; no alternate access is provided.
- The run panel disappears below `lg`, making all eight run tabs, terminal state, files, Git, and browser evidence inaccessible on phones and many tablets.
- Settings reduces to a horizontal strip of 22 labels; it does not provide a usable hierarchy, search, or contextual explanation.
- The top navigation has no explicit overflow/fade treatment for narrow widths.
- There is no phone diff review, one-tap approval, or confirmed GitHub merge landing flow.
- Focus order, focus restoration, dialog announcements, live-region strategy for streaming, keyboard equivalents, reduced motion, contrast, touch targets, and virtualized-list semantics are not accepted by tests.

Required v1 behavior:

- mobile bottom navigation and contextual full-screen sheets;
- no capability or action available only by hover;
- stream updates announced by policy, not every token;
- keyboard access to navigation, task actions, approval decisions, tabs, and diff controls;
- focus restoration after palette/dialog/sheet closure;
- reduced-motion alternatives to decorative animation;
- 44-by-44 CSS-pixel touch targets for primary phone actions;
- safe horizontal diff handling without hiding line context or decision controls;
- automated and manual acceptance at phone, tablet, laptop, and wide desktop widths.

## Migration guardrails

1. Do not move `lib/data.ts` into production packages or use fixture IDs as domain identities.
2. Do not make React components responsible for source authentication, protocol selection, or persistence.
3. Put source query/mutation services behind the shared SDK; keep the streaming hook a consumer, not the service boundary.
4. Render only features advertised by a versioned source capability manifest and include an unavailable fallback.
5. Treat all runtime text, Markdown, tool arguments, files, diffs, URLs, and HTML as untrusted content.
6. Keep broad LangSmith, GitHub, and deployment credentials out of the browser and desktop bundle.
7. Preserve semantic presentation selectively; migrate behavior only after its owning plan is ready and its external contract is verified.

## Acceptance gates for frontend plan readiness

The frontend audit can be merged into canonical plans only when:

- every FE item above maps to exactly one owning feature plan and zero or more explicit dependencies;
- every selected v1 surface has loading, empty, error, offline, permission, reconnect, stale, and capability-unavailable behavior where applicable;
- desktop, tablet, and phone journeys can reach equivalent task, run, approval, and recovery outcomes;
- approval decisions preserve ordered runtime batches and reject unsupported actions;
- a fixture journey and its live-contract journey pass the same UI acceptance scenarios;
- no visible control is inert unless intentionally disabled with an explanation;
- no prototype string, route, or mock schema is used as proof of an external capability;
- the canonical implementation plan is repinned to `8866d39` or superseded by a migration inventory generated from this audit.

## Evidence index

All source paths below are evaluated at `deep-work-frontend@8866d39a2888e358091208063693f260cff6d261`:

- routes: `app/**/page.tsx`;
- shell and navigation: `components/app-shell.tsx`, `components/sidebar-nav.tsx`, `components/command-bar.tsx`;
- task surfaces: `components/task-inbox.tsx`, `components/new-task.tsx`, `components/task-detail.tsx`, `components/run-panel.tsx`;
- approvals: `components/approvals-view.tsx`, `components/approval-actions.tsx`;
- agents: `components/agent-fleet.tsx`, `components/agent-builder.tsx`;
- settings: `components/settings/settings-shell.tsx`, `components/settings/*.tsx`, `components/config/*.tsx`;
- fixtures: `lib/data.ts`;
- dependencies: `package.json`.
