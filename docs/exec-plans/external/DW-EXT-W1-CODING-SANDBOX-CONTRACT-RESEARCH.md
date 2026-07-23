---
packet_id: DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH
title: External dispatch - prove an isolated recoverable coding sandbox
status: ready-for-external-dispatch
base_commit: b2243109d0cfb2e093cc37a57017e8e70b5ea64b
branch: external/research/coding-sandbox-contracts
owner: external-coding-sandbox-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-SANDBOX-001, SPIKE-SANDBOX-002, SPIKE-EGRESS-001, AC-DW-CODE-001-01, AC-DW-CODE-001-02, AC-DW-CODE-001-03, AC-DW-CODE-001-04]
allowed_paths: [tools/contract-spikes/coding-sandbox/**, docs/references/research/coding-sandbox-contracts/**, docs/exec-plans/external/DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH.md]
dependencies: [SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-sandbox]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
---

# External dispatch - prove an isolated recoverable coding sandbox

## Dispatch identity

- Exact base SHA:
  `b2243109d0cfb2e093cc37a57017e8e70b5ea64b`.
- Branch to create:
  `external/research/coding-sandbox-contracts`.
- ExecPlan: this file.
- This is contract research and an isolated probe harness. It does not authorize
  application, agent, provider-adapter, environment-management, or UI
  implementation.
- The worker may prove a sandbox contract only in an explicitly supplied
  non-production classic account. It receives no production credential, customer
  content, deployment authority, or release authority.

## Purpose and observable result

Produce a version-pinned, independently reviewable contract corpus for an
isolated and recoverable coding sandbox. The corpus must decide
`SPIKE-SANDBOX-001`, `SPIKE-SANDBOX-002`, and `SPIKE-EGRESS-001` row by row,
without treating official prose, installed types, deterministic fakes, or a
successful create call as end-to-end acceptance.

The observable result is a reviewer can determine, for one selected classic
sandbox provider and Python agent-backend version:

1. which lifecycle, command, file-transfer, snapshot, TTL, quota, and error
   operations are public and actually supported;
2. whether one Deep Work task/thread remains bound to exactly one intended
   sandbox across initial work, follow-up, reconnect, process restart, failure,
   expiry, recreation, and cleanup;
3. which network destinations, redirects, DNS resolutions, ports, callbacks, and
   update paths are allowed or denied, including bypass attempts; and
4. what recovery source exists after expiry, without implying that uncommitted
   work survived.

An environment is a versioned Deep Work configuration, a snapshot is an immutable
provider image/reference, and a sandbox is an ephemeral provider runtime. The
probe must not collapse those identities or execute code on the API, web, desktop,
probe-runner, or contributor host as a fallback.

## Allowed paths and exclusions

The worker may change only:

```text
tools/contract-spikes/coding-sandbox/**
docs/references/research/coding-sandbox-contracts/**
docs/exec-plans/external/DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH.md
```

The probe is one isolated Python/uv project with its own `pyproject.toml`,
`uv.lock`, tests, schemas, validators, scrubber, deterministic fake provider, and
network-denied offline suite. It must not import another repository project or
write a root/shared manifest or lock.

Application/package code, shared fixtures, root manifests/locks, product specs,
architecture, decisions, source ledger, generated docs, program/index records,
CI, `docs/plans/**`, and the two downstream coding packet paths are read-only.

Explicitly out of scope:

- GitHub authorization, clone, push, pull request, CI, merge, file-review UI,
  interactive terminal UI, and browser/computer-use;
- arbitrary Docker build contexts, customer repositories, shared mutable
  sandboxes, and assistant-wide reuse across unrelated tasks;
- MDA/Fleet/private routes or undocumented connector APIs;
- production credentials, credentials in environment variables/files/arguments,
  runtime deployment, release, push, merge, or capability enablement; and
- any `E2E-*` acceptance claim.

## Dependencies and evidence precedence

Pinned read-only inputs are:

- `SRC-LC` at `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`;
- `SRC-DA` at `7794b61a6e76230e8c7a49bdce808b3728305914`;
- `SRC-LG` at `31f90df3e6b0268fa77fd2d118a917d420b84a68`;
- current official documentation and installed/generated public package
  contracts; and
- only for live-required rows, an explicitly supplied non-production classic
  sandbox with account tier, region, server/package versions, auth context,
  quotas, and synthetic data recorded.

Every observation is one of `accepted-live`, `installed-public`,
`official-documented`, `pinned-reference`, `deterministic-fake`, or `unknown`.
Final row state is `accepted-live`, `blocked-live-evidence`, `rejected`, or
`unknown`. Deterministic fakes prove the harness and fail-closed behavior, not the
provider. Installed/generated APIs and official prose do not accept live
lifecycle, binding, cleanup, or egress behavior.

If non-production access is absent, complete the public/generated inventory,
offline state machine, negative corpus, validators, and scrub proof. Keep every
live-required row `blocked-live-evidence`; do not substitute a local process,
container, or application host.

## Authoritative checkout sources

Read these exact checkout-local authorities before acting:

- `AGENTS.md` and `docs/AGENTS.md`;
- `ARCHITECTURE.md`;
- `docs/PRODUCT_SENSE.md` and `docs/PLANS.md`;
- `docs/SECURITY.md` and `docs/RELIABILITY.md`;
- `docs/product-specs/coding/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md`;
- `docs/product-specs/index.md` and
  `docs/product-specs/acceptance-scenarios.md`;
- `docs/design-docs/decisions/index.md`;
- `docs/references/source-ledger.md`; and
- `docs/exec-plans/templates/feature.md`.

If these sources or a higher-precedence accepted artifact disagree, stop the
affected row, record the contradiction, owner, blocker, and fallback, and request
coordinator resolution. Do not edit an authority from this packet.

## Required immutable scope and matrices

Before observations, retain `matrix-scope.json` with exact provider, SDK, Python,
agent-backend, account/tier/region expectations, and the required row identities.
The validator derives completeness from this scope rather than trusting rows
selected after probes run. A newly discovered public operation expands the scope
through a reviewed scope revision before its result is recorded.

### Sandbox lifecycle matrix

For `SPIKE-SANDBOX-001`, cover:

- create/get/list/delete and create-timeout reconciliation with an idempotency
  identity;
- provisioning, ready, idle, expiring, expired, stopping, stopped, deleted,
  stale-provider-state, cleanup-failed, permission, quota, capacity, timeout, and
  unknown states;
- discrete command start/output/exit/reconnect/cancel where public, including
  ordering, truncation, concurrent command, timeout, restart, and orphan cleanup;
- upload/download/list/read, bounded size/count, encoding, binary, symlink,
  traversal, changed-during-read, expiry, and authorization failures;
- snapshot reference/build/capture/restore where public, including immutable
  identity, provenance, secret scan, permission, timeout, and unsupported cases;
- TTL, extend/renew if public, health/reconcile, explicit stop/delete, retention,
  repeated cleanup, quota, and provider error normalization; and
- cross-tenant, cross-task, cross-sandbox, guessed-ID, replay, and application-host
  execution negatives.

### Task/thread binding and recovery matrix

For `SPIKE-SANDBOX-002`, use this durable binding key:

```text
tenant/workspace/task/thread/environment-version
```

`run` and `attempt` are append-only observations/history under that durable key;
`providerSandboxId` is the currently resolved value, not part of the key. Test
initial run, same-thread follow-up, queued follow-up, reconnect, API/worker
restart, agent-backend recreation, duplicate/out-of-order events, concurrent
attempts, provider failure, stale mapping, sandbox expiry, explicit recreation,
completion retention, and cleanup. Prove that:

- no two nonterminal provider sandboxes exist for one durable key across retries,
  concurrent attempts, reconnects, or process restarts;
- a sandbox cannot be rebound across tenant, task, or thread;
- a retry reconciles and completes or records cleanup of the prior resolved
  sandbox before any replacement is created;
- setup success gates agent execution and a clean retry does not reuse a failed
  mutable instance;
- recreation uses the same immutable environment version unless a reviewed new
  task/version is chosen; and
- recovery lists only confirmed Git branch, artifact, or accepted snapshot
  evidence. Uncommitted files are never described as durable.

### Egress and auth-proxy-policy matrix

For `SPIKE-EGRESS-001`, establish provider default posture and Deep Work's explicit
allow-list posture. Cover:

- allowed and denied HTTP/S hosts, subdomains, IP literals, redirects, DNS
  changes/rebinding, alternate ports, raw TCP/UDP where applicable, IPv4/IPv6,
  proxy variables, metadata/private/link-local addresses, and hostname tricks;
- allow-list update, remove, narrowing, concurrent request, stale policy, restart,
  sandbox recreation, and snapshot behavior;
- package-registry and source-control destinations as classes, without granting
  GitHub credentials or claiming the downstream GitHub contract;
- provider-authenticated callback, host/path/method/audience binding, nonce,
  expiry, replay, failure, and redaction using synthetic credentials only; and
- SDK, shell, subprocess, library, DNS, direct-IP, redirect, service URL, and
  alternate-protocol bypass attempts.

Also cover credential/header/cookie forwarding for same-origin and cross-origin
redirects, URL userinfo, proxy authorization, and caller-supplied alternate auth
headers. Prove response byte/time/decompression limits, content-type mismatch,
polyglot/active content, oversized and compression-amplified responses, and
fail-closed truncation before parsing. Retain only bounded sanitized metadata for
these negatives, never the response body.

The matrix records request intent and sanitized policy/result, never raw secret,
body, customer host, reusable callback URL, or environment dump.

## Required retained outputs

Under `docs/references/research/coding-sandbox-contracts/`, retain:

- `matrix-scope.json`: immutable dimensions, version pins, required row IDs, and
  scope hash;
- `matrix.json`: lifecycle/binding/egress rows with identity, operation, evidence
  tier, version/account/region/date, sanitized request/result schema, fixture hash,
  conclusion, contradiction, blocker/owner, fallback, and cleanup state;
- `report.md`: public contract inventory, contradictions, per-spike disposition,
  isolation/recovery conclusion, and downstream consumption contract;
- `fixtures/`: deterministic provider transcripts, lifecycle races, binding/
  recovery histories, egress negatives, hashes, and expected outcomes;
- `schemas/`: probe-only versioned lifecycle, binding, egress-policy, error, and
  evidence schemas;
- `versions.json`: interpreter, packages, generated contracts, provider/server,
  account tier, region, auth class, collection date, and source pins;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero secrets, credential references/values, customer or
  tenant data, reusable endpoints/callbacks, raw headers/cookies, unsafe absolute
  paths, or unsanitized command output; and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, and row/per-spike acceptance state.

The validator rejects missing scope rows, duplicate identities, undocumented
operations labeled public, fake/public evidence promoted to live, a successful
create without cleanup/recovery proof, two nonterminal sandboxes for one durable
binding, unconfirmed work labeled durable, default-open egress, credential
forwarding, unbounded/unsafe response handling, missing bypass negatives, missing
fallbacks, accepted rows with unresolved precedence conflicts, and accepted-live
rows without complete live metadata.

## Acceptance contribution and limits

| ID | Required evidence and limit |
|---|---|
| `SPIKE-SANDBOX-001` | Lifecycle, command, transfer, snapshot, TTL, permission, quota, idempotency, error, and cleanup rows are independently decided for the pinned provider/version. |
| `SPIKE-SANDBOX-002` | Initial/follow-up/reconnect/restart/failure/expiry/recreation rows prove stable task/thread binding and cleanup, or retain the stateless/non-coding fallback. |
| `SPIKE-EGRESS-001` | Allow/deny, redirect, DNS, port, callback, update, and bypass rows establish an explicit secure default, or networked coding remains disabled. |
| `AC-DW-CODE-001-01` | Supports setup-failure/no-agent-start contract evidence only; application orchestration remains downstream. |
| `AC-DW-CODE-001-02` | Supports expiry and confirmed-recovery-source semantics only; product recovery UI remains downstream. |
| `AC-DW-CODE-001-03` | Supports explicit allow-list and no-credential egress negatives only; application policy integration remains downstream. |
| `AC-DW-CODE-001-04` | Supports no-sandbox/no-host-execution behavior in the probe; application capability enforcement remains downstream. |

This packet neither satisfies nor claims `E2E-V1-07-CODING-DRAFT-PR`,
`E2E-V1-09-SECURITY-RECOVERY`, or any release acceptance.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/coding-sandbox
uv sync --project tools/contract-spikes/coding-sandbox --frozen
uv run --project tools/contract-spikes/coding-sandbox --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/coding-sandbox --frozen python -m coding_sandbox_spikes.inventory --output docs/references/research/coding-sandbox-contracts/versions.json
uv run --project tools/contract-spikes/coding-sandbox --frozen python -m coding_sandbox_spikes.validate_matrix docs/references/research/coding-sandbox-contracts/matrix.json --scope docs/references/research/coding-sandbox-contracts/matrix-scope.json --require-complete-cross-product --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/coding-sandbox --frozen python -m coding_sandbox_spikes.scrub docs/references/research/coding-sandbox-contracts
uv run --project tools/contract-spikes/coding-sandbox --frozen python -m coding_sandbox_spikes.validate_scope --base b2243109d0cfb2e093cc37a57017e8e70b5ea64b --include-untracked
uv lock --project tools/contract-spikes/coding-sandbox --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/coding-sandbox --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check b2243109d0cfb2e093cc37a57017e8e70b5ea64b...HEAD
git diff --name-only b2243109d0cfb2e093cc37a57017e8e70b5ea64b
git status --short
```

Only with explicitly supplied non-production classic-sandbox access, run:

```bash
uv run --project tools/contract-spikes/coding-sandbox --frozen pytest -m live_contract --live-profile non-production-classic-sandbox --evidence-dir docs/references/research/coding-sandbox-contracts/live
uv run --project tools/contract-spikes/coding-sandbox --frozen python -m coding_sandbox_spikes.scrub docs/references/research/coding-sandbox-contracts/live
```

The live command fails closed when its profile is absent. It uses only synthetic
bounded files/commands, is rate/quota bounded, proves cleanup, and never prints or
persists a credential, raw header/cookie, reusable endpoint/callback, customer
identifier/content, provider body, or environment dump.

## Deterministic fallback, recovery, and idempotence

Until all required rows for a source are independently accepted:

- report `sandbox: unavailable` and disable coding execution for that source;
- never execute on FastAPI, Next.js, Tauri, the probe runner, or a contributor
  host;
- use a stateless non-coding task or require a new task after environment loss;
- use no networked coding environment, or only the independently accepted minimal
  allow-list with affected tools disabled;
- show only confirmed persisted recovery sources; and
- keep research/writing and credential-free fixture work independent.

Repeated offline runs overwrite only deterministic generated probe evidence.
Live retries reconcile the recorded idempotency/binding identity before creating
anything. Interrupted cleanup remains a visible blocked row and is retried only by
the bounded cleanup command; evidence is never deleted to manufacture success.

## Handoff and independent review

Commit only allowed paths on the named branch. Keep this packet current with
progress, exact versions, scope revisions, commands, contradictions, blockers,
and evidence hashes. The author cannot accept their own evidence.

Runtime-contract review owns public-surface/version conclusions and lifecycle/
binding behavior. Security review owns isolation, path, secret, egress, callback,
SSRF/bypass, and cleanup conclusions. Product review owns whether the observable
recovery/fallback is honest and sufficient. All three record verdicts in
`review.json`; a rejected or unresolved required row keeps its fallback active.

The coordinator alone may update the source ledger, decisions, product specs,
application/runtime code, capability manifest, program/index, or release state.
No worktree creation outside the assigned branch, push, merge, deployment,
publication, production mutation, credential collection, or self-approval is
authorized.
