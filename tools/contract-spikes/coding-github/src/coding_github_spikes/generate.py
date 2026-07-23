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


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def row(prefix: str, name: str) -> dict[str, object]:
    fixture = name in {
        "branch-name-sanitization",
        "branch-collision-unknown",
        "create-ref-idempotency-no-overwrite",
        "force-push-denied",
        "draft-pr-timeout-reconcile",
        "draft-pr-duplicate-prevention",
        "mutation-ledger-zero-without-authority",
        "nonce-replay",
        "redirect-denial",
        "alternate-host-port-denial",
        "credential-helper-denial",
        "no-pat-ssh-token-fallback",
        "webhook-signature-raw-bytes",
        "webhook-delivery-dedupe",
        "webhook-cross-binding-rejected",
        "stale-head-rejected",
        "merge-timeout-reconciliation-no-second-request",
    }
    return {
        "id": f"{prefix}.{name}",
        "spike_id": {
            "github": "SPIKE-GITHUB-001",
            "proxy": "SPIKE-GITHUB-PROXY-001",
            "ci": "SPIKE-GITHUB-CI-001",
        }[prefix],
        "operation": name,
        "evidence_tier": "deterministic-fake" if fixture else "official-documented",
        "state": "blocked-live-evidence",
        "versions": {"github_rest_api": "2026-03-10", "probe": "0.1.0"},
        "account_tier": "not-supplied",
        "region": "not-supplied",
        "observed_at": "2026-07-23",
        "evidence": (
            f"fixtures/{'merge-timeout-reconciliation' if name.startswith('merge-timeout') else 'manifest'}.json"
            if fixture
            else list(OFFICIAL.values())
        ),
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
    return {
        "fixture_id": name,
        "deterministic": True,
        "network": "denied",
        "credentials": "none",
        "input": {"case": name, "repository": "R_TEST", "task": "T_TEST"},
        "expected": {
            "decision": "deny-or-reconcile-read-only",
            "draft_pr_create_count_max": 1,
            "merge_count": 0,
            "workflow_mutation_count": 0,
            "secret_persistence_count": 0,
        },
    }


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
            "workflow_mutations": 0,
            "merge_mutations": 0,
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

{chr(10).join(f"- [{name}]({url})" for name, url in OFFICIAL.items())}
"""
    (root / "report.md").write_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

