# Coding review surfaces contract report

Date: 2026-07-23  
Evidence class: deterministic offline corpus plus pinned checkout metadata  
Live status: blocked  
E2E credit: zero

## Outcome

The offline probe is complete and deterministic. It proves the fail-closed
schemas, fake adapters, malicious-input fixtures, exact fake diff, transcript
sanitization, capability enums, immutable scope, upstream locks, and evidence
scrub required by the packet.

It does not accept a live file tree, file read, GitHub diff, terminal, browser
evidence, or service URL. The two mandatory upstream branches contain only their
dispatch packets. They contain no independently reviewed output matrices,
versions, fixtures, mutation ledger, hashes, or review verdicts. No current
read-only grant or separate terminal grant was supplied. The live profiles were
therefore not run.

Final spike states:

| Spike | State | Accepted product capability from this packet | Deterministic fallback |
|---|---|---|---|
| `SPIKE-FILES-001` | `blocked-live-evidence` | `files: none`, `diff: none` | Exact authorized commit/PR evidence if separately available, otherwise metadata-only source handoff |
| `SPIKE-TERMINAL-001` | `blocked-live-evidence` | `terminal: none`, `commandInput: none` | A transcript/discrete-command fixture proves schema behavior only; it does not enable Terminal |
| `SPIKE-BROWSER-001` | `blocked-live-evidence` | `browser: none` | Ordinary destinations remain external links and are never Browser evidence |

## Immutable identity and locks

The assigned checkout was verified before implementation:

- exact base: `b2243109d0cfb2e093cc37a57017e8e70b5ea64b`;
- exact seed: `f3d937f5e10819d09a46c94e046993fe40a28ab1`;
- named branch: `external/research/coding-review-surfaces-contracts`;
- scope hash:
  `629080c0b88a9d65b5f67735971639951de7db6f6ca39d2905483d77f9b24317`;
- upstream lock hash:
  `7f71e0a4196a895618d00c070f90366b9e81b086884919cf68f46626bbd7dfdb`;
- fake patch hash:
  `b6efdffb5a186abbf9dc97822065a15029afd34b788d5a7d346e206b3a74db53`;
- normalized fake diff-document hash:
  `d2621b7bb61d0db717d17278e8fb6ada80b157dad9d656cb9c92e9c14e0a1dbf`.

The checkout pair is validation metadata, not provider or GitHub acceptance.
`upstream-lock.json` records exact observed dependency commits and packet hashes,
but both dependencies are non-consumable because their reviewed outputs are
missing.

## File and freshness contract

The only safe source order is:

1. an accepted, currently authorized sandbox API for mutable working files;
2. an exact, currently authorized GitHub commit or PR API for committed
   base/head evidence; then
3. a metadata-only artifact or source link.

The application must never merge metadata or bytes from different authorities,
tasks, sandboxes, repositories, checksums, versions, or freshness observations
into one asserted file or diff document. Uncommitted sandbox bytes are not
committed-head evidence.

The retained file schema requires:

- source identity and an opaque path reference;
- validated relative display path and server-enforced workspace root;
- kind, size, declared and detected media type, encoding/newline where relevant;
- checksum, version/freshness, expiry, and truncation bounds; and
- a distinct inline-safe, metadata-only, or separately authorized download mode.

Bounds apply before decode, decompression, image/PDF parsing, or rendering.
Binary, unknown, oversized, MIME-mismatched, polyglot, active markup, malformed,
or amplification-risk content stays metadata-only. This packet retains no active
HTML, SVG, script, unsafe media, customer bytes, or unbounded output.

The deterministic path adapter rejects NUL, absolute paths, traversal, dot
segments, backslash forms, symlink following, guessed references, wrong identity,
expired references, and ambiguous Unicode/case input before a read. Hard-link
identity and provider symlink semantics remain live blockers.

The mutation fixture proves that metadata version A cannot be combined with
content version B. The result is stale with no mixed bytes. When a sandbox
expires, mutable files are unavailable; separately authorized exact-commit
evidence may remain readable under its own authority.

## Exact diff contract

The normalized diff document binds:

- repository identity;
- full base SHA, full head SHA, and explicit merge-base assumption;
- exact patch-byte checksum and normalized document checksum;
- stable file ordering and paths;
- status, prior path, binary fact, additions/deletions, hunks, and no-newline
  markers; and
- large-diff summary-first and bounded-hunk behavior.

The fake patch covers rename, added binary, deletion with no final newline, and a
text modification. Copied, type-change, and submodule rows are explicitly
unsupported rather than invented. Binary entries have no fabricated hunks.

The validator recomputes both patch and document hashes. It rejects duplicate
file entries, missing prior paths for rename/copy, new checksums on deleted
files, and hunks on binary files.

Head A remains immutable evidence after a branch advances to head B. Any
head-A-bound comment or mutation is stale and blocked until it is reviewed or
remapped against B. This packet performs no comment, branch, PR, CI, review,
approval, or merge mutation.

## Terminal contract

