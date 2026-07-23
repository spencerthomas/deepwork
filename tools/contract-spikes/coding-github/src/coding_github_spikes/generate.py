"""Generate deterministic, credential-free retained evidence."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

from coding_github_spikes.catalog import (
    CI_ROWS,
    FIXTURES,
    GITHUB_ROWS,
    PROXY_ROWS,
    canonical_hash,
    scope_document,
)


OFFICIAL = {
    "installation_tokens": "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app",
    "app_permissions": "https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app",
    "git_refs": "https://docs.github.com/en/rest/git/refs",
    "pull_requests": "https://docs.github.com/en/rest/pulls/pulls",
    "webhook_validation": "https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries",
    "status_checks": "https://docs.github.com/en/pull-requests/reference/status-checks",
}

FIXTURE_FOR_ROW = {
    "github.branch-name-sanitization": "wrong-binding",
    "github.branch-collision-unknown": "fake-git-clone-fetch-push",
    "github.create-ref-idempotency-no-overwrite": "fake-git-clone-fetch-push",
    "github.force-push-denied": "fake-git-clone-fetch-push",
    "github.draft-pr-timeout-reconcile": "ambiguous-remote-create",
    "github.draft-pr-duplicate-prevention": "ambiguous-remote-create",
    "github.mutation-ledger-zero-without-authority": "unsafe-grant-file",
    "github.mutation-ledger-one-and-read-only-after": "two-worker-race",
    "proxy.nonce-replay": "grant-replay",
    "proxy.callback-binding": "wrong-binding",
    "proxy.redirect-denial": "wrong-binding",
    "proxy.alternate-host-port-denial": "wrong-binding",
    "proxy.credential-helper-denial": "proxy-leak-negative",
    "proxy.no-pat-ssh-token-fallback": "proxy-leak-negative",
    "ci.webhook-signature-raw-bytes": "webhook-valid",
    "ci.webhook-delivery-dedupe": "webhook-valid",
    "ci.webhook-retry-duplicate-out-of-order": "webhook-invalid-signature",
    "ci.webhook-cross-binding-rejected": "webhook-cross-installation",
    "ci.stale-head-rejected": "stale-head-check",
    "ci.workflow-rerun-contract-no-mutation": "workflow-rerun-contract",
    "ci.workflow-cancel-contract-no-mutation": "workflow-cancel-contract",
    "ci.merge-timeout-reconciliation-no-second-request": "merge-timeout-reconciliation",
}

FIXTURE_CASES: dict[str, dict[str, object]] = {
    "two-worker-race": {
        "kind": "mutation-grant",
        "request": {"workers": ["worker-a", "worker-b"], "grant_id": "GRANT_TEST"},
        "transcript": [
            {"worker": "worker-a", "operation": "atomic-create", "result": "claimed"},
            {"worker": "worker-b", "operation": "atomic-create", "result": "already-exists"},
        ],
        "observed": {"claims": 1, "create_budget_holders": 1},
        "expected": {"decision": "one-claim-only", "draft_pr_create_count_max": 1},
    },
    "grant-replay": {
        "kind": "mutation-grant",
        "request": {"grant_id": "GRANT_TEST", "attempts": 2},
        "transcript": [
            {"attempt": 1, "result": "claimed"},
            {"attempt": 2, "result": "denied-replay"},
        ],
        "observed": {"claims": 1, "replays_denied": 1},
        "expected": {"decision": "deny-replay", "claims": 1},
    },
    "wrong-binding": {
        "kind": "proxy",
        "request": {
            "expected_repository": "owner/repository",
            "requested_repository": "other/repository",
            "audience": "wrong-installation",
        },
        "transcript": [{"operation": "authorize", "result": "denied-binding-path-audience"}],
        "observed": {"network_calls": 0, "credential_issues": 0},
        "expected": {"decision": "deny", "network_calls": 0},
    },
    "unsafe-grant-file": {
        "kind": "mutation-grant",
        "request": {"file_type": "symlink", "mode": "0644"},
        "transcript": [{"operation": "lstat-mode-owner", "result": "denied-before-claim"}],
        "observed": {"claims": 0, "mutations": 0},
        "expected": {"decision": "deny-unsafe-file", "mutations": 0},
    },
    "ambiguous-remote-create": {
        "kind": "github-api",
        "request": {"operation": "create-draft-pr", "simulated_result": "timeout-after-remote"},
        "transcript": [
            {"operation": "create", "result": "ambiguous", "budget_spent": True},
            {"operation": "authoritative-read", "result": "matching-PR_1"},
            {"operation": "retry-create", "result": "not-attempted"},
        ],
        "observed": {"create_attempts": 1, "pr_identities": ["PR_1"]},
        "expected": {"decision": "reconcile-read-only", "create_attempts_max": 1},
    },
    "workflow-rerun-contract": {
        "kind": "github-api",
        "request": {"operation": "workflow-rerun", "method": "POST"},
        "transcript": [{"operation": "inventory-only", "required_permission": "actions:write"}],
        "observed": {"requests_sent": 0, "workflow_mutations": 0},
        "expected": {"decision": "contract-only", "workflow_mutations": 0},
    },
    "workflow-cancel-contract": {
        "kind": "github-api",
        "request": {"operation": "workflow-cancel", "method": "POST"},
        "transcript": [{"operation": "inventory-only", "required_permission": "actions:write"}],
        "observed": {"requests_sent": 0, "workflow_mutations": 0},
        "expected": {"decision": "contract-only", "workflow_mutations": 0},
    },
    "merge-timeout-reconciliation": {
        "kind": "github-api",
        "request": {"operation": "merge", "simulated_result": "timeout"},
        "transcript": [
            {"operation": "merge", "result": "not-authorized-not-sent"},
            {"operation": "read-pr-state", "result": "fixture-open"},
        ],
        "observed": {"merge_requests": 0, "second_merge_requests": 0},
        "expected": {"decision": "contract-only-read-before-retry", "merge_requests": 0},
    },
    "webhook-valid": {
        "kind": "webhook",
        "request": {"event": "pull_request", "delivery": "D_VALID", "raw_body_hash": "sha256:fixture-valid"},
        "transcript": [
            {"operation": "verify-raw-HMAC", "result": "valid"},
            {"operation": "parse-signed-bytes", "result": "valid-json"},
            {"operation": "trusted-binding-compare", "result": "match"},
        ],
        "observed": {"projected": 1, "duplicates": 0},
        "expected": {"decision": "project-once", "projected": 1},
    },
    "webhook-invalid-signature": {
        "kind": "webhook",
        "request": {"event": "pull_request", "delivery": "D_BAD", "signature": "invalid-fixture"},
        "transcript": [{"operation": "verify-raw-HMAC", "result": "denied"}],
        "observed": {"parsed": 0, "projected": 0},
        "expected": {"decision": "deny-before-parse", "projected": 0},
    },
    "webhook-cross-installation": {
        "kind": "webhook",
        "request": {"signed_installation": "I_OTHER", "expected_installation": "I_TEST"},
        "transcript": [
            {"operation": "verify-raw-HMAC", "result": "valid"},
            {"operation": "trusted-binding-compare", "result": "denied-installation"},
        ],
        "observed": {"projected": 0},
        "expected": {"decision": "deny-cross-installation", "projected": 0},
    },
    "stale-head-check": {
        "kind": "ci",
        "request": {"check_sha": "SHA_OLD", "current_head_sha": "SHA_CURRENT", "conclusion": "success"},
        "transcript": [{"operation": "normalize-check", "result": "stale"}],
        "observed": {"normalized_state": "stale", "green": False},
        "expected": {"decision": "not-green", "state": "stale"},
    },
    "proxy-leak-negative": {
        "kind": "proxy",
        "request": {"surfaces": ["env", "filesystem", "argv", "git-config", "output", "snapshot"]},
        "transcript": [{"operation": "scrub", "result": "zero-credential-markers"}],
        "observed": {"credential_markers": 0, "fallback_credentials": 0},
        "expected": {"decision": "clean", "credential_markers": 0},
    },
    "fake-git-clone-fetch-push": {
        "kind": "git",
        "request": {"repository": "owner/repository", "head_ref": "deep-work/task"},
        "transcript": [
            {"operation": "clone", "result": "fixture-ok"},
            {"operation": "fetch", "result": "fixture-ok"},
            {"operation": "push-fast-forward", "result": "fixture-ok"},
            {"operation": "force-push", "result": "denied"},
            {"operation": "unknown-ref-overwrite", "result": "denied"},
        ],
        "observed": {"force_pushes": 0, "unknown_overwrites": 0},
        "expected": {"decision": "bounded-fast-forward-only", "force_pushes": 0},
    },
}


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def row(prefix: str, name: str) -> dict[str, object]:
    row_id = f"{prefix}.{name}"
    fixture_name = FIXTURE_FOR_ROW.get(row_id)
    official_source = {
        "github": OFFICIAL["pull_requests"] if "pr" in name else OFFICIAL["git_refs"],
        "proxy": OFFICIAL["installation_tokens"],
        "ci": OFFICIAL["status_checks"],
    }[prefix]
    return {
        "id": row_id,
        "spike_id": {
            "github": "SPIKE-GITHUB-001",
            "proxy": "SPIKE-GITHUB-PROXY-001",
            "ci": "SPIKE-GITHUB-CI-001",
        }[prefix],
        "operation": name,
        "evidence_tier": "deterministic-fake" if fixture_name else "official-documented",
        "state": "blocked-live-evidence",
        "versions": {"github_rest_api": "2026-03-10", "probe": "0.1.0"},
        "account_tier": "not-supplied",
        "region": "not-supplied",
        "observed_at": "2026-07-23",
        "evidence": f"fixtures/{fixture_name}.json" if fixture_name else official_source,
        "schema_hash": canonical_hash({"prefix": prefix, "operation": name}),
        "conclusion": "offline contract/negative behavior retained; live behavior not accepted",
        "contradiction": None,
        "inherited_blocker": "sandbox packet has no reviewed accepted evidence or hashes",
        "owner": {
            "github": "runtime-contracts",
            "proxy": "security",
            "ci": "runtime-contracts",
        }[prefix],
        "fallback": "disable private GitHub mutation; retain local/source-native work and downloadable patch",
        "cleanup": "no live resource created; deterministic fake state discarded after test",
    }


def fixture(name: str) -> dict[str, object]:
    case = {
        "schema_version": 1,
        "fixture_id": name,
        "deterministic": True,
        "network": "denied",
        "credentials": "none",
        **FIXTURE_CASES[name],
    }
    case["case_hash"] = canonical_hash(case)
    return case


SCHEMAS = {
    "installation": ["installation_id", "repository_node", "permissions", "expires_at"],
    "repository-ref": ["repository_node", "base_ref", "base_sha", "head_ref", "head_sha"],
    "proxy-intent": ["binding_hash", "host", "path", "method", "use", "audience", "expires_at", "nonce"],
    "pull-request": ["node_id", "number", "draft", "base", "head", "head_sha"],
    "ci": ["repository_node", "pr_node", "head_sha", "checks", "freshness"],
    "webhook": ["delivery_id", "signature", "installation", "repository", "action", "pull_request"],
    "mutation-ledger": ["state", "grant_hash", "repository_binding_hash", "pr_identity", "create_attempted"],
    "evidence": ["id", "spike_id", "evidence_tier", "state", "conclusion", "fallback"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root: Path = args.output

    scope = scope_document()
    scope["scope_hash"] = canonical_hash(scope)
    dump(root / "matrix-scope.json", scope)

    upstream = {
        "packet_id": "DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH",
        "observed_commit": "5a518c40fb44b5d64b8eb36f618c8ecd58bad188",
        "expected_base": "b2243109d0cfb2e093cc37a57017e8e70b5ea64b",
        "review_verdict": "missing",
        "reviewed_commit": None,
        "hashes": {"matrix_scope": None, "matrix": None, "versions": None, "fixtures": None},
        "consumed_rows": [],
        "state": "blocked-live-evidence",
        "reason": "upstream worktree contains only the seed packet; retained outputs and independent review are absent",
        "fallback": "offline research and deterministic negatives only; no proxy, egress, push, or PR mutation",
    }
    dump(root / "upstream-lock.json", upstream)

    rows = (
        [row("github", name) for name in GITHUB_ROWS]
        + [row("proxy", name) for name in PROXY_ROWS]
        + [row("ci", name) for name in CI_ROWS]
    )
    matrix = {
        "schema_version": 1,
        "scope_hash": scope["scope_hash"],
        "upstream_state": upstream["state"],
        "rows": rows,
        "matrix_hash": canonical_hash(rows),
    }
    dump(root / "matrix.json", matrix)

    for name in FIXTURES:
        dump(root / "fixtures" / f"{name}.json", fixture(name))
    fixture_manifest = {
        "fixtures": list(FIXTURES),
        "hashes": {name: canonical_hash(fixture(name)) for name in FIXTURES},
    }
    dump(root / "fixtures" / "manifest.json", fixture_manifest)

    for name, required in SCHEMAS.items():
        dump(
            root / "schemas" / f"{name}.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": name,
                "type": "object",
                "required": required,
                "additionalProperties": True,
            },
        )

    dump(
        root / "live-mutation-ledger.json",
        {
            "state": "not-run",
            "reason": "no mutation grant, GitHub App, disposable repository, or accepted upstream evidence supplied",
            "draft_pr_create_attempts": 0,
            "draft_pr_identities": [],
            "ready_mutations": 0,
            "review_mutations": 0,
            "approval_mutations": 0,
            "workflow_mutations": 0,
            "workflow_cancel_mutations": 0,
            "merge_mutations": 0,
            "force_push_mutations": 0,
            "branch_delete_mutations": 0,
            "deployment_mutations": 0,
            "credentials_observed": 0,
            "authoritative_link": None,
        },
    )
    dump(
        root / "review.json",
        {
            "state": "pending-independent-review",
            "reviewed_commit": None,
            "mutation_count": 0,
            "spikes": {spike: "blocked-live-evidence" for spike in scope["spikes"]},
            "reviews": {
                "runtime-contracts": {"verdict": "pending", "reviewer": None, "findings": []},
                "security": {"verdict": "pending", "reviewer": None, "findings": []},
                "product": {"verdict": "pending", "reviewer": None, "findings": []},
            },
        },
    )
    report = f"""# GitHub/App/proxy/CI contract research

