# Product coverage matrix

Status: canonical coverage source
Frontend evidence: `deep-work-frontend@26c698b30ff08d5122cfaeedbd4a95296a7884f4`
Vision and roadmap evidence: `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`
Canonical feature library: `docs/product-specs/` accepted 2026-07-23

## How to read this matrix

Each row has exactly one owning feature ID. An owning plan may depend on other plans, but dependencies are not co-owners and are intentionally omitted from the owner column. A row is not permission to implement a prototype assumption: the named plan and its contract gates control implementation.

Release criteria resolve from their owner here to stable feature and program IDs in
the [acceptance-scenario index](acceptance-scenarios.md). This matrix assigns
scope ownership; that index assigns executable proof ownership.

Current-state labels match the frontend audit:

- **Functional**: completes the prototype-local outcome, including persistence when that outcome claims persistence.
- **Simulated**: changes local UI state or navigates but does not invoke or persist the represented product operation.
- **Inert**: visible control has no meaningful handler or uses a placeholder target.
- **Missing**: required experience or state has no surface.
- **Contract-invalid**: the represented runtime or product behavior contradicts accepted contract evidence.

Disposition labels are **v1**, **Flagged v1**, **Later**, **Fold**, and **Remove**. Flagged v1 requires an advertised capability plus the plan's accepted contract test. Later means no production control in v1.

Inventory check:

| Inventory | Required | Mapped here | Note |
|---|---:|---:|---|
| Page modules / route patterns | 13 | 13 | `/agents/new` is the special `id="new"` behavior of `/agents/[id]`, not a separate page module. |
| Desktop top-navigation destinations | 7 | 7 | Canonical v1 reduces this to five primary destinations. |
| RunPanel tabs | 8 | 8 | All eight currently disappear below `lg` with no alternate mobile access. |
| Settings sections | 22 | 22 | Each receives a single scope owner and disposition. |

## Page routes

| ID | Page route and evidence | Current state at `26c698b` | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| ROUTE-01 | `/` - `app/page.tsx` | Functional redirect to `/tasks`; not session-aware | `DW-FND-002` | v1 | Resolve session/demo/onboarding state before the final landing redirect. |
| ROUTE-02 | `/login` - `app/login/page.tsx` | Simulated workspace, OAuth, device, and API-key UI; actions only navigate | `DW-ONB-001` | v1 | Ship application-session plus server-held API-key baseline; expose OAuth only after its spike passes. |
| ROUTE-03 | `/tasks` - `app/tasks/page.tsx` | Simulated fixture inbox with local filters/grouping | `DW-TASK-001` | v1 | Replace fixtures with authorized per-source aggregation, URL state, stable pagination, and recovery states. |
| ROUTE-04 | `/tasks/new` - `app/tasks/new/page.tsx` | Simulated composer; Dispatch always opens fixture `t-901` | `DW-TASK-002` | v1 | Add durable draft/preflight, idempotent creation, source capability gates, and real pending/failure outcomes. |
| ROUTE-05 | `/tasks/[id]` - `app/tasks/[id]/page.tsx` | Simulated fixture lookup and local-only run controls | `DW-TASK-003` | v1 | Hydrate durable source truth, stream through the accepted adapter, and add reconnect/stale/error behavior. |
| ROUTE-06 | `/approvals` - `app/approvals/page.tsx` | Contract-invalid flattened approvals and local success messages | `DW-HITL-001` | v1 | Rebuild around ordered action/review batches, allowed decisions, freshness, idempotency, and audit. |
| ROUTE-07 | `/agents` - `app/agents/page.tsx` | Simulated global fixture catalog; filters and Clone are inert | `DW-AGENT-002` | v1 | Aggregate registered sources, preserve source identity/authority, and show real health and capability state. |
| ROUTE-08 | `/agents/[id]`, including `id="new"` - `app/agents/[id]/page.tsx` | Simulated builder; chat send and Save do not publish; `new` clones a fixture | `DW-AGENT-003` | v1 | Use detail subroutes for versioned drafts, validation, explicit Deploy, revision history, and safe create/import. |
| ROUTE-09 | `/schedules` - `app/schedules/page.tsx` | Simulated static list; badges are not controls | `DW-OPS-001` | Flagged v1 | Show per-source ownership; enable mutations only for a verified schedule capability or project-deploy workflow. |
| ROUTE-10 | `/activity` - `app/activity/page.tsx` | Simulated static feed and fabricated trace identifiers; sidebar filters inert | `DW-OPS-001` | v1 | Combine authorized application audit events and source run events with safe filters and real trace/task links. |
| ROUTE-11 | `/observability` - `app/observability/page.tsx` | Simulated static metrics and charts | `DW-OPS-002` | Fold | Move slim summaries to Activity and agent detail; retain source-native trace deep links instead of a duplicate product. |
| ROUTE-12 | `/config` - `app/config/page.tsx` | Functional legacy redirect to `/settings` | `DW-FND-002` | Remove | Keep only a measured compatibility redirect, then remove the route. |
| ROUTE-13 | `/settings` and `/settings/:section` - catch-all page | Simulated 22-section local form library; scope and persistence are mixed | `DW-AGENT-004` | Fold | Move workspace controls to workspace Settings, agent controls to Agent detail, environment controls to Environment, and deploy facts to Deploy. |

## Desktop top navigation

| ID | Destination | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| NAV-01 | Tasks | Functional navigation to simulated route | `DW-TASK-001` | v1 | Primary desktop and phone destination. |
| NAV-02 | Approvals | Functional navigation to contract-invalid route | `DW-HITL-001` | v1 | Primary destination with pending count and source freshness. |
| NAV-03 | Agents | Functional navigation to simulated route | `DW-AGENT-002` | v1 | Primary destination with capability-aware index. |
| NAV-04 | Schedules | Functional navigation to simulated route | `DW-OPS-001` | v1 | Primary desktop destination with an honest no-capable-source state. |
| NAV-05 | Activity | Functional navigation to simulated route | `DW-OPS-001` | v1 | Primary destination and home for slim observability summaries. |
| NAV-06 | Observability | Functional navigation to simulated route | `DW-OPS-002` | Fold | Remove primary tab after summaries move into Activity/agent detail. |
| NAV-07 | Settings | Functional navigation to simulated route | `DW-FND-002` | Fold | Move to workspace/account menu and command palette; expose context settings from Agent/Environment detail. |

Canonical desktop navigation after review is Tasks, Approvals, Agents, Schedules, and Activity. Canonical phone navigation is Tasks, Approvals, Agents, and More; More contains Schedules, Activity, Settings, account/workspace, and connection state.

## Application shell and global controls

