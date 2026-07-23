# Vision and Scope Audit

Status: staged proposal; resolutions require review before canonical integration
Canonical plan pin: `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`
Frontend evidence pin: `deep-work-frontend@8866d39a2888e358091208063693f260cff6d261`
LangChain documentation pin: `langchain-docs-reference@7b9215d708e0b57e6fbae7b5d0762c4118b8e309`
Audit date: 2026-07-22

## Executive finding

The vision has a strong product center: an agent work inbox that makes delegated work observable, steerable, reviewable, and reachable across devices. The current canonical documents, however, describe a broader and more integrated product than their architecture and external contracts can support. The largest unresolved issue is not a missing UI detail: the application backend and durable state model are undefined while the product promises authentication, cross-source aggregation, idempotent approvals, notifications, mobile handoff, configuration drafts, and team-compatible authorization.

That contradiction is release-blocking. “Thin Next.js glue with no database” cannot safely provide the stated v1 experience. The staged resolution is a Python 3.12 FastAPI application service with Postgres durable application state, a Python `deepagents` agent package, Next.js web/PWA, Tauri desktop using the same application API, and shared TypeScript client/UI packages. This application backend remains separate from Agent Server and the LangSmith control/data/platform planes.

The second major issue is authority. The vision sometimes treats MDA, Fleet, Context Hub, sandboxes, deployments, and Agent Server as a uniform public platform. The contract audit shows they have different availability, ownership, authentication, and lifecycle rules. Classic LangSmith Deployment must be the supported public v1 remote baseline; MDA is a capability-detected private-beta adapter.

## What remains true

The following statements are coherent and should anchor the revised vision:

- Users need one place to dispatch, observe, steer, approve, verify, and recover agent work.
- Verification UX—not merely chat—is the differentiator: plans, todos, evidence, diffs, verdicts, and trace links reduce the cost of deciding whether work is safe to land.
- Deep Work should operate over user-controlled agents and runtimes rather than become another proprietary model/runtime.
- Coding, research, and writing share a task lifecycle but require capability-specific detail surfaces and outcomes.
- Web is the primary surface and complete phone baseline; install/PWA/push enable only on qualified browser cells, and Tauri hosts the same product rather than forking its domain logic.
- Platform-native tracing and execution remain authoritative; Deep Work stores the application state necessary to coordinate and explain the experience.
- Organizational knowledge changes are proposals that humans review, never invisible automatic writes.
- The frontend prototype is a useful visual hypothesis, not evidence that a feature or API exists.

## Contradiction register and proposed resolutions

