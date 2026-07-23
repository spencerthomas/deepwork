# Existing Plan Audit

Status: staged evaluation; no existing plan is modified
Canonical plan pin: `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`
Delivery-plan evidence: untracked `docs/plans/2026-07-22-001-feat-deepwork-v1-delivery-plan.md`, 957 lines
Evidence SHA-256 at audit time: `5e6a30202417d6261e2bd4e973e7b71d92171e9a8cbf8031753a93c1632bf813`
Audit date: 2026-07-22

## Verdict

The 957-line delivery plan is valuable evidence of intent and sequencing, but it is not implementation-ready. It mixes program requirements, architecture decisions, guessed hosted contracts, exact file operations, and acceptance criteria inside 19 delivery units. Several units duplicate ownership, depend on a backend that is not designed, or encode external APIs contradicted or not established by the pinned LangChain documentation.

The plan must remain unchanged until review. After approval, its best role is a **program-level index**: milestones, unit status, dependencies, release gates, and links to stable capability plans. Exact interfaces, state matrices, security/persistence rules, responsive behavior, and executable acceptance scenarios belong in the owning feature plans.

The most important missing unit is a real application backend. The plan's thin Next.js server-route model and “no database” premise cannot own authenticated sessions, cross-source aggregation, app identities, approval idempotency, notification subscriptions, webhooks, configuration drafts/deploy jobs, artifacts, recovery, or audit. A Python 3.12 FastAPI service and Postgres are release-blocking prerequisites, not optional infrastructure polish.

## Evaluation method

Each delivery unit was checked for:

- stable feature-family ownership;
- user outcome and journey coverage;
- loading/empty/error/offline/permission/reconnect/stale/destructive states;
- external contract validity at `langchain-docs-reference@7b9215d`;
- persistence, security, responsive/accessibility, metrics, rollout, and recovery;
- executable acceptance evidence;
- stale frontend references against `deep-work-frontend@8866d39`.

Readiness labels:

- **Reframe**: keep the outcome but replace architecture/contract assumptions.
- **Expand**: direction is useful but material plans/states are missing.
- **Gate**: capability is optional or externally unverified and cannot block v1.
- **Split**: unit owns multiple independently releasable features.
- **Index-only**: retain as program coordination, with detail delegated to feature plans.

No unit is marked ready while it contains unresolved implementation decisions, unverified external contracts, or lacks an owning feature plan's complete state/acceptance matrix.

## Mapping of all 19 delivery units

