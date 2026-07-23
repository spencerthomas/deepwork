---
packet_id: DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS
title: External dispatch - add a file to the first task safely
status: prepared-for-independent-review
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
branch: external/research/first-task-safe-attachments
owner: external-attachment-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-ATTACH-001, AC-DW-TASK-002-03, AC-DW-QUAL-001-03, AC-DW-QUAL-001-04]
allowed_paths: [tools/contract-spikes/attachments/**, docs/references/research/attachment-contract-spikes/**, docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS.md]
dependencies: [SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-object-scanner-runtime]
created: 2026-07-23
reviewed_at: null
review_result: pending
---

# External dispatch - add a file to the first task safely

## Dispatch identity

- Exact base SHA:
  `fff1bfd278d550d01de6e8d74f553f45c4003a8c`.
- Branch to create:
  `external/research/first-task-safe-attachments`.
- ExecPlan: this file.
- This packet is contract research and a probe harness. It does not authorize
  application upload APIs, object storage, malware-scanner procurement, provider
  adapters, credential collection, or attachment capability enablement.
- This packet is for an external worker. The program coordinator has not assigned
  its implementation scope to an internal agent.

## Purpose and observable result

Answer `SPIKE-ATTACH-001` with a version-pinned, source-precedence-aware matrix
showing where attachment bytes may live and how a selected classic runtime may
receive them without exposing unsafe content to an agent.

The result must separately establish:

1. application/object ownership and quarantine state;
2. declared and detected media type, byte/count limits, hash, filename handling,
   malware/unsafe-content verdict, retention, and deletion;
3. the selected runtime transfer representation and authorization boundary;
4. failure, retry, expiry, cleanup, and source-unavailable behavior; and
5. the deterministic fallback for every unproved source/media combination.

The credential-free, pasted-text first-task path remains usable while this work is
open. This packet is supporting evidence only and must not block or claim
`E2E-V1-01-FIRST-VALUE`.

## Allowed paths

The worker may change only:

```text
tools/contract-spikes/attachments/**
docs/references/research/attachment-contract-spikes/**
docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS.md
```

`tools/contract-spikes/attachments/**` is an isolated Python/uv project with its
own `pyproject.toml`, `uv.lock`, tests, validators, scrubber, and deterministic
fake object-store/scanner/runtime adapters. It must not import another repository
project or write through a root/shared lock.

Application/package source, shared fixtures, root manifests/locks, product specs,
decision tables, source ledger, generated docs, program/index records, CI, object
store configuration, and `docs/plans/**` are read-only. Do not add real malware,
customer files, credentials, reusable signed URLs, or operational endpoints.

## Exact dependencies and evidence precedence

Pinned evidence inputs:

- `SRC-LC` at `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`;
- `SRC-DA` at `7794b61a6e76230e8c7a49bdce808b3728305914`;
- `SRC-LG` at `31f90df3e6b0268fa77fd2d118a917d420b84a68`;
- reviewed official documentation and public package/index artifacts; and
- only for live acceptance, explicitly supplied non-production object storage,
  scanner, and classic runtime access with account tier, region, server/service
  versions, authentication context, and synthetic test data recorded.

Every matrix observation records one evidence tier: `accepted-live`,
`installed-public`, `official-documented`, `pinned-reference`,
`deterministic-fake`, or `unknown`. Live evidence outranks public/generated
contracts, which outrank official prose, which outranks pinned internals.
Deterministic fakes prove the harness and safety state machine, not a hosted
provider contract.

Without sanctioned non-production access, complete the public/installed and fake
rows, but mark object-store, scanner, and runtime-transfer rows that require
real behavior `blocked-live-evidence`. Never infer an accepted route, upload
grant, media representation, scanner guarantee, retention promise, or provider
capability from reference internals.

## Required contract matrix

At minimum, retain matrix rows for:

- preflight rejection by count, declared type, size, empty content, unsafe
  filename, traversal-like name, duplicate/hash mismatch, and unsupported media;
- quarantine creation with actor/workspace/object binding and no agent visibility;
- detected-type mismatch, scanner clean/unsafe/error/timeout/unavailable verdicts,
  and explicit fail-closed transition rules;
- clean transfer by each officially supported representation, with destination,
  authorization scope, expiry, idempotency, hash/size verification, and receipt;
- transfer rejection for stale grant, wrong actor/workspace/task, wrong
  destination, replay, redirect, range/partial behavior, or source capability
  mismatch;
- remove-before-transfer, delete-after-transfer, orphan cleanup, retention expiry,
  provider deletion failure, retry, and auditable terminal state; and
- recovery after process restart without changing an unsafe or unknown verdict
  into clean.

Fake adapters must model these states deterministically and deny all network
access. Fixture contents are harmless synthetic bytes and verdicts; do not commit
an executable, macro document, active HTML, decompression bomb, or a real malware
sample. A scanner result is an untrusted external input and cannot alone authorize
cross-workspace or cross-task transfer.

## Required retained outputs

Under `docs/references/research/attachment-contract-spikes/`, retain:

- `matrix.json`: one row per scenario/source/media/operation with exact
  package/service/runtime versions, account/region/auth/date when applicable,
  source observations, state transitions, request/response schemas, hashes,
  conclusion, blocker/owner, and fallback;
- `report.md`: architecture boundary, contradictions, complete/blocked/rejected
  rows, downstream contribution wording, and reviewer disposition;
- `fixtures/`: harmless synthetic metadata and sanitized transcripts plus hashes
  and expected state transitions;
- `versions.json`: Python, dependencies, generated/public contracts, selected
  object/scanner/runtime versions, account tier/region, and collection date;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero secrets, credential references, customer/tenant data,
  reusable endpoints or signed grants, raw headers/cookies, unsafe binary content,
  and unsanitized absolute paths; and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, and per-row acceptance/blocking state.

The matrix validator rejects missing cross-products, duplicate row identities,
unknown statuses, absent evidence provenance, accepted-live rows without live
metadata, deterministic-fake rows labeled as provider proof, missing fallbacks,
or unresolved source-precedence conflicts.

## Acceptance IDs and downstream contribution

Every `AC-*` row is supporting attachment-contract evidence only. This packet does
not satisfy composer UI, application persistence, authorization, object-service,
provider integration, browser, or release acceptance by itself.

| ID | Required evidence and limit |
|---|---|
| `SPIKE-ATTACH-001` | Media/type/size, quarantine, scanner, transfer, retention, deletion, failure, and recovery rows are independently decided for each selected source/media combination. Live-required rows remain blocked without sanctioned non-production proof. |
| `AC-DW-TASK-002-03` | Supports the unsafe-before-agent-visibility state-machine slice with negative fixtures. The complete scenario still requires application upload/dispatch integration evidence. |
| `AC-DW-QUAL-001-03` | Supports only the named attachment-gate conclusion and fallback. Release-manifest disablement/omission remains coordinator evidence. |
| `AC-DW-QUAL-001-04` | Supports only attachment traversal, media, quarantine, scanner, transfer, tenant/task-binding, replay, and deletion abuse cases. The full cross-layer security suite remains downstream. |

No row contributes to `E2E-V1-01-FIRST-VALUE`. Pasted text with explicit size
limits is the first-task fallback and remains independent of this packet.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/attachments
uv sync --project tools/contract-spikes/attachments --frozen
uv run --project tools/contract-spikes/attachments --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.inventory --output docs/references/research/attachment-contract-spikes/versions.json
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.validate_matrix docs/references/research/attachment-contract-spikes/matrix.json --require-complete-cross-product --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.scrub docs/references/research/attachment-contract-spikes
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
uv lock --project tools/contract-spikes/attachments --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/attachments --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c
git status --short
```

Only with all three sanctioned non-production dependencies explicitly supplied,
run:

```bash
uv run --project tools/contract-spikes/attachments --frozen pytest -m live_contract --live-profile non-production-classic-attachments --evidence-dir docs/references/research/attachment-contract-spikes/live
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.scrub docs/references/research/attachment-contract-spikes/live
```

The live command fails closed if any required profile component is absent. It must
be rate-bounded, use harmless synthetic bytes, prove cleanup, and never print or
persist secrets, signed URLs, raw headers/cookies, customer content, reusable
endpoints, or an environment dump.

## Deterministic fallback

Until a source/media row is independently accepted:

- expose no file-attachment capability for that row;
- allow only bounded pasted text through its separately validated text path;
- preserve local draft metadata without claiming an upload completed;
- reject unsafe, unknown, expired, mismatched, or scanner-unavailable objects;
- never transfer quarantined bytes to a source, sandbox, model, previewer, or
  downstream extractor; and
- keep the text-only first-task demonstration and unrelated Wave 1 work moving.

## Idempotence, rollback, and handoff

Probe and fake-adapter runs are deterministic, use temporary directories, and
leave no external object. Live probes use unique synthetic identities, explicit
cleanup, bounded retry, and retained deletion evidence. Re-running a transfer or
cleanup fixture must not duplicate visibility or broaden authority.

Commit only allowed paths on the named branch. Keep this packet current with
progress, discoveries, decisions, commands, evidence state, and blockers. The
author cannot accept their own work. Runtime-contract, security, and product
reviewers independently decide each matrix row and overall spike disposition.

The coordinator alone updates source ledgers, product/program/index records,
application adapters, object/scanner configuration, capability flags, normalized
contracts, or release scope. No worktree creation, push, merge, deployment,
publication, production mutation, credential collection, external purchase, or
destructive cleanup is authorized by this packet.