| ID | Surface/control | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| SHELL-01 | Logo/home link | Functional navigation | `DW-FND-002` | v1 | Resolve to the authorized landing route without discarding active filters. |
| SHELL-02 | Workspace selector | Inert | `DW-ONB-001` | v1 | Select an authorized workspace and retain explicit source context. |
| SHELL-03 | Prototype announcement banner dismissal | Functional only in component memory | `DW-FND-002` | Remove | Remove prototype marketing chrome; future announcements require versioned dismissal. |
| SHELL-04 | Design brief link | Inert `href="#"` | `DW-FND-002` | Remove | Remove from product shell; approved documentation belongs under Help/Docs. |
| SHELL-05 | Command palette open, Escape, arrows, Enter, route commands | Functional over six static commands | `DW-FND-002` | v1 | Keep safe navigation/actions; add entity search only through authorized indexed data. |
| SHELL-06 | Global task/agent command search | Missing despite "Search" label | `DW-FND-002` | v1 | Search permitted local/app projections and label partial source coverage. |
| SHELL-07 | External Docs link | Functional generic LangChain link | `DW-FND-001` | v1 | Link to versioned Deep Work user/deploy/architecture docs, then to primary provider docs as needed. |
| SHELL-08 | Theme toggle | Functional and persisted in `localStorage` | `DW-FND-002` | v1 | Preserve system/light/dark and accessible contrast; account sync is optional. |
| SHELL-09 | New task action | Functional route link | `DW-TASK-002` | v1 | Disable with explanation when no invokable source exists; preserve demo entry. |
| SHELL-10 | Context sidebars/right rails on tablet and phone | Missing; hidden below desktop breakpoints | `DW-SURF-001` | v1 | Move to labelled sheets/tabs without hiding any action or state. |
| SHELL-11 | Mobile bottom/More navigation | Missing | `DW-SURF-001` | v1 | Implement canonical phone IA with accessible destination and pending-state labels. |
| SHELL-12 | Session/account menu and sign-out | Missing | `DW-ONB-001` | v1 | Show actor/workspace, auth method, security actions, and reliable sign-out. |
| SHELL-13 | Source health/reconnect status | Missing | `DW-AGENT-001` | v1 | Expose stale/degraded/unauthorized capability state and targeted retry. |
| SHELL-14 | Notification center/preferences entry | Missing | `DW-OPS-002` | v1 | Provide in-app state even when device push is denied or unsupported. |

## Task inbox, composer, detail, and lifecycle controls

| ID | Surface/control | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| TASK-CTRL-01 | Task rows and detail links | Simulated fixture records; links function locally | `DW-TASK-001` | v1 | Render normalized source-aware task summaries and stable IDs. |
| TASK-CTRL-02 | Status sidebar filters | Simulated local filters | `DW-TASK-001` | v1 | Use canonical reducer states and URL-addressable filters. |
| TASK-CTRL-03 | "By status" / "Recent" grouping | Simulated local state | `DW-TASK-001` | v1 | Preserve only if backed by deterministic ordering and usable at scale. |
| TASK-CTRL-04 | Repository filter | Inert | `DW-TASK-001` | v1 | Enable after repository identity is normalized and authorized. |
| TASK-CTRL-05 | Hard-coded Research filter | Inert | `DW-TASK-001` | Fold | Replace with normalized task-kind/template filter. |
| TASK-CTRL-06 | "Last 7 days" filter | Inert | `DW-TASK-001` | v1 | Add timezone-aware date filter. |
| TASK-CTRL-07 | Inbox search | Missing | `DW-TASK-001` | v1 | Search per source/application projection; never imply a global provider API. |
| TASK-CTRL-08 | Pagination/large-list behavior | Missing | `DW-TASK-001` | v1 | Add opaque merged cursor, partial failures, focus-safe refresh, and virtualization. |
| TASK-CTRL-09 | "Review now" attention callout | Simulated local filter change | `DW-TASK-001` | v1 | Derive attention from current interrupt/failure state and preserve source freshness. |
| TASK-CTRL-10 | Template prompt buttons | Simulated local prompt fill | `DW-TASK-002` | v1 | Use versioned task templates with source requirements and immutable task provenance. |
| TASK-CTRL-11 | Agent picker | Simulated fixture selection | `DW-TASK-002` | v1 | Select source plus assistant/agent and gate on invoke health/capability. |
| TASK-CTRL-12 | Add/search/remove tool, context, skill, and subagent chips | Simulated local state | `DW-TASK-002` | v1 | Bind only supported, authorized manifest items and validate before dispatch. |
| TASK-CTRL-13 | File/media attachments | Simulated names only; no bytes or handoff | `DW-TASK-002` | Flagged v1 | Require upload, scan, provenance, limits, retention, and source transfer contract. |
| TASK-CTRL-14 | Ask/Auto autonomy selector | Simulated and over-broad | `DW-TASK-002` | v1 | Render a normalized task policy limited by agent/source permissions; no blanket fake auto-approval. |
| TASK-CTRL-15 | Rubric/completion criteria | Missing from composer | `DW-HITL-002` | v1 | Add versioned criteria and deterministic verdict history where middleware is verified. |
| TASK-CTRL-16 | Require plan approval | Missing | `DW-TASK-002` | Flagged v1 | Offer only when the source passes the plan-interrupt contract. |
| TASK-CTRL-17 | Preflight summary | Missing | `DW-TASK-002` | v1 | Review source, agent, repository/environment, policy, criteria, and attachments before dispatch. |
| TASK-CTRL-18 | Dispatch | Contract-invalid: always routes to existing fixture `t-901` | `DW-TASK-002` | v1 | Use idempotent create/start, pending/reconcile states, and an honest failure result. |
| TASK-CTRL-19 | Draft persistence/recovery | Missing | `DW-TASK-002` | v1 | Persist bounded drafts with explicit expiry/delete and cross-device policy. |
| TASK-CTRL-20 | Demo/no-source composer path | Missing | `DW-ONB-002` | v1 | Offer clearly labelled fixture task or source setup, never silent fixture fallback. |
| TASK-CTRL-21 | Main transcript and tool cards | Simulated fixture history; card expand/collapse is local | `DW-TASK-003` | v1 | Hydrate and reduce verified messages/tools with untrusted-content limits. |
| TASK-CTRL-22 | Main Fullscreen button | Inert | `DW-TASK-003` | Remove | Remove duplicate or connect to the one accessible task workspace expansion. |
| TASK-CTRL-23 | Run-panel fullscreen and close | Functional local dialog, Escape, scroll lock | `DW-TASK-003` | v1 | Retain on desktop; use a labelled full-screen sheet on phone. |
| TASK-CTRL-24 | Run-panel show/hide | Functional local state | `DW-TASK-003` | v1 | Persist per-device preference without hiding current approval or status. |
| TASK-CTRL-25 | Steering composer submit | Simulated; only clears input | `DW-TASK-004` | v1 | Submit through verified queue/interrupt behavior with pending, conflict, and failure states. |
| TASK-CTRL-26 | Queue versus interrupt choice | Missing | `DW-TASK-004` | v1 | Expose only verified multitask strategies and explain their effect. |
| TASK-CTRL-27 | Cancel active task/run | Missing | `DW-TASK-004` | v1 | Record requested, confirmed, too-late, failed, and capability-unavailable states. |
| TASK-CTRL-28 | Retry failed task | Missing | `DW-TASK-004` | v1 | Start a related run/task from safe state with lineage and idempotency. |
| TASK-CTRL-29 | Checkpoint branch/fork | Missing | `DW-TASK-004` | Flagged v1 | Enable only from a verified checkpoint contract; otherwise copy to a related task. |
| TASK-CTRL-30 | Rename task | Missing | `DW-TASK-004` | v1 | Persist app-owned title with conflict and audit behavior. |
| TASK-CTRL-31 | Archive/restore task | Missing | `DW-TASK-004` | v1 | Keep source thread intact and preserve audit/provenance. |
| TASK-CTRL-32 | Delete/duplicate task | Missing | `DW-TASK-004` | Later | Defer until retention/source-deletion and duplication semantics are accepted. |
| TASK-CTRL-33 | First-class artifact list/download | Missing | `DW-TASK-005` | v1 | Separate durable artifacts from sandbox files and user attachments. |
| TASK-CTRL-34 | Research, writing, and coding journey variants | Only hard-coded fixture labels/prompts | `DW-TASK-005` | v1 | Use one task model with journey-specific preflight, capabilities, artifacts, and completion evidence. |
| TASK-CTRL-35 | Verification/verdict history | Missing | `DW-HITL-002` | v1 | Show criteria, attempts, evidence, verdict, override, and terminal reason. |
| TASK-CTRL-36 | Terminal session switch | Functional local switching over fixture output | `DW-CODE-003` | Flagged v1 | Render bounded read-only execution streams for capable coding sources. |
| TASK-CTRL-37 | New/close terminal session | New is inert; close glyphs are non-buttons; pane close works locally | `DW-CODE-003` | Later | V1 remains read-only unless an interactive-terminal security contract is accepted. |

