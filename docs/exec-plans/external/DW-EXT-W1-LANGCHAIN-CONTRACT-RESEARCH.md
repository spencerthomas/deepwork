---
packet_id: DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH
title: External dispatch - LangChain contract-spike research
status: completed-research-blocked-live-evidence
base_commit: 85187827e018d4aeee4a4e4bd685de49cb2f5a6a
branch: external/research/langchain-contract-spikes
owner: external-langchain-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: medium
acceptance_ids: [SPIKE-SOURCE-001, SPIKE-CONFIG-001, SPIKE-DEPLOY-001, SPIKE-COMPOSE-001, SPIKE-STREAM-001, SPIKE-STREAM-002, SPIKE-STREAM-003, SPIKE-HITL-001, SPIKE-CANCEL-001, SPIKE-CHECKPOINT-001, SPIKE-THREADS-001, AC-DW-FND-004-01, AC-DW-FND-004-02, AC-DW-FND-004-03, AC-DW-TASK-002-01, AC-DW-TASK-002-02, AC-DW-TASK-003-01, AC-DW-TASK-003-02, AC-DW-TASK-003-04, AC-DW-TASK-004-01, AC-DW-TASK-004-02, AC-DW-TASK-004-03, AC-DW-AGENT-003-01, AC-DW-AGENT-003-05]
allowed_paths: [tools/contract-spikes/langchain/**, docs/references/research/langchain-contract-spikes/**, docs/exec-plans/external/DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH.md]
dependencies: [SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LCPY@592055e15e138f5369dce95dd049ce22430996e2, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:classic-sandbox-account]
created: 2026-07-23
---

# External dispatch - LangChain contract-spike research

## Dispatch identity

- Exact base SHA: `85187827e018d4aeee4a4e4bd685de49cb2f5a6a`.
- Branch to create: `external/research/langchain-contract-spikes`.
- ExecPlan: this file.
- This is a research/probe packet, not permission to add a provider adapter or
  enable a capability.
- This packet is for an external worker. The program coordinator has not assigned
  it to an internal agent.

## Purpose and observable result

Produce a version-pinned, source-precedence-aware contract matrix and executable
probe kit for the public LangChain, LangGraph, Deep Agents, Agent Server, and
classic LangSmith deployment surfaces that gate the next walking skeleton.

The worker must distinguish four evidence levels for every operation:

1. official documented contract;
2. installed public/generated package contract;
3. sanitized live classic-sandbox behavior; and
4. unsupported, contradictory, private, or unknown behavior with the exact
   deterministic fallback.

Reference-repository internals may explain behavior but never establish a hosted
or public package contract. No route, header, cursor, entitlement, field, status,
or provider capability may be inferred into an accepted result.

## Bounded spike set

Research and probe only these named gates:

- source/config/deploy: `SPIKE-SOURCE-001`, `SPIKE-CONFIG-001`,
  `SPIKE-DEPLOY-001`;
- create/threads: `SPIKE-COMPOSE-001`, `SPIKE-THREADS-001`;
- base and projected streaming: `SPIKE-STREAM-001`, `SPIKE-STREAM-002`,
  `SPIKE-STREAM-003`;
- decisions/lifecycle: `SPIKE-HITL-001`, `SPIKE-CANCEL-001`,
  `SPIKE-CHECKPOINT-001`.

MDA, Fleet, direct-browser streaming, Context Hub, schedules, MCP, sandboxes,
subagents, artifacts, attachments, GitHub, PWA, and Tauri are out of scope. Their
existing unavailable fallbacks remain unchanged.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/langchain/**
docs/references/research/langchain-contract-spikes/**
docs/exec-plans/external/DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH.md
```

The probe directory may contain its own Python manifest and `uv.lock`, tests,
schema validators, scrubber, and synthetic server. It may not change application
or package source, any existing manifest/lock, normalized contracts, shared
fixtures, source ledger, product specs, generated docs, CI, or `docs/plans/**`.

## Exact evidence dependencies

Pinned local evidence inputs:

- `SRC-LC` at `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`;
- `SRC-DA` at `7794b61a6e76230e8c7a49bdce808b3728305914`;
- `SRC-LCPY` at `592055e15e138f5369dce95dd049ce22430996e2`;
- `SRC-LG` at `31f90df3e6b0268fa77fd2d118a917d420b84a68`.

Execution dependencies:

- official documentation and reviewed public package-index access;
- an isolated probe lock recording exact Python, package, SDK, transitive, and
  generated-contract versions; and
- only for live acceptance, a human-provided non-production classic sandbox with
  account tier, region, authentication context, server revision, and test data.

If sandbox access is absent, complete documented/installed/negative research and
mark every live-dependent gate `blocked-live-evidence`; do not use production
credentials, ask the browser for a reusable key, or copy secrets into evidence.

## Required outputs

Under `docs/references/research/langchain-contract-spikes/`, retain:

- `matrix.json`: one row per spike/operation with package/server/account/region/
  auth/date, evidence level, exact request shape, sanitized response schema,
  errors, idempotency, retry/cancel/reconnect semantics, result, and fallback;
- `report.md`: contradictions, accepted/blocked/rejected conclusions, source
  precedence, downstream acceptance IDs, and recommended adapter boundary;
- `fixtures/`: synthetic and sanitized request/response/event transcripts with
  scrub attestations and hashes;
- `versions.json`: interpreter, public packages, generated schemas, server, SDK,
  account tier, region, and collection date;
- `scrub-report.json`: zero secret, credential-reference, tenant/customer, and
  unapproved host findings; and
- `commands.txt`: exact commands and exit status without environment dumps.

Under `tools/contract-spikes/langchain/`, retain an isolated, reproducible probe
kit with offline synthetic tests and opt-in live tests. Every live test is marked,
time-bounded, read-only unless the named spike requires a mutation, uses synthetic
records, and has explicit cleanup/idempotency behavior.

## Acceptance IDs and qualification

The packet produces gate evidence for the spike IDs in front matter. It also
supports, but does not by itself satisfy, these downstream product scenarios:

- stream/recovery/HITL: `AC-DW-FND-004-01`, `AC-DW-FND-004-02`,
  `AC-DW-FND-004-03`, `AC-DW-TASK-003-01`, `AC-DW-TASK-003-02`,
  `AC-DW-TASK-003-04`;
- compose/plan: `AC-DW-TASK-002-01`, `AC-DW-TASK-002-02`;
- queue/cancel/checkpoint: `AC-DW-TASK-004-01`, `AC-DW-TASK-004-02`,
  `AC-DW-TASK-004-03`;
- config/deploy: `AC-DW-AGENT-003-01`, `AC-DW-AGENT-003-05`.

A spike is `accepted` only when its required evidence row is complete against the
exact installed package/generated contract and, where the decision table requires
it, sanitized live classic-sandbox behavior. Documentation-only evidence may be
`documented`, never silently promoted to `accepted-live`.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/langchain
uv sync --project tools/contract-spikes/langchain --frozen
uv run --project tools/contract-spikes/langchain --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/langchain --frozen python -m langchain_contract_spikes.inventory --output docs/references/research/langchain-contract-spikes/versions.json
uv run --project tools/contract-spikes/langchain --frozen python -m langchain_contract_spikes.validate_matrix docs/references/research/langchain-contract-spikes/matrix.json
uv run --project tools/contract-spikes/langchain --frozen python -m langchain_contract_spikes.scrub docs/references/research/langchain-contract-spikes
uv lock --project tools/contract-spikes/langchain --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/langchain --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check
git diff --name-only 85187827e018d4aeee4a4e4bd685de49cb2f5a6a
```

Only with explicitly provided classic-sandbox access, run:

```bash
uv run --project tools/contract-spikes/langchain --frozen pytest -m live_contract --live-profile classic-sandbox --evidence-dir docs/references/research/langchain-contract-spikes/live
uv run --project tools/contract-spikes/langchain --frozen python -m langchain_contract_spikes.scrub docs/references/research/langchain-contract-spikes/live
```

The live command must fail closed when the profile is absent; it must never print
or persist tokens, raw headers, reusable endpoints, customer content, or an
environment dump.

## Handoff and review

Commit only allowed paths on the named branch. Keep this packet current with
progress, contradictions, decisions, exact evidence state, and blockers. An
external author cannot accept their own spike. Runtime-contract, security, and
product reviewers decide each spike row independently; one failed optional spike
must not invalidate unrelated accepted rows. The coordinator alone updates the
source ledger/product plans, adds normalized application code, integrates the
branch, or changes a capability from unavailable. No push, merge, deploy,
publication, production mutation, or private-beta enablement is authorized.

## Progress

- [x] 2026-07-23: Verified the prepared branch, exact seed, implementation-base
  ancestry, clean status, and base diff containing only this ExecPlan.
- [x] 2026-07-23: Verified all four local evidence repositories were clean at
  their exact pinned revisions.
- [x] 2026-07-23: Independently reviewed source/config/deploy,
  compose/threads/HITL, and stream/cancel/checkpoint contract groups.
- [x] 2026-07-23: Built the dependency-free probe scaffold, matrix validator,
  evidence inventory, synthetic fixtures, hash manifest, scrubber, and
  fail-closed live profile gate under the allowed paths.
- [x] 2026-07-23: Recorded one complete row for every named spike and retained
  package/source/server/account/region/auth/date state without promoting
  package-source evidence to an installed contract.
- [x] 2026-07-23: Ran offline synthetic tests, matrix validation, evidence
  scrubbing, lock checks, documentation validation, and diff checks.
- [x] 2026-07-23: Ran the documented live command without a complete sandbox
  profile and confirmed it failed closed without printing credentials.
- [ ] Independent runtime-contract, security, and product reviewers accept or
  reject each row. The author has not self-accepted any spike.
- [ ] A human provides an explicitly authorized non-production classic sandbox
  and approved public package-index access for installed/live acceptance.
- [ ] Produce a genuinely isolated lock including the exact public distributions,
  test runner, and transitive dependencies. Current validation delegates to the
  workspace's exact `pytest 9.0.2` and is environment-bound.

## Surprises and discoveries

- Public package-index egress was not authorized in this environment. The
  candidate source versions are pinned, but the retained inventory correctly
  records no installed LangChain/LangGraph/Deep Agents distributions.
- Current typed event streaming is protocol v3. Earlier audit prose calling the
  `/threads/{thread_id}/stream/events` surface protocol v2 is stale; legacy
  `Last-Event-ID` streams remain separate.
- The pinned Python HITL contract has no action IDs in `action_requests`,
  `review_configs`, or `decisions`. Fidelity is positional, including repeated
  tool names. An initial synthetic ID-join model was rejected and replaced.
- The current Python event-stream candidate aliases `subagents` to `subgraphs`,
  while official Deep Agents prose describes a distinct product-level subagent
  projection.
- Thread search is limit/offset based and returns no cursor or stable-snapshot
  promise.
- Run creation exposes no caller run ID or mutation idempotency key.
  `if_not_exists` concerns a missing thread, not run deduplication.
- `/ok` may be shallow when metadata checks are disabled, so it cannot by itself
  establish source readiness or enabled capabilities.

## Decision log

- **2026-07-23 — Keep every gate blocked.** Without installed public
  distributions and sanitized live classic-sandbox evidence, no named spike is
  accepted and no product capability changes state.
- **2026-07-23 — Preserve evidence classes.** Pinned public package source may
  explain candidate signatures but is recorded as unsupported/unknown at the
  installed-contract level.
- **2026-07-23 — Separate streaming protocols.** Protocol-v3 body cursor `since`
  and durable `event_id` dedupe are not combined with legacy
  `Last-Event-ID` thread/run joins.
- **2026-07-23 — Preserve positional HITL.** Synthetic probes validate exact
  upstream snake_case keys and ordered arrays; they do not add provider IDs.
- **2026-07-23 — Keep deployment operator-owned.** The pinned control-plane
  evidence is insufficient for a safe app-owned mutation adapter, retry policy,
  or success state.
- **2026-07-23 — Use an offline dependency-free probe runner.** Because package
  egress was blocked, the probe lock contains only the probe package and requires
  the exact workspace `pytest 9.0.2`; it does not masquerade as installed
  LangChain evidence.

## Outcomes and retrospective

The packet produced the required matrix, report, fixture set, version inventory,
scrub report, command ledger, and an executable environment-bound offline probe
scaffold within the allowed paths. The research resolves several contract-shape
errors and supplies deterministic fallbacks, but it deliberately does not satisfy
the installed-distribution, isolated-lock, or live-dependent acceptance gates.

The most important integration result is negative and actionable: the
coordinator must keep source registration, generic config mutation, deployment,
dispatch, typed event-stream UX, steering queues, HITL submission, cancellation,
and checkpoint restore/fork unavailable. Future work must first install exact
public distributions from an approved index and run sanitized tests against an
explicit non-production classic sandbox with recorded account tier, region,
authentication context, and server revision.
