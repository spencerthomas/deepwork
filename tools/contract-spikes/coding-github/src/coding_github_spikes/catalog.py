"""Immutable scope catalog used by generators and validators."""

from __future__ import annotations

from hashlib import sha256
import json

SPIKES = ("SPIKE-GITHUB-001", "SPIKE-GITHUB-PROXY-001", "SPIKE-GITHUB-CI-001")

GITHUB_ROWS = (
    "app-install",
    "app-reconfigure",
    "app-suspend",
    "app-delete",
    "callback-state-expiry",
    "selected-account-repositories",
    "actor-workspace-authorization",
    "repository-pagination-search",
    "grant-revoked-changed",
    "installation-token-audience",
    "installation-token-repository-scope",
    "installation-token-permission-scope",
    "installation-token-ttl-refresh-expiry-revocation",
    "installation-token-wrong-binding",
    "installation-token-rate-limit",
    "repository-id-base-ref-sha-preflight",
    "branch-name-sanitization",
    "branch-collision-ours",
    "branch-collision-unknown",
    "create-ref-idempotency-no-overwrite",
    "force-push-denied",
    "head-reconciliation",
    "clone-fetch",
    "bounded-edit-test-commit",
    "push",
    "authoritative-head-refetch",
    "draft-pr-create-read",
    "draft-pr-timeout-reconcile",
    "draft-pr-repeated-command",
    "draft-pr-existing-match",
    "draft-pr-wrong-head-base",
    "draft-pr-permission-loss-provider-error",
    "draft-pr-duplicate-prevention",
    "merge-methods-read",
    "protection-permission-read",
    "mutation-ledger-zero-without-authority",
    "mutation-ledger-one-and-read-only-after",
)

PROXY_ROWS = (
    "callback-provider-auth",
    "callback-binding",
    "intent-host-path-method-use",
    "intent-audience-scope-ttl",
    "nonce-replay",
    "concurrency",
    "refresh-expiry-revocation-policy-update",
    "https-clone",
    "https-fetch",
    "https-push",
    "minimum-api-operation",
    "redirect-denial",
    "alternate-host-port-denial",
    "submodule-lfs-detection",
    "credential-helper-denial",
    "wrong-tenant-workspace-actor-task",
    "wrong-sandbox-repository-installation",
    "stale-binding-expired-sandbox",
    "suspended-installation-permission-change",
    "branch-protection-rate-limit-outage",
    "leak-env-filesystem-process-args",
    "leak-git-config-remotes-helper-history",
    "leak-output-snapshot-log-trace-evidence",
    "no-pat-ssh-token-fallback",
)

CI_ROWS = (
    "webhook-signature-raw-bytes",
    "webhook-delivery-dedupe",
    "webhook-retry-duplicate-out-of-order",
    "webhook-missing-event-poll-reconcile",
    "webhook-app-install-repository-binding",
    "webhook-tenant-workspace-binding",
    "webhook-event-action-pr-base-head-binding",
    "webhook-cross-binding-rejected",
    "checks-suite-runs-statuses",
    "actions-workflow-association",
    "required-check-discovery",
    "check-state-cross-product",
    "stale-head-rejected",
    "fork-protection-merge-queue-facts",
    "workflow-read-contract",
    "workflow-rerun-contract-no-mutation",
    "workflow-cancel-contract-no-mutation",
    "workflow-rate-limit-errors",
    "merge-method-protection-contract",
    "merge-request-identity-contract",
    "merge-timeout-reconciliation-no-second-request",
    "draft-pr-authoritative-evidence",
    "merge-readiness-read-only",
)

NEGATIVE_CASES = (
    "absent-authority",
    "wrong-tenant",
    "wrong-workspace",
    "wrong-actor",
    "wrong-task",
    "wrong-sandbox",
    "wrong-installation",
    "wrong-repository",
    "wrong-base",
    "wrong-head",
    "expired-grant",
    "unsafe-grant-mode",
    "grant-symlink",
    "replayed-grant",
    "concurrent-grant",
    "unknown-branch-collision",
    "ambiguous-create-timeout",
    "stale-check-head",
    "bad-webhook-signature",
    "duplicate-webhook",
    "cross-installation-webhook",
    "redirect",
    "alternate-host",
    "alternate-port",
    "credential-helper",
    "pat-fallback",
    "ssh-fallback",
)

FIXTURES = (
    "two-worker-race",
    "grant-replay",
    "wrong-binding",
    "unsafe-grant-file",
    "ambiguous-remote-create",
    "workflow-rerun-contract",
    "workflow-cancel-contract",
    "merge-timeout-reconciliation",
    "webhook-valid",
    "webhook-invalid-signature",
    "webhook-cross-installation",
    "stale-head-check",
    "proxy-leak-negative",
    "fake-git-clone-fetch-push",
)


def required_row_ids() -> tuple[str, ...]:
    """Return stable matrix row IDs."""
    return tuple(
        [f"github.{name}" for name in GITHUB_ROWS]
        + [f"proxy.{name}" for name in PROXY_ROWS]
        + [f"ci.{name}" for name in CI_ROWS]
    )


def canonical_hash(value: object) -> str:
    """Hash canonical JSON."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{sha256(payload).hexdigest()}"


def scope_document() -> dict[str, object]:
    """Return immutable scope without its self-hash."""
    return {
        "schema_version": 1,
        "packet_id": "DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH",
        "base_commit": "b2243109d0cfb2e093cc37a57017e8e70b5ea64b",
        "spikes": list(SPIKES),
        "repository_class": "disposable-private-non-production-only",
        "api": {
            "rest_version": "2026-03-10",
            "accept": "application/vnd.github+json",
            "auth_class": "github-app-installation-only",
        },
        "app_permissions": {
            "contents": "write",
            "pull_requests": "write",
            "checks": "read",
            "actions": "read",
            "metadata": "read",
        },
        "forbidden_permissions": ["administration", "members", "secrets", "workflows:write"],
        "branch_policy": {
            "prefix": "deep-work/",
            "immutable_base_sha": True,
            "force_push": False,
            "overwrite_unknown": False,
            "delete_branch": False,
        },
        "mutation_budget": {
            "draft_pull_requests": 1,
            "ready": 0,
            "reviews": 0,
            "approvals": 0,
            "workflow_reruns": 0,
            "workflow_cancels": 0,
            "merges": 0,
            "force_pushes": 0,
            "deployments": 0,
        },
        "required_rows": list(required_row_ids()),
        "negative_cases": list(NEGATIVE_CASES),
        "required_fixtures": list(FIXTURES),
        "upstream_requirements": [
            "reviewed-commit",
            "review.json:accepted",
            "matrix-scope-hash",
            "matrix-hash",
            "versions-hash",
            "fixture-hash",
            "accepted-create-command-file-cleanup-rows",
            "accepted-binding-expiry-recovery-rows",
            "accepted-egress-allowlist-and-bypass-rows",
        ],
        "forbidden_credentials": [
            "personal-access-token",
            "oauth-user-token",
            "ssh-key",
            "reusable-installation-token",
            "credential-bearing-remote",
        ],
    }