## RunPanel tabs

All tabs are currently inaccessible below `lg` because the containing aside is hidden without a sheet or alternate route.

| ID | Tab | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| PANEL-01 | Stream | Simulated replay of fixture events | `DW-TASK-003` | v1 | Bind to verified normalized events, cursor, dedupe, malformed-event, and reconnect behavior. |
| PANEL-02 | Agents | Simulated subagent tree with invented progress | `DW-TASK-005` | Flagged v1 | Render only supplied linked-run/subagent identity and state; never invent percentages. |
| PANEL-03 | Context | Simulated token/window/compaction accounting | `DW-TASK-003` | v1 | Show a read-only, redacted source summary only when accounting is trustworthy. |
| PANEL-04 | Trace | Simulated local waterfall | `DW-OPS-002` | Fold | Replace with compact run metadata and an allowlisted LangSmith trace link. |
| PANEL-05 | Browser | Simulated screenshot/history and unverified external URL | `DW-CODE-003` | Flagged v1 | Show safe browser evidence only for a tested sandbox/browser capability. |
| PANEL-06 | Status | Simulated task metadata and todos | `DW-TASK-003` | Fold | Put canonical status in the task header and retain compact run/todo diagnostics. |
| PANEL-07 | Files | Simulated fixture tree/viewer | `DW-CODE-003` | Flagged v1 | Enforce file/artifact boundary, path authorization, media safety, size limits, and mobile review. |
| PANEL-08 | Git | Simulated branch/commit/PR/CI state | `DW-CODE-002` | Flagged v1 | Derive from authorized repository state and require fresh checks before land/merge actions. |

## Approval controls

| ID | Surface/control | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| APPROVAL-01 | Cross-agent approval queue | Simulated fixtures | `DW-HITL-001` | v1 | Project current interrupts per source with freshness and permission state. |
| APPROVAL-02 | Tool/agent queue filters | Inert | `DW-HITL-001` | v1 | Filter by normalized source, action, capability, risk, and freshness where available. |
| APPROVAL-03 | "Approve all safe" | Inert and unsafe | `DW-HITL-001` | Remove | No bulk approval in v1. |
| APPROVAL-04 | Approve | Simulated local success | `DW-HITL-001` | v1 | Submit one allowed ordered decision per action with idempotency. |
| APPROVAL-05 | Edit | Simulated as immediate local resolution; no form | `DW-HITL-001` | v1 | Render schema-valid edited arguments only when the review config allows edit. |
| APPROVAL-06 | Respond | Simulated as immediate local resolution; no input | `DW-HITL-001` | v1 | Collect and validate response only for response-capable requests. |
| APPROVAL-07 | Ignore | Contract-invalid decision | `DW-HITL-001` | Remove | Replace with Reject only where allowed; dismissal never resumes a live interrupt. |
| APPROVAL-08 | Reject | Missing | `DW-HITL-001` | v1 | Offer only where allowed and preserve optional reason. |
| APPROVAL-09 | Ordered multi-action batch | Missing; prototype flattens one command/detail | `DW-HITL-001` | v1 | Preserve aligned `actionRequests[]`, `reviewConfigs[]`, and one ordered decision per action. |
| APPROVAL-10 | Stale/raced approval handling | Missing | `DW-HITL-001` | v1 | Refetch before ambiguous submission and show durable current outcome. |
| APPROVAL-11 | Task deep link | Functional navigation over fixtures | `DW-HITL-001` | v1 | Open authorized task/current interrupt and preserve source/batch identity. |
| APPROVAL-12 | Mobile push one-tap review | Missing | `DW-HITL-001` | v1 | Permit only fully visible simple approve/reject; edit/respond opens complete sheet. |
| APPROVAL-13 | Decision audit trail | Missing | `DW-HITL-001` | v1 | Record actor, observed batch version, decisions, source result, time, and stale/idempotency outcome. |
| APPROVAL-14 | Plan review card | Missing | `DW-HITL-001` | Flagged v1 | Use the same ordered batch model after the starter agent passes its plan-interrupt contract. |

## Agent controls

| ID | Surface/control | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| AGENT-CTRL-01 | Agent index/cards | Simulated global fixtures | `DW-AGENT-002` | v1 | Use composite source identity, real authority, capabilities, health, and pagination. |
| AGENT-CTRL-02 | All/Active/Templates/Org library filters | Inert | `DW-AGENT-002` | v1 | Add source, runtime, health, and capability filters; keep template gallery in creation. |
| AGENT-CTRL-03 | Health/active status | Simulated decorative state | `DW-AGENT-002` | v1 | Show cached probe time, degraded/unauthorized/unknown states, and re-probe. |
| AGENT-CTRL-04 | Configure/detail link | Functional navigation to simulated builder | `DW-AGENT-002` | v1 | Open Overview, Configuration, Schedules, Environment, and Deploy according to authority. |
| AGENT-CTRL-05 | New agent route | Simulated fixture clone through `id="new"` | `DW-AGENT-003` | Flagged v1 | Create from portable templates for supported classic source; MDA uses export/CLI handoff. |
| AGENT-CTRL-06 | Clone button | Inert and assumes mutation authority | `DW-AGENT-003` | Later | Prefer validated export/import; add clone only after source/secret semantics are explicit. |
| AGENT-CTRL-07 | Builder chat send | Inert | `DW-FUT-204` | Later | Do not port until chat-to-configure produces reviewable versioned diffs. |
| AGENT-CTRL-08 | AGENTS/tools/subagents/schedules tabs | Simulated local selection/static content | `DW-AGENT-003` | Fold | Replace with versioned Agent detail sections and source-aware schedule/environment ownership. |
| AGENT-CTRL-09 | Per-tool Auto/Ask | Simulated local state | `DW-AGENT-005` | v1 | Compile only supported policy, separate filesystem rules, and audit high-risk Auto changes. |
| AGENT-CTRL-10 | Save changes | Inert and semantically ambiguous | `DW-AGENT-003` | v1 | Save versioned draft only; Validate and Deploy remain separate explicit actions. |
| AGENT-CTRL-11 | Validate, semantic diff, Deploy, status, rollback | Missing | `DW-AGENT-003` | v1 | Add optimistic concurrency, safe build logs, active-revision protection, and CLI handoff for MDA. |
| AGENT-CTRL-12 | Import/export portable project ZIP | Missing | `DW-AGENT-003` | v1 | Validate/extract safely and preserve supported project provenance. |
| AGENT-CTRL-13 | Implied org-wide create/update/share/Fleet CRUD | Contract-invalid product copy | `DW-AGENT-001` | Remove | Fleet remains capability-tested read/invoke; unsupported mutations link out or export. |

## Schedule, activity, and observability controls