| ID | Canonical tension | Evidence at `06f0515` | Risk | Proposed resolution |
|---|---|---|---|---|
| VS-01 | Team-compatible product versus “single-user v1” | `01-vision.md` names solo primary and team secondary with shared inbox; RBAC is deferred in `04-roadmap.md` | Cross-user leakage or a rewrite after launch | v1 acceptance is one actor in one selected workspace, but all records and queries carry actor, tenant, workspace, and source identity. No shared team inbox or admin RBAC UI in v1. Team-safe architecture is mandatory from day one. |
| VS-02 | OAuth product promise versus API-key fallback | `01-vision.md`, `02-architecture.md`, and `03-ui-spec.md` lead with Sign in with LangSmith while scopes are an M0 unknown | Simulated login presented as trust | API-key/key-proxy is the supported baseline. OAuth ships only if a live scope/audience spike proves every required plane; otherwise label it unavailable/experimental, not complete. |
| VS-03 | “Stores essentially nothing” / no database versus durable product behavior | `01-vision.md` and `02-architecture.md` say LangSmith is source of truth and no v1 database; roadmap requires sessions, aggregation, push, drafts, approvals, and handoff | Impossible persistence, replay, idempotency, and security model | Adopt Postgres for Deep Work-owned application state while keeping runtime payloads/traces source-authoritative. Replace “stores nothing” with “stores only the minimum application coordination state.” |
| VS-04 | Five-, six-, and seven-tab information architecture | `03-ui-spec.md` specifies five tabs; prototype exposes seven; Observability/Settings vary by document | Navigation churn and duplicate products | Desktop primary nav is Tasks, Approvals, Agents, Schedules, Activity. Fold Observability into Activity. Put Settings in workspace menu/command palette. Mobile uses Tasks, Approvals, Agents, More. |
| VS-05 | One client over every runtime versus material contract differences | `01-vision.md` and `02-architecture.md` describe common Assistants/Threads/Runs behavior | False portability and dead controls | Normalize only a proven common core; expose a source capability manifest and adapter-specific fallback. Classic deployment is baseline; local/Fleet/MDA are explicit adapters. |
| VS-06 | MDA primary/dogfood exit versus private beta | M1 exit requires real MDA; MDA is called private beta elsewhere | Public v1 blocked by entitlement/region | Make classic LangSmith Deployment the public release path. MDA is a non-blocking beta validation track. |
| VS-07 | Fleet manager versus no proven Fleet CRUD | Vision promises create/configure/operate like Fleet; architecture admits CRUD is not public | Unsupported product promise | v1 agent management means per-source list, inspect, invoke, health, and supported versioned configuration. Fleet remains read/invoke. Create/deploy is source-capability-gated. |
| VS-08 | Rich phone outcome versus web desktop-first prototype | Vision success criterion includes full phone dispatch-to-merge; prototype hides critical panels on mobile | Unverifiable flagship claim | Retain phone approval and coding review as v1 goals, but define exact mobile flows and a GitHub-backed merge contract. If merge cannot be verified, v1 criterion is review/approve/open GitHub, not claimed merge. |
| VS-09 | “Mark resolved” as force-end versus runtime authority | `03-ui-spec.md` proposes an END-equivalent dismissal | State corruption or hidden pending interrupt | Remove the user-visible action in v1. Reconciliation removes stale projections only after refetch proves no pending interrupt; pending work requires a valid decision or verified cancellation. |
| VS-10 | Save/configure versus deploy semantics | Builder/settings use Save language while roadmap mixes file editing and deployment | Accidental live mutation and lost revisions | Save creates a versioned draft. Deploy validates and asynchronously publishes an immutable revision through the supported source workflow. Status and rollback are separate. |
| VS-11 | Org memory lives outside Deep Work versus review/audit obligations | `07-org-intelligence.md` says no Deep Work-side store but promises proposals and approvals | No durable proposal, reviewer, or idempotency record | Context Hub/versioned target remains content authority; Postgres stores proposal metadata, review decisions, source commit references, and audit events. |
| VS-12 | Cancellation, retry, rename, archive, and delete are unspecified | Task loop and UI imply lifecycle controls without semantics | Inconsistent destructive behavior | Adopt the explicit lifecycle resolutions in this audit and encode them in the domain/status plans. |
| VS-13 | Backend stack undefined | `02-architecture.md` calls Next server routes thin glue; no application service, DB schema, migration, or job model owns core behavior | Release cannot be secured, recovered, or operated | Adopt the staged FastAPI/Postgres architecture below before any feature plan is implementation-ready. |

## Proposed product promise

> Deep Work is an open-source workspace for delegated agent work. Connect an authorized agent source, dispatch a task, follow its run, steer or approve it, inspect evidence and artifacts, and land the result from web, desktop, or phone. Your runtime remains authoritative for agent execution and traces; Deep Work stores the minimum secure application state needed for identity, coordination, recovery, and cross-source experience.

The promise intentionally avoids “Fleet CRUD,” “everything runs through one API,” “no database,” and “Sign in with LangSmith” until their contracts are proven.

## v1 actor and team boundary

### Accepted v1 journey

One authenticated actor selects one workspace, connects one or more sources they are authorized to use, and manages only their visible tasks and approvals. A workspace administrator may preconfigure a source or GitHub installation outside Deep Work, but v1 does not require a team administration console.

### Team-safe invariants required in v1

- Every session resolves an actor and workspace; every source reference resolves a tenant/workspace context.
- Composite identities include source and workspace boundaries; raw thread IDs are never treated as globally unique.
- Authorization is enforced in the FastAPI service before source credentials are resolved or queries are issued.
- App-owned projections, approval records, notifications, artifacts, and drafts are scoped by workspace and actor policy.
- Logs, traces, push payloads, desktop deep links, and URLs do not reveal cross-tenant secrets or unrestricted resource identifiers.
- A source response is filtered by the source's authorization, not by client-side hiding.
- Fixtures include two-workspace and two-actor negative tests even though team UI is deferred.

### Explicitly deferred