| Unit | Intended outcome | Owning feature families | Evaluation | Required correction/expansion |
|---|---|---|---|---|
| U1 Monorepo scaffold | Workspace/toolchain/CI foundation | `DW-FND`, `DW-QUAL` | Expand; index-only after extraction | Include independently locked API/agent Python packages with root Make fan-out, Ruff plus `ty`/strict mypy by package, pnpm/Turbo/Node 24/Oxfmt/Oxlint, `packages/domain`, private fixtures/standard tests, Postgres/object-store test path, dependency direction, clean-install matrix, release artifacts, and LangChain-shaped contribution workflow. Do not treat a successful web build as system readiness. |
| U2 Import frontend as `apps/web` + hygiene | One-way migration from prototype | `DW-FND`, `DW-SURF`, `DW-QUAL` | Reframe and split | Pin import to `8866d39`, preserve sandbox repo, generate a surface manifest, migrate tokens/primitives before behavior, and prohibit fixture/API-schema leakage. Current “10 pages” and 53-file-era references are stale; mobile and state matrices are absent. |
| U3 OAuth probe | Decide authentication launch path | `DW-ONB`, `DW-FND` | Gate | Test exact scopes/audiences across platform, control plane, classic data plane, Fleet, desktop device flow. API-key/key-proxy remains supported baseline. Add session, revocation, rotation, CSRF/PKCE, actor/workspace mapping, and secret ownership acceptance. |
| U4 MDA loop | Prove MDA deployment/invocation | `DW-ONB`, `DW-AGENT` | Gate and reframe | MDA is private beta and non-blocking. Use official `mda` workflow; remove handcrafted tarball/API reimplementation. Prove entitlement/region/capabilities and define unavailable fallback to classic deployment. |
| U5 Stream contract | Establish live streaming | `DW-FND`, `DW-TASK`, `DW-HITL` | Split and reframe | Compose the pinned public LangGraph Python SDK server-side; separate protocol-v2 `since` cursor from legacy/run-join behavior; expose one normalized FastAPI application stream and record dedupe, gaps, reconnect, malformed events, cancellation and HITL replay in golden transcripts. |
| U6 `packages/agent` v0 | Deployable Deep Agents project | `DW-AGENT`, `DW-TASK` | Expand | Define Python 3.12 package, graph inputs/state/outputs, runtime-agnostic boundaries, templates, middleware version gates, local/classic deploy path, setup/fixture/eval tests, non-coding artifacts, and security. Keep backend/store/checkpointer outside agent code where runtime-owned. |
| U7 `packages/sdk` AgentSource + DataProvider | Normalize source access for UI | `DW-FND`, `DW-ONB`, `DW-TASK` | Reframe and split | Add pure `packages/domain`; narrow SDK to the Deep Work API/application stream and separate it from React hooks. FastAPI owns provider clients, capability probes, `authRef`, source cursors, fan-out and pagination merge. Client views retain composite identity, capability/credential state, partial failures and provenance without provider secrets/cursors. |
| U8 Server routes + sign-in | Authentication and proxy glue | `DW-FND`, `DW-ONB`, `DW-SURF` | Replace architecture | Replace thin Next-only routes with `apps/api` FastAPI + Postgres; Next.js is a client/BFF only if justified. Own sessions, CSRF, workspace/source registry, credential references, authorization, audit, migrations, health, rate limits, and failure recovery. |
| U9 Live inbox + composer | Discover and dispatch tasks | `DW-TASK`, `DW-ONB` | Expand | Per-source aggregation/index, search/filter/pagination, source freshness/partial error, drafts/templates/attachments, no-source/demo state, idempotent dispatch, validation, permission, cancellation-before-start, and 15-minute onboarding link. |
| U10 Live task detail | Observe and steer a run | `DW-TASK`, `DW-SURF` | Reframe and split | Replace invented `stream.send()`/`stream.interrupt()` with verified normalized services. Add status reducer, ordered events, tool/reasoning safety, todos, reconnect/dedupe, cancel/retry/rename/archive, artifacts, mobile panel/sheets, capability fallbacks, and failed/ambiguous mutations; explicitly defer task delete pending retention/source-deletion policy. |
| U11 Approvals HITL | Review runtime interrupts | `DW-HITL`, `DW-TASK` | Reframe | Preserve `action_requests[]`, `review_configs[]`, and ordered decisions. Remove “ignore” as runtime decision. Add allowed edit/respond schemas, idempotency/audit, stale refetch, partial/batch behavior, permissions, mobile one-tap limits, and explicit cancellation. |
| U12 Verification | Rubrics, verdicts, resilience middleware | `DW-HITL`, `DW-AGENT`, `DW-QUAL` | Gate and expand | Do not implement a parallel rubric middleware by default: `SRC-DA` exports beta `RubricMiddleware`. Pin/reuse/conformance-test its public behavior, then add only product persistence/presentation. Separate user goal/rubric, plan approval, verdict history, retries/fallbacks, cost/iteration limits, failure presentation, metrics and release acceptance. Fix stale `new-task-composer.tsx` reference. |
| U13 Coding surfaces | Sandbox, GitHub, files/diff/PR | `DW-CODE`, `DW-TASK`, `DW-HITL` | Split and reframe | Add sandbox lifecycle/snapshot/setup/egress/expiry, repository/branch cleanup, GitHub App install/token proxy, untrusted files/diffs, comments, PR/CI/merge, artifacts, mobile landing and recovery. Remove unsupported arbitrary MDA connector routes. |
| U14 Subagents + branching | Parallel visibility and checkpoint forks | `DW-TASK`, `DW-AGENT` | Gate and expand | Define stable parent/child identities, lazy subscriptions, cancellation, aggregation, checkpoint capability and invalidation, fork provenance, cost/status behavior, mobile summary and fallback. Async workstreams remain v1.x; do not equate them with synchronous subagents. |
| U15 Fleet manager | Agent index/builder/config/deploy | `DW-AGENT`, `DW-ONB` | Reframe and split | Rename to Agents and Configuration. Fleet is read/invoke; `/v1/deepagents/*` CRUD is unsupported/unknown. Classic create/deploy is supported path; MDA is beta adapter. Add versioned Draft/Validate/Deploy, source permissions/capabilities, import/export, health, rollback and exact settings dispositions. Fix stale `components/settings/connectors-section.tsx` path. |
| U16 Schedules + Activity | Operate recurring work and audit activity | `DW-OPS`, `DW-TASK` | Split and reframe | Agent Server crons are per deployment; MDA schedules are project/deploy-owned. Aggregate per source with partial failure/timezone semantics. Activity needs app/source event ownership, retention, pagination, untrusted payload handling, trace links, retry/cancel relations, and notification ownership. |
| U17 Org intelligence Layers 0–1 | Configure memory and learn from work | `DW-OPS`, `DW-AGENT`, `DW-HITL` | Gate and reframe | Remove `/v1/deepagents/:id/memory`. Use verified Context Hub SDK/project path and optimistic versions. Add proposal/evidence/diff, approve/edit/reject, conflict, audit/publish, permissions/retention, cross-workspace boundary, rate limits, and failure recovery. No automatic org-memory write. |
| U18 PWA + Tauri | Mobile/offline/push and desktop shell | `DW-SURF`, `DW-ONB` | Split and expand | Push requires Postgres subscription/preferences/delivery state, verified webhook ingestion/dedupe and secret rotation. Define offline cache/conflict, background/reconnect, deep-link auth, desktop hosted/local topology, same FastAPI API, secure storage, tray, updater/signing, and native notification parity. |
| U19 Polish, accessibility, performance, docs | Release quality | `DW-QUAL`, `DW-SURF` | Expand and move left | Quality is continuous, not last-unit polish. Add accessibility/keyboard/reduced motion, long-stream virtualization, performance budgets, untrusted content, threat/security testing, migrations/backup/restore, release rollback, browser/device matrix, documentation and executable release acceptance. |

