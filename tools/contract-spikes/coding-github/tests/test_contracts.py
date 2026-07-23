from __future__ import annotations

import json
import pytest

from coding_github_spikes.contracts import (
    Binding,
    ContractDenied,
    MutationLedger,
    ProxyIntent,
    ProxyPolicy,
    normalize_check_state,
    sanitize_branch,
    sign_webhook,
    verify_webhook,
)


BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


def binding() -> Binding:
    return Binding(
        tenant="TENANT_TEST",
        workspace="WORKSPACE_TEST",
        actor="ACTOR_TEST",
        task="TASK_123",
        sandbox="SANDBOX_TEST",
        installation="1001",
        repository_node="R_TEST",
        base_ref="main",
        base_sha=BASE_SHA,
        head_ref="deep-work/task_123",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Feature 123", "deep-work/feature-123"), ("TASK_123", "deep-work/task_123")],
)
def test_sanitize_branch(raw: str, expected: str) -> None:
    assert sanitize_branch(raw) == expected


@pytest.mark.parametrize("raw", ["", "../", "x.lock", "@{"])
def test_sanitize_branch_rejects_unsafe(raw: str) -> None:
    with pytest.raises(ContractDenied):
        sanitize_branch(raw)


def test_binding_digest_is_deterministic() -> None:
    assert binding().digest() == binding().digest()


def test_grant_claim_is_atomic_and_replay_denied() -> None:
    ledger = MutationLedger()
    ledger.claim("sha256:grant")
    with pytest.raises(ContractDenied, match="already claimed"):
        ledger.claim("sha256:grant")


def test_ambiguous_create_spends_budget_until_reconciled() -> None:
    ledger = MutationLedger()
    ledger.claim("sha256:grant")
    ledger.before_create()
    ledger.record_remote_result(None)
    with pytest.raises(ContractDenied, match="already attempted"):
        ledger.before_create()
    assert ledger.reconcile("PR_1") == "PR_1"


def test_proxy_exact_binding_and_nonce() -> None:
    bind = binding()
    policy = ProxyPolicy(now=100, expected_binding_hash=bind.digest())
    intent = ProxyIntent(bind.digest(), "github.com", "/org/repo.git", "git-upload-pack", "fetch", "installation", 200, "n1")
    policy.authorize(intent)
    with pytest.raises(ContractDenied, match="replay"):
        policy.authorize(intent)


@pytest.mark.parametrize(
    "intent",
    [
        ProxyIntent("wrong", "github.com", "/org/repo.git", "git-upload-pack", "fetch", "installation", 200, "n1"),
        ProxyIntent("HASH", "evil.example", "/x", "GET", "read", "installation", 200, "n2"),
        ProxyIntent("HASH", "github.com:8443", "/x", "git-upload-pack", "fetch", "installation", 200, "n3"),
        ProxyIntent("HASH", "github.com", "/x", "git-receive-pack", "push", "installation", 99, "n4"),
    ],
)
def test_proxy_denies_wrong_scope(intent: ProxyIntent) -> None:
    policy = ProxyPolicy(now=100, expected_binding_hash="HASH")
    with pytest.raises(ContractDenied):
        policy.authorize(intent)


def webhook_payload() -> dict:
    bind = binding()
    return {
        "action": "opened",
        "tenant": bind.tenant,
        "workspace": bind.workspace,
        "installation": {"id": 1001},
        "repository": {"node_id": bind.repository_node},
        "pull_request": {
            "base": {"ref": bind.base_ref, "sha": bind.base_sha},
            "head": {"ref": bind.head_ref, "sha": HEAD_SHA},
        },
        "expected_head_sha": HEAD_SHA,
    }


def test_webhook_signature_then_full_binding_and_dedupe() -> None:
    payload = webhook_payload()
    raw = json.dumps(payload, sort_keys=True).encode()
    signature = sign_webhook(b"fixture-secret", raw)
    seen: set[str] = set()
    verify_webhook(
        secret=b"fixture-secret",
        raw_body=raw,
        signature=signature,
        delivery_id="D1",
        seen_deliveries=seen,
        payload=payload,
        expected=binding(),
    )
    with pytest.raises(ContractDenied, match="duplicate"):
        verify_webhook(
            secret=b"fixture-secret",
            raw_body=raw,
            signature=signature,
            delivery_id="D1",
            seen_deliveries=seen,
            payload=payload,
            expected=binding(),
        )


def test_webhook_rejects_cross_repository() -> None:
    payload = webhook_payload()
    payload["repository"]["node_id"] = "R_OTHER"
    raw = json.dumps(payload, sort_keys=True).encode()
    with pytest.raises(ContractDenied, match="binding"):
        verify_webhook(
            secret=b"fixture-secret",
            raw_body=raw,
            signature=sign_webhook(b"fixture-secret", raw),
            delivery_id="D2",
            seen_deliveries=set(),
            payload=payload,
            expected=binding(),
        )


@pytest.mark.parametrize(
    ("status", "conclusion", "observed", "expected"),
    [
        ("completed", "success", HEAD_SHA, "success"),
        ("completed", "failure", HEAD_SHA, "failure"),
        ("completed", "neutral", HEAD_SHA, "neutral"),
        ("completed", "skipped", HEAD_SHA, "skipped"),
        ("in_progress", None, HEAD_SHA, "pending"),
        ("completed", "success", BASE_SHA, "stale"),
        ("completed", None, HEAD_SHA, "unknown"),
    ],
)
def test_check_state(status: str, conclusion: str | None, observed: str, expected: str) -> None:
    assert normalize_check_state(status, conclusion, observed, HEAD_SHA) == expected