Shared inbox ownership/assignment, team roles, admin policy, billing, SSO administration, workspace membership management, and cross-workspace organization views are v2/RBAC work. “Architecture can support teams” is not the same as “v1 is a team product.”

## Release-blocking application architecture

### Required stack

| Layer | Staged decision | Owns | Must not own |
|---|---|---|---|
| `apps/api` | Python 3.12 FastAPI application service | sessions; actors/workspaces; Agent Source registry; auth references; cross-source task index; normalized IDs/status; approval idempotency/audit; notifications/webhooks; GitHub token proxy; configuration drafts/deploy jobs; feature/capability state; artifact metadata | Agent graph execution, source-authoritative thread/run state, LangSmith traces, arbitrary platform reimplementation |
| Postgres | Durable app database with migrations and backup/retention policy | minimum coordination/projection state required for secure multi-surface behavior | full duplicate transcript/trace store by default; plaintext provider credentials |
| `packages/agent` | Python `deepagents` application/project | Deep Work agent graph, middleware composition, tools/templates, coding/research/writing behavior | application sessions, cross-source aggregation, browser auth, deployment control-plane emulation |
| `apps/web` | Next.js responsive web/PWA | rendering, interaction, offline shell/cache policy, browser session client | broad source/platform secrets, direct cross-plane orchestration, canonical domain state |
| `apps/desktop` | Tauri host of the same product/API | secure shell integration, native notifications, deep links, tray, updater | forked business logic, bundled API keys, a separate desktop data model |
| `packages/sdk` | Shared TypeScript client/types | typed app API, normalized domain models, capability manifest, query/mutation clients, streaming consumer integration | secret resolution, server authorization, a universal guessed runtime API |
| `packages/ui` | Shared TypeScript design system | accessible tokens/components/patterns | data fetching, source contracts, product persistence |

### Plane separation

```text
Web/PWA and Tauri
        |
        v
Deep Work FastAPI + Postgres  -----> GitHub App/API
        |
        +-----> Agent Server data plane (assistants/threads/runs/state/stream/crons)
        |
        +-----> LangSmith control plane (deployment lifecycle)
        |
        +-----> LangSmith platform APIs/SDKs (Context Hub/sandboxes/traces)
        |
        +-----> MDA official beta workflow adapter (when entitled)
```

The application API orchestrates these systems; it does not present itself as Agent Server and does not merge their credentials or routes. The frontend calls the application API except for narrowly justified direct streaming paths whose identity, CORS, credential exposure, reconnect, and desktop behavior have passed security review.

### Minimum durable state

Postgres must have an accepted ownership/retention design for:

- users/actors, sessions, organizations/workspaces, membership references;
- Agent Sources, endpoint/assistant identity, workspace context, opaque auth references, capabilities, health/freshness;
- normalized composite task/thread/run/checkpoint identities and app display metadata;
- task title rename, archive state, retry/branch relationships, last-seen/unread state;
- approval batch references, decisions, idempotency keys, stale status, actor/time audit;
- source cursors, event/webhook dedupe, last successful sync, partial-failure state;
- notification subscriptions/preferences and delivery attempts;
- configuration drafts, immutable revision/deploy job references, validation results;
- GitHub installation/repository references and token-proxy audit metadata;
- attachment/artifact metadata, provenance, storage/source references, retention and scan state;
- feature flags, beta entitlements, contract/capability versions;
- organizational-memory proposal/review/commit references;
- security/audit events required to explain sensitive actions.

Do not copy full LangSmith traces or thread state into Postgres by default. Store identifiers, cursors, projections, and user-owned metadata; fetch source-authoritative details as needed under a documented cache/retention policy.

## Canonical glossary proposal