## Requirements and success criteria coverage

The delivery plan's requirements R1–R13 and six success criteria are not independently traceable to executable scenarios. They are embedded across units and often depend on beta or unsupported contracts. Before integration, the coverage matrix must give each requirement exactly one owning feature plan and list dependencies separately.

The current release claims need these corrections:

- First task under 15 minutes must pass on the classic supported baseline; MDA may be an additional result, not the only result.
- “Sign in” accepts API-key/key-proxy as baseline; OAuth is conditional on the live spike.
- Inbox/task search is app aggregation of per-source Agent Server queries, not one control-plane search.
- Full phone merge is accepted only after real GitHub permission, branch protection, CI, confirmation, and result tests; otherwise the accepted phone outcome stops at review/approve/open-in-GitHub.
- Agent config export must define a versioned, round-trippable format and unsupported source fields; “Fleet-compatible” is not self-verifying.
- A trace link criterion must include unavailable/permission/expired-source behavior and must not recreate trace content as app authority.
- Release quality must include backend/database migration, backup/restore, webhook replay, source partial failure, secret rotation, and desktop signing/updater—not only TypeScript CI and web docs.

## Stale frontend references

| Delivery-plan reference | Finding at frontend pin `8866d39` | Correction |
|---|---|---|
| `docs/plan/06-frontend-implementation.md` as authoritative migration checklist | It is pinned to older frontend `c46b994` and older counts | Repin/supersede after review using the staged frontend audit |
| Prototype described as 53 files | Pinned frontend has 77 tracked files; `lib/data.ts` is 1,784 lines and run panel is 683 lines | Generate a pinned file/surface manifest during migration |
| “all 10 pages” | Route inventory has 13 patterns plus dynamic/redirect behavior | Use route IDs and explicit redirects/dynamics; do not rely on page count shorthand |
| `apps/web/components/new-task-composer.tsx` in U12 | Actual prototype component is `components/new-task.tsx` | Reference migrated target selected by the owning composer plan |
| `apps/web/components/settings/connectors-section.tsx` in U15 | Actual prototype file is `components/config/connectors-section.tsx` | Do not copy path until settings ownership restructure is accepted |
| “remove the 7th Config tab” | Prototype primary nav has seven entries but Config is a redirect, not a nav label; entries include Observability and Settings | Apply approved five-tab IA; remove legacy `/config` redirect separately |
| Move all fixtures to `packages/ui` | Domain fixtures are not UI package responsibility | Put pure semantics in `packages/domain` and synthetic records/transcripts in private `internal/fixtures`; UI owns presentation stories only |

## Unsupported or invalid contract references

