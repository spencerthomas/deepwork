# Feature catalog

This catalog assigns one stable feature ID and one owning plan to every coherent capability. The [coverage matrix](coverage-matrix.md) maps routes, tabs, controls, settings, requirements, criteria, and backlog items onto these owners. The [acceptance-scenario index](acceptance-scenario-index.md) freezes 179 feature scenarios and composes them into twelve release end-to-end stories plus one capability-gated Fleet story.

## Readiness labels

| Label | Meaning |
|---|---|
| Proposed for review | The proposal contains the required product and experience detail, but decisions still require review and it is not implementation-ready. |
| Contract-gated | The plan has a deterministic fallback, but one or more named live-contract spikes must close before the affected path can be enabled. |
| Discovery-gated | Later-release brief; product outcome is defined, while implementation waits for its explicit discovery gates. |

## Runtime-scope metadata

Plan front matter uses `runtime_scopes`, with the closed planning enum `any`,
`classic`, `mda`, `fleet`, `local`, `fixture`, and prospective `oss`. This field
describes where a product outcome may apply; it does not claim availability or
encode a capability state. Readiness belongs in `contract_gates`, the decision
register, and the evidence-bearing capability envelope. `any` means every enabled
runtime scope relevant to that release, not every prototype or future runtime.
The current public `RuntimeKind` is `classic | mda | fleet | local | fixture`;
`oss` cannot enter that product contract until the v2 runtime decision is accepted.

## V1 capabilities

### Foundations

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-FND-001 | Canonical monorepo, LangChain-aligned contribution method, Harness document/ExecPlan system, mechanical architecture, isolated product demo, quality/debt maintenance, CI/releases, and governed Symphony pilot/manual fallback | [Repository, OSS, and delivery foundation](../plans/v1/dw-fnd-001-repository-oss-and-delivery-foundation.md) | Proposed for review; harness/Symphony cells are spike-gated |
| DW-FND-002 | Shared tokens/components, responsive shell, canonical navigation, command palette, browser-local UI harness, and visibly isolated API-backed product demo | [Design system, shell, and demo mode](../plans/v1/dw-fnd-002-design-system-shell-and-demo-mode.md) | Proposed for review |
| DW-FND-003 | Python/FastAPI API and worker, PostgreSQL/outbox/jobs, application objects, server-only provider adapters/streams, credentials, sessions, aggregation, and security | [Application service, state, and security](../plans/v1/dw-fnd-003-application-service-state-and-security.md) | Contract-gated by auth/source-adapter/stream spikes |
| DW-FND-004 | Browser-safe Deep Work API/application-stream SDK, evidence-bearing capability mapping, query/mutation separation, opaque recovery, language-neutral fixtures, and TypeScript client conformance | [SDK, stream, and fixture contracts](../plans/v1/dw-fnd-004-sdk-stream-and-fixture-contracts.md) | Base stream gated by SPIKE-STREAM-001; optional operations use separate gates |
| DW-FND-005 | Pure `packages/domain` identities, capabilities, safe errors, task/run status reducer, lifecycle transitions, and audit semantics | [Domain identity, status, and audit model](../plans/v1/dw-fnd-005-domain-identity-status-and-audit-model.md) | Contract-gated by SPIKE-STREAM-001 |

The staged [application architecture](../architecture/application-architecture.md)
and [engineering conventions](../architecture/engineering-conventions.md) are
cross-cutting review documents, not additional feature owners. Architecture
concerns remain owned by `DW-FND-001/003/004/005`, `DW-SURF-001/002`, and
`DW-FUT-202`.

### Onboarding

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-ONB-001 | API-key baseline, gated OAuth/device flow, sessions, org/workspace choice, switching, recovery, and demo entry | [Authentication, session, workspace, and demo](../plans/v1/DW-ONB-001-auth-session-workspace-demo.md) | Contract-gated by SPIKE-AUTH-001/002 |
| DW-ONB-002 | Source probe/registration, classic deployment, MDA CLI handoff, Fleet connect, and measured first task | [Source connection, deployment, and first task](../plans/v1/DW-ONB-002-source-connection-deployment-first-task.md) | Contract-gated by MDA/Fleet spikes |

