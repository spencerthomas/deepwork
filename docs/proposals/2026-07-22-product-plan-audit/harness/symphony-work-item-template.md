---
name: Deep Work agent-ready work item
about: Bounded implementation work derived from an accepted product spec and ExecPlan
title: "<scope>: <observable outcome>"
labels: []
assignees: []
---

> Staged tracker template. Do not install or apply `agent-ready` until
> `SPIKE-SYMPHONY-001` accepts the tracker adapter, field/state mapping, and policy.

```yaml
work_item_id: DW-<milestone>-<lane>-<sequence>
owner: <maintainer or team>
type: spike | contract | implementation | migration | test | docs | release
milestone: M0 | M1 | M2 | M3 | M4 | M5 | M6
lane: docs | platform | api | domain-sdk | web | agent | coding | operations | desktop | quality
affected_packages: []
architecture_layers: []
primary_feature_id: DW-<FEATURE-ID>
supporting_feature_ids: []
product_spec: docs/product-specs/<path>.md
exec_plan: docs/exec-plans/active/<path>.md
exec_plan_status: reviewed | active
blocked_by: []
contract_gates: []
decision_gates: []
allowed_paths: []
acceptance_scenario_ids: []
risk: low | medium | high
rollout_cell: fixture | classic-internal | classic-limited | web-public | desktop-gated | beta-gated
required_reviewers: []
permissions_reviewed_by: []
agent_review_required: true
```

## Objective

<One observable user, contributor, or operator outcome.>

## In scope

- <bounded work>

## Out of scope

- <work that belongs to another issue/spec>

## Authority and dependencies

- Product specification: <link>
- Active ExecPlan: <link>
- Architecture/decision: <links>
- Source/contract pins: <links and exact versions>
- Blockers: <tracker relationships, not prose-only dependencies>

The tracker adapter must derive `dispatchable=false`—before workspace creation—if
any mandatory field is empty, the spec is unaccepted, the ExecPlan is not reviewed
or active, a decision/contract gate is open for this cell, permissions/reviewers
are unapproved, `agent_review_required` is not the boolean `true`, a blocker is not
terminal-success, or the reachable blocker graph is cyclic, unknown,
self-referential, canceled, or duplicate. `dispatchable` is derived adapter state
and cannot be asserted by issue prose or an agent. The accepted launcher or
separate review queue must release the author session before Agent Review and the
reviewer session before Rework, start a fresh role thread over preserved workspace
evidence, and record author/reviewer session provenance; prompt instructions alone
do not satisfy independent review.

## Interfaces and constraints

<Schema/API/event/package boundaries, migration, compatibility, security,
accessibility, observability, and generated-artifact requirements.>

## Permissions

- External network/services: <none or exact allow-list>
- Credentials/secret references: <none or approved host-only references>
- Destructive operations: <prohibited or exact approved operation>
- Release/merge authority: <normally none; Human Review handoff>

## Acceptance and validation

- Scenario IDs: <IDs>
- Exact commands: <commands>
- Expected observations: <results>
- Proof packet: <browser/log/metric/trace/test/generated paths>
- Rollback or capability fallback: <behavior>

## Completion and handoff

- [ ] ExecPlan living sections are current.
- [ ] Relevant package, architecture, docs, contract, security, accessibility, and
      product-demo checks pass.
- [ ] Human and agent review feedback is addressed.
- [ ] Sanitized evidence is attached to the issue/PR.
- [ ] Out-of-scope discoveries have separate non-agent-ready follow-ups.
- [ ] Implementation session moved the issue to Agent Review.
- [ ] A distinct review-only session recorded findings and moved it to Rework or
      Human Review; no agent self-approved, self-granted authority, or merged.