| Term | Canonical meaning | Disallowed ambiguity |
|---|---|---|
| Task | Deep Work's user-facing unit of delegated work. It projects one primary source thread and may relate retries/branches/runs/artifacts. | Do not use as a synonym for an individual run or background subagent job. |
| Thread | Source-authoritative durable conversation/state container, scoped to one Agent Source. | Never assume a thread ID is globally unique. |
| Run | One execution attempt in a thread, with a terminal or interrupted outcome. | Steering input is not necessarily a run until the source accepts it. |
| Checkpoint | Source-authoritative saved graph state/address usable for resume or branch when supported. | Not a generic database snapshot or sandbox snapshot. |
| Agent | User-facing configured worker/persona that can be selected or inspected. | Do not assume every agent is mutable or deployed by Deep Work. |
| Assistant | Agent Server resource/version used to invoke a graph. | Do not display raw assistant identity as a universal agent identity without source context. |
| Deployment | Hosted Agent Server instance/revision managed through its deployment authority. | Not an agent, source connection, or Deep Work release. |
| Source / Agent Source | A configured connection to a runtime/deployment plus assistant identity, auth reference, workspace context, and capabilities. | Not merely a base URL or API key. |
| Environment | User/project configuration describing repository, setup, egress, variables, and desired execution policy. | Not a running sandbox. |
| Snapshot | Immutable or versioned sandbox/filesystem image used to provision an environment. | Not a graph checkpoint or database backup. |
| Sandbox | Isolated runtime/filesystem instance used for execution, with a documented task/thread/run scope and lifecycle. | Do not assume all sources expose or map sandboxes identically. |
| Interrupt | Source runtime state requesting input before execution can proceed. | Not the same as cancelling a run. |
| Approval | A user-facing review of an interrupt action request under its review config. | Not every interrupt is a binary approval. |
| Decision | One ordered approve/edit/reject/respond result for one action request. | “Ignore” and app dismissal are not runtime decisions. |
| File | Path-addressed content in a task/runtime workspace or versioned project. | Not automatically durable after sandbox termination. |
| Artifact | Durable task output with provenance, media type, size, retention, and download/reference semantics. | Not every sandbox file is an artifact. |
| Attachment | User-supplied input bound to a draft/task, scanned and handed to a source under explicit limits. | Not an untrusted direct filesystem mount by default. |
| Organization | Top-level external/account grouping where provided; may contain workspaces. | Do not conflate with a Deep Work workspace. |
| Workspace | Selected authorization and product context for app records and source connections. | Not a sandbox working directory. |
| Tenant | Security-isolation identifier used by a source/platform. | Not a user-visible label unless the source uses it that way. |
| Actor | Authenticated human/service identity responsible for an app action. | Not inferred solely from an email or client-supplied header. |

The separate catalog glossary should become the canonical term registry after review; feature plans may reference it but must not redefine these identities locally.

## Task lifecycle resolutions

| Operation | Proposed v1 semantics | Persistence/audit | Capability fallback |
|---|---|---|---|
| Cancel | Request cancellation/interruption of the current run, preserving the thread and existing checkpoints. Show requested, confirmed, too-late, and failed states. | Record actor, time, source request/result, and last confirmed run state. | If source cannot cancel, disable with explanation; never simulate success. |
| Retry | Create a new run from the latest safe source state/checkpoint; if unsafe or unsupported, create a branched task/thread. Never mutate the failed run. | Record parent run/task, selected checkpoint, reason, idempotency key. | New task with copied prompt/context and explicit provenance. |
| Rename | Change app-owned display title. Optionally patch source metadata only when advertised and explicitly selected. | Version/audit app title and optional source sync result. | App title remains authoritative for Deep Work display. |
| Archive | Hide from default Deep Work views while preserving source thread and recovery. | Actor/time plus restore state. | Always app-owned; source archive is a separate feature if it exists. |
| Delete | Deferred from v1. Archive/restore is the supported lifecycle action. A later delete design must distinguish removing the Deep Work projection from separately deleting source threads, traces, artifacts, and attachments. | Future work requires target/scope, actor, retention/tombstone, legal/audit policy, and independently confirmed source results. | Offer archive/restore only; never imply source data was erased. |
| Retry approval submission | Refetch pending interrupt after ambiguous failure before any retry. | Stable batch reference and idempotency key. | Escalate manual recovery when source cannot prove state. |
| Branch | Create a new task/thread/run lineage from a selected source checkpoint. | Parent/child relationship and checkpoint reference. | Disable or copy into a new task when unsupported. |

`rollback` multitask strategy is not the default Cancel operation. It is an advanced, source-specific run-start strategy with separate destructive semantics.

## Approval and stale-state resolutions