### Task loop and experiences

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-TASK-001 | Cross-source task inbox, canonical status, search, grouping, filtering, pagination, partial failure, and empty states | [Inbox, search, filters, status, and pagination](../plans/v1/DW-TASK-001-inbox-search-filter-status-pagination.md) | Contract-gated by SPIKE-THREADS-001 |
| DW-TASK-002 | New-task composition, task types, attachments, agent/environment/repository choice, rubric, and plan approval | [Composer, templates, attachments, rubric, and plan](../plans/v1/DW-TASK-002-composer-templates-attachments-rubric-plan.md) | Contract-gated by compose/attachment/plan spikes |
| DW-TASK-003 | Live task detail, narration, tools, reasoning, todos, stream recovery, completed history, and operational events | [Task detail, streaming, tools, reasoning, todos, and reconnect](../plans/v1/DW-TASK-003-detail-streaming-tools-reasoning-todos-reconnect.md) | Contract-gated by SPIKE-STREAM-001 |
| DW-TASK-004 | Steering, queue/interrupt strategy, cancel/retry/rename/archive, checkpoints, branches, and race handling | [Steering, queue, lifecycle, checkpoints, and branching](../plans/v1/DW-TASK-004-steering-queue-lifecycle-checkpoints-branching.md) | Contract-gated by SPIKE-STREAM-001 |
| DW-TASK-005 | Coding, research, and writing journeys; artifact contract; subagent visibility; compacted context and evidence | [Task journeys, artifacts, and subagents](../plans/v1/DW-TASK-005-journeys-artifacts-subagents.md) | Contract-gated by artifact/subagent spikes |

### Approvals and verification

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-HITL-001 | Cross-agent approvals, aligned request/config arrays, ordered decisions, editable args, plan approval, stale races, and phone action | [Ordered approvals, plan approval, stale races, and mobile](../plans/v1/DW-HITL-001-ordered-approvals-plan-stale-mobile.md) | Contract-gated by SPIKE-STREAM-001 |
| DW-HITL-002 | Task rubrics, upstream verification middleware, verdict/evidence history, iteration caps, and reviewed exceptions | [Rubrics, goals, and verification](../plans/v1/DW-HITL-002-rubrics-goals-verification.md) | Contract-gated by middleware spike |

### Coding runtime and review

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-CODE-001 | Environment versions, sandbox lifecycle, snapshots, setup, egress, TTL, execution tools, reconstruction, and provenance | [Sandbox, environments, snapshots, setup, and egress](../plans/v1/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md) | Contract-gated by sandbox spike |
| DW-CODE-002 | GitHub installation, repo/branch binding, zero-secret token broker, commit, draft PR, CI, and explicit merge | [GitHub authentication, repository, PR, CI, and merge](../plans/v1/DW-CODE-002-github-auth-repository-pr-ci-merge.md) | Contract-gated by SPIKE-GITHUB-001 |
| DW-CODE-003 | File/artifact viewers, exact-SHA diffs, batched comments, read-only terminal, browser flag, and phone review/landing | [Files, diff, terminal, browser, and phone](../plans/v1/DW-CODE-003-files-diff-terminal-browser-phone.md) | Contract-gated by file/sandbox capability |

### Agent sources and configuration

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-AGENT-001 | Runtime registration and safe capability negotiation across classic, MDA, Fleet, and local sources | [Runtime sources and capabilities](../plans/v1/dw-agent-001-runtime-sources-and-capabilities.md) | Contract-gated by MDA/Fleet spikes |
| DW-AGENT-002 | Source-aware agent index/detail, health, ownership, capabilities, recent work, and responsive inspection | [Agent index, detail, and health](../plans/v1/dw-agent-002-agent-index-detail-and-health.md) | Contract-gated by source/Fleet spikes |
| DW-AGENT-003 | Templates, validated project ZIP, versioned drafts, semantic diff, classic deploy, MDA CLI handoff, revision and rollback | [Create, draft, import/export, and deploy](../plans/v1/dw-agent-003-create-draft-import-export-and-deploy.md) | Contract-gated by config/deploy/source spikes |
| DW-AGENT-004 | Supported models/profiles plus explicit disposition of runtime, interpreter, backend, multimodal, hook, worktree, and protocol settings | [Models, profiles, runtime, and advanced settings](../plans/v1/dw-agent-004-model-profile-runtime-and-advanced-settings.md) | Contract-gated by SPIKE-CONFIG-001 |
| DW-AGENT-005 | Tools, connector accounts, MCP, tool/filesystem permission separation, skills, plugins, scoped memory, and subagent definitions | [Tools, connectors, permissions, skills, memory, and subagents](../plans/v1/dw-agent-005-tools-connectors-permissions-skills-memory-and-subagents.md) | Contract-gated by MCP/Context/source spikes |

### Operations and organizational intelligence

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-OPS-001 | Source-owned versus mutable schedules, timezone/DST, run history, activity feed, idempotency, and untrusted payload boundaries | [Schedules, activity, and untrusted content](../plans/v1/dw-ops-001-schedules-activity-and-untrusted-content.md) | Contract-gated by SPIKE-SCHEDULE-001 and source gates |
| DW-OPS-002 | Trace provenance, slim summaries, Insights fallback, signed webhooks, push/native notifications, device preferences, and quiet hours | [Observability, traces, notifications, and Insights](../plans/v1/dw-ops-002-observability-traces-notifications-and-insights.md) | Contract-gated by trace/PWA/desktop spikes |
| DW-OPS-003 | Reviewed org context, trace conventions, weekly analyst digest, staged proposals, approval, and memory provenance | [Organizational intelligence layers 0 and 1](../plans/v1/dw-ops-003-organizational-intelligence-layers-zero-one.md) | Contract-gated by Context/trace spikes |

