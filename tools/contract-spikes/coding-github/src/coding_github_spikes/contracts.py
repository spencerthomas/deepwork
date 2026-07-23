"""Fail-closed deterministic contract models."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac
import json
import re
from typing import Any

BRANCH_RE = re.compile(r"[^a-z0-9._/-]+")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ContractDenied(ValueError):
    """A requested operation violates the immutable contract."""


def sanitize_branch(task_id: str) -> str:
    """Produce a deterministic bounded branch without traversal or ref tricks."""
    cleaned = BRANCH_RE.sub("-", task_id.strip().lower()).strip("-./")
    while ".." in cleaned:
        cleaned = cleaned.replace("..", ".")
    if not cleaned or cleaned.endswith(".lock") or "@{" in cleaned:
        raise ContractDenied("unsafe task identity")
    return f"deep-work/{cleaned[:80]}"


@dataclass(frozen=True)
class Binding:
    tenant: str
    workspace: str
    actor: str
    task: str
    sandbox: str
    installation: str
    repository_node: str
    base_ref: str
    base_sha: str
    head_ref: str

    def validate(self) -> None:
        if not all(self.__dict__.values()) or not SHA_RE.fullmatch(self.base_sha):
            raise ContractDenied("incomplete or invalid binding")
        if self.head_ref != sanitize_branch(self.task):
            raise ContractDenied("head ref does not match deterministic task branch")

    def digest(self) -> str:
        self.validate()
        raw = json.dumps(self.__dict__, sort_keys=True, separators=(",", ":")).encode()
        return f"sha256:{sha256(raw).hexdigest()}"


@dataclass
class MutationLedger:
    """In-memory model of the durable exactly-one PR ledger."""

    grant_hash: str | None = None
    pr_identity: str | None = None
    create_attempted: bool = False
    ambiguous: bool = False

    def claim(self, grant_hash: str) -> None:
        if self.grant_hash is not None:
            raise ContractDenied("grant already claimed")
        self.grant_hash = grant_hash

    def before_create(self) -> None:
        if self.grant_hash is None:
            raise ContractDenied("mutation grant not claimed")
        if self.pr_identity is not None:
            raise ContractDenied("draft PR already exists; reconcile read-only")
        if self.create_attempted:
            raise ContractDenied("create already attempted; reconcile before retry")
        self.create_attempted = True

    def record_remote_result(self, identity: str | None) -> None:
        if not self.create_attempted:
            raise ContractDenied("no create attempt")
        if identity is None:
            self.ambiguous = True
            return
        if self.pr_identity not in (None, identity):
            raise ContractDenied("second PR identity")
        self.pr_identity = identity
        self.ambiguous = False

    def reconcile(self, identity: str | None) -> str:
        if identity is None:
            self.ambiguous = True
            raise ContractDenied("remote create remains ambiguous; budget spent")
        self.record_remote_result(identity)
        return identity


@dataclass(frozen=True)
class ProxyIntent:
    binding_hash: str
    host: str
    path: str
    method: str
    use: str
    audience: str
    expires_at: int
    nonce: str


@dataclass
class ProxyPolicy:
    """Exact destination/use allow-list with nonce replay protection."""

    now: int
    expected_binding_hash: str
    used_nonces: set[str] = field(default_factory=set)

    def authorize(self, intent: ProxyIntent) -> None:
        if intent.binding_hash != self.expected_binding_hash:
            raise ContractDenied("binding mismatch")
        if intent.expires_at <= self.now:
            raise ContractDenied("intent expired")
        if intent.nonce in self.used_nonces:
            raise ContractDenied("nonce replay")
        if intent.host not in {"github.com", "api.github.com"}:
            raise ContractDenied("host denied")
        if ":" in intent.host or intent.path.startswith("//") or ".." in intent.path:
            raise ContractDenied("alternate port or unsafe path denied")
        allowed = {
            ("github.com", "git-upload-pack", "fetch"),
            ("github.com", "git-receive-pack", "push"),
            ("api.github.com", "GET", "read"),
            ("api.github.com", "POST", "create-draft-pr"),
        }
        if (intent.host, intent.method, intent.use) not in allowed:
            raise ContractDenied("method/use denied")
        self.used_nonces.add(intent.nonce)


def sign_webhook(secret: bytes, raw_body: bytes) -> str:
    """Return GitHub's HMAC-SHA256 signature representation."""
    return "sha256=" + hmac.new(secret, raw_body, sha256).hexdigest()


def verify_webhook(
    *,
    secret: bytes,
    raw_body: bytes,
    signature: str,
    delivery_id: str,
    seen_deliveries: set[str],
    payload: dict[str, Any],
    expected: Binding,
) -> None:
    """Verify raw bytes, delivery dedupe, and full projection binding."""
    if not hmac.compare_digest(sign_webhook(secret, raw_body), signature):
        raise ContractDenied("webhook signature mismatch")
    if delivery_id in seen_deliveries:
        raise ContractDenied("duplicate delivery")
    repo = payload.get("repository", {})
    installation = payload.get("installation", {})
    pull = payload.get("pull_request", {})
    base = pull.get("base", {})
    head = pull.get("head", {})
    observed = (
        str(installation.get("id")),
        str(repo.get("node_id")),
        str(payload.get("tenant")),
        str(payload.get("workspace")),
        str(base.get("ref")),
        str(base.get("sha")),
        str(head.get("ref")),
        str(head.get("sha")),
    )
    required = (
        expected.installation,
        expected.repository_node,
        expected.tenant,
        expected.workspace,
        expected.base_ref,
        expected.base_sha,
        expected.head_ref,
        str(payload.get("expected_head_sha")),
    )
    if observed != required:
        raise ContractDenied("webhook projection binding mismatch")
    if payload.get("action") not in {"opened", "synchronize", "reopened", "closed"}:
        raise ContractDenied("event action denied")
    seen_deliveries.add(delivery_id)


def normalize_check_state(status: str, conclusion: str | None, observed_sha: str, head_sha: str) -> str:
    """Normalize a current-head check without defaulting unknown to green."""
    if observed_sha != head_sha:
        return "stale"
    if status != "completed":
        return "pending" if status in {"queued", "in_progress", "requested", "waiting"} else "unknown"
    if conclusion == "success":
        return "success"
    if conclusion in {"failure", "cancelled", "timed_out", "action_required"}:
        return "failure"
    if conclusion in {"neutral", "skipped"}:
        return conclusion
    return "unknown"

