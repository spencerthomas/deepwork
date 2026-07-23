# GitHub/App/proxy/CI contract research

Date: 2026-07-23

## Outcome

No live mutation was attempted. The required sandbox packet has no reviewed
accepted outputs, and no dedicated GitHub App, test organization, disposable
private repository, or external mutation grant was supplied. The live mutation
ledger therefore records zero draft pull requests and every live-required row is
`blocked-live-evidence`.

The isolated probe retains 84 scoped rows and 14
credential-free fixtures. They prove fail-closed branch, grant, proxy, webhook,
current-head, workflow-mutation, and merge-timeout behavior. Deterministic fake
evidence is never promoted to live acceptance.

## Minimum GitHub App manifest

Repository permissions are Contents write, Pull requests write, Checks read,
Actions read, and Metadata read, restricted to one selected disposable private
repository. Administration, Members, Secrets, and Workflows write are forbidden.
Installation tokens must be repository- and permission-scoped and are never
delivered to the sandbox. GitHub documents that installation tokens expire after
one hour; this probe treats expiry/revocation and token-format changes as opaque
proxy concerns.

## Proxy boundary

Only an accepted provider callback may authorize an exact task/sandbox/
installation/repository binding. The deterministic policy permits HTTPS Git
upload-pack, receive-pack, read-only API calls, and one draft-PR create use.
Redirects, alternate hosts/ports, credential helpers, PAT/SSH fallback, replay,
stale bindings, and broader methods fail closed. The accepted live rows inherit
the sandbox packet and remain blocked.

## Exactly-one draft PR result

Live draft PR count: **0**. This is the only safe result without the external
grant and reviewed upstream evidence. The fake ledger atomically claims once,
spends the create budget on an ambiguous remote result, reconciles before retry,
and rejects a second identity. Ready, review, approval, workflow rerun/cancel,
merge, force-push, branch deletion, and deploy budgets are zero.

## CI authority

Webhook signatures are verified over raw bytes with HMAC-SHA256 before projection.
Delivery ID and installation/repository/tenant/workspace/base/head bindings are
required. Polling/refetch is authoritative after gaps or disagreement. A check for
a stale SHA is never green. Workflow rerun/cancel and merge endpoints are retained
as contract-only rows and are never invoked.

## Spike dispositions

- `SPIKE-GITHUB-001`: blocked-live-evidence; offline installation/ref/PR contract
  and duplicate-prevention fixtures complete.
- `SPIKE-GITHUB-PROXY-001`: blocked-live-evidence; upstream sandbox/proxy review
  absent, while fail-closed intent and leak negatives are complete.
- `SPIKE-GITHUB-CI-001`: blocked-live-evidence; signed/bound webhook, polling,
  check-state, workflow-contract, and merge-timeout fixtures complete without
  mutation.

## Downstream limits

This evidence supports only the contract portions of AC-DW-CODE-002-01..04. It
earns zero E2E credit and does not enable application capability, private
repository mutation, phone confirmation, merge readiness, workflow mutation,
merge, release, or deployment.

## Official sources

- [installation_tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
- [app_permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app)
- [git_refs](https://docs.github.com/en/rest/git/refs)
- [pull_requests](https://docs.github.com/en/rest/pulls/pulls)
- [webhook_validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [status_checks](https://docs.github.com/en/pull-requests/reference/status-checks)