The canonical public capability pair is:

| `terminal` | Allowed `commandInput` | Meaning |
|---|---|---|
| `interactive` | `pty` | Requires accepted TTY allocation, resize, control, input echo, lifetime, reconnect, and close evidence |
| `transcript` | `discrete_reviewed` or `none` | Ordered read-only output, with an optional separately reviewed audited command action |
| `none` | `none` | No Terminal capability |

The fake transcript demonstrates ordered stdout/stderr, observed exit, sequence
cursor, explicit returned/omitted bounds, reconnect metadata, and no PTY controls.
It proves only schema and rendering behavior. It is not a provider transcript and
does not enable `terminal: transcript`.

TTY allocation, resize, control sequences, input echo, lifetime, reconnect, and
close are unproven. The accepted capability from this packet is therefore
`terminal: none`, `commandInput: none`.

ANSI CSI, OSC title, OSC hyperlink, bidi/control text, hostile prompt, and
oversized-control fixtures render as bounded escaped plain text with no active
links. Wrong origin, cross-actor/session, replay, expired authority, and a second
controller fail closed. A disconnect leaves process state unknown; it never
claims the command stopped.

No command ran on a sandbox, application service, web host, desktop host, probe
runner, or contributor device. The fake adapter is in-memory and executes no
shell command.

## Browser contract

The canonical browser classification is exactly one of `evidence`,
`service_url`, or `none`.

Accepted evidence would require session/evidence identity, task/sandbox identity,
origin, actor/controller, capture time, live/stale state, action provenance,
screenshot hash and media metadata, expiry, reconnect, authorization, and mobile
read behavior.

An accepted service URL would require provider service binding, exact allowed
origin/port, audience-bound opaque authority, TTL, refresh/revocation, redirect
handling, permission loss, sandbox expiry, redaction, user confirmation, and no
automatic open.

None of that evidence exists here. Browser control is outside this packet.
Therefore the accepted capability is `browser: none`. The fixture contains no
placeholder screenshot and no model-authored timeline. An ordinary destination
is labelled **Open external link**, has no Browser capability, and is not opened
automatically.

## Contradictions and precedence

There are no unresolved precedence conflicts in the retained corpus. The
following apparent capabilities are deliberately not promoted:

- a deterministic file tree is not a provider file API;
- a local Git-format patch is not current GitHub PR authority;
- a transcript fixture is not a provider transcript and never a PTY;
- an ordinary external link is neither browser evidence nor a service URL;
- an accepted upstream packet design is not an accepted upstream runtime output;
  and
- a seed branch or build result is not current external authorization.

If higher-precedence evidence later conflicts with this scope, the affected row
must stop and receive a reviewed scope/lock revision. Reviewed evidence is never
overwritten in place.

## Acceptance contribution and limits

The corpus supports only bounded evidence for:

- `AC-DW-CODE-003-01`: path-boundary contract behavior;
- `AC-DW-CODE-003-02`: exact-head anchor staleness;
- `AC-DW-CODE-003-03`: honest terminal fallback;
- `AC-DW-CODE-003-04`: exact file/diff facts that a later phone flow may consume;
  and
- `AC-DW-CODE-003-05`: browser-none/no-simulation behavior.

Application authorization, review-comment persistence and steering, UI
rendering/control, responsive behavior, phone approval/merge, and product
capability mapping remain downstream.

This packet contributes no credit to `E2E-V1-07-CODING-DRAFT-PR`,
`E2E-V1-08-RESPONSIVE-ACCESS`, `E2E-V1-09-SECURITY-RECOVERY`, or any other E2E
scenario.

## Blockers to live acceptance

1. The sandbox packet must produce independently accepted reviewed outputs,
   including exact matrix/scope/version/fixture hashes and consumed file,
   command, TTL, cleanup, task-binding, egress, service-origin, and callback rows.
2. The GitHub packet must produce independently accepted reviewed outputs,
   including exact matrix/scope/version/fixture/mutation-ledger hashes and
   repository/PR/base/head/read-authority rows.
3. A fresh read-only grant must bind exact tenant, workspace, actor, task,
   sandbox, repository, PR, base, head, operations, issuer, reviewer, and expiry.
4. Current provider and GitHub read permission must be revalidated before each
   live read.
5. Any terminal input test additionally requires a separate current terminal
   grant and an accepted public input/session contract.
6. Browser control remains unauthorized by this packet.

Until all applicable blockers close, the retained fallbacks are mandatory.

## Retained proof

- `matrix-scope.json`: immutable dimensions and scope hash.
- `upstream-lock.json`: exact dependency observations and inherited blockers.
- `matrix.json`: eighteen complete rows and three blocked spike dispositions.
- `fixtures/manifest.json`: exact fixture hashes.
- `schemas/`: six closed probe-only schemas.
- `versions.json`: sanitized interpreter/tool/source inventory.
- `commands.txt`: exact validation commands and statuses.
- `scrub-report.json`: zero retained findings.
- `review.json`: independent runtime-contract, security, and product review.
