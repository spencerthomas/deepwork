# Harness engineering and Symphony audit

Status: proposed evidence and recommendations for review
Reviewed: 2026-07-23

## Scope

This audit evaluates the staged Deep Work planning package against official OpenAI
guidance for agent-first repository harnesses, living ExecPlans, and Symphony
orchestration. It does not install repository instructions, execute Symphony, or
change canonical plans.

Primary sources:

- [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/),
  OpenAI, published 2026-02-11, accessed 2026-07-23;
- [Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans),
  OpenAI, published 2025-10-07, accessed 2026-07-23;
- [An open-source spec for Codex orchestration: Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/),
  OpenAI, published 2026-04-27, accessed 2026-07-23;
- [Symphony specification](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/SPEC.md),
  pinned to `1f3219bb1ea5f69a1305dc594e79b0db57c113c5` and accessed 2026-07-23; and
- [official example `WORKFLOW.md`](https://github.com/openai/symphony/blob/1f3219bb1ea5f69a1305dc594e79b0db57c113c5/elixir/WORKFLOW.md),
  at the same pin.

These sources govern Deep Work's proposed engineering method only. They do not
establish LangChain product contracts or Deep Work user scope.

## Finding summary

| Area | Current staged package | Missing or unsafe | Required disposition |
|---|---|---|---|
| Root instructions | Ten short staged root/package `AGENTS.md` drafts with source precedence and boundaries | Root draft does not yet map the Harness document taxonomy, ExecPlans, architecture check, or Symphony workflow | Keep root concise; make it a map to canonical sources and stable commands |
| Repository docs | Rich audits, catalogs, architecture, conventions, and 39 stable-ID plans | Proposal taxonomy is a review package, not the intended canonical `design-docs` / `product-specs` / `exec-plans` system | Reclassify on integration; do not copy the proposal tree blindly |
| Architecture | Explicit Python hexagonal layers and TypeScript package graph | No short root `ARCHITECTURE.md`, machine-readable graph, actionable custom lint, or exception lifecycle | Add manifest, structural checks, and reviewed exceptions before migration |
| Plans | Detailed product plans and a protected delivery plan | Product specifications, program roadmap, and living execution plans can still be confused | Separate durable product spec from roadmap and per-work-item ExecPlan |
| Generated knowledge | OpenAPI and schema drift are proposed | No canonical generated-doc directory contract or hand-edit protection | Generate schema/API/package/architecture/coverage/issue maps with commands and provenance |
| Agent feedback | Fixture mode and stable commands are proposed | Per-worktree ports/data/object/telemetry isolation and proof packet are incomplete | Add collision-free full-stack demo and queryable logs/metrics/traces |
| Quality maintenance | Release plan includes quality and docs | No evidence scale, freshness-by-code-change check, or recurring gardening work item | Add `QUALITY_SCORE.md`, docs lint, debt ownership, and scheduled gardening |
| Orchestration | Detailed feature/dependency plans exist | Current feature-level prose/frontmatter contains cycles and is not a schedulable DAG; tracker/credential/recovery policy is unset | Decompose reviewed feature specs into acyclic work items; prove Symphony in a low-risk pilot |

## Harness conclusions

### Root `AGENTS.md` is navigation, not the repository handbook

The Harness approach uses a concise repository map that points agents into deeper
sources. Deep Work's root draft should stay approximately 100 lines and contain:

1. repository role and source precedence;
2. links to `ARCHITECTURE.md`, `docs/PLANS.md`, `docs/PRODUCT_SENSE.md`,
   `docs/SECURITY.md`, and `WORKFLOW.md`;
3. bootstrap, fixture, check, architecture, docs, and test commands;
4. a compact package/dependency table;
5. when an ExecPlan is mandatory;
6. external-contract, security, and destructive-action gates; and
7. required proof before handoff.

Nested instructions add only local ownership, legal dependencies, forbidden
content, exact commands, and required specialist review. They must not repeat the
whole root file.

### Canonical repository knowledge model

The proposal should integrate into this authority model:

```text
AGENTS.md                         navigation and invariants
ARCHITECTURE.md                   short canonical system/package/layer graph
WORKFLOW.md                       pinned Symphony execution policy
docs/PRODUCT_SENSE.md             product promise and judgment principles
docs/PLANS.md                     release roadmap and planning system
docs/DESIGN.md                    visual/interaction standards
docs/FRONTEND.md                  client architecture and experience rules
docs/RELIABILITY.md               failure, recovery, SLO, operations
docs/SECURITY.md                  product security model and verification
docs/QUALITY_SCORE.md             evidence-backed quality posture
docs/design-docs/**               durable rationale and accepted decisions
docs/product-specs/**             durable stable-ID feature outcomes/contracts
docs/exec-plans/active/**         living implementation plans
docs/exec-plans/completed/**      completed plans with outcomes/retrospectives
docs/exec-plans/tech-debt-tracker.md
docs/generated/**                 reproducible machine-owned views
docs/references/**                pinned external and legacy evidence
```

The 39 detailed feature plans are product specifications. The consolidated final
plan becomes the program roadmap. A Symphony issue receives a separate living
ExecPlan for the bounded implementation. Completed means implemented and closed,
not simply superseded by newer prose.

### Documentation enforcement

`make check-docs` should fail on:

- broken internal links or orphaned canonical documents;
- duplicate stable IDs or missing owner/status/source/last-verified metadata;
- feature, acceptance-scenario, work-item, or issue-map drift;
- invalid product-spec or ExecPlan state transitions;
- an active ExecPlan missing `Progress`, `Surprises & Discoveries`, `Decision
  Log`, or `Outcomes & Retrospective`;
- a generated file changed without its source/generator output;
- references to renamed routes, commands, packages, or schemas;
- a canonical claim supported only by an unaccepted proposal; and
- glossary conflicts.

Freshness should be change-aware. A canonical document records the last verified
commit and governed paths; changes to those paths flag the document for review.
Calendar review remains useful but cannot be the only freshness signal.

### Mechanical architecture

The supplied diagram's valuable invariant is fixed directional layers with
explicit cross-cutting providers—not its exact labels. Map it to Deep Work:

```text
Python:
domain -> ports -> application -> runtime/transport
adapters implement ports
bootstrap is the concrete composition root

TypeScript:
domain <- SDK <- web service/runtime/UI composition
domain <- UI <- web composition
desktop exposes only a typed native bridge to the exact hosted web origin
```

`tools/architecture/graph.yaml` (or an equivalently reviewed typed manifest)
defines zones, public entry points, server/browser classification, legal edges,
composition roots, and exception records. AST-aware Python/TypeScript checks plus
structural tests must catch at least:

- undeclared/cyclic package and domain edges;
- provider SDKs outside approved adapters or the agent package;
- SQLAlchemy in transport/contracts and FastAPI in domain/application;
- React/Next/network/generated wire code in `packages/domain`;
- SDK/network imports in `packages/ui`;
- raw provider credentials or `authRef` in browser-safe schemas;
- raw `fetch` or provider protocol work inside React components;
- concrete adapter imports outside bootstrap and adapter tests;
- private/deep imports into upstream LangChain packages;
- generated-contract drift and hand-edited generated files; and
- boundary logs/errors that omit required structure or expose secrets.

An error names the rule, importing file, allowed destination, reproduction command,
architecture anchor, and likely repair. An exception needs owner, issue, rationale,
affected edge, expiry/review trigger, and deletion test. Secret and tenant boundary
violations cannot receive an exception.

### Per-worktree legibility

An agent touching the application needs more than tests. A stable command such as
`make dev-agent` should create a worktree-qualified fixture stack with isolated:

- web/API/worker/telemetry ports;
- Postgres database or schema;
- object-store prefix;
- queue/outbox fixtures;
- browser storage/origin where practical; and
- logs, traces, metrics, screenshots, and proof directory.

It writes only non-secret endpoints and identifiers to a gitignored status file,
prints health and teardown commands, and restarts idempotently. Two simultaneous
worktrees must not see or stop each other's data or processes. OTLP is the proposed
instrumentation boundary; the local storage/UI vendor remains a scaffold decision.

## ExecPlan conclusions

An ExecPlan is required for multi-package, migration, security-sensitive,
contract-sensitive, multi-session, or Symphony-dispatched work. It is self-contained
for a contributor with only the repository checkout and contains:

- observable outcome and context;
- non-goals, paths, vocabulary, permissions, and prerequisites;
- independently verifiable milestones;
- live progress, discoveries, decisions, and outcome sections;
- exact commands and expected observations;
- interface/data/security/accessibility/observability impact;
- idempotence, rollback, and recovery; and
- proof and remaining debt.

The plan is updated during work. Chat history is never the only home of a decision,
discovery, command, or remaining step.

## Symphony conclusions

### Correct role

Symphony is an external developer scheduler/runner. It reads eligible tracker
work, creates deterministic per-issue workspaces, starts coding-agent sessions,
reconciles state, applies bounded concurrency, and retries with backoff. The issue
tracker remains the work control plane and agent tools normally write comments,
status, and pull-request links.

It is not:

- Deep Work's product backend or application worker;
- a durable general-purpose workflow engine;
- a replacement for product specs, ExecPlans, CI, or human review;
- proof that a GitHub Issues adapter exists; or
- a sandbox/security boundary by itself.

### Preview caveats

The pinned implementation/specification must be treated as an engineering preview
for trusted environments:

- scheduler state is intentionally in memory; restart reconciliation relies on
  tracker state and preserved workspaces rather than restoring live sessions and
  timers;
- `WORKFLOW.md` hooks are trusted shell code;
- workspace containment reduces collisions but is not a complete sandbox;
- tracker, child-process, network, and approval credentials require explicit host
  policy;
- successful work may stop at Human Review rather than Done;
- terminal issue cleanup means durable proof must already be attached to the issue,
  pull request, or retained sanitized artifact;
- the base lifecycle may continue one Codex thread across active-state changes, so
  an independent Agent Review requires a proven launcher/session-rotation extension
  or a separately configured review queue; prompt role text is not separation;
- invalid dynamic workflow configuration must retain the last valid policy; and
- Deep Work must pin a reviewed revision rather than silently follow `main`.

### Required pilot policy

Only a maintainer-applied `agent-ready` issue that is active, unblocked, fully
specified, and permissioned may dispatch. Its issue includes stable feature and
work-item IDs, owner/lane, plan/spec links, allowed paths, dependencies, contract
gates, risk, exact acceptance scenarios, validation, proof, rollback, and required
reviewers.

The proposed flow is:

```text
Intake -> Spec review -> Ready -> Agent ready -> In progress
       -> Agent review -> Human review -> Done
                         \-> Rework -> In progress
                         \-> Blocked

Canceled and Duplicate are terminal.
```

`SPIKE-SYMPHONY-001` must prove the selected tracker adapter, exact state/label and
blocker semantics, deterministic safe workspace, two-workspace isolation, host-only
tracker credentials, environment filtering, reconciliation after state change,
crash/restart behavior, idempotent external effects/PR creation, backoff/retry,
proof attachment, exact `agent_review_required: true` validation, fresh-session
rotation with author/reviewer provenance across implementation, review, and rework,
Human Review handoff, cleanup, and emergency disable. The pilot uses low-risk
fixture/docs/package work and a maximum concurrency of two.

The deterministic fallback is manual one-agent-per-worktree execution using the
same issue and ExecPlan.

## Dependency-DAG warning

Current feature plans are durable product scopes, not directly schedulable issues.
Several describe reciprocal integration dependencies—for example service/SDK,
onboarding/first task, task detail/HITL, coding journey/runtime, and agent draft/deploy.
Before Symphony dispatch, split them into acyclic work cells:

- fixture shell before live integration;
- service/domain/SDK skeleton before source-specific behavior;
- source connection before the end-to-end first-task integration;
- text compose/base stream before HITL/plan approval;
- artifact/journey contract before coding activation;
- agent draft/version/schema before deployment activation;
- responsive web before PWA install/push qualification; and
- web/PWA release before independently gated desktop and beta adapters.

`all-v1-capability-plans` and similar narrative dependencies are not machine blocker
IDs. The generated issue map must be acyclic before any `agent-ready` label is
applied.

## Required decisions and spikes

Add and review:

- Harness document authority/taxonomy and short progressive-disclosure agent maps;
- machine-readable architecture boundaries and exception lifecycle;
- product-spec / roadmap / ExecPlan separation;
- two named fixture modes and per-worktree isolation;
- evidence-backed quality score and recurring gardening;
- pinned Symphony revision, tracker adapter, trust/credential/network/review policy;
- `SPIKE-HARNESS-DOCS-001`, `SPIKE-HARNESS-ARCH-001`,
  `SPIKE-WORKTREE-001`, `SPIKE-DEV-OBS-001`, `SPIKE-DOC-GARDEN-001`, and
  `SPIKE-SYMPHONY-001`.

## Acceptance scenarios

```gherkin
Scenario: Architecture feedback is actionable
  Given a fixture change imports a provider SDK from a browser-safe package
  When the architecture check runs
  Then it fails with the importing path, violated rule, legal adapter boundary,
    architecture link, and local reproduction command

Scenario: Product specification and execution plan are distinct
  Given a stable feature outcome is approved
  When a bounded implementation issue becomes agent-ready
  Then the issue links the owning product spec and a self-contained active ExecPlan
  And implementation progress does not rewrite the durable product outcome

Scenario: Blocked Symphony work cannot dispatch
  Given an agent-ready issue has a non-terminal required blocker
  When Symphony reconciles the tracker
  Then the issue is not dispatchable
  And no workspace or coding session is created for it

Scenario: Parallel workspaces do not collide
  Given two independent low-risk issues are eligible
  When Symphony starts both at the configured concurrency of two
  Then each has a distinct safe workspace, ports, database/schema, object prefix,
    telemetry namespace, and proof directory
  And neither can stop or read the other's fixture stack

Scenario: Orchestrator restart is recoverable
  Given an issue has an active workspace and an existing pull request
  When the Symphony process is killed and restarted
  Then tracker reconciliation does not create a duplicate external effect or PR
  And the next attempt uses preserved issue/workspace evidence or stops safely

Scenario: Tracker credentials remain host-side
  Given Symphony can read the selected tracker
  When an agent inspects its environment, workspace, logs, and proof artifacts
  Then the reusable tracker credential is absent
  And issue updates occur only through the approved tool boundary
```
