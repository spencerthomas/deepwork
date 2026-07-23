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
    app_id: str
    installation: str
    account_node: str
    repository_node: str
    repository_owner: str
    repository_name: str
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
    expected_binding: Binding
    max_ttl_seconds: int = 900
    used_nonces: set[str] = field(default_factory=set)

    def authorize(self, intent: ProxyIntent) -> None:
        binding = self.expected_binding
        binding.validate()
        if intent.binding_hash != binding.digest():
            raise ContractDenied("binding mismatch")
        if intent.expires_at <= self.now:
            raise ContractDenied("intent expired")
        if intent.expires_at > self.now + self.max_ttl_seconds:
            raise ContractDenied("intent TTL exceeds policy")
        if intent.nonce in self.used_nonces:
            raise ContractDenied("nonce replay")
        expected_audience = f"github-installation:{binding.installation}"
        if intent.audience != expected_audience:
            raise ContractDenied("audience mismatch")
        if intent.host not in {"github.com", "api.github.com"}:
            raise ContractDenied("host denied")
        if ":" in intent.host or intent.path.startswith("//") or ".." in intent.path:
            raise ContractDenied("alternate port or unsafe path denied")
        repository_path = f"/{binding.repository_owner}/{binding.repository_name}.git"
        api_root = f"/repos/{binding.repository_owner}/{binding.repository_name}"
        allowed = {
            ("github.com", repository_path, "git-upload-pack", "fetch"),
            ("github.com", repository_path, "git-receive-pack", "push"),
            ("api.github.com", api_root, "GET", "read"),
            ("api.github.com", f"{api_root}/pulls", "GET", "read"),
            ("api.github.com", f"{api_root}/pulls", "POST", "create-draft-pr"),
            ("api.github.com", f"{api_root}/commits", "GET", "read"),
        }
        if (intent.host, intent.path, intent.method, intent.use) not in allowed:
            raise ContractDenied("path/method/use denied")
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
    event_name: str,
    delivered_at: int,
    now: int,
    seen_deliveries: set[str],
    expected: "WebhookExpectation",
    current_authorized_actor: str,
) -> dict[str, Any]:
    """Verify raw bytes, delivery dedupe, and full projection binding."""
    if not hmac.compare_digest(sign_webhook(secret, raw_body), signature):
        raise ContractDenied("webhook signature mismatch")
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractDenied("invalid signed webhook JSON") from exc
    if delivery_id in seen_deliveries:
        raise ContractDenied("duplicate delivery")
    if delivered_at > now or now - delivered_at > expected.max_age_seconds:
        raise ContractDenied("webhook timestamp outside freshness window")
    if event_name != expected.event_name:
        raise ContractDenied("event type denied")
    binding = expected.binding
    binding.validate()
    if not expected.current_authorized or current_authorized_actor != binding.actor:
        raise ContractDenied("current actor authorization denied")
    repo = payload.get("repository", {})
    installation = payload.get("installation", {})
    pull = payload.get("pull_request", {})
    base = pull.get("base", {})
    head = pull.get("head", {})
    observed = (
        str(payload.get("hook", {}).get("app_id")),
        str(installation.get("id")),
        str(repo.get("node_id")),
        str(repo.get("owner", {}).get("node_id")),
        str(repo.get("owner", {}).get("login")),
        str(repo.get("name")),
        str(pull.get("node_id")),
        str(base.get("ref")),
        str(base.get("sha")),
        str(head.get("ref")),
        str(head.get("sha")),
    )
    required = (
        binding.app_id,
        binding.installation,
        binding.repository_node,
        binding.account_node,
        binding.repository_owner,
        binding.repository_name,
        expected.pr_node,
        binding.base_ref,
        binding.base_sha,
        binding.head_ref,
        expected.current_head_sha,
    )
    if observed != required:
        raise ContractDenied("webhook projection binding mismatch")
    if payload.get("action") not in expected.allowed_actions:
        raise ContractDenied("event action denied")
    seen_deliveries.add(delivery_id)
    return payload


@dataclass(frozen=True)
class WebhookExpectation:
    """Trusted application state used after raw-byte signature verification."""

    binding: Binding
    pr_node: str
    current_head_sha: str
    event_name: str = "pull_request"
    allowed_actions: tuple[str, ...] = ("opened", "synchronize", "reopened", "closed")
    current_authorized: bool = True
    max_age_seconds: int = 300


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