- A pending interrupt is rendered as an ordered batch of action requests and review configs.
- The app accepts one valid decision per request, in order, and records the exact batch version observed by the reviewer.
- The app refetches before submitting when freshness cannot be proven.
- No “Mark resolved” or force-resolve control appears in v1. A refetch/reconciliation silently removes a stale app projection only when no source interrupt is pending; otherwise the user sees the current decision or separately verified cancellation path.
- If a source interrupt is still pending, the user must submit allowed decisions or cancel the run.
- Bulk approval is excluded from v1. A later policy-driven batch feature requires risk classification, explicit preview, partial-failure behavior, and audit.
- Phone one-tap approval is limited to simple approve/reject requests whose full material arguments and consequences fit the review contract; edit/respond opens a complete review sheet.

## Configuration save and deploy resolution

The product has four explicit states:

1. **Source revision**: currently deployed/read source-authoritative configuration.
2. **Draft**: app/project-owned versioned edit not affecting live behavior.
3. **Validated draft**: passed schema, contract, security, and source-capability checks.
4. **Deployment job/revision**: asynchronous publish attempt and immutable source result.

“Save” only creates/updates a draft. “Deploy” requires an explicit confirmation that identifies source, workspace, assistant/deployment, changes, secret references, and expected effect. Classic deployment uses its supported control-plane/project path. MDA beta uses the official `mda` workflow rather than guessed CRUD. Fleet remains read/invoke unless a verified contract proves a mutation. Failure leaves the previous deployed revision intact and the draft available for correction.

## Organizational-memory review resolution

Layer 0–1 organizational intelligence may ship only as a reviewable loop:

1. an agent produces a proposal with source evidence and a diff against a pinned Context Hub/project version;
2. Deep Work stores proposal metadata and review status, not a secret shadow knowledge base;
3. a human approves, edits, or rejects the proposal through the approvals experience;
4. publish uses optimistic concurrency against the versioned target;
5. conflict returns to review rather than overwriting;
6. the app records reviewer, decision, target commit/version, and publish result;
7. runtime agents mount/read only the accepted version according to source policy.

Automated weekly digests may create proposals. They must not automatically modify organization memory, policies, or instructions. Cross-workspace synthesis is deferred until authorization, export/query rate limits, and organization-scoped access are proven.

## Phone landing and merge resolution

The vision's phone success criterion is retained only with exact boundaries:

- Push/deep link opens an authenticated task or approval target without embedding credentials.
- The phone view shows task/run status, plan, approval request, changed files, summary diff, CI/branch state, and provenance with accessible fallback.
- Draft PR creation happens through the server-side GitHub App integration.
- Merge requires explicit confirmation, current branch protection/CI state, repository permission, and a fresh GitHub result.
- If any condition cannot be verified, the primary action is “Open in GitHub,” not a simulated Merge button.
- Partial mobile review does not claim parity with desktop until the same executable acceptance scenario passes at phone width and on a real device/browser.

## Canonical information architecture

| Context | Primary destinations | Secondary/contextual experiences |
|---|---|---|
| Desktop web/Tauri | Tasks, Approvals, Agents, Schedules, Activity | Settings via workspace menu; task run panel; command palette; trace deep-links |
| Phone PWA | Tasks, Approvals, Agents, More | More: Schedules, Activity, Settings, connection/account; run panel as sheets |
| Task detail | Conversation/stream plus outcome controls | Todos, Status, Agents, Context, Files, Git/Diff, Browser, Artifacts, Verification, trace link by capability |
| Agent detail | Overview and supported configuration | Environment, schedules, deployment revision/status; no global 22-section settings clone |

Schedules remains a primary desktop destination because it is a named v1 outcome, but it must render a clear no-capable-source state. If user research shows low use after v1, it may fold into Agents/Activity without changing the domain plan.

## v1 scope after resolution

### Required

- FastAPI/Postgres application foundation, domain identity/status model, security and audit;
- real session/workspace/source onboarding with API-key/key-proxy baseline and explicit demo mode;
- classic LangSmith Deployment and local Agent Server adapters; MDA/Fleet only as optional adapters;
- 15-minute first task journey against the supported baseline, not a beta-only account;
- task inbox/search/filter, composer, streaming detail, steering, reconnect, cancellation, retry, artifacts;
- ordered HITL approvals, stale handling, goals/rubrics and verdict history where middleware is verified;
- coding sandbox/repository/branch/files/diff/draft-PR journey where the source advertises capabilities;
- agent source index/detail and versioned draft/save/deploy semantics for supported sources;
- per-source schedules/activity and slim observability/trace links;
- responsive web/PWA, Tauri host on the same API, offline/error/permission/recovery behavior;
- accessibility, security, performance, untrusted-content, documentation, migration, backup, and release acceptance.