| Plan location/assumption | Contract finding | Required plan change |
|---|---|---|
| R10, U15: `/v1/deepagents/*` CRUD | MDA API is private-beta/finalizing; public CRUD not established | Remove from v1 baseline; capability gate exact accepted beta contract |
| U4: handcrafted `/v2/deployments` tarball flow to replace `mda deploy` | MDA official workflow owns compilation, Context Hub sync, source archive, deploy and schedules | Use `mda` workflow for MDA; separately plan supported classic deployment control plane |
| U7/U9/U11/U16: `threads.search` on “control plane” or global | Thread search belongs to one Agent Server/deployment | Query per source; app service indexes/aggregates with partial-failure semantics |
| U10: `stream.send()` and `stream.interrupt()` | Pinned frontend uses `submit`; protocol v2 wire uses `run.start`/`input.respond`; cancellation is separate | Verify installed client, expose normalized input/cancel services, remove invented methods |
| U5/U10/U18: one `Last-Event-ID` resume model | Protocol v2 resumes with body `since`; legacy/join paths differ; pinned LangGraph Python SDK already implements protocol mechanics | Compose the public SDK in FastAPI, retain upstream cursors server-side, expose an opaque application cursor, and test each adapter/application recovery path |
| U11: simplified approval decisions | Runtime requires ordered action request/config arrays and allowed decisions | Exact normalized HITL model plus golden two-action tests |
| U13: `/connectors/deepwork/sandbox/:threadId/*` as MDA-sanctioned route | No pinned public MDA contract establishes arbitrary route | Use verified sandbox/platform/project mechanisms or gate discovery |
| U15: Fleet management mutations | Pinned Fleet prose supports authorized read/invoke; non-owner is read-only | Re-scope Fleet adapter; every mutation disabled unless proven |
| U17: `/v1/deepagents/:id/memory` | Unsupported guessed route | Use official Context Hub SDK/project workflow with versions/conflicts |
| U18: push fan-out from one stateless route | Durable subscription, dedupe, preference and delivery state is missing | FastAPI/Postgres notification service and webhook processing plan |
| U3/U8: universal OAuth/bearer acceptance | Cross-plane scope/audience is unproven; auth headers differ | API-key/key-proxy baseline and per-plane credential matrix |

## Duplicate ownership

| Concern | Duplicated across | Consequence | Single owning plan direction |
|---|---|---|---|
| Authentication/session/workspace | U3, U7, U8 | Inconsistent token and actor models | `DW-ONB` auth/session plan; `DW-FND` service/security as dependency |
| Source registry/capabilities | U4, U7, U8, U15 | MDA/classic/Fleet semantics leak into UI | `DW-AGENT` runtime-source product plan backed by `DW-FND-003` server probing and `DW-FND-005` client-safe capability vocabulary |
| Streaming/reconnect | U5, U7, U10, U14, U18 | Cursor and subscription rules diverge | `DW-FND-003` owns upstream SDK/cursors; `DW-FND-004` owns the application stream/client; task/mobile plans consume them |
| HITL/approvals | U5, U10, U11, U12 | Flattened schemas and competing resume behavior | `DW-HITL` ordered interrupt plan |
| Sandbox/files/Git | U6, U10, U13 | Runtime and presentation lifecycle conflated | `DW-CODE` sandbox and GitHub plans; task detail consumes capabilities |
| Agent config/skills/memory/Context Hub | U6, U15, U17 | Draft/live/runtime/org memory blurred | `DW-AGENT` versioned config; `DW-OPS` org proposal review |
| Schedules | U6, U15, U16, U17 | Project declarations and crons treated as one mutable list | `DW-OPS` schedules plan with source adapters |
| Notifications | U16, U18 | No durable backend owner | `DW-OPS` notification service; `DW-SURF` delivery clients |
| Responsive/accessibility | U2, U10, U11, U13, U18, U19 | Deferred mobile/a11y rework | `DW-SURF` cross-surface behavior plus `DW-QUAL` release gates; each feature owns its states |
| Persistence/status/audit | Implied in U7–U18, owned nowhere | No recovery or accountable mutation | `DW-FND` application state/domain identity/status/audit plans |

The owning plan defines the contract and acceptance scenarios. Consumer plans list it as a dependency and add only journey-specific presentation/behavior. A coverage matrix may list many consumers, but exactly one owner.

## Missing plan inventory

### Release-blocking foundations