Date: {date(2026, 7, 23).isoformat()}

## Outcome

No live mutation was attempted. The required sandbox packet has no reviewed
accepted outputs, and no dedicated GitHub App, test organization, disposable
private repository, or external mutation grant was supplied. The live mutation
ledger therefore records zero draft pull requests and every live-required row is
`blocked-live-evidence`.

The isolated probe retains {len(rows)} scoped rows and {len(FIXTURES)}
credential-free fixtures. They prove fail-closed branch, grant, proxy, webhook,
current-head, workflow-mutation, and merge-timeout behavior. Deterministic fake
evidence is never promoted to live acceptance.

## Minimum GitHub App manifest

Repository permissions are Contents write, Pull requests write, Administration
read, Commit statuses read, Checks read, Actions read, and Metadata read,
restricted to one selected disposable private repository. Administration write,
Members, Secrets, and Workflows write are forbidden.
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
grant and reviewed upstream evidence. The durable claim model atomically claims once,
spends the create budget on an ambiguous remote result, reconciles before retry,
and rejects a second identity. Ready, review, approval, workflow rerun/cancel,
merge, force-push, branch deletion, and deploy budgets are zero.

## CI authority

Webhook signatures are verified over raw bytes with HMAC-SHA256 before projection.
Delivery timestamp/ID and trusted App, installation, account, repository,
current-authorization, PR, base, and current-head bindings are required.
Tenant/workspace/task/sandbox/actor remain in trusted application binding rather
than provider payload. Polling/refetch is authoritative after gaps or
disagreement. A check for a stale SHA is never green. Workflow rerun/cancel and
merge endpoints are retained as contract-only rows and are never invoked.

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

{chr(10).join(f"- [{name}]({url})" for name, url in OFFICIAL.items())}
"""
    (root / "report.md").write_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