| ID | Surface/control | Current state | Owner feature ID | Disposition | Planned resolution |
|---|---|---|---|---|---|
| OPS-CTRL-01 | Schedule list and On/Paused badges | Simulated static rows; badges are not controls | `DW-OPS-001` | Flagged v1 | Aggregate per source and identify schedule owner/mutation mechanism. |
| OPS-CTRL-02 | All/Active/Paused filters | Inert | `DW-OPS-001` | v1 | Use real URL-backed filters over known records. |
| OPS-CTRL-03 | Create/edit schedule | Missing | `DW-OPS-001` | Flagged v1 | Support verified classic cron mutation or edit project declaration then Deploy. |
| OPS-CTRL-04 | Pause/resume/delete | Missing | `DW-OPS-001` | Flagged v1 | Confirm destructive scope and disable for read-only/Fleet sources. |
| OPS-CTRL-05 | Cron/timezone/DST/input/delivery/overlap validation | Missing | `DW-OPS-001` | v1 | Validate and preview local plus UTC semantics before save/deploy. |
| OPS-CTRL-06 | Next run, run history, generated task and trace links | Only static next-time text | `DW-OPS-001` | v1 | Link each firing to schedule, task, source, outcome, and trace where available. |
| OPS-CTRL-07 | Activity feed | Simulated static rows | `DW-OPS-001` | v1 | Combine application audit and normalized source events with actor/source provenance. |
| OPS-CTRL-08 | Activity event-type filters | Inert | `DW-OPS-001` | v1 | Filter time, actor, source, agent, type, and outcome. |
| OPS-CTRL-09 | Activity trace links | Simulated fabricated IDs | `DW-OPS-002` | v1 | Generate allowlisted links only from verified source metadata. |
| OPS-CTRL-10 | Activity pagination/partial-source/stale states | Missing | `DW-OPS-001` | v1 | Preserve healthy source events and label unavailable coverage. |
| OPS-CTRL-11 | Standalone observability KPI/charts | Simulated static data | `DW-OPS-002` | Fold | Keep cheap summaries in Activity/agent detail; deep-link to LangSmith for trace analytics. |
| OPS-CTRL-12 | Run/approval/failure notifications and preferences | Missing | `DW-OPS-002` | v1 | Add signed webhook receipt, dedupe, minimal push payload, quiet hours, and revocation. |
| OPS-CTRL-13 | Organizational memory seed, proposal, review, and publish loop | Missing; Memory settings imply direct local mutation | `DW-OPS-003` | v1 | Seed reviewed context and publish analyst proposals only through human-approved, versioned service action. |

## Settings: 22-section disposition

The current catch-all settings experience mixes workspace, agent, environment, and deployment ownership. Each section below has one owner; "Fold" names the migration out of global Settings.

| ID | Prototype section | Current state | Owner feature ID | Disposition | Planned location/behavior |
|---|---|---|---|---|---|
| SETTINGS-01 | Models | Simulated local controls | `DW-AGENT-004` | Fold | Agent draft: portable provider/model, verified profile, safe parameters, fallback order. |
| SETTINGS-02 | Configuration | Simulated; placeholder config link and inert Diagnose/Reinstall | `DW-AGENT-004` | Fold | Split normalized agent fields from environment/runtime diagnostics; remove Codex-specific assumptions. |
| SETTINGS-03 | Profiles | Simulated local selection | `DW-AGENT-004` | Later | Ship only after a portable versioned profile contract is accepted. |
| SETTINGS-04 | Goals & rubrics | Simulated local edit/add/remove | `DW-HITL-002` | Flagged v1 | Put rubric defaults in task template/agent draft; full goal lifecycle stays later. |
| SETTINGS-05 | Sandboxes | Simulated controls; wording conflates task, thread, worktree | `DW-CODE-001` | v1 | Environment detail with scope, snapshot, resources, lifecycle, setup, egress, and capability fallback. |
| SETTINGS-06 | Interpreters | Simulated local toggles | `DW-AGENT-004` | Later | Hold until interpreter/PTC packages and security model are stable and verified. |
| SETTINGS-07 | Backends | Simulated editable backend/checkpointer selectors | `DW-AGENT-004` | Fold | Read-only source diagnostics; runtime-owned backend/store/checkpointer are not arbitrary settings. |
| SETTINGS-08 | Tools | Simulated local toggles | `DW-AGENT-005` | Fold | Agent Configuration with schemas, source, risk, availability, and versioned draft. |
| SETTINGS-09 | Permissions | Simulated local Auto/Ask/Off matrix | `DW-AGENT-005` | Fold | Agent policy editor only where enforceable; keep filesystem and tool HITL separate. |
| SETTINGS-10 | Multimodality | Simulated unsupported toggles | `DW-AGENT-004` | Flagged v1 | Read capability by model/source; expose composer media only after validated handoff. |
| SETTINGS-11 | Memory | Simulated compaction/store controls | `DW-AGENT-005` | Fold | Agent/user policy with scope/provenance; org publication requires human review. |
| SETTINGS-12 | Subagents | Simulated toggles/selectors; New subagent inert | `DW-AGENT-005` | Fold | Agent draft with declarative identity, instructions, tools, model, limits, and cycle validation. |
| SETTINGS-13 | Streaming | Simulated transport/event toggles | `DW-AGENT-004` | Fold | Read-only source diagnostics; transport policy stays in verified adapter configuration. |
| SETTINGS-14 | Hooks | Simulated enable state; other actions inert | `DW-AGENT-004` | Later | Ship audited built-ins only in v1; defer custom execution editor. |
| SETTINGS-15 | Environments | Simulated local edit; Add Project inert; Save only navigates | `DW-CODE-001` | v1 | Environment detail with versioned secret-safe persistence and validation. |
| SETTINGS-16 | Worktrees | Simulated local controls; Refresh inert | `DW-FUT-205` | Later | Defer multi-repository/worktree lifecycle and partial-failure semantics. |
| SETTINGS-17 | Git | Simulated local branch/PR toggles | `DW-CODE-002` | Fold | Repository/environment policy with installation authority, branch protection, PR, CI, and merge checks. |
| SETTINGS-18 | Connectors | Simulated filters/modal; connect/add/tool actions inert | `DW-AGENT-005` | v1 | Split workspace credential account from agent connector binding; protect against SSRF and scope drift. |
| SETTINGS-19 | Plugins | Simulated details; install/build inert | `DW-AGENT-005` | Later | Permit only reviewed skill/MCP manifests; no opaque executable bundle. |
| SETTINGS-20 | Skills | Simulated search/preview; toolbar/edit/save inert | `DW-AGENT-005` | Fold | Agent project/Context Hub versioned `SKILL.md` browser/editor with provenance. |
| SETTINGS-21 | Protocols | Simulated static ACP/MCP/A2A claims; connect actions inert | `DW-AGENT-004` | Remove | Fold verified MCP setup into Connectors; ACP/A2A belong to the later interoperability brief. |
| SETTINGS-22 | Deployment | Simulated MDA-only status; Open inert | `DW-AGENT-003` | Fold | Deploy tab: classic baseline revision/build/health; MDA export/CLI handoff behind capability. |

## Existing delivery units U1-U19

The existing delivery plan is a program artifact whose units often bundle several independently owned capabilities. Each unit below has one **program-index owner**; supporting feature IDs are dependencies or consumers, not co-owners. Integration must replace bundled implementation detail with links to those feature plans.

