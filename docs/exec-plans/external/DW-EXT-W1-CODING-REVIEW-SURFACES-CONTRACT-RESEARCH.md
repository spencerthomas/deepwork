---
packet_id: DW-EXT-W1-CODING-REVIEW-SURFACES-CONTRACT-RESEARCH
title: External dispatch - prove exact files and diff with honest runtime surfaces
status: prepared-for-independent-review
base_commit: b2243109d0cfb2e093cc37a57017e8e70b5ea64b
branch: external/research/coding-review-surfaces-contracts
owner: external-coding-review-surfaces-contract-researcher
reviewers: [runtime-contracts, security, product]
risk: high
acceptance_ids: [SPIKE-FILES-001, SPIKE-TERMINAL-001, SPIKE-BROWSER-001, AC-DW-CODE-003-01, AC-DW-CODE-003-02, AC-DW-CODE-003-03, AC-DW-CODE-003-04, AC-DW-CODE-003-05]
allowed_paths: [tools/contract-spikes/coding-review-surfaces/**, docs/references/research/coding-review-surfaces-contracts/**, docs/exec-plans/external/DW-EXT-W1-CODING-REVIEW-SURFACES-CONTRACT-RESEARCH.md]
dependencies: [DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH, DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH, SPIKE-SANDBOX-001, SPIKE-SANDBOX-002, SPIKE-EGRESS-001, SPIKE-GITHUB-001, SPIKE-GITHUB-PROXY-001, SPIKE-GITHUB-CI-001, SRC-LC@7b9215d708e0b57e6fbae7b5d0762c4118b8e309, SRC-DA@7794b61a6e76230e8c7a49bdce808b3728305914, SRC-LG@31f90df3e6b0268fa77fd2d118a917d420b84a68, public-package-index-access, official-documentation-access, optional:accepted-non-production-sandbox-and-draft-pr-evidence]
created: 2026-07-23
reviewed_at: null
review_result: pending
---

# External dispatch - prove exact files and diff with honest runtime surfaces

## Dispatch identity

- Exact base SHA:
  `b2243109d0cfb2e093cc37a57017e8e70b5ea64b`.
- Branch to create:
  `external/research/coding-review-surfaces-contracts`.
- ExecPlan: this file.
- This is contract research and an isolated probe harness. It does not authorize
  file-browser/diff/terminal/browser UI, application endpoints, provider adapters,
  interactive local control, phone implementation, or capability enablement.
- The packet consumes the accepted sandbox and GitHub packet evidence. It does
  not recreate their sandboxes, create another pull request, rerun CI, approve,
  merge, or mutate the reviewed repository.

## Purpose and observable result

Produce a version-pinned, independently reviewable corpus deciding
`SPIKE-FILES-001`, `SPIKE-TERMINAL-001`, and `SPIKE-BROWSER-001`.

The observable result is a reviewer can inspect one immutable evidence bundle and
verify:

1. the exact task/repository/sandbox identity and exact base/head SHAs;
2. a bounded file tree and file contents tied to source identity, path policy,
   checksum, encoding/media metadata, freshness, and expiry;
3. a changed-file summary and diff whose paths, statuses, renames, binary facts,
   hunks, additions/deletions, and checksum all match that exact base/head pair;
4. whether runtime command evidence is a read-only transcript, reviewed discrete
   command stream, or a real PTY, with unsupported controls absent; and
5. whether browser capability is verified evidence, an authorized expiring
   service URL, or `none`, with an ordinary external link never mislabeled as
   browser/computer-use evidence.

The corpus must remain useful when Terminal or Browser is unavailable. Missing
public/live proof yields an explicit unavailable/fallback row, never a simulated
tab, screenshot, action timeline, live terminal, or browser session.

## Allowed paths and exclusions

The worker may change only:

```text
tools/contract-spikes/coding-review-surfaces/**
docs/references/research/coding-review-surfaces-contracts/**
docs/exec-plans/external/DW-EXT-W1-CODING-REVIEW-SURFACES-CONTRACT-RESEARCH.md
```

The probe is one isolated Python/uv project with its own manifest, lock, tests,
schemas, validators, scrubber, deterministic fake file/Git/command/browser
adapters, and network-denied offline suite. It must not import another repository
project or write a root/shared manifest or lock.

Application/package source, root manifests/locks, product specs, architecture,
decisions, source ledger, generated docs, program/index records, CI,
`docs/plans/**`, and the two upstream packet output trees are read-only.

Explicitly out of scope:

- application file/diff/session endpoints, web/PWA/Tauri/phone UI, file editing,
  GitHub review comments, IDE/editor integration, and artifact-catalog ownership;
- local/host filesystem browsing or commands, active HTML/SVG/script rendering,
  auto-opened URLs, mobile terminal/control, or unbounded downloads/output;
- creating/updating a branch or PR, workflow mutation, review, approval, merge,
  deployment, release, credential use, or customer content; and
- any `E2E-*` or full accessibility/performance/application acceptance claim.

## Exact dependencies and inherited blockers

This packet consumes exact reviewed artifacts from both prior packets.

From `DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH`:

- reviewed commit/reviewer verdict and matrix/scope/version/fixture hashes;
- accepted sandbox identity, file/command operation, TTL/expiry, cleanup, and
  task/thread binding rows; and
- accepted egress/service-URL/origin/callback rows relevant to runtime panels.

From `DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH`:

- reviewed commit/reviewer verdict and matrix/scope/version/fixture hashes;
- sanitized repository binding, exact base/head refs and SHAs, draft PR identity,
  changed-file/commit/check provenance, and mutation-ledger hash; and
- accepted authorization/proxy facts needed to read repository/PR evidence.

The worker records both sets in `upstream-lock.json`. It verifies hashes and
version compatibility before any dependent row. Missing, rejected, incompatible,
unknown, or `blocked-live-evidence` inputs are inherited and cannot be promoted by
a deterministic adapter or a visually plausible diff. Offline schema/fallback/
negative work may proceed while live-dependent rows remain blocked.

Other pinned inputs are `SRC-LC` at
`7b9215d708e0b57e6fbae7b5d0762c4118b8e309`, `SRC-DA` at
`7794b61a6e76230e8c7a49bdce808b3728305914`, `SRC-LG` at
`31f90df3e6b0268fa77fd2d118a917d420b84a68`, official documentation,
installed/generated public clients/schemas, and only with a fresh read grant, the
same non-production sandbox/repository/PR.

Accepted upstream evidence proves a contract; it does not authorize a new
external read. The live profile requires a current read-only grant outside
committed evidence, bound to exact tenant/workspace/actor/task/sandbox/repository/
PR/base/head identities and permitted operations, with unique grant ID, issuer,
reviewer, and expiry but no secret. Revalidate current provider/GitHub permissions
before every read. Stale upstream evidence, changed head, revoked permission,
unsafe grant file, or absent/expired grant fails closed without credential use.

Evidence tiers are `accepted-live`, `installed-public`, `official-documented`,
`pinned-reference`, `deterministic-fake`, and `unknown`; final row states are
`accepted-live`, `blocked-live-evidence`, `rejected`, or `unknown`. A fake
transcript proves rendering/schema fallbacks only.

## Authoritative checkout sources

Read these exact checkout-local authorities before acting:

- `AGENTS.md` and `docs/AGENTS.md`;
- `ARCHITECTURE.md`;
- `docs/PRODUCT_SENSE.md` and `docs/PLANS.md`;
- `docs/SECURITY.md` and `docs/RELIABILITY.md`;
- `docs/product-specs/coding/DW-CODE-003-files-diff-terminal-browser-phone.md`;
- `docs/product-specs/coding/DW-CODE-001-sandbox-environments-snapshots-setup-egress.md`
  and
  `docs/product-specs/coding/DW-CODE-002-github-auth-repository-pr-ci-merge.md`;
- `docs/product-specs/index.md` and
  `docs/product-specs/acceptance-scenarios.md`;
- `docs/design-docs/decisions/index.md`;
- `docs/references/source-ledger.md`; and
- `docs/exec-plans/templates/feature.md`.

If these sources, an upstream lock, or higher-precedence accepted evidence
disagree, stop the affected row and record the contradiction, owner, blocker, and
fallback. Do not edit an authority or upstream output from this packet.

## Required immutable scope and matrices

Retain `matrix-scope.json` before observations. It pins upstream hashes, SDK/
provider/Git versions, source priority, file/media/path/size classes, base/head
pair, terminal modes, browser modes, negative cases, and required row IDs. The
validator derives completeness from this file. Newly discovered public operations
or modes require a reviewed scope revision before their result is recorded.

### Files and exact-diff matrix

For `SPIKE-FILES-001`, cover:

- root and paged directory list, stable ordering/cursor, empty directory, nested
  scale, file metadata, safe text/code read, encoding/BOM/newline, supported image/
  PDF metadata, binary/unknown/large/truncated content, download/range if public,
  and checksum/freshness;
- normalized relative path/opaque reference, NUL/absolute/traversal rejection,
  Unicode/case ambiguity, symlink/hard-link escape, directory/file confusion,
  guessed ID, wrong tenant/task/sandbox/repository, expired signed reference, and
  provider error;
- declared/detected MIME mismatch, polyglot, active HTML/SVG, hostile or malformed
  PDF/image, decompression amplification, bidi/control characters in filenames
  and paths, and decode/parse byte/time/dimension/page limits;
- changed-during-list/read, sandbox expiring/expired/deleted, repository head
  movement, permission revocation, restart/reconnect, and fallback source
  selection;
- exact Git base/head resolution, merge-base assumptions, changed-file status,
  added/modified/deleted/renamed/copied/type-change/submodule where supported,
  binary facts, additions/deletions, patch/hunk ordering, no-newline markers,
  large-diff bounds, path quoting, and diff checksum;
- sandbox working-tree versus exact Git commit/PR source. Each result names its
  authority and freshness; uncommitted sandbox files never appear as committed
  head evidence; and
- mutation races proving a file/diff/comment anchor cannot silently cross from
  head SHA A to head SHA B.

Bounds are enforced before decode or parse. Unsupported or failed validation
produces metadata-only/download handoff where independently authorized, never
inline rendering. The report must define a deterministic source order: accepted authorized sandbox
API for current working files, exact GitHub commit/PR API for committed base/head,
then metadata-only artifact/source link. It must not merge bytes from different
freshness or identity into one asserted file/diff document.

### Terminal-mode matrix

For `SPIKE-TERMINAL-001`, retain the canonical public capability:

```text
terminal: interactive | transcript | none
```

Record an orthogonal probe fact:

```text
commandInput: pty | discrete_reviewed | none
```

Cover command/source identity, authorization, open/start, input, stdout/stderr
ordering, exit, reconnect, cursor/sequence, truncation/download, timeout, cancel,
close, expiry, concurrent viewers/sessions, permission change, cleanup, and audit.
Bind open/input/reconnect/resize/cancel/close to tenant/workspace/actor/task/
sandbox/session/audience/expiry with short-lived non-replayable channel authority.
Reject cross-actor/session, wrong Origin, replay, expired grant, and concurrent
controller negatives. Every discrete command or input is an explicit audited user
action.

For claimed PTY support, also prove TTY allocation, resize, control sequences,
input echo, process/session lifetime, reconnect, and close semantics.

If only command run/reconnect exists, the accepted outcome is transcript plus a
separately reviewed discrete command action:
`terminal: transcript`, `commandInput: discrete_reviewed`. It must not expose PTY
keystroke, resize, shell-prompt, or "live terminal" claims. `terminal:
interactive` requires `commandInput: pty`; `terminal: none` requires
`commandInput: none`. Every command executes only in the upstream-locked sandbox;
never on FastAPI, Next.js, Tauri, the probe runner, or a contributor device.

Transcript/content rows include ANSI CSI/OSC, terminal hyperlinks, cursor/control
escapes, bidi/control text, hostile prompts, and oversized escape sequences.
Unsupported or unsafe output renders as bounded escaped plain text with explicit
truncation, never as active terminal markup or a clickable injected link.

### Browser-mode matrix

For `SPIKE-BROWSER-001`, classify the source as exactly one of:

```text
evidence | service_url | none
```

For evidence, cover session/evidence ID, task/sandbox identity, origin, actor/
controller, capture time, live/stale state, action/event provenance, screenshot
hash/media metadata, expiry, reconnect, authorization, and mobile read behavior.

For service URLs, cover provider-supported service binding, exact allowed origin/
port, audience, signed/opaque authorization, TTL, refresh/revocation, redirect,
permission loss, sandbox expiry, logging/redaction, user confirmation, and no
automatic open. Prove whether the URL is merely an external link or conveys any
browser-control/evidence contract.

For unsupported, unknown, blocked, or permission-denied capability, record
`browser: none`. Do not retain a placeholder screenshot or model-authored action
timeline. Normal repository/docs/app URLs remain labelled external links.

## Required cross-surface scenarios

The deterministic and accepted-live corpus must include:

- path traversal, absolute path, NUL, and symlink escape all rejected before bytes
  leave the selected task workspace;
- file mutation during read marks the view stale and never combines metadata and
  bytes from different versions;
- exact base/head SHA A diff matches Git/source authority; after head advances to
  B, A remains immutable evidence and any A-bound comment/mutation is blocked;
- binary, rename, deletion, no-newline, large file, large diff, and unavailable
  content remain exact without fabricated lines;
- MIME mismatch/polyglot, active HTML/SVG, malformed PDF/image, decompression,
  bidi/control-path, ANSI/OSC/link, and terminal-escape fixtures fail closed before
  unsafe inline rendering or parsing;
- command run/reconnect with no PTY produces transcript/discrete-command evidence
  and no PTY controls;
- transcript truncation states exact omitted bounds and safe retrieval behavior;
- terminal disconnect does not claim the process stopped;
- `browser: none` produces no Browser evidence while an external URL stays an
  external link;
- expired service URL/evidence cannot be refreshed or replayed across actor/task/
  sandbox; and
- upstream sandbox expiry leaves committed exact-SHA GitHub evidence readable
  where authorized, while mutable working files are unavailable/stale.

## Required retained outputs

Under `docs/references/research/coding-review-surfaces-contracts/`, retain:

- `matrix-scope.json`: immutable file/diff/terminal/browser dimensions, upstream
  requirements, base/head pair, version pins, and scope hash;
- `upstream-lock.json`: both reviewed packet commits/verdicts and exact matrix/
  scope/version/fixture/mutation-ledger hashes and consumed rows;
- `matrix.json`: file/diff/terminal/browser rows with source identity, evidence
  tier, versions/date, sanitized schemas/transcripts, checksums, conclusion,
  contradiction, inherited blocker, owner, fallback, and cleanup;
- `report.md`: exact file/diff contract, source/freshness rules, terminal/browser
  capability table, contradictions, per-spike disposition, and downstream limits;
- `fixtures/`: bounded file trees/content, Git histories/patches, path negatives,
  mutation races, transcripts/PTY negatives, browser/service-URL evidence,
  hashes, and expected outcomes;
- `schemas/`: probe-only file node/content, diff document/hunk, runtime
  capability, command transcript/session, browser evidence/service URL, and
  evidence schemas;
- `versions.json`: interpreter, packages, sandbox/GitHub/provider/Git versions,
  upstream commits/hashes, account tier/region/auth class/date;
- `commands.txt`: exact commands and exit statuses without environment dumps;
- `scrub-report.json`: zero credentials/auth refs, raw headers/cookies, customer
  data, reusable signed URLs/endpoints, active HTML/script, control-sequence abuse,
  host/cross-workspace paths, or unsanitized absolute paths; and
- `review.json`: independent runtime-contract, security, and product verdicts,
  finding resolutions, reviewed commit, per-row/per-spike state, exact accepted
  capability values, read/terminal grant hashes, and confirmation of no persistent
  repository/PR/CI/browser mutation.

The validator rejects changed/missing upstream hashes, blocked inputs promoted to
accepted, mixed file authorities/freshness, path escapes, exact-diff mismatch,
fabricated binary/hunk data, unsafe content parsed/rendered inline, active ANSI/
OSC/link output, stale-head mutation acceptance, transcript labeled PTY,
noncanonical terminal capability values, browser link labeled evidence,
placeholder/simulated browser output, application/device-host command execution,
missing/current-authority grant, live acceptance from fake/public evidence,
missing fallbacks, or unresolved precedence conflicts.

## Acceptance contribution and limits

| ID | Required evidence and limit |
|---|---|
| `SPIKE-FILES-001` | List/read/download, encoding/media/binary, symlink/traversal, size, rename, mutation race, expiry, and exact-base/head diff rows are independently decided. |
| `SPIKE-TERMINAL-001` | Canonical `terminal` is honestly classified as interactive, transcript, or none; orthogonal command input is pty, discrete reviewed, or none with authorization/order/reconnect/truncation/TTL/close evidence appropriate to both facts. |
| `SPIKE-BROWSER-001` | The source is honestly classified as evidence, service URL, or none with auth/origin/expiry/control/provenance/mobile facts appropriate to that mode. |
| `AC-DW-CODE-003-01` | Supports server-side path-boundary contract evidence only; application authorization remains downstream. |
| `AC-DW-CODE-003-02` | Supports exact-head diff/anchor staleness only; application review-comment persistence/steering remains downstream. |
| `AC-DW-CODE-003-03` | Supports the honest terminal fallback only; product terminal rendering/control remains downstream. |
| `AC-DW-CODE-003-04` | Supports exact files/diff/PR/CI evidence consumed by phone review; responsive UI, approvals, and merge remain downstream. |
| `AC-DW-CODE-003-05` | Supports browser-none/no-simulation behavior only; product capability rendering remains downstream. |

This packet does not satisfy `E2E-V1-07-CODING-DRAFT-PR`,
`E2E-V1-08-RESPONSIVE-ACCESS`, `E2E-V1-09-SECURITY-RECOVERY`, or release
acceptance.

## Exact validation commands

The worker must implement and run:

```bash
uv lock --project tools/contract-spikes/coding-review-surfaces
uv sync --project tools/contract-spikes/coding-review-surfaces --frozen
uv run --project tools/contract-spikes/coding-review-surfaces --frozen pytest -m 'not live_contract'
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.inventory --output docs/references/research/coding-review-surfaces-contracts/versions.json
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.validate_matrix docs/references/research/coding-review-surfaces-contracts/matrix.json --scope docs/references/research/coding-review-surfaces-contracts/matrix-scope.json --upstream-lock docs/references/research/coding-review-surfaces-contracts/upstream-lock.json --require-complete-cross-product --require-exact-diff --reject-blocked-dependency-promotion --reject-simulated-capabilities --reject-unresolved-precedence-conflicts
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.scrub docs/references/research/coding-review-surfaces-contracts
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.validate_scope --base b2243109d0cfb2e093cc37a57017e8e70b5ea64b --include-untracked
uv lock --project tools/contract-spikes/coding-review-surfaces --check --offline
UV_OFFLINE=true uv run --project tools/contract-spikes/coding-review-surfaces --frozen pytest -m 'not live_contract'
python3 tools/docs/generate.py --check
python3 tools/docs/check.py
git diff --check b2243109d0cfb2e093cc37a57017e8e70b5ea64b...HEAD
git diff --name-only b2243109d0cfb2e093cc37a57017e8e70b5ea64b
git status --short
```

Only when both upstream packets are independently accepted, their non-production
evidence is available, and a fresh exact read-only grant is supplied, run:

```bash
uv run --project tools/contract-spikes/coding-review-surfaces --frozen pytest -m live_contract --live-profile accepted-non-production-review-evidence --read-grant /approved/non-production/read-grant.json --evidence-dir docs/references/research/coding-review-surfaces-contracts/live
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.verify_exact_diff docs/references/research/coding-review-surfaces-contracts/live --upstream-lock docs/references/research/coding-review-surfaces-contracts/upstream-lock.json
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.scrub docs/references/research/coding-review-surfaces-contracts/live
```

If the public contract exposes interactive or discrete input and a separate exact,
fresh, non-production terminal grant is supplied, run one bounded synthetic
session outside the reviewed repository working tree:

```bash
uv run --project tools/contract-spikes/coding-review-surfaces --frozen pytest -m terminal_live_contract --live-profile accepted-non-production-terminal --read-grant /approved/non-production/read-grant.json --terminal-grant /approved/non-production/terminal-grant.json --evidence-dir docs/references/research/coding-review-surfaces-contracts/live/terminal
uv run --project tools/contract-spikes/coding-review-surfaces --frozen python -m coding_review_surface_spikes.scrub docs/references/research/coding-review-surfaces-contracts/live/terminal
```

The terminal grant binds tenant/workspace/actor/task/sandbox/session/audience,
allowed synthetic commands/input/resize/reconnect/close, issuer/reviewer, and
expiry with no secret. The test proves cleanup and no repository/PR/CI mutation.
Without this grant, interactive/input rows remain `blocked-live-evidence`.
Browser control is not authorized by this packet; any control-required row remains
blocked and production capability is `browser: none`.

Both live profiles fail closed for missing/rejected/mismatched upstream evidence,
unsafe/expired grants, or revoked current permission. They perform no branch, PR,
CI, review, approval, merge, browser-control, or deployment mutation and never
print or persist credentials, raw headers/cookies, reusable URLs/endpoints,
customer content, unsafe active content, or environment dumps.

## Deterministic fallback, recovery, and idempotence

Until each row is independently accepted:

- files/diff fall back to exact authorized GitHub commit/PR evidence, then
  metadata-only artifact/source links; no file browser or diff is claimed when
  exact evidence is absent;
- Terminal shows an accepted read-only transcript, optionally a separately
  accepted discrete command action, or `none`; it never implies a PTY;
- Browser is `none`; an ordinary URL remains an external link;
- stale/expired/permission-denied content removes mutation/session controls and
  preserves only authorized immutable evidence; and
- task messages, artifacts, approvals, and external PR handoff remain independent.

Offline reruns are deterministic. Review-evidence live runs are read-only and bind
every request to `upstream-lock.json`. The terminal live profile may perform only
the terminal grant's bounded synthetic ephemeral session actions and remains
read-only with respect to repository, PR, CI, browser, deployment, and all other
persistent external state. Changed upstream state creates a new blocked/stale
observation rather than overwriting reviewed evidence. Interrupted reads may be
retried, but bytes, metadata, and diff hunks from different versions are never
combined.

## Handoff and independent review

Commit only allowed paths on the named branch and keep this packet current with
progress, upstream hashes, versions, capability classifications, commands,
contradictions, and blockers. The author cannot accept their own evidence.

Runtime-contract review owns provider/file/Git/command/browser public-surface and
version conclusions. Security review owns path/symlink/content/ANSI/service-URL,
tenant/task binding, command-host, origin/expiry, redaction, and no-mutation
conclusions. Product review owns exact-review usefulness and honest unavailable/
stale/fallback language. All three record verdicts in `review.json`.

The coordinator alone may update the source ledger, decisions, product specs,
application/runtime/UI code, capability manifest, program/index, or release state.
No worktree creation outside the assigned branch, push, merge, deployment,
publication, production mutation, credential collection, or self-approval is
authorized.
