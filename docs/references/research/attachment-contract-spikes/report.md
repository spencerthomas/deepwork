# SPIKE-ATTACH-001 attachment contract report

Date: 2026-07-23
Packet: `DW-EXT-W1-FIRST-TASK-SAFE-ATTACHMENTS`
Scope SHA-256: `3b52de1224cdd46183ed35a3be2e9410b3f3985a921bc94be652ffed1f07ff6e`

## Disposition

The attachment capability remains disabled for the public Classic LangSmith
Deployment baseline. The deterministic harness accepts the local policy and
fail-closed state-machine contract only. It does not accept a hosted object
store, scanner, model, provider-file service, or Classic runtime transfer
contract.

No sanctioned non-production object-store, scanner, or Classic runtime profile
was supplied. All rows requiring their real behavior remain
`blocked-live-evidence`, `unknown`, `unsupported`, or deliberately `rejected`.
The bounded pasted-text path and credential-free fixture/demo remain usable.
This result neither blocks nor satisfies `E2E-V1-01-FIRST-VALUE`.

## Immutable scope and complete matrix

`matrix-scope.json` was committed before matrix generation. It fixes:

- four media classes: bounded text file, image, PDF, and code;
- two Deep Work byte boundaries: quarantine and authorized object;
- one source: the public Classic LangSmith Deployment baseline;
- 38 lifecycle and abuse operations; and
- three discovered candidate content representations: inline base64, URL
  reference, and provider-managed file ID.

The validator derives the full `4 × 2 × 1 × 38 × 3 = 912` row set from that
scope. It rejects worker-selected omissions, extra rows, missing unsupported or
unknown outcomes, MDA/Fleet rows, scope-hash drift, missing provenance or
fallbacks, live overclaims, fake-as-provider-proof claims, and unresolved
source-precedence conflicts.

| Conclusion | Rows | Meaning |
|---|---:|---|
| `accepted-fixture-only` | 624 | The no-network fake proves the bounded local policy or fail-closed transition only. |
| `blocked-live-evidence` | 240 | Real object-store, scanner, deletion, or Classic receipt behavior needs sanctioned non-production proof. |
| `rejected` | 16 | Inline or URL transfer from quarantine is forbidden before clean, authorized promotion. |
| `unknown` | 24 | Public evidence does not establish provider-file creation, ownership, receipt, or deletion behavior. |
| `unsupported` | 8 | Quarantined Deep Work bytes cannot already be represented as a provider-managed file ID. |

There are zero `accepted-live` rows.

## Architecture and authorization boundary

Deep Work owns attachment metadata, hash, declared and detected type, byte/count
policy, filename policy, actor/workspace/task/object binding, quarantine verdict,
retention, deletion state, and audit. Bytes remain in quarantine with agent
visibility denied until all required conditions are independently satisfied.

A scanner verdict is untrusted input. `clean` is necessary but not sufficient:
the transfer intent must separately bind actor, workspace, task, object,
destination, representation, expiry, idempotency key, hash, and size. Receipt
processing rechecks hash and size. Unsafe, error, timeout, unavailable, expired,
mismatched, replayed, redirected, or partial behavior fails closed. Restart and
retry preserve the prior unsafe or unknown verdict and never broaden authority.

Local deletion and provider deletion are recorded separately. A provider
deletion failure remains unverified and retryable rather than being presented as
complete.

## Public and pinned observations

Evidence precedence was applied as follows:

1. `SRC-LC` at `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`
   documents standard image/file content blocks using inline base64, URL
   reference, and provider-managed file ID.
2. Pinned public `langgraph-sdk==0.4.2` source at `SRC-LG`
   `31f90df3e6b0268fa77fd2d118a917d420b84a68` sends graph-defined JSON input
   to Classic runs. The examined pinned client source does not define a generic
   attachment upload, scanner, media-acceptance, retention, or deletion schema.
3. `deepagents==0.6.12` at `SRC-DA`
   `7794b61a6e76230e8c7a49bdce808b3728305914` is pinned reference behavior,
   not hosted-service authority.
4. Deterministic fakes prove only the local harness and transition invariants.

The apparent contradiction is resolved by treating the three documented content
blocks as candidate representations, not as proof that any selected graph,
model, Classic account, or provider file service accepts or safely retains the
attachment.

## Failure and recovery evidence

The retained tests cover count, declared type, size, empty content, unsafe and
traversal-like filenames, duplicate/hash mismatch, unsupported media, detected
type mismatch, every scanner verdict, pre-agent visibility, wrong
actor/workspace/task/destination, stale grants, redirect, range/partial behavior,
idempotent intent and receipt replay, changed-payload conflict, object
substitution, capability mismatch, source unavailable/error, remove-before-
transfer, orphan cleanup, provider deletion failure, retry, and restart recovery.
The test plugin confines the exact root-invoked pytest command to this isolated
project, and its ordinary suite denies socket access.

Harmless media metadata, public observations, expected transitions, fixture
hashes, package versions, command outcomes, and the evidence scrub are retained
beside the matrix. No production data, credentials, reusable grants, endpoints,
raw headers/cookies, customer content, or unsafe binary sample is present.

## Downstream contribution limits

- `AC-DW-TASK-002-03`: supports only the unsafe-before-agent-visibility state
  machine and negative fixtures. Application upload/dispatch integration remains
  downstream.
- `AC-DW-QUAL-001-03`: supports only the attachment gate conclusion and
  deterministic fallback. Release-manifest disablement or omission remains
  coordinator evidence.
- `AC-DW-QUAL-001-04`: supports only attachment traversal, media, quarantine,
  scanner, transfer, actor/workspace/task binding, replay, deletion, and recovery
  abuse cases. The full cross-layer security suite remains downstream.

This packet contributes to no other acceptance ID and does not enable an
attachment capability.

## Independent review

The first fixed-SHA runtime-contract, security, and product review requested
changes. The implementation now binds transfer authority back to the supplied
object and tenant/task metadata; enforces store-level count/duplicate and runtime
representation policy; models intent idempotency, orphan cleanup, and source
failure; validates every row's exact semantics; classifies the public client
source as pinned reference evidence; strengthens private-data scrubbing; and
expires grants at the boundary instant.

The first-round findings, resolutions, and fresh-review disposition are retained
in `review.json`. Fresh acceptance from all three roles remains required before
handoff.