| Missing plan | Minimum contents | Suggested family |
|---|---|---|
| Application service and API | Python 3.12 FastAPI topology, request/auth context, query/mutation boundaries, jobs, health, rate limits, API versioning, error model, observability, deployment/rollback | `DW-FND` |
| Postgres state and operations | Schema ownership, migrations, RLS/authorization strategy if used, transactions/idempotency, backup/restore, retention/export/delete, connection pooling, HA/recovery | `DW-FND` |
| Domain identity and status reducer | Composite source/workspace/thread/run/checkpoint identities, canonical statuses/transitions, retry/branch/archive lineage, freshness and audit events | `DW-FND` |
| Source capability/auth manifest | Endpoints, assistant identity, auth reference, workspace context, protocol/capabilities/version/health, credential matrix and refresh | `DW-FND`/`DW-AGENT` |
| Fixture/live contract parity | Sanitized golden data, malformed/partial/error fixtures, adapter conformance tests, demo labeling, deterministic scenario runner | `DW-FND`/`DW-QUAL` |
| Security and untrusted content | Threat model, credential boundaries, content sandboxing, SSRF/path traversal/HTML/Markdown/file/diff safety, audit, dependency/secret scanning | `DW-FND`/`DW-QUAL` |

### Onboarding and connection

- session creation/expiry/logout/revocation and actor/workspace selection;
- API-key/key-proxy baseline and conditional OAuth;
- classic deployment connect/create/health/test flow;
- MDA entitlement/capability detection and unavailable fallback;
- Fleet read/invoke connection and owner/non-owner states;
- GitHub App installation, repository authorization and revocation;
- explicit demo entry and conversion to live source;
- a measured 15-minute first-task journey with clean-account prerequisites, timeouts, errors and recovery.

### Task/runtime experience

- per-source index/search/filter/pagination and partial failures;
- composer drafts, templates, attachment upload/scan/limits/provenance/retention;
- event/status reducer, reconnect/dedupe/gaps/offline and cross-device handoff;
- cancellation, retry, rename, archive, delete, checkpoint, branch and stale task behavior;
- subagent identities, queues, steering and multitask fallbacks;
- artifact publication, MIME/size safety, storage/reference authority, preview/download, expiration;
- coding/research/writing journey-specific inputs, capabilities, verification and outcomes.

### Coding runtime

- sandbox provision/reuse/idle/expire/terminate and task-thread-run mapping;
- environment snapshots, setup/cleanup scripts, variables/secrets, egress, quotas;
- GitHub installation token proxy, repository clone, branch naming/collision/cleanup;
- safe files/terminal/browser/diff/comment interfaces;
- draft PR, CI/protection status, merge confirmation, failure/rollback and phone landing;
- artifact extraction before sandbox termination.

### Operations and surfaces

- webhook verification, replay, dedupe, ordering and dead-letter recovery;
- notification subscription/preferences/delivery/retry/revocation and push privacy;
- offline cache boundaries, queued drafts, conflict and source freshness;
- Tauri hosted-versus-local API topology, session transfer, deep links, tray, secure storage, signing/updater/rollback;
- operational logs/metrics/traces, source health, deployment jobs, user-visible incidents;
- release runbook, migrations, backup/restore drill, feature flags and rollback.

## Backend gap: required staged correction

The revised delivery architecture must introduce this dependency boundary before feature implementation:

```text
apps/web (Next.js/PWA) -> packages/sdk -> packages/domain
           |                    |
           +-> packages/ui ----+
           |
           +-> apps/api (Python 3.12 FastAPI application API/stream)
                    |-> Postgres + outbox/jobs -> separately deployed worker
                    |-> S3-compatible application object storage
                    |-> Agent Server and LangSmith through pinned public Python SDKs
                    +-> GitHub/sandbox/MDA-gated supported adapters

apps/desktop (Tauri) -> exact trusted hosted apps/web origin + narrow native bridge
packages/agent (Python Deep Agents) -> separately deployable runtime artifact
```

`apps/api` owns application identity, authorization, source aggregation, upstream
streams/cursors, durable mutations, objects, and jobs. `packages/domain` owns
client-safe semantics; `packages/sdk` is only the Deep Work application client.
`packages/agent` owns agent behavior. Agent Server owns execution state.
LangSmith control plane owns deployment lifecycle; platform APIs own their
respective resources. This separation must appear in repository layout, package
dependency direction, threat model, CI, local development, deployment and
acceptance tests.

## Proposed sequencing

### Gate 0 — accepted decisions and live contracts

- approve FastAPI/Postgres/backend ownership;
- pin Python/Node/client/server packages;
- verify classic Agent Server, protocol v2/legacy fallback, HITL, auth headers, control plane, Context Hub, crons, sandbox and GitHub contracts;
- document MDA/Fleet as optional capability results;
- accept glossary, domain identities, status transitions, credential/state ownership matrices.