### Feature-flagged v1

- MDA private-beta adapter;
- Fleet read/invoke;
- protocol-v2 streaming if exact source version supports it, with legacy fallback;
- browser tab, platform sandbox lifecycle, checkpoint branching, GitHub merge, multimodality, goals/rubrics, and advanced agent editing where capabilities and tests exist;
- OAuth if scope/audience spike succeeds.

### Later

Goal lifecycle and async workstreams; memory synthesis; pure-OSS backend; native Expo; Slack/Linear/Teams channels; chat-to-configure; GitLab/multirepo/worktrees/editor protocols; RBAC/evals; structured organizational knowledge; temporal organizational graph.

## Revised success criteria

1. A fresh user can start from API-key/key-proxy or a proven OAuth flow, select a workspace, connect or deploy a supported classic source, and complete a first non-destructive task in under 15 minutes.
2. The same task can disconnect and reconnect without duplicate events or a lost approval, with clear recovery if continuity cannot be proven.
3. A two-action HITL batch can be reviewed and submitted in exact order from desktop and phone, with an idempotent audit record and stale protection.
4. A coding-capable source can produce a reviewed draft PR with repository/branch/sandbox/artifact provenance; phone merge is counted only if real GitHub permission, CI, protection, and result are verified.
5. Every run has a working source trace link or an explicit “trace unavailable” capability state.
6. MDA/Fleet absence does not prevent onboarding, task completion, approval, or release acceptance.
7. No broad platform/GitHub credential reaches the browser, Tauri bundle, runtime state, sandbox, or logs.
8. Every selected v1 journey passes loading, empty, error, permission, offline/reconnect, stale, and recovery scenarios at phone, tablet, and desktop widths where applicable.
9. Backup/restore, database migration, webhook replay/dedupe, deployment rollback, and source partial-failure drills pass before production release.
10. Canonical docs and shipped UI make no unsupported external contract claim.

## Decisions required before integration

| Decision | Recommendation | Blocking scope |
|---|---|---|
| Application backend | Python 3.12 FastAPI in `apps/api` | All v1 product work |
| Durable app state | Postgres with explicit ownership/retention/security matrix | Sessions, aggregation, approvals, push, drafts, audit, recovery |
| Remote runtime baseline | Classic LangSmith Deployment | First-task and release acceptance |
| Beta adapter | MDA capability-detected and non-blocking | MDA-specific journeys only |
| Auth baseline | Server-side API-key/key-proxy; OAuth conditional | Onboarding/security |
| Primary nav | Five desktop destinations; four mobile destinations | UI spec and migration |
| Team boundary | Solo acceptance, team-safe identities; no shared inbox/RBAC UI | Domain model/security |
| Mobile merge | Real GitHub verification or downgrade criterion | Coding/mobile acceptance |
| Config semantics | Versioned Save Draft, explicit async Deploy | Agent/configuration plans |
| Org memory | Human-reviewed proposals with app audit + versioned target | Operations/intelligence |

## Canonical documents affected after approval

No canonical file is modified in this stage. After review, the resolutions map to:

- `docs/plan/01-vision.md`: product promise, v1 actor boundary, success criteria, scope;
- `docs/plan/02-architecture.md`: FastAPI/Postgres service, plane separation, auth/source model;
- `docs/plan/03-ui-spec.md`: five/four-destination IA, lifecycle semantics, responsive states;
- `docs/plan/04-roadmap.md`: classic baseline, Gate 0 contracts, sequencing and release criteria;
- `docs/plan/07-org-intelligence.md`: proposal/audit/publish ownership and durable review state;
- `docs/plan/08-deepagents-feature-map.md`: source capability gates and MDA/private-beta boundaries.

## Evidence index

Primary internal evidence at `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`:

- `docs/plan/01-vision.md`;
- `docs/plan/02-architecture.md`;
- `docs/plan/03-ui-spec.md`;
- `docs/plan/04-roadmap.md`;
- `docs/plan/07-org-intelligence.md`;
- `docs/plan/08-deepagents-feature-map.md`.

Frontend and external-contract corrections are detailed in the adjacent staged audits and inherit their pinned commits.
