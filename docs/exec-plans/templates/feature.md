---
exec_plan_id: DW-EXEC-<stable-work-item-id>
title: <observable outcome>
status: draft
superseded_by: null
owner: <owner>
reviewed_by: []
reviewed_at: null
primary_feature_id: <DW-FEATURE-ID>
supporting_feature_ids: []
issue: <tracker reference>
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
base_commit: <full reviewed git commit>
last_verified_commit: <git commit or null while draft>
risk: low | medium | high
governed_paths: []
contract_gates: []
decision_gates: []
gate_review_status: unreviewed
gate_reviewed_by: []
gate_reviewed_at: null
authoritative_sources: []
scenario_ids: []
dispatch_kind: cell
dispatch_ready: false
agent_review_required: true
dependencies: []
blockers: []
---

# <Observable outcome>

> Staged template for `docs/exec-plans/active/`. Delete instructional angle
> brackets when creating a real plan. A real plan must be self-contained from the
> checkout and remain current during implementation.

Status semantics are `draft`, `reviewed`, `active`, `completed`, or `superseded`.
Only a maintainer-reviewed `reviewed` or `active` ExecPlan with non-empty authority,
reviewer, governed-path, and verification metadata plus completed gate review can
make a Symphony issue dispatchable. `gate_review_status` is `reviewed-with-gates`
when either gate array is non-empty and `reviewed-none` only when a maintainer has
explicitly confirmed that both arrays are intentionally empty; either reviewed
state requires reviewer and time metadata. Empty arrays with `unreviewed` never
mean “no gates.” `completed` requires the retrospective and retained proof;
`superseded` requires a non-null `superseded_by` pointing to its replacement.
Every dispatched cell also records its exact reviewed `base_commit`, stable issue
identity, scenario IDs, dependency/blocker IDs, `dispatch_kind: cell`, exact
boolean `dispatch_ready: true`, and exact boolean `agent_review_required: true`.
A program-control ExecPlan uses `dispatch_kind: program` and remains
`dispatch_ready: false`; it coordinates cells but is not itself a work item.

## Purpose and observable result

<State what a user, contributor, operator, test, or reviewer can do or observe
after completion. Link the owning product specification; do not duplicate its
durable scope.>

## Context and orientation

<Explain the relevant repository areas, architecture layers, domain vocabulary,
current behavior, and why this work is needed. Give exact paths and public
interfaces. Assume the reader has no chat history.>

## Scope

### In scope

- <bounded change>

### Non-goals

- <explicitly excluded work>

### Permissions and risk boundary

- Allowed paths: <paths>
- External systems: <none or exact test system>
- Credentials: <none or approved secret reference; never paste values>
- Destructive/migration/release operations: <explicitly prohibited or approved>
- Required human/specialist review: <owners>

## Authoritative sources and prerequisites

- Product spec: <canonical link>
- Architecture/ADR: <canonical links>
- Contract evidence: <pinned links/versions/spike memo>
- Root and scoped `AGENTS.md`: <links>
- Dependencies/blockers: <IDs and terminal evidence>

## Interfaces and invariants

<List public types, endpoints/events, schema/data changes, legal dependency edges,
security/accessibility/observability invariants, and compatibility requirements.
State what must remain unchanged.>

## Milestones

### Milestone 1 — <independently verifiable result>

<Describe implementation in prose, then exact proof. Each milestone should leave
the tree in a coherent state and be verifiable independently.>

Acceptance:

- <observable result>
- Command: `<exact command>`
- Expected observation: <what proves success>
- Evidence artifact: <path/link>

### Milestone 2 — <result>

<Repeat as needed.>

## Progress

- [ ] <YYYY-MM-DD HH:MM TZ> — Plan reviewed; prerequisites and blockers verified.
- [ ] <timestamp> — Milestone 1 complete; evidence: <link/path>.
- [ ] <timestamp> — Milestone 2 complete; evidence: <link/path>.
- [ ] <timestamp> — Required checks, review, rollout, and documentation complete.

Update this section whenever work stops or a milestone changes. Split partially
complete work into completed and remaining facts rather than leaving an ambiguous
checkbox.

## Surprises & Discoveries

- <timestamp> — Observation: <concise fact>. Evidence: <command/output/path>.
  Consequence: <plan or follow-up change>.

Record unexpected contracts, failures, performance facts, dependency behavior,
and repository conditions as they are found. Do not hide them in chat.

## Decision Log

- <timestamp> — Decision: <choice>. Rationale: <evidence and tradeoff>.
  Consequence: <interfaces/migration/follow-up>. Approved by: <owner if required>.

An implementation agent may record a bounded choice within accepted authority. A
new product outcome, external contract, permission, destructive action, or
architecture edge requires the appropriate decision/spike/reviewer first.

## Detailed implementation approach

<Describe the sequence of edits with exact files/modules/symbols. Name generated
artifacts and commands. Keep code snippets small; the repository is the code.>

## Validation and proof

Run, as applicable:

```text
make doctor
make check-architecture
make check-docs
<package format/lint/type/unit/contract/build command>
<fixture/product-demo E2E command>
<security/accessibility/performance/migration command>
```

For application work, include:

- exact acceptance scenario IDs;
- browser before/after or interaction proof;
- console/network review;
- relevant structured log, metric, and trace queries;
- fixture and live/captured-contract tier;
- supported viewport/platform/assistive-technology evidence; and
- sanitized artifact paths.

## Idempotence, rollback, and recovery

<Explain safe rerun behavior, partial failure, interrupted work, workspace/app
restart, data/schema rollback or forward recovery, feature flag/capability fallback,
and cleanup. Name irreversible steps and required approval.>

## Rollout and handoff

<State flags/rings, compatibility window, monitoring, stop/rollback criteria,
documentation, reviewer, and expected issue state. Symphony work normally hands
off at Human Review rather than declaring Done.>

## Outcomes & Retrospective

<At completion, compare observable result with purpose. List evidence, deviations,
what remains, debt/follow-up issue IDs, and any source/decision/product-spec update.
Do not erase earlier progress, discoveries, or decisions.>
