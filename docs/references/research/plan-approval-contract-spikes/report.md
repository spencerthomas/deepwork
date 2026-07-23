# Plan approval contract spikes

## Outcome

This packet prepares a deterministic, offline plan-approval harness only. It does
not accept `SPIKE-PLAN-001` or `SPIKE-HITL-002`, enable plan approval, or prove a
hosted runtime contract.

Every dependent row is either `blocked-upstream-contract`,
`blocked-live-evidence`, or both:

- `SPIKE-HITL-001`, `SPIKE-COMPOSE-001`, and `SPIKE-CONFIG-001` remain
  `blocked-live-evidence` on this base;
- the LangChain research head
  `758c1d4a2230b7c4261fcfbd0f3008634509e096` is provenance only and is not
  integrated into this branch; and
- no sanctioned non-production classic sandbox, account tier, region, server
  revision, authentication context, or live transcript was supplied.

The safe product result is therefore unchanged: source capabilities expose
`planApproval: false` with a typed unavailable reason, **Require plan approval**
is disabled, and a user may explicitly choose another compatible source or
dispatch without plan approval. The text-only first-task path remains available
when the optional control is disabled.

## Evidence precedence

The retained matrix uses this order:

1. accepted sanitized live fixture for an explicitly pinned classic sandbox;
2. installed public/generated contract for pinned versions;
3. official primary documentation;
4. pinned reference repository evidence;
5. deterministic synthetic state-machine evidence; and
6. unknown.

No higher-precedence evidence is available for the target gates. Synthetic
transcripts can prove deterministic local invariants but cannot stand in for an
accepted provider payload, hosted resume transport, durable deployment recovery,
or current runtime authorization.

## Consumed upstream boundary

This packet consumes, without redefining, the upstream normalized ordered-HITL
decision vocabulary `approve`, `edit`, `reject`, and `respond`; one decision per
request in original order; generic count/order validation; generic stale and
duplicate handling; and provider resume syntax. `respond` is valid only when the
aligned review configuration allows it. Cancellation is not a decision. Local
abandonment records no normalized decision and never invokes provider resume.

The packet adds only plan-specific checks:

- stable plan, request, task, run, actor, and workspace identity;
- revision and supersession;
- current actor authority at decision and resume time;
- immutable task permission and side-effect envelopes;
- a rule that editing or approving a plan cannot widen the original authority;
- append-only decision audit and idempotent local resume; and
- zero protected work before the accepted current plan revision is resumed.

The consumed upstream evidence is pinned to LangChain research commit
`758c1d4a2230b7c4261fcfbd0f3008634509e096`:

| Consumed artifact | Git blob | SHA-256 | Upstream conclusion |
|---|---|---|---|
| `fixtures/hitl-ordered-batch.json` | `75746cc028ec15209e93e0c6c8afd64c967c2185` | `bcbb3f0e0e5cd745795e3687271f03e0a91061089841aa4f22837f08c18b062d` | synthetic ordered HITL only; `SPIKE-HITL-001` blocked |
| `fixtures/manifest.json` | `e738b326404ea19c2c22105ce36670d9d9eb3114` | `cd536c5b04681eb40cb56ce3dd97e385d236ff6abeccbb70067616365826923b` | synthetic/documentary evidence only |
| `matrix.json` | `07c07b824061784a5ac075a7ee45fc09bb20fc67` | `682241e63d76f8507b41efec38f5d4b911704a27f951b3c40d9639c7adc93629` | `SPIKE-HITL-001`, `SPIKE-COMPOSE-001`, and `SPIKE-CONFIG-001` blocked |
| `versions.json` | `b6a52b0a431241540f33ddea8f706453577880e3` | `92ecc768d7f2ff63003ddb647408fef750b0e461144e19bef8b76d5e7482fe74` | no installed public distribution or live context |
| `report.md` | `22c3e802cfe02c2b8b8f2dea44e6c688bc22dfc0` | `492a9aa4ace044524fc014bbb75a9059c1fd7f94e118ed903fab18c334733bd0` | no capability accepted or enabled |

These artifacts are read as blocked upstream evidence. Copying their syntax or
hashes does not integrate that commit and does not raise their evidence tier.
Pinned source revisions remain:

- `SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309`;
- `SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914`;
- `SRC-LCPY@592055e15e138f5369dce95dd049ce22430996e2`; and
- `SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68`.

## Deterministic coverage

Research, writing, coding, and blank templates share the same plan gate but keep
distinct template/config identity and permission envelopes. The retained matrix
contains 128 rows: 32 plan-specific scenarios for each of the four templates.
The fixture manifest pins one deterministic transcript per template. The matrix
covers:

- initial revision `1` proposal and correlated request;
- approve unchanged, edit to a new revision then approve, reject with and without
  a safe reason, permitted `respond`, abandonment without resume, and explicit
  restart after rejection;
- wrong request, plan, task, run, actor, or workspace; stale/superseded revision;
  expired authority; cross-workspace replay; and permission/side-effect widening;
- reconnect before decision, reconnect after a persisted decision but before
  resume, reconnect after resume, process restart, and deployment restart;
- model text or tool output impersonating approval, direct resume without a
  current recorded decision, repeated delivery, timeout retry, and
  config/template drift; and
- unsupported-capability fallback with no silent downgrade.

Every deterministic row requires append-only state transitions and
`side_effect_count_before_approval: 0`. Only the eight scenarios that both
persist a current approval and invoke the local release boundary end with one
protected-effect transition; every other scenario ends with zero. Replaying the
same local release key remains at one. This counter is a synthetic stand-in for
the protected execution boundary, not a provider resume, real tool, or provider
mutation.

## Recommended normalized boundary

A plan proposal should bind:

```text
schema_version
plan_id
plan_revision
template_id
template_version
config_version
workspace_id
actor_id
task_id
run_id
request_id
ordered_steps
original_permission_envelope
original_side_effect_envelope
created_at
```

A recorded plan decision should bind the same workspace, actor authority, task,
run, request, plan, and current revision. An `edit` creates a new proposal
revision and supersedes the prior revision; it does not mutate history. Approval
is effective only for the current revision, and only after an authority recheck
at resume. Any permission or side-effect envelope outside the original reviewed
task boundary fails closed.

The provider-facing request/decision/resume payload remains owned by
`SPIKE-HITL-001`. This packet does not prescribe a new wire contract.

## Contradictions and unresolved evidence

- Official and pinned source evidence describe candidate ordered-HITL semantics,
  but the upstream packet has no accepted installed-package or live hosted
  contract.
- Candidate thread/run and config APIs are deployment-defined; the upstream
  compose and config gates remain blocked.
- A process-local checkpoint can demonstrate deterministic replay, but cannot
  prove hosted checkpoint durability or redeploy recovery.
- Prompt text and model/tool output can imitate approval language; neither has
  decision authority.
- A local abandonment action is useful application state but is neither a
  provider decision nor a resume signal.

There is no unresolved precedence conflict: all conclusions remain at the lowest
applicable blocked state.

## Gate disposition and downstream contribution

| ID | Disposition | Contribution |
|---|---|---|
| `SPIKE-PLAN-001` | unaccepted; `implemented-offline-harness-blocked-upstream` | local plan identity, revision, authority, bypass, recovery, and side-effect invariants only |
| `SPIKE-HITL-002` | unaccepted; `implemented-offline-harness-blocked-upstream` | local conformance around the consumed decision vocabulary only |
| `AC-DW-TASK-002-02` | supporting evidence only | truthful `planApproval: false`, disabled control, preserved draft, explicit fallback |
| `AC-DW-QUAL-001-03` | supporting evidence only | truthful unavailable state for the two target gates |

No row satisfies an end-to-end scenario, composer or approvals UI, application
persistence, hosted authorization, deployment, browser reconnect, or release
acceptance. This packet does not block or satisfy `E2E-V1-01-FIRST-VALUE`.

## Required follow-up before acceptance

Acceptance requires a later reviewed base that contains independently accepted
`SPIKE-HITL-001`, `SPIKE-COMPOSE-001`, and `SPIKE-CONFIG-001` artifacts, plus an
explicitly sanctioned non-production classic sandbox. The live run must pin
account tier, region, server/package versions, authentication context, synthetic
task data, cleanup behavior, current authority, and sanitized transcripts. Fresh
runtime-contract, security, and product reviewers must then decide every row and
both target gate dispositions.