| Unit | Existing outcome | Program-index owner | Supporting feature IDs | Evaluation and required expansion |
|---|---|---|---|---|
| U1 | Monorepo scaffold | `DW-FND-001` | `DW-FND-003`, `DW-QUAL-001` | Add Python/API/Postgres workspace, migrations, dependency direction, OSS/clean-install/release/security evidence. |
| U2 | Import frontend and hygiene | `DW-FND-002` | `DW-SURF-001`, `DW-QUAL-001` | Preserve one-way migration from `26c698b`; port tokens/primitives and audited surfaces, not fixtures or guessed contracts. |
| U3 | OAuth probe | `DW-ONB-001` | `DW-FND-003` | Gate OAuth on exact scope/audience tests; retain server-side API-key/session baseline and complete revocation/recovery states. |
| U4 | MDA loop | `DW-ONB-002` | `DW-AGENT-001`, `DW-AGENT-003` | Remove MDA from the critical path, use official CLI workflow, detect entitlement, and fall back to classic Deployment. |
| U5 | Stream contract | `DW-FND-004` | `DW-TASK-003`, `DW-HITL-001` | Separate protocol-v2 `since`/durable-event semantics from legacy resume and add golden reconnect/HITL transcripts. |
| U6 | Deployable `packages/agent` v0 | `DW-AGENT-003` | `DW-AGENT-005`, `DW-TASK-005` | Define independently deployable Python project, templates/middleware, fixtures/evals, artifacts, boundaries, and classic deploy path. |
| U7 | `AgentSource` and data provider | `DW-FND-004` | `DW-AGENT-001`, `DW-FND-005` | Split query/mutation/stream services, use composite identities, per-source cursors/partial failure, and fixture/live parity. |
| U8 | Server routes and sign-in | `DW-FND-003` | `DW-ONB-001`, `DW-SURF-001` | Replace thin Next-only glue with shared FastAPI/Postgres ownership for sessions, authorization, source registry, jobs, audit, and recovery. |
| U9 | Live inbox and composer | `DW-TASK-001` | `DW-TASK-002`, `DW-ONB-002` | Add per-source aggregation/search/pagination plus drafts, templates, attachments, idempotent dispatch, demo/no-source, and recovery. |
| U10 | Live task detail | `DW-TASK-003` | `DW-TASK-004`, `DW-TASK-005`, `DW-SURF-001` | Replace invented stream methods; add reducer, reconnect/dedupe, steering, lifecycle, artifacts, mobile panels, and capability fallbacks. |
| U11 | HITL approvals | `DW-HITL-001` | `DW-TASK-003` | Preserve aligned arrays and ordered decisions; add allowed schemas, stale/idempotent races, audit, permissions, and phone limits. |
| U12 | Verification | `DW-HITL-002` | `DW-TASK-002`, `DW-AGENT-005` | Gate middleware versions and define rubric/goal, plan approval, evidence/verdict history, iteration caps, failures, and metrics. |
| U13 | Coding surfaces | `DW-CODE-002` | `DW-CODE-001`, `DW-CODE-003`, `DW-TASK-005` | Complete sandbox/environment/GitHub/files/diff/comment/PR/CI/phone lifecycle; remove arbitrary MDA connector routes. |
| U14 | Subagents and branching | `DW-TASK-004` | `DW-TASK-005`, `DW-AGENT-005` | Define checkpoint/fork provenance and parent-child identity, cancellation, aggregation, mobile summary, and no-capability fallback. |
| U15 | Fleet manager | `DW-AGENT-003` | `DW-AGENT-001`, `DW-AGENT-002`, `DW-AGENT-004`, `DW-AGENT-005` | Rename to Agents/Configuration; Fleet is read/invoke, classic owns supported deploy, MDA is gated, and drafts are versioned. |
| U16 | Schedules and Activity | `DW-OPS-001` | `DW-OPS-002` | Separate project declarations from deployment crons; add per-source aggregation, timezone/DST, audit, trace links, notifications, and failures. |
| U17 | Organizational intelligence Layers 0-1 | `DW-OPS-003` | `DW-AGENT-005`, `DW-HITL-001` | Use versioned official Context Hub/project paths with staged proposal/evidence/diff/review/conflict/audit; no automatic org-memory write. |
| U18 | PWA and Tauri | `DW-SURF-001` | `DW-SURF-002`, `DW-OPS-002` | Add durable push ownership, offline/freshness behavior, authenticated deep links, same-API desktop host, signing/updater, and rollback. |
| U19 | Polish, accessibility, performance, and docs | `DW-QUAL-001` | all v1 feature owners | Move quality into every plan and enforce accessibility, performance, untrusted content, security, migration/recovery, and executable release gates. |

## Existing delivery-plan requirements R1-R13

| Requirement | Protected-plan claim | Owner feature ID | Disposition | Planned correction |
|---|---|---|---|---|
| R1 | pnpm/Turborepo monorepo with web, desktop, agent, SDK, UI, and CI | `DW-FND-001` | Expand | Add `apps/api`, Python 3.12, Postgres/migrations, package direction, OSS/release/security gates, and clean-install fixtures. |
| R2 | Import prototype as `apps/web` and apply hygiene | `DW-FND-002` | Reframe | Port audited shell/tokens/components one way from `26c698b`; do not import fixture behavior or treat a bulk copy as migration. |
| R3 | OAuth, MDA, and stream spikes before implementation | `DW-FND-004` | Expand | Use the complete named spike register; classic/API-key fallbacks let unaffected foundation work proceed while gated capabilities stay off. |
| R4 | SDK `AgentSource` registry and one `DataProvider` consumed by UI | `DW-FND-004` | Reframe | Use capability-aware source identity plus separate queries, mutations, streams, normalization, and per-source aggregation. |
| R5 | Deployable research/writing `packages/agent` | `DW-AGENT-003` | Expand | Keep the Python agent package independent; define versioned project/template, validation/export/deploy, artifacts, middleware, and classic baseline. |
| R6 | Inbox, composer, and detail through React `useStream` | `DW-TASK-003` | Split | Task list/composer use framework-neutral services; only active streaming uses a React binding, with durable hydration and recovery. |
| R7 | OAuth or API-key key-proxy sign-in | `DW-ONB-001` | Reframe | Server-side application session and API key are baseline; OAuth appears only after audience/scope acceptance. |
| R8 | Approvals use a simplified `HITLRequest` decision contract | `DW-HITL-001` | Correct | Preserve ordered `actionRequests[]` and aligned `reviewConfigs[]`, exact allowed decisions, stale protection, and idempotent audit. |
| R9 | Files/Git use sandbox connector routes; diff/comments and GitHub App ship | `DW-CODE-003` | Correct and split | Remove arbitrary connector routes; consume verified sandbox/files/GitHub capabilities owned by `DW-CODE-001/002` with safe mobile review. |
| R10 | Fleet manager/builder/schedules use `/v1/deepagents/*` and crons | `DW-AGENT-003` | Correct and split | Remove unsupported CRUD; Fleet is read/invoke, classic owns supported config/deploy, MDA is CLI/gated, and schedules are per source under `DW-OPS-001`. |
| R11 | PWA, Web Push, offline shell, and Tauri wrapper ship | `DW-SURF-001` | Expand | Define durable notification ownership, offline data/cache policy, authenticated deep links, mobile parity, and Tauri security/updater gate. |
| R12 | All canonical v1 release criteria pass | `DW-QUAL-001` | Expand | Trace every criterion to an executable owning-plan scenario plus migration, backup/restore, security, source-outage, and rollback evidence. |
| R13 | Quickstart, self-deploy, and agent-authoring docs ship | `DW-QUAL-001` | Expand | Test docs from a clean environment against the supported classic/API-key baseline and include API/database/desktop operations. |

## Canonical Deep Agents feature map

This section maps every named feature row in `docs/plan/08-deepagents-feature-map.md` at `06f0515`. Its original include/defer labels are evidence, not retained automatically; the contract audit and owning plan determine the revised disposition.

