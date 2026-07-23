---
packet_id: DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH
title: External dispatch - create exactly one safe draft pull request
status: ready-for-external-dispatch
base_commit: b2243109d0cfb2e093cc37a57017e8e70b5ea64b
branch: external/research/coding-github-contracts
owner: external-coding-github-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-GITHUB-001, SPIKE-GITHUB-PROXY-001, SPIKE-GITHUB-CI-001, AC-DW-CODE-002-01, AC-DW-CODE-002-02, AC-DW-CODE-002-03, AC-DW-CODE-002-04]
allowed_paths: [tools/contract-spikes/coding-github/**, docs/references/research/coding-github-contracts/**, docs/exec-plans/external/DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH.md]
dependencies: [DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH, SPIKE-SANDBOX-001, SPIKE-SANDBOX-002, SPIKE-EGRESS-001, SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, official-github-documentation-access, public-package-index-access, optional:non-production-github-app-and-classic-sandbox]
created: 2026-07-23
reviewed_at: 2026-07-23
review_result: accepted
---

# External dispatch - create exactly one safe draft pull request

## Dispatch identity

- Exact base SHA:
  `b2243109d0cfb2e093cc37a57017e8e70b5ea64b`.
- Branch to create:
  `external/research/coding-github-contracts`.
- ExecPlan: this file.
- This is GitHub/sandbox contract research and an isolated probe harness. It
  does not authorize application/provider implementation, a product PR workflow,
  automatic merge, repository administration, or capability enablement.
- A sanctioned live run may create exactly one draft pull request in one
  explicitly supplied disposable non-production repository. It may not create a
  second pull request, mark ready, approve, merge, bypass protection, force-push,
  publish, deploy, or mutate production.

## Purpose and observable result

Produce one source-precedence-aware contract corpus deciding
`SPIKE-GITHUB-001`, `SPIKE-GITHUB-PROXY-001`, and
`SPIKE-GITHUB-CI-001` for the pinned GitHub App, API client, selected classic
sandbox, and accepted sandbox/egress evidence.

When sanctioned live dependencies exist, the observable result is exactly one
reviewable draft pull request created from an authorized repository, immutable
base SHA, deterministic task branch, bounded synthetic change, and tested head
SHA. Clone/fetch/push and the permitted PR operation use short-lived GitHub App
installation authority through the verified sandbox auth-proxy path. No personal
access token or reusable installation token enters the browser, sandbox
environment, filesystem, process arguments/list, Git config/remotes, credential
helper, shell history, command output, snapshot, logs, traces, fixtures, or
evidence.

If any required dependency or authority is absent, create zero live pull requests,
complete public/generated/fake research, and mark live rows
`blocked-live-evidence`. A UI fixture, GitHub link, public clone, patch, or local
Git commit is not the requested live outcome.

## Allowed paths and exclusions

The worker may change only:

```text
tools/contract-spikes/coding-github/**
docs/references/research/coding-github-contracts/**
docs/exec-plans/external/DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH.md
```

The probe is one isolated Python/uv project with its own manifest, lock, tests,
schemas, validators, scrubber, synthetic Git server/webhook receiver, fake GitHub
API, and opt-in live profile. It must not import another repository project or
write a root/shared manifest or lock.

Application/package source, shared fixtures, root manifests/locks, product specs,
architecture, decisions, source ledger, generated docs, program/index records,
CI configuration, `docs/plans/**`, sandbox packet outputs, and review-surfaces
packet paths are read-only.

Explicitly out of scope:

- PATs, OAuth user tokens, SSH keys, credentials in sandbox state, broad
  installation grants, forks, stacked PRs, multi-repository work, or unrecognized
  existing branches;
- ready-for-review changes, reviews/approvals, workflow rerun/cancel mutations,
  merge queue enrollment, merge, branch deletion, force-push, or protection
  bypass;
- application GitHub callbacks/webhooks, UI, phone flow, persistence, deployment,
  release, or any `E2E-*` acceptance claim; and
- GitLab, Bitbucket, MDA/Fleet/private routes, or undocumented proxy endpoints.

## Exact dependencies and inherited blockers

This packet consumes, and never duplicates or silently widens, the accepted
artifacts from
`DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH`:

- reviewed commit SHA and `review.json`;
- `matrix-scope.json`, `matrix.json`, `versions.json`, and scope/fixture hashes;
- accepted provider create/command/file/cleanup rows;
- accepted task/thread/sandbox binding and expiry/recovery rows; and
- accepted allow-list, GitHub-destination, callback, redirect/DNS/port, and bypass
  rows.

The worker records these exact hashes in `upstream-lock.json`. A missing,
rejected, version-mismatched, or `blocked-live-evidence` upstream row is inherited
without promotion. It blocks the dependent live operation but does not block
offline GitHub contract inventory and negative harness tests.

Other pinned inputs are `SRC-LC` at
`7b9215d708e0b57e6fbae7b5d0762c4118b8e309`, `SRC-DA` at
`7794b61a6e76230e8c7a49bdce808b3728305914`, `SRC-LG` at
`31f90df3e6b0268fa77fd2d118a917d420b84a68`, official GitHub documentation,
installed/generated public clients/schemas, and, only for live acceptance:

- an explicitly supplied non-production GitHub App secret reference with minimum
  reviewed permissions and one selected disposable repository;
- the accepted non-production classic sandbox/auth-proxy profile matching
  `upstream-lock.json`; and
- synthetic repository content, actor/workspace/install/repository bindings,
  account tier/region/provider versions, and a recorded mutation authorization.

Evidence tiers are `accepted-live`, `installed-public`, `official-documented`,
`pinned-reference`, `deterministic-fake`, and `unknown`. Final row states are
`accepted-live`, `blocked-live-evidence`, `rejected`, or `unknown`. Only an
independently reviewed live transcript can accept a live installation/proxy/
push/PR/CI behavior.

## Authoritative checkout sources

Read these exact checkout-local authorities before acting:

- `AGENTS.md` and `docs/AGENTS.md`;
- `ARCHITECTURE.md`;
- `docs/PRODUCT_SENSE.md` and `docs/PLANS.md`;
- `docs/SECURITY.md` and `docs/RELIABILITY.md`;
- `docs/product-specs/coding/DW-CODE-002-github-auth-repository-pr-ci-merge.md`;
- `docs/product-specs/coding/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md`;
- `docs/product-specs/index.md` and
  `docs/product-specs/acceptance-scenarios.md`;
- `docs/design-docs/decisions/index.md`;
- `docs/references/source-ledger.md`; and
- `docs/exec-plans/templates/feature.md`.

If these sources, an upstream lock, or higher-precedence accepted evidence
disagree, stop the affected row and record the contradiction, owner, blocker, and
fallback. Do not edit an authority or upstream output from this packet.

## Required immutable scope and contract matrices

Retain `matrix-scope.json` before observations. It pins GitHub App permissions,
API versions/media types, client versions, sandbox/upstream hashes, repository
class, branch policy, required operations, negative cases, and one-draft-PR
mutation budget. The validator derives required rows from this scope. Public
contract discovery expands scope through review before results are recorded.

### GitHub installation, repository, ref, and draft-PR matrix

For `SPIKE-GITHUB-001`, cover:

- install/reconfigure/suspend/delete observations; callback state/expiry; selected
  account/repositories; current actor/workspace authorization; minimum permission
  categories; repository pagination/search; revoked or changed grants;
- installation-token audience, repository scope, permission scope, TTL, refresh/
  expiry/revocation, wrong installation/repository/actor/workspace, and rate-limit
  behavior without persisting a real token;
- immutable repository ID, base branch and base SHA preflight, branch-name
  sanitization, collision ours/unknown, create-ref idempotency, no overwrite, no
  force-push, and head reconciliation;
- clone/fetch, bounded synthetic edit/test, commit, push, and authoritative head
  re-fetch through the accepted proxy path;
- draft PR create/read/reconcile by repository/base/head/task identity, including
  timeout after remote success, repeated command, existing matching PR, wrong
  head/base, permission loss, provider error, and duplicate prevention; and
- supported merge methods plus repository protection and permission responses as
  non-mutating public/generated, deterministic-fixture, and read-only live rows.
  These rows do not grant merge authority or make a merge-readiness claim; and
- exactly-one mutation ledger behavior: absent authority creates zero PRs; an
  authorized live run creates or reconciles one matching draft PR and every
  subsequent run is read-only against that PR.

### Short-lived auth-proxy matrix

For `SPIKE-GITHUB-PROXY-001`, cover:

- provider-authenticated callback, sandbox/task/thread/repository/install binding,
  host/path/method/use/audience/scope/TTL, nonce, replay, concurrency, refresh,
  expiry, revocation, and policy update;
- HTTPS Git clone/fetch/push and the minimum permitted API operation through the
  callback, with redirects, alternate hosts/ports, Git submodules/LFS if detected,
  credential-helper behavior, and denial of every unapproved target/use;
- wrong tenant/workspace/actor/task/sandbox/repository, stale binding, expired
  sandbox, suspended installation, changed permission, branch protection, rate
  limit, and callback outage;
- leak scans over environment, filesystem, process list/arguments, Git config and
  remotes, credential helpers, shell history, stdout/stderr, command transcripts,
  snapshots, logs, traces, fixtures, errors, and evidence; and
- failure with no PAT, SSH key, token-in-environment/file/argument, or public-write
  fallback.

### CI and authoritative draft-PR evidence matrix

For `SPIKE-GITHUB-CI-001`, cover:

- signed webhook validation, timestamp/delivery dedupe, retry, duplicate,
  out-of-order, missing event, permission change, and bounded polling
  reconciliation;
- signature verification over raw bytes followed by binding to the expected
  GitHub App/installation, repository node ID/account, tenant/workspace, allowed
  event/action, PR/base/head identity, and current authorization before any
  projection; reject cross-installation/repository/tenant and mismatched-head
  events;
- check suites, check runs, commit statuses, actions/workflow association where
  public, required-check discovery, pending/success/failure/cancelled/neutral/
  skipped/unknown, stale head SHA, and fork/protection/merge-queue policy facts;
- workflow read, rerun, and cancel API availability, required permissions, rate
  limits, and error shapes as public/generated and deterministic-fixture rows;
- supported merge methods, protection/permission responses, merge request
  identity, and ambiguous/timeout reconciliation as contract-only rows. The
  fixture binds repository/PR/head/idempotency identity, re-reads authoritative
  open/merged state before any retry, and proves no second merge request; and
- the exact draft PR base/head, changed files, commit/test evidence, current check
  freshness, and authoritative external link; and
- read-only merge-readiness observations only. This packet performs no workflow
  mutation, review, approval, ready transition, merge, or branch deletion.

Polling/re-fetch is authoritative after webhook gaps or disagreement. Workflow
rerun/cancel and merge rows that require live mutation remain
`blocked-live-evidence` unless a separate future packet grants that exact
mutation; this packet cannot accept the full CI/merge gate from draft-PR reads.

## Exactly-one draft-PR protocol

The optional live profile must require a human-supplied `mutation-grant.json`
outside committed evidence. The grant contains a unique grant ID and exact
tenant/workspace/actor/installation/repository-node/task/base-ref/base-SHA/head-ref
tuple, allowed operations, maximum pull requests `1`, issuer, reviewer, and
expiry. It contains no secret and must be a regular non-symlink file with
restrictive ownership and mode.

Before mutation, the probe:

1. validates the exact grant tuple, file safety, expiry, issuer/reviewer, accepted
   upstream hashes, and current App/repository permission;
2. atomically claims the unique grant before any ref or PR mutation and rejects a
   concurrent/replayed claim or tuple mismatch;
3. lists matching task branches and open/closed PRs;
4. aborts on an unknown collision or any prior nonmatching probe PR;
5. confirms base SHA and deterministic head ref match the grant;
6. creates/reconciles the branch, runs bounded tests, and pushes through the
   accepted proxy; and
7. creates the draft PR with an idempotency identity, then reconciles on every
   timeout before any retry.

`live-mutation-ledger.json` records sanitized repository binding hash, task
identity, base/head refs and SHAs, PR node/number, draft state, request/reconcile
times, grant hash, and no secret. Once a PR identity is recorded or discovered,
the probe refuses any second create and performs read-only reconciliation. If the
first remote create might have succeeded but cannot be reconciled, final state is
blocked/unknown, the mutation budget is permanently treated as spent, and the
probe stops. Two-worker, replay, wrong-binding, unsafe-grant-file, and ambiguous
remote-create fixtures are mandatory.

## Required retained outputs

Under `docs/references/research/coding-github-contracts/`, retain:

- `matrix-scope.json`: immutable operation/permission/negative-case scope,
  mutation budget, upstream requirements, and scope hash;
- `upstream-lock.json`: accepted sandbox packet commit, reviewer verdict, matrix/
  scope/version/fixture hashes, and exact consumed rows;
- `matrix.json`: installation/repository/ref/proxy/PR/CI rows with evidence tier,
  exact versions, account/region/date, sanitized schemas/transcripts, hashes,
  conclusion, contradiction, inherited blocker, owner, fallback, and cleanup;
- `report.md`: minimum App manifest, proxy boundary, exactly-one PR result,
  contradictions, per-spike disposition, and downstream limits;
- `fixtures/`: fake GitHub/API/Git/webhook transcripts, timeout/idempotency races,
  leak negatives, hashes, and expected outcomes;
- `schemas/`: probe-only installation, repository/ref, proxy intent, PR, CI,
  webhook, mutation-ledger, and evidence schemas;
- `versions.json`: interpreter, packages, API versions, App permission manifest,
  sandbox/provider upstream pins, account tier/region/auth class/date;
- `live-mutation-ledger.json` when a live run is authorized, or a sanitized
  explicit `not-run` record when it is not;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero PATs, App keys, installation tokens, auth refs, raw
  headers/cookies, credential-bearing remotes/helpers, customer data, reusable
  endpoints, or unsanitized absolute paths; and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, per-row/per-spike state, and confirmation
  that the live mutation count is zero or exactly one.

The validator rejects absent/changed upstream hashes, blocked dependencies
promoted to accepted, missing scope rows, excessive App permissions, token
persistence/disclosure, PAT/SSH fallback, unknown branch overwrite, force-push,
non-atomic/replayed mutation grants, more than one PR identity/create attempt
without reconciliation, nondraft PR, cross-installation/repository/tenant webhook
projection, accepted CI from stale/nonmatching head, absent workflow/merge-timeout
contract rows, workflow/merge mutations, fake/public evidence promoted to live,
missing fallbacks, and unresolved precedence conflicts.

## Acceptance contribution and limits

| ID | Required evidence and limit |
|---|---|
| `SPIKE-GITHUB-001` | Installation, selected repository, minimum permissions, short-lived token, ref/commit/push, one idempotent draft PR, supported merge-method/protection/permission observations, revocation, audit, and negative permission rows are decided without granting merge authority. |
| `SPIKE-GITHUB-PROXY-001` | Private clone/fetch/push and a permitted API call use the accepted callback with complete scope/TTL/replay/redaction/leak negatives and no reusable credential in the sandbox. |
| `SPIKE-GITHUB-CI-001` | Signed and correctly bound webhook/polling/check/status/required-check/stale-head/protection/rate-limit plus workflow/merge-method/merge-timeout contract rows are complete. Live-required mutation rows remain blocked; no CI mutation or merge is authorized. |
| `AC-DW-CODE-002-01` | Supports the no-token private-repository path only; application/browser/persistence evidence remains downstream. |
| `AC-DW-CODE-002-02` | Supports timeout reconciliation to one draft PR only; application idempotency remains downstream. |
| `AC-DW-CODE-002-03` | Supports current-head/check/protection facts only; phone confirmation and merge remain downstream. |
| `AC-DW-CODE-002-04` | Supports proxy-unavailable/no-token-fallback behavior only; product fallback rendering remains downstream. |

This packet does not satisfy `E2E-V1-04-CREDENTIAL-BOUNDARY`,
`E2E-V1-07-CODING-DRAFT-PR`, responsive review, or release acceptance.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/coding-github
uv sync --project tools/contract-spikes/coding-github --frozen
uv run --project tools/contract-spikes/coding-github --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.inventory --output docs/references/research/coding-github-contracts/versions.json
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.validate_matrix docs/references/research/coding-github-contracts/matrix.json --scope docs/references/research/coding-github-contracts/matrix-scope.json --upstream-lock docs/references/research/coding-github-contracts/upstream-lock.json --require-complete-cross-product --require-workflow-and-merge-timeout-fixtures --max-draft-prs 1 --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.scrub docs/references/research/coding-github-contracts
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.validate_scope --base b2243109d0cfb2e093cc37a57017e8e70b5ea64b --include-untracked
uv lock --project tools/contract-spikes/coding-github --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/coding-github --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check b2243109d0cfb2e093cc37a57017e8e70b5ea64b...HEAD
git diff --name-only b2243109d0cfb2e093cc37a57017e8e70b5ea64b
git status --short
```

Only with accepted upstream artifacts and an explicit non-production mutation
grant, run:

```bash
uv run --project tools/contract-spikes/coding-github --frozen pytest -m live_contract --live-profile non-production-github-draft-pr --mutation-grant /approved/non-production/mutation-grant.json --evidence-dir docs/references/research/coding-github-contracts/live
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.validate_live_ledger docs/references/research/coding-github-contracts/live-mutation-ledger.json --max-draft-prs 1 --require-draft --forbid-merge
uv run --project tools/contract-spikes/coding-github --frozen python -m coding_github_spikes.scrub docs/references/research/coding-github-contracts/live
```

The live command fails closed when the grant, GitHub App, repository, sandbox,
accepted upstream hash, or exact permission is absent. It never prints or
persists a PAT, App key, installation token, raw header/cookie, credential-bearing
remote, reusable endpoint, customer content, or environment dump.

## Deterministic fallback, recovery, and idempotence

Until every required row and dependency is independently accepted:

- disable GitHub commit/push/PR actions for private repositories;
- inject no GitHub credential into an environment and accept no PAT;
- retain a source-native/local coding path, downloadable patch or artifact, and
  external GitHub link only where separately authorized;
- show the last verified PR/CI event as stale or unknown, never green by default;
  and
- perform no merge-readiness, workflow mutation, approval, or merge action.

Repeated offline runs are deterministic. Live retries read
`live-mutation-ledger.json` and authoritative GitHub state before any mutation.
An ambiguous timeout reconciles or stops blocked; it never spends a second PR
budget. Evidence and the draft PR remain for independent review. Closing the PR or
deleting the branch is a separate external mutation requiring coordinator
authority and is not authorized here.

## Handoff and independent review

Commit only allowed paths on the named branch and keep the packet current with
progress, upstream hashes, versions, mutation count, commands, contradictions,
and blockers. The author cannot accept their own evidence.

Runtime-contract review owns GitHub/API/App/version and sandbox-proxy behavior.
Security review owns least privilege, secret absence, callback/egress/replay,
tenant/repository binding, webhook, and mutation-budget conclusions. Product
review owns whether exactly one draft PR is reviewable and whether every
unavailable/stale state is honest. All three record verdicts in `review.json`.

The coordinator alone may update the source ledger, decision register, product
specs, application/runtime code, capability manifest, program/index, or release
state. No unassigned worktree, push from this planning packet, merge, deployment,
publication, production mutation, credential collection, or self-approval is
authorized.
