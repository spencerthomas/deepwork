---
packet_id: DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL
title: External dispatch - require a real plan before the first task executes
status: prepared-for-independent-review
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
branch: external/research/first-task-plan-approval
owner: external-plan-approval-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-PLAN-001, SPIKE-HITL-002, AC-DW-TASK-002-02, AC-DW-QUAL-001-03]
allowed_paths: [tools/contract-spikes/plan-approval/**, docs/references/research/plan-approval-contract-spikes/**, docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL.md]
dependencies: [SPIKE-HITL-001, SPIKE-COMPOSE-001, SPIKE-CONFIG-001, SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LCPY@592055e15e138f5369dce95dd049ce22430996e2, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-sandbox]
blockers: [accepted-SPIKE-HITL-001, accepted-SPIKE-COMPOSE-001, accepted-SPIKE-CONFIG-001, sanctioned-non-production-classic-sandbox]
created: 2026-07-23
reviewed_at: null
review_result: pending
---

# External dispatch - require a real plan before the first task executes

## Dispatch identity

- Exact base SHA:
  `fff1bfd278d550d01de6e8d74f553f45c4003a8c`.
- Branch to create:
  `external/research/first-task-plan-approval`.
- ExecPlan: this file.
- This packet is contract research and a probe harness. It does not authorize
  product composer/approval implementation, a new HITL protocol, runtime
  deployment, capability enablement, or prompt wording presented as enforcement.
- This packet is for an external worker. The program coordinator has not assigned
  its implementation scope to an internal agent.

## Purpose and observable result

Answer `SPIKE-PLAN-001` and `SPIKE-HITL-002` for the selected starter templates by
proving that a versioned plan proposal is a real, durable, bypass-resistant
approval gate before execution, using the already-owned normalized ordered-HITL
contract.

The result distinguishes:

1. plan proposal schema, stable identity, template/config revision, editable
   fields, immutable fields, and supersession;
2. approval, edit, rejection, response, local abandonment, stale plan revision, and
   invalid plan authority;
3. normalized ordered-HITL request/decision correlation and resume semantics;
4. reconnect, process restart, and redeploy recovery without pre-approval work;
5. bypass-prevention across model output, repeated messages, retries, stale
   capabilities, and direct resume attempts; and
6. the exact unavailable fallback for every template/source not fully proved.

This work may complete deterministic fake-model/state-machine rows while upstream
or live evidence is unavailable. It does not block the first text-only task or
`E2E-V1-01-FIRST-VALUE`.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/plan-approval/**
docs/references/research/plan-approval-contract-spikes/**
docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-PLAN-APPROVAL.md
```

The probe is an isolated Python/uv project with its own manifest, lock, tests,
validators, scrubber, deterministic fake model, durable fake checkpoint store,
and no-network runtime. It must not import another repository project or write a
root/shared lock.

Application/package source, agent templates, shared fixtures, upstream LangChain
probe outputs, root manifests/locks, product specs, decisions, source ledger,
generated docs, program/index records, CI, and `docs/plans/**` are read-only.

## Dependencies: consume, do not duplicate

This exact dispatch base does not contain accepted artifacts for the three
upstream gates. The external LangChain research head
`758c1d4a2230b7c4261fcfbd0f3008634509e096` is coordinator provenance only: all
three relevant rows remain `blocked-live-evidence`, and that head is not integrated
into this base. Therefore this dispatch is offline-harness-only. It may produce
`implemented-offline-harness-blocked-upstream`; it must not accept
`SPIKE-PLAN-001` or `SPIKE-HITL-002` until a later reviewed base contains accepted
upstream artifacts and the required live evidence.

This packet consumes these separately owned gates and must not redefine or
re-probe them:

- `SPIKE-HITL-001`: exact ordered HITL payload, aligned decision arrays, the
  `approve`, `edit`, `reject`, and `respond` values, value/count/order validation,
  generic stale/duplicate handling, and provider resume syntax;
- `SPIKE-COMPOSE-001`: accepted thread/run input, creation, unknown-field, and
  normalized-result contract; and
- `SPIKE-CONFIG-001`: accepted starter-project/template/config schema,
  version/unknown-field rules, and deployment round trip.

The worker records the exact accepted artifact/commit and hashes any consumed
fixture subset. If one is absent, unresolved, contradictory, or
`blocked-live-evidence`, dependent plan/live rows inherit that state. Generic
decision value/count/order, stale/duplicate delivery, and resume syntax belong
only to `SPIKE-HITL-001`; this packet tests plan identity, revision, current actor
authority, permission/side-effect boundaries, and whether protected work stays
blocked. A deterministic fake may exercise that local state machine, but it
cannot accept an upstream gate or stand in for the pinned provider contract.

Pinned evidence inputs are `SRC-LC` at
`7b9215d708e0b57e6fbae7b5d0762c4118b8e309`, `SRC-DA` at
`7794b61a6e76230e8c7a49bdce808b3728305914`, `SRC-LCPY` at
`592055e15e138f5369dce95dd049ce22430996e2`, and `SRC-LG` at
`31f90df3e6b0268fa77fd2d118a917d420b84a68`, plus official documentation,
installed public/generated packages, and, only for live acceptance, an explicitly
supplied non-production classic sandbox with account tier, region, server/package
versions, authentication context, and synthetic task data.

Evidence precedence is accepted live fixture, installed public/generated
contract, official documentation, pinned reference, deterministic fake, then
unknown. No prompt, prototype, internal helper, or model assertion proves an
enforceable gate.

## Required contract matrix

At minimum, retain rows for each selected research, writing, coding, and blank
starter template covering:

- initial proposal with plan ID, schema version, template/config version, task/run
  identity, revision `1`, ordered steps, permissions/side-effect boundary, and
  normalized HITL request correlation;
- approve unchanged, edit then approve as a new revision, reject with/without a
  safe reason, `respond` where the consumed review config permits it, local
  abandonment without provider resume, and explicit restart after rejection;
- wrong request/plan/task/run, stale or superseded plan revision, expired actor
  authorization, cross-workspace replay, and an edit/approval attempt that widens
  the original permission or side-effect boundary;
- reconnect before decision, after persisted decision but before resume, after
  resume, process restart, and deployment restart;
- fake/model text that says approved, tool output that imitates a decision,
  direct resume without a recorded current-authority decision, repeated delivery,
  retry after timeout, and config/template drift; and
- proof that no protected execution/tool side effect occurs before the accepted
  current plan revision is resumed, and that approval never grants more authority
  than the original reviewed task boundary.

The deterministic harness must use explicit state transitions and an append-only
decision log. Hidden model reasoning is never evidence. Editable plan text is
untrusted input; decision authority is actor/workspace/task/request/revision
bound, current at mutation time, and idempotent.

## Required retained outputs

Under `docs/references/research/plan-approval-contract-spikes/`, retain:

- `matrix.json`: one row per template/scenario/evidence tier with exact versions,
  upstream artifact pins, proposal/request/decision/resume schemas, state
  transitions, side-effect count, recovery result, conclusion, blocker, and
  fallback;
- `report.md`: source precedence, upstream consumption, contradictions,
  recommended normalized boundary, complete/blocked/rejected rows, and explicit
  downstream contribution wording;
- `fixtures/`: deterministic fake-model/checkpoint transcripts and sanitized
  public/live transcripts with hashes;
- `versions.json`: Python, dependencies, starter template/config, public/generated
  contracts, runtime/server/account/region/date, and consumed upstream artifacts;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero secrets, credentials, customer/tenant data, reusable
  endpoints, raw headers/cookies, hidden reasoning, or unsanitized absolute paths;
  and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, and per-row state.

The matrix validator rejects incomplete template/scenario coverage, duplicate
identity, unpinned upstream input, accepted target spikes on this harness-only
base, accepted rows that inherit a blocked dependency, use of `cancel` as a
normalized HITL decision, permission/side-effect widening, side effects before
approval, non-idempotent resume, fake evidence promoted to provider proof, missing
fallbacks, and unresolved evidence-precedence conflicts.

## Acceptance IDs and downstream contribution

Every `AC-*` row is supporting contract evidence only. This packet does not
satisfy composer UI, approval UI, application persistence, authorization, runtime
deployment, browser, reconnect, or release acceptance by itself.

| ID | Required evidence and limit |
|---|---|
| `SPIKE-PLAN-001` | Selected starter templates emit a versioned, revisioned plan and accept only a current, correlated decision/resume signal; bypass, restart, and stale cases are independently decided. |
| `SPIKE-HITL-002` | Plan proposal, edit, approval, rejection, reconnect, restart, and redeploy rows conform to the consumed normalized ordered-HITL contract. |
| `AC-DW-TASK-002-02` | Supports the no-silent-downgrade and unavailable-manifest rule. The full scenario still requires composer/application/source integration proof. |
| `AC-DW-QUAL-001-03` | Supports only the two named gate conclusions and truthful unavailable fallback. Release-manifest omission/disablement remains coordinator evidence. |

No row contributes to an end-to-end scenario. In particular, the packet does not
block or satisfy `E2E-V1-01-FIRST-VALUE`.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/plan-approval
uv sync --project tools/contract-spikes/plan-approval --frozen
uv run --project tools/contract-spikes/plan-approval --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/plan-approval --frozen python -m plan_approval_contract_spikes.inventory --output docs/references/research/plan-approval-contract-spikes/versions.json
uv run --project tools/contract-spikes/plan-approval --frozen python -m plan_approval_contract_spikes.validate_matrix docs/references/research/plan-approval-contract-spikes/matrix.json --require-complete-cross-product --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/plan-approval --frozen python -m plan_approval_contract_spikes.scrub docs/references/research/plan-approval-contract-spikes
uv run --project tools/contract-spikes/plan-approval --frozen python -m plan_approval_contract_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
uv lock --project tools/contract-spikes/plan-approval --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/plan-approval --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c
git status --short
```

The following command is prohibited on this dispatch base. It may run only after a
reviewed rebase contains accepted upstream artifacts and an explicitly supplied
non-production classic sandbox:

```bash
uv run --project tools/contract-spikes/plan-approval --frozen pytest -m live_contract --live-profile non-production-classic-plan-approval --evidence-dir docs/references/research/plan-approval-contract-spikes/live
uv run --project tools/contract-spikes/plan-approval --frozen python -m plan_approval_contract_spikes.scrub docs/references/research/plan-approval-contract-spikes/live
```

The live command fails closed if the profile or any accepted dependency is absent.
It is synthetic, time-bounded, idempotent, verifies cleanup/current authority, and
never prints or persists secrets, raw headers/cookies, reusable endpoints,
customer content, hidden reasoning, or an environment dump.

## Deterministic fallback

Until both plan gates and all consumed dependencies are independently accepted for
a template/source combination:

- expose `planApproval: false` with a typed unavailable reason;
- disable **Require plan approval** for that source/template;
- preserve the user's draft and offer an explicit choice of another compatible
  source or dispatch without plan approval;
- never call prompt wording, a model-authored message, or a manual note an
  enforceable plan gate; and
- keep the text-only first-task path available without this optional capability.

## Idempotence, rollback, and handoff

Offline probes write only deterministic evidence and temporary state. A repeated
decision/resume produces one transition and no duplicate side effect. Restart
fixtures reload the append-only decision state rather than trusting process
memory. Live synthetic tasks are uniquely named, bounded, and cleaned up where the
accepted public contract permits.

Commit only allowed paths on the named branch. Keep this packet current with
progress, discoveries, decisions, commands, dependency states, evidence, and
blockers. The author cannot accept their own work. Runtime-contract, security, and
product reviewers independently decide every matrix row and both spike
dispositions.

The coordinator alone updates source ledgers, upstream spike state, product/
program/index records, starter agents, application adapters, normalized
contracts, capability flags, or release scope. No worktree creation, push, merge,
deployment, publication, production mutation, credential collection, or
destructive cleanup is authorized by this packet.