| Source item | Documented feature or claim | Owner feature ID | Disposition | Audited treatment |
|---|---|---|---|---|
| DAFM-01 | Overview, Quickstart, Customization, and `create_deep_agent` composition | `DW-AGENT-003` | v1 | Keep the Python agent package independently deployable and pin middleware override behavior before relying on it. |
| DAFM-02 | Models and `provider:model` configuration | `DW-AGENT-004` | v1 | Expose only validated provider/model/profile fields and preserve an explicit unsupported state. |
| DAFM-03 | Comparison/positioning against other agent SDKs | `DW-FND-001` | Fold | Treat claims as documentation evidence requiring verification; never turn vendor comparison copy into an authorization or tenancy guarantee. |
| DAFM-04 | Deep Agents Code (`dcode`) companion patterns | `DW-AGENT-005` | Fold | Reuse compatible project conventions/skills only; do not make a separate CLI a product-runtime dependency. |
| DAFM-05 | Changelog/dependency monitoring | `DW-FND-001` | v1 | Pin dependency groups and make contract revalidation part of upgrade acceptance rather than tracking an unbounded alpha channel. |
| DAFM-06 | Managed Deep Agents | `DW-AGENT-001` | Flagged v1 | Private-beta, region/tier-capability adapter; classic deployment remains the release baseline and official CLI owns deploy. |
| DAFM-07 | Going to production/classic deployment | `DW-ONB-002` | v1 | Supported remote baseline for first task, reconnect, HITL, and release acceptance. |
| DAFM-08 | Fault-tolerance middleware stack | `DW-AGENT-005` | Flagged v1 | Version-test retry/fallback/error/limit middleware; surface bounded outcomes without claiming every middleware is universally available. |
| DAFM-09 | Built-in and curated tools | `DW-AGENT-005` | v1 | Versioned tool schemas, source capability, risk, permission, failure, and untrusted-result handling. |
| DAFM-10 | State/composite/sandbox/context backends | `DW-AGENT-004` | Fold | Runtime-owned backend facts are diagnostics; user editing is limited to portable verified project/environment choices. |
| DAFM-11 | Filesystem and per-tool permissions | `DW-AGENT-005` | v1 | Preserve separate filesystem and tool/HITL enforcement domains; do not imply one matrix governs both. |
| DAFM-12 | Multimodality | `DW-AGENT-004` | Flagged v1 | Gate composer/viewer media by exact model, runtime, storage, summarization, security, and accessibility capability. |
| DAFM-13 | Sandboxes and snapshots | `DW-CODE-001` | Flagged v1 | Distinguish environment, snapshot, platform sandbox, and MDA per-thread ownership; require lifecycle/egress/expiry evidence. |
| DAFM-14 | Interpreters and dynamic subagents beta | `DW-AGENT-004` | Later | Keep out of default v1 until execution authority, package stability, limits, observability, and security pass discovery. |
| DAFM-15 | Event streaming beta and frontend streaming | `DW-FND-004` | Flagged v1 | Separate protocol-v2 `since`/event IDs from legacy/run-join resume and capability-test every source. |
| DAFM-16 | Skills | `DW-AGENT-005` | v1 | Versioned, provenance-bearing project/Context Hub skill path with safe preview/edit and no opaque install execution. |
| DAFM-17 | User, tenant, and organization memory | `DW-AGENT-005` | v1 | Define scope/ownership explicitly; organization publication is a human-reviewed proposal flow under `DW-OPS-003`. |
| DAFM-18 | Context engineering, offload, summarization, and runtime identity | `DW-TASK-005` | Flagged v1 | Render compaction/provenance honestly and verify identity propagation; do not promise all harness behavior “for free.” |
| DAFM-19 | Harness profiles beta | `DW-AGENT-004` | Later | Require a portable, versioned, conflict-safe profile contract before exposing reusable profile editing. |
| DAFM-20 | Synchronous subagents | `DW-TASK-005` | Flagged v1 | Gate on stable namespace/parent identity and provide generic parent-timeline fallback. |
| DAFM-21 | Asynchronous subagents/workstreams preview | `DW-FUT-101` | Later | Detailed v1.x goal/workstream brief with lifecycle, steering, ownership, recovery, and explicit discovery gates. |
| DAFM-22 | Human-in-the-loop | `DW-HITL-001` | v1 | Preserve exact ordered batches, review configs, allowed decisions, stale/idempotent behavior, and phone limits. |
| DAFM-23 | Grading rubrics beta | `DW-HITL-002` | Flagged v1 | Pin middleware and evidence/verdict loop; fall back to human-authored criteria without an automated pass claim. |
| DAFM-24 | Frontend subagent/todo/sandbox IDE patterns | `DW-TASK-003` | v1 | Treat patterns as interaction evidence; normalize events and capability-gate subagent/files/browser/terminal projections. |
| DAFM-25 | MCP | `DW-AGENT-005` | Flagged v1 | Separate workspace credential account from agent binding and verify transport/auth/tool schemas; protect SSRF and secrets. |
| DAFM-26 | ACP editor integration | `DW-FUT-205` | Later | Discover stable protocol, identity, permissions, task mapping, and editor lifecycle before product commitment. |
| DAFM-27 | A2A endpoints/interoperability | `DW-FUT-205` | Later | Do not assume universal `/a2a/{assistant_id}`; verify source/version/auth and inbound delegation trust boundaries. |
| DAFM-28 | Research, data, RAG, and content use-case templates | `DW-TASK-002` | v1 | Ship reviewed research/writing/blank templates first; data/RAG variants remain capability/data-governance gated. |

## Reference-code and application-architecture ownership

These rows make the new cross-cutting audit traceable without creating a second
feature owner.

| Source item | Architecture/convention concern | Owner feature ID | Disposition | Owning result |
|---|---|---|---|---|
| REF-ARCH-01 | Repository/package/contributor conventions | `DW-FND-001` | v1 | Package-local Python locks/Makefiles, pnpm/Turbo/Oxc, scoped contribution workflow, no-credential path, clean consumers, and release method. |
| REF-ARCH-02 | API/worker/Postgres outbox/object-store/provider-adapter topology | `DW-FND-003` | v1 | FastAPI owns sessions, secrets, capability probes, aggregation and upstream streams; worker/object lifecycle is durable and auditable. |
| REF-ARCH-03 | Browser-safe Deep Work API/application-stream client | `DW-FND-004` | v1 | SDK calls only `/api/v1`, uses opaque application cursors, maps DTOs, and never contains provider/auth-reference logic. |
| REF-ARCH-04 | Pure TypeScript domain package and reducer | `DW-FND-005` | v1 | `packages/domain` owns safe identities/capabilities/status/errors/events/reducers with no I/O or framework dependency. |
| REF-ARCH-05 | Next.js responsive web/PWA architecture | `DW-SURF-001` | v1 | App Router, query cache plus pure stream reducer, complete phone journeys, bounded offline, safe push, and no separate v1 mobile app. |
| REF-ARCH-06 | Exact-trusted-origin Tauri host | `DW-SURF-002` | Flagged v1 | Narrow native bridge/session bootstrap, deep links/tray/notifications/updater; web/PWA fallback when qualification fails. |
| REF-ARCH-07 | Expo/native client boundary | `DW-FUT-202` | Later | Create a native app only after measured PWA gaps; reuse domain/API contracts, never DOM UI or a separate backend. |

## Canonical vision: v1 scope bullets

Compound bullets are split into atomic clauses so each row still has one owner.