### Foundation — supported baseline

- U1 scaffold expanded for Python/API/database/TS packages;
- application service, migrations and auth/session/source registry;
- shared SDK/query/mutation/fixture contracts and UI design system;
- classic deployment/local adapters and source capability health;
- one-way frontend shell migration with explicit demo mode.

### Task loop

- onboarding/15-minute first task;
- task index/composer/attachments;
- streaming detail/reconnect/status/cancel/retry/artifacts;
- research/writing baseline before coding-only capabilities become release-critical.

### Approval and coding loop

- ordered HITL and verification;
- sandbox/environment/GitHub/files/diff/draft PR;
- mobile approval and coding review with real recovery paths.

### Agent configuration and operations

- source-aware agent index/detail;
- versioned drafts/validation/deploy;
- schedules/activity/trace links/notifications;
- organizational intelligence Layers 0–1 only after review/publish ownership exists.

### Surfaces and release

- PWA/offline/push; Tauri same-API host;
- accessibility/performance/security/documentation;
- migrations/backup/restore/source-outage/webhook-replay/desktop-update drills;
- classic-baseline release acceptance, with MDA beta reported separately.

MDA beta work may run in parallel after Gate 0 but cannot sit on the critical path.

## How the delivery plan becomes a program index

After this proposal is approved, preserve the delivery plan's history and replace its implementation-detail role with an index shaped like:

| Field | Program-index content |
|---|---|
| Milestone/unit | Stable U number and outcome, not a file-edit recipe |
| Owning plan | One stable feature-plan ID/link |
| Dependencies | Feature-plan IDs and accepted decisions/contracts |
| Status | Proposed / discovery / blocked / ready / in progress / verified / released, with evidence link |
| Release gate | Executable scenario IDs and required environments |
| Capability scope | Baseline, flagged, later; source/version requirements |
| Risks/decisions | Decision-register IDs, owner, due/revalidation date |
| Evidence | PR/commit, contract transcript, test run, migration/rollback result, user-validation artifact |

The index must not duplicate interface schemas, state matrices, security rules, responsive specifications, or test steps from the owning plan. A unit that needs multiple independently shippable owners should be split or made an umbrella milestone.

## Acceptance mapping required before canonical merge

Every v1 release criterion must reference executable end-to-end scenarios. At minimum:

| Scenario ID | Outcome | Required variants |
|---|---|---|
| E2E-ONB-01 | Fresh actor connects a classic source and completes first task within 15 minutes | API-key baseline; OAuth only if accepted; source unavailable; invalid/revoked key; demo path |
| E2E-TASK-01 | Dispatch, stream, steer, complete and reopen task | protocol v2; fallback stream; disconnect/reconnect; duplicate/malformed event; cancel and retry |
| E2E-HITL-01 | Review two-action ordered interrupt | mixed decisions; edit/respond validation; stale batch; ambiguous response; phone and desktop |
| E2E-CODE-01 | Coding task reaches reviewed draft PR | sandbox expiry/setup failure; GitHub auth revoke; unsafe file; diff/comment; CI fail; cleanup/artifact persistence |
| E2E-MOB-01 | Push/deep link opens authenticated task/approval | logged out, wrong workspace, expired item, offline, reconnect, one-tap limits |
| E2E-AGENT-01 | Read agent, save draft, validate, deploy supported revision | classic baseline; validation fail; deploy fail/rollback; Fleet read-only; MDA unavailable |
| E2E-OPS-01 | Aggregate tasks/schedules/activity across two sources | one source down/slow/unauthorized; cursor pagination; timezone; trace unavailable |
| E2E-MEM-01 | Agent proposes org-memory diff and human publishes | edit/reject, optimistic conflict, permission failure, audit/commit reference |
| E2E-REL-01 | Release and recover application | DB migrate/rollback, backup/restore, webhook replay/dedupe, secret rotation, source outage, desktop updater rollback |

Fixture and live implementations must run the same user-level scenarios; fixtures add determinism but cannot substitute for contract acceptance.

## Preservation and integration rule

During this proposal phase:

- do not edit, move, reformat, or mark tracked the 957-line delivery plan;
- do not modify `docs/plan/01-vision.md` through `08-deepagents-feature-map.md`;
- do not alter the frontend repository;
- treat the delivery-plan SHA above as the preservation check;
- stage all replacements, additions, and mappings inside this proposal directory.

After review, the integration merge map—not this audit—controls exact canonical edits and eventual `AGENTS.md` placement.