### Client surfaces and release quality

| ID | Capability and outcome | Owning plan | Readiness |
|---|---|---|---|
| DW-SURF-001 | Responsive Next.js web/PWA, mobile navigation, offline read-only behavior, safe caches, push, and phone task loop | [Responsive web, PWA, offline, and push](../plans/v1/dw-surf-001-responsive-web-pwa-offline-and-push.md) | Contract-gated by auth/stream/PWA spikes |
| DW-SURF-002 | Tauri remote-origin shell, secure bootstrap, deep links, tray, native notifications, signed updater, and platform fallback | [Tauri desktop hosting, deep links, and updates](../plans/v1/dw-surf-002-tauri-desktop-hosting-deep-links-and-updates.md) | Contract-gated by SPIKE-DESKTOP-001 |
| DW-QUAL-001 | Cross-feature accessibility, performance, resilience, security abuse tests, release criteria, staged rollout, and rollback | [Accessibility, performance, security, testing, and release](../plans/v1/dw-qual-001-accessibility-performance-security-testing-and-release.md) | Contract-gated by all enabled v1 plan gates |

## Later-release briefs

| ID | Release | Capability | Owning brief |
|---|---|---|---|
| DW-FUT-101 | v1.x | Reviewed goal lifecycle and durable asynchronous child workstreams | [Goal lifecycle and async workstreams](../plans/v1x/dw-fut-101-goal-lifecycle-and-async-workstreams.md) |
| DW-FUT-102 | v1.x | Trace/task-derived memory proposals, review, merge, conflict, provenance, and rollback | [Memory synthesis review loop](../plans/v1x/dw-fut-102-memory-synthesis-review-loop.md) |
| DW-FUT-103 | v1.x | Governed outcome signals, evaluation dataset staging/export, labels, consent, and LangSmith links | [Evaluation datasets and outcome learning](../plans/v1x/dw-fut-103-evaluation-datasets-and-outcome-learning.md) |
| DW-FUT-201 | v2 | Pure-OSS protocol runtime, storage, sandbox, identity, conformance, and operations | [Pure-OSS runtime](../plans/v2/dw-fut-201-pure-oss-runtime.md) |
| DW-FUT-202 | v2 | Expo/React Native task, approval, artifact, secure-storage, share, and native push experience | [Native mobile](../plans/v2/dw-fut-202-native-mobile.md) |
| DW-FUT-203 | v2 | Slack, Linear, and Teams task creation, identity, idempotency, untrusted input, and status delivery | [External task channels](../plans/v2/dw-fut-203-task-creation-channels.md) |
| DW-FUT-204 | v2 | Conversational agent configuration producing reviewed, reversible, validated project patches | [Chat-to-configure builder](../plans/v2/dw-fut-204-chat-to-configure-agent-builder.md) |
| DW-FUT-205 | v2 | GitLab, multi-repository worktrees, cross-repo review, and stable editor/agent protocols | [GitLab, multirepo, worktrees, and protocols](../plans/v2/dw-fut-205-gitlab-multirepo-worktrees-and-editor-protocols.md) |
| DW-FUT-206 | v2 | Application roles derived safely from upstream workspace/runtime authority | [Team governance and RBAC](../plans/v2/dw-fut-206-team-governance-and-rbac.md) |
| DW-FUT-207 | v2 | Reviewed organizational knowledge plus governed semantic metrics and read-only data analysis | [Organizational knowledge and structured data](../plans/v2/dw-fut-207-organizational-knowledge-and-structured-data.md) |
| DW-FUT-301 | v3 | Opt-in user-owned temporal graph with provenance, review, permissions, history, export, and deletion | [Temporal organizational graph](../plans/v3/dw-fut-301-temporal-organizational-graph.md) |

## Catalog rules

- Every coverage item has one primary owner. Cross-cutting quality requirements link to DW-QUAL-001 but do not replace product ownership.
- A plan may depend on another plan without duplicating its contract.
- A feature ID is never reused or silently renamed after integration.
- Prototype-only surfaces that are removed or folded remain visible in the coverage matrix with their disposition.
- Later-release briefs do not become implementation-ready until their discovery gates and source versions are accepted.
- Coverage generation rejects `runtime_tiers`, readiness suffixes such as
  `-gated`/`-verified`, and values outside the `runtime_scopes` enum; it never
  derives capability availability from product-spec scope.