| Source item | Canonical promise at `06f0515` | Prototype/plan issue | Owner feature ID | Disposition | Proposed resolution |
|---|---|---|---|---|---|
| VISION-V1-01 | LangSmith sign-in, PKCE/device flow, API-key fallback, org/workspace picker | Login is simulated; OAuth audience is unverified | `DW-ONB-001` | v1 | API-key/application-session baseline; OAuth and device flow only after spike/capability success. |
| VISION-V1-02 | Connect MDA, any Deployment, Fleet invoke/read, and local `langgraph dev` | No connections exist; MDA/Fleet capabilities are overclaimed | `DW-AGENT-001` | v1 | Classic Deployment and explicit local development baseline; MDA/Fleet are optional tested adapters. |
| VISION-V1-03 | Inbox, live task detail, tools/subagents/todos, steering, double-texting | All content and actions are fixtures/local | `DW-TASK-003` | v1 | Use normalized per-source task lifecycle and verified stream/multitask adapters. |
| VISION-V1-04 | HITL inbox with approve/edit/reject/respond and batches | Prototype uses flattened approve/edit/respond/ignore | `DW-HITL-001` | v1 | Ordered batch, allowed decisions, stale-race protection, idempotency, and audit. |
| VISION-V1-05 | Coding sandbox, environments/setup, GitHub proxy, files, diff, draft PR | Visual fragments are simulated and credentials/lifecycle are absent | `DW-CODE-003` | v1 | Complete supported coding journey with capability gates and safe artifact/file distinction. |
| VISION-V1-06A | List/inspect and configure/deploy the Deep Work agent | Prototype implies global CRUD and unversioned Save | `DW-AGENT-003` | v1 | Versioned classic project workflow; Fleet read/invoke only; MDA export/CLI handoff. |
| VISION-V1-06B | Schedules CRUD | Static list; API ownership differs by source | `DW-OPS-001` | Flagged v1 | Verified classic mutations or project-declaration deploy; otherwise read-only/unavailable. |
| VISION-V1-07A | Trace deep link on every run | Fixture links and a simulated waterfall | `DW-OPS-002` | v1 | Working trace link for trace-enabled runs or explicit unavailable capability. |
| VISION-V1-07B | Context-backed instructions, skills, and memory editing | Prototype local forms do not persist or preserve ownership | `DW-AGENT-005` | v1 | Versioned supported project/Context Hub paths with org-memory review guardrail. |
| VISION-V1-08A | Responsive web and installable mobile PWA with push | Responsive shell hides key surfaces; PWA/push absent | `DW-SURF-001` | v1 responsive / Flagged v1 install-push | One complete responsive product; enable install, offline cache, and push only on `SPIKE-PWA-001`-qualified cells, with web/in-app fallbacks. |
| VISION-V1-08B | Tauri desktop with tray, notifications, and deep links | No desktop app exists | `DW-SURF-002` | v1 | Thin trusted host over the same FastAPI contract, gated by remote-origin security spike. |
| VISION-V1-09 | First-class research/report and content tasks with artifact viewing | Only hard-coded fixture prompts/labels; artifact model missing | `DW-TASK-005` | v1 | Journey-specific preflight and completion over one canonical task/artifact model. |

## Canonical vision success criteria

