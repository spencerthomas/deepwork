---
packet_id: DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS
title: External dispatch - add a file to the first task safely
status: in-progress
base_commit: fff1bfd278d550d01de6e8d74f553f45c4003a8c
branch: external/research/first-task-safe-attachments
owner: external-attachment-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-ATTACH-001, AC-DW-TASK-002-03, AC-DW-QUAL-001-03, AC-DW-QUAL-001-04]
allowed_paths: [tools/contract-spikes/attachments/**, docs/references/research/attachment-contract-spikes/**, docs/exec-plans/external/DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS.md]
dependencies: [SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:non-production-classic-object-scanner-runtime]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
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

The credential-free fixture/demo and bounded pasted-text path remain usable while
this work is open. This packet is supporting evidence only: it neither blocks nor
satisfies the clean-account, API-key, source-registration, and first-value journey
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

Before any observation or probe, commit an immutable `matrix-scope.json`. The
scope file pins the package/service versions being examined and defines the full
required cross-product. `validate_matrix` derives required row identities from
that file; it must not trust worker-selected rows in `matrix.json`.

The pre-observation dimensions are:

- media class: bounded text file, image, PDF, and code;
- byte owner/boundary: Deep Work quarantine/object boundary;
- target source: the public Classic LangSmith baseline only;
- lifecycle operation: preflight, quarantine create, metadata/hash/detected type,
  scan, transfer intent, every discovered public transfer representation,
  transfer receipt/rejection, remove, retention expiry, deletion, orphan cleanup,
  retry, restart/recovery, and unavailable/error;
- evidence tier and expected conclusion state, including unsupported and unknown.

MDA and Fleet are explicitly excluded. A newly discovered public Classic transfer
representation expands the immutable scope through a reviewed scope revision
before observations are recorded; it cannot be omitted because it failed or was
unsupported. Version pins and scope hash are retained in every matrix row.

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

- `matrix-scope.json`: immutable pre-observation version pins and the required
  media/boundary/source/lifecycle/representation/evidence cross-product;
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

The matrix validator derives the complete row set from `matrix-scope.json` and
rejects missing or extra unreviewed rows, omitted unsupported/unknown conclusions,
missing discovered Classic transfer representations, MDA/Fleet rows, duplicate
row identities, unknown statuses, absent evidence provenance, accepted-live rows
without live metadata, deterministic-fake rows labeled as provider proof, missing
fallbacks, or unresolved source-precedence conflicts.

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

No row blocks or satisfies `E2E-V1-01-FIRST-VALUE`. The credential-free
fixture/demo and bounded pasted-text path remain usable independently; the clean
account, API-key, source-registration, and first-value journey needs its own
end-to-end evidence.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/attachments
uv sync --project tools/contract-spikes/attachments --frozen
uv run --project tools/contract-spikes/attachments --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.inventory --output docs/references/research/attachment-contract-spikes/versions.json
uv run --project tools/contract-spikes/attachments --frozen python -m attachment_contract_spikes.validate_matrix docs/references/research/attachment-contract-spikes/matrix.json --scope docs/references/research/attachment-contract-spikes/matrix-scope.json --require-complete-cross-product --reject-unresolved-precedence-conflicts
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
- keep the credential-free fixture/demo, bounded pasted-text path, and unrelated
  Wave 1 work moving.

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

## Progress

- [x] 2026-07-23: Verified the exact clean worktree, branch
  `external/research/first-task-safe-attachments`, seed
  `e0f1087b3fd6af530288fb18e3213c7c08459add`, and base ancestry from
  `fff1bfd278d550d01de6e8d74f553f45c4003a8c`.
- [x] 2026-07-23: Read the repository and documentation instructions, this full
  packet, and the canonical architecture, product, security, reliability,
  attachment, quality, acceptance, glossary, and source-ledger references.
- [x] 2026-07-23: Verified the read-only `SRC-LC`, `SRC-DA`, and `SRC-LG`
  checkouts at their exact pinned commits.
- [x] 2026-07-23: Created the isolated project manifest and locked only its
  credential-free test dependency set using CPython 3.12.11.
- [x] Freeze the immutable pre-observation scope and generate the complete
  derived matrix without narrowing unsupported or unknown rows.
- [x] Complete the deterministic no-network adapters, harmless fixtures, and
  negative/recovery tests.
- [x] Generate retained inventory, scrub, command, and report evidence; the
  review record is staged with pending independent dispositions.
- [x] Run every required validation, offline replay, scope, documentation, and
  base-qualified diff command.
- [ ] Resolve findings, obtain a fresh independent review, and commit only the
  allowed paths.

## Surprises and discoveries

- The pinned Classic Agent Server contract accepts graph-defined JSON input; the
  public generic server API does not establish a source-independent attachment
  upload endpoint or media schema.
- Pinned LangChain documentation defines standard message content blocks for
  plain text, image, and generic file data using inline data, URL, and
  provider-managed identifiers. That public message representation is not by
  itself proof that a selected deployed graph, model, authorization boundary, or
  Classic account accepts or safely retains any attachment.
- No sanctioned non-production object store, scanner, or Classic runtime profile
  was supplied with this dispatch. All rows needing hosted behavior therefore
  remain `blocked-live-evidence`; the live suite is not authorized to run.
- The immutable scope derives 912 rows: four media classes by two Deep Work byte
  boundaries by one Classic baseline by 38 lifecycle/abuse operations by three
  candidate content representations. The decided distribution is 624
  `accepted-fixture-only`, 240 `blocked-live-evidence`, 16 `rejected`, 24
  `unknown`, and 8 `unsupported`, with zero `accepted-live`.
- The exact root-invoked pytest command initially selected the repository test
  configuration. A project-owned pytest plugin now confines collection to the
  isolated spike tests without modifying shared configuration.

## Decision log

- 2026-07-23: Keep the project dependency-light and deterministic. Standard
  library code owns the matrix, fake adapters, inventory, and scrubber; the only
  test dependency is exactly pinned.
- 2026-07-23: Treat each discovered standard content-block form as a candidate
  representation that expands the matrix. Do not promote it to an accepted
  Classic transfer contract without graph, model, account, and live cleanup
  evidence.
- 2026-07-23: Preserve the packet fallback for every unaccepted media/source row:
  attachment capability remains disabled and bounded pasted text remains the
  separately validated path.
- 2026-07-23: Commit `matrix-scope.json` alone before matrix generation. Its
  validator compares the current bytes with the immutable add-commit blob and
  rejects any observation commit that precedes or shares that add commit.
- 2026-07-23: Treat deterministic `clean` as necessary but insufficient. Only a
  separately bound transfer intent can move a fake object to transfer-ready, and
  hosted behavior remains unaccepted.

## Outcomes and retrospective

The immutable scope and complete 912-row matrix are retained with deterministic
no-network policy, quarantine, scanner-input, authorization, transfer, deletion,
retry, and restart fixtures. All required ordinary, offline, scope, scrub,
documentation, and base-qualified validation commands pass. Independent
runtime-contract, security, and product review remains before final handoff.

No attachment capability is enabled. Hosted object-store, scanner, and Classic
runtime rows remain blocked without sanctioned non-production access. The
credential-free fixture/demo and bounded pasted-text path remain usable. This
packet remains supporting evidence only and neither blocks nor satisfies
`E2E-V1-01-FIRST-VALUE`.