These pinned criteria retain one executable owner and an explicit amended/flagged
disposition in the [acceptance-scenario index](acceptance-scenarios.md#pinned-canonical-success-criterion-reconciliation).

| Source item | Criterion | Owner feature ID | Disposition | Executable ownership statement |
|---|---|---|---|---|
| VISION-SC-01 | Sign-in to deployed agent to completed task with draft PR in under 15 minutes | `DW-ONB-002` | Amend | Measure first useful task within 15 minutes and the exact-revision draft-PR journey separately; do not hide the original promise. |
| VISION-SC-02 | Dispatch, steer, approve, review diff, and merge from a phone | `DW-SURF-001` | v1 | Real PWA/device journey; Merge counts only with current GitHub permission, CI, and protection state. |
| VISION-SC-03 | Fleet agent drives inbox/approvals without smith.langchain.com | `DW-AGENT-001` | Flagged v1 | Count only invoke/read and HITL operations proven for the current account; Fleet absence cannot block release. |
| VISION-SC-04A | Every run has one-click trace link | `DW-OPS-002` | v1 | Require a working link for trace-enabled runs and explicit unavailable state otherwise. |
| VISION-SC-04B | Every agent config exports as a portable Fleet-compatible deepagents project | `DW-AGENT-003` | v1 | Round-trip the accepted project ZIP; do not promise reverse Fleet mutation. |
| VISION-SC-05 | LangChain can fork and ship the repository | `DW-FND-001` | v1 | Verify OSS structure, reproducible setup, conventions, branding, licensing, and contribution posture. |

## Canonical roadmap v1 release criteria

| Source item | Release criterion | Owner feature ID | Disposition | Executable ownership statement |
|---|---|---|---|---|
| ROADMAP-RC-01 | Fresh sign-in to deployed agent to completed draft PR in under 15 minutes | `DW-ONB-002` | Amend | Same split as VISION-SC-01: 15-minute first useful task plus separately measured draft-PR journey. |
| ROADMAP-RC-02 | Full dispatch/steer/approve/diff/merge loop from a phone; installed PWA where qualified | `DW-SURF-001` | v1 responsive / Flagged v1 install | Complete on a real supported phone browser with no desktop-only action; installation is not a blocker on an unqualified platform. |
| ROADMAP-RC-03 | Fleet agent connected and driven through inbox plus approvals | `DW-AGENT-001` | Flagged v1 | Capability-tested Fleet path; release baseline remains classic when unavailable. |
| ROADMAP-RC-04A | Trace link on 100% of runs | `DW-OPS-002` | v1 | Measure trace-enabled supported runs; explicit unavailable sources are not falsely counted as linked. |
| ROADMAP-RC-04B | Agent config round-trips through export format | `DW-AGENT-003` | v1 | Validate safe ZIP import/export and normalized manifest preservation. |
| ROADMAP-RC-05A | Zero secrets in sandboxes | `DW-CODE-001` | v1 | Automated credential/path/trace inspection plus short-lived proxy tests. |
| ROADMAP-RC-05B | Untrusted boundaries on all webhook/schedule content | `DW-OPS-001` | v1 | Replay and malicious payload tests prove typed, non-HTML, non-policy input handling. |
| ROADMAP-RC-06A | Typecheck, lint, and tests green; quickstart/deploy/architecture docs complete | `DW-QUAL-001` | v1 | Release workflow executes all checks and follows docs from a clean environment. |
| ROADMAP-RC-06B | MIT and trademark hygiene audited | `DW-FND-001` | v1 | Verify license, attribution, naming, and non-affiliation language. |

## Staged revised success criteria

These audit criteria become canonical only after review, but mapping them now prevents the feature library from optimizing for corrected prose without an executable owner.

| Source item | Revised criterion | Owner feature ID | Disposition |
|---|---|---|---|
| AUDIT-SC-01 | API-key/proven OAuth, workspace, supported classic source, first non-destructive task under 15 minutes | `DW-ONB-002` | v1 |
| AUDIT-SC-02 | Disconnect/reconnect without duplicates or lost approval, with honest recovery | `DW-TASK-003` | v1 |
| AUDIT-SC-03 | Two-action HITL batch reviewed in order on desktop and phone with stale/idempotency protection | `DW-HITL-001` | v1 |
| AUDIT-SC-04 | Coding-capable source produces reviewed draft PR; phone merge only with fresh GitHub verification | `DW-CODE-003` | v1 |
| AUDIT-SC-05 | Working trace link or explicit trace-unavailable state | `DW-OPS-002` | v1 |
| AUDIT-SC-06 | MDA/Fleet absence does not block core onboarding/task/approval release | `DW-AGENT-001` | v1 |
| AUDIT-SC-07 | No broad platform/GitHub credential in browser, Tauri bundle, runtime state, sandbox, or logs | `DW-FND-003` | v1 |
| AUDIT-SC-08 | Selected journeys pass loading/empty/error/permission/offline/reconnect/stale/recovery at supported widths | `DW-QUAL-001` | v1 |
| AUDIT-SC-09 | Backup/restore, migration, webhook dedupe, rollback, and partial-source drills pass | `DW-QUAL-001` | v1 |
| AUDIT-SC-10 | Canonical docs and shipped UI make no unsupported contract claim | `DW-QUAL-001` | v1 |

## Explicit post-v1 backlog

Repeated items in the Vision cut line and Roadmap backlog are consolidated only when they describe the same capability. Every explicit item remains named in the source column.

| Source reference | Deferred item | Owner feature ID | Disposition | Discovery/acceptance boundary |
|---|---|---|---|---|
| Vision cut 1; Roadmap backlog 2 | Native Expo mobile applications | `DW-FUT-202` | Later | Reuse domain/API contracts only after native auth, push, files, streaming, and store-release design. |
| Vision cut 2; Roadmap backlog 3 | Slack, Linear, and Teams task-creation channels | `DW-FUT-203` | Later | Verify channel identity, signatures, thread mapping, approvals, delivery, and tenant isolation. |
| Vision cut 3; Roadmap backlog 1 | Pure-OSS backend/runtime tier | `DW-FUT-201` | Later | Prove protocol, persistence, streaming, HITL, auth, migration, and feature-degradation compatibility. |
| Vision cut 4; Roadmap backlog 4 | Chat-to-configure visual agent builder | `DW-FUT-204` | Later | Produce reviewable versioned diffs and never mutate live config directly from chat. |
| Vision cut 5; Roadmap backlog 7 | Multi-org/enterprise governance, team RBAC, SCIM, and admin/audit surfaces | `DW-FUT-206` | Later | Define roles, policy inheritance, assignment, shared inbox ownership, admin audit, and cross-workspace isolation. |
| Vision cut 6; Roadmap backlog 5 | GitLab/non-GitHub provider | `DW-FUT-205` | Later | Match repository, auth proxy, branch, merge request, pipeline, and review security guarantees. |
| Roadmap backlog 6 | Multi-repository tasks and worktree parallelism | `DW-FUT-205` | Later | Define repository manifest, partial failure, credential boundaries, provenance, and cross-repo landing. |
| Roadmap backlog 8 | LangSmith evaluation datasets from task outcomes | `DW-FUT-103` | Later | Consent, dataset schema, label provenance, privacy, sampling, and outcome-to-task lineage. |
| Roadmap backlog 9 | Goal draft/review/amend lifecycle | `DW-FUT-101` | Later | Version criteria, approval, amendments, evidence, pause/cancel, and completion reducer. |
| Roadmap backlog 10 | Async-subagent supervisor / linked parallel workstreams | `DW-FUT-101` | Later | Verify protocol, persistence, cancellation, compaction, child identity, and parent completion semantics. |
| Roadmap backlog 11 | Interpreter/PTC template hardening | `DW-AGENT-004` | Later | Hold controls until pinned beta packages and sandbox/security behavior stabilize. |
| Roadmap backlog 12 | ACP server for Zed/JetBrains editor integration | `DW-FUT-205` | Later | Verify protocol stability, editor identity, data disclosure, consent, and fallback handoff. |
| Roadmap backlog 13 | A2A/MCP exposure of Deep Work agents | `DW-FUT-205` | Later | Threat-model peer identity, capability disclosure, task authorization, and stable interop contracts. |
| Roadmap org ladder v1.x | Memory-synthesis review loop | `DW-FUT-102` | Later | Human-reviewed proposals with provenance, concurrency, publish audit, and no direct agent writes. |
| Roadmap org ladder v2, layer 3 | OKF/openwiki organizational knowledge base | `DW-FUT-207` | Later | Permission inheritance, citations, staleness, conflict, deletion, and retrieval evaluation. |
| Roadmap org ladder v2, layer 4 | Structured data plane, dbt MCP, and data-analyst template | `DW-FUT-207` | Later | Governed metrics, read-only query proposal/approval, row/column policy, cost, and exfiltration controls. |
| Roadmap org ladder v3 | Graphiti temporal organizational graph | `DW-FUT-301` | Later | Explicit opt-in, temporal provenance, correction/deletion, access filtering, and measurable value. |

## Cross-cutting completeness obligations

### Harness, architecture, and orchestration coverage

These are cross-cutting requirements, not additional feature IDs. Each still has
one primary plan owner so it cannot disappear between foundation and quality work.

| Coverage item | Requirement | Primary owner | Acceptance disposition |
|---|---|---|---|
| HARNESS-01 | Short root/nested `AGENTS.md` maps and canonical repository knowledge taxonomy | `DW-FND-001` | V1 foundation; staged until review |
| HARNESS-02 | Root `ARCHITECTURE.md`, machine-readable layer/package/domain/browser/provider graph, structural checks, and expiring exceptions | `DW-FND-001` | V1 foundation; `SPIKE-HARNESS-ARCH-001` |
| HARNESS-03 | Stable product specifications separated from program roadmap and self-contained living ExecPlans | `DW-FND-001` | V1 foundation; `SPIKE-HARNESS-DOCS-001` |
| HARNESS-04 | Indexed/generated docs, governed-path freshness, evidence quality score, owned debt, and recurring gardening | `DW-QUAL-001` | Continuous v1 release gate; `SPIKE-DOC-GARDEN-001` |
| HARNESS-05 | Browser-local UI harness and API-backed product demo have distinct proof levels and visible disclosure | `DW-FND-002` | V1; product demo is end-to-end authority |
| HARNESS-06 | Collision-free per-agent worktree ports/data/objects/browser origin/telemetry/proof | `DW-FND-001` | V1 before parallel app work; `SPIKE-WORKTREE-001` |
| HARNESS-07 | Queryable development logs/metrics/traces and browser proof for application changes | `DW-QUAL-001` | V1 quality cell; `SPIKE-DEV-OBS-001` |
| HARNESS-08 | Pinned Symphony tracker/DAG/workspace/reconciliation/retry/security/Human Review pilot | `DW-FND-001` | V1 developer-experience cell; manual dispatch fallback; `SPIKE-SYMPHONY-001` |
| HARNESS-09 | Generated release criterion → scenario → work item → PR → evidence traceability | `DW-QUAL-001` | V1 release gate; no manual duplicate ownership table |

The feature owner in every row must also satisfy these single-owner rules before the matrix can be accepted:

- `DW-FND-005` defines canonical identity/status/audit vocabulary; feature plans consume it without redefining task, thread, run, checkpoint, source, tenant, or actor.
- `DW-FND-003` owns application state/security primitives, but each feature owner specifies exactly which state it creates, reads, retains, redacts, and deletes.
- `DW-FND-003` owns secret-bearing source adapters and their server conformance; `DW-FND-004` owns the application client/stream and private fixture contracts. Each feature owner supplies its live and fixture journey scenarios without redefining either boundary.
- `DW-SURF-001` owns shared responsive/PWA mechanics, while each feature owner remains responsible for a complete phone journey and recovery states.
- `DW-QUAL-001` owns release enforcement, while a feature cannot delegate its own loading, empty, validation, permission, partial failure, offline, reconnect, stale, cancelled, success, accessibility, security, metrics, and rollback behavior to the quality plan.

Acceptance condition: every row above resolves to one existing feature plan, no owner is a family placeholder, all Flagged v1 rows name a deterministic fallback in that plan, and no Remove/Fold/Later surface remains as an apparently functional production control.
