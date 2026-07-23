"""Fail-closed live-profile preflight and durable grant claim.

No credentialed transport is enabled while the sandbox/proxy dependency is
blocked. This module validates the exact external authority and atomically
claims it before a future accepted transport can be composed.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import time

from coding_github_spikes.contracts import Binding, ContractDenied


@dataclass(frozen=True)
class MutationGrant:
    grant_id: str
    issuer: str
    reviewer: str
    expires_at: int
    maximum_pull_requests: int
    allowed_operations: tuple[str, ...]
    binding: Binding
    digest: str


def load_mutation_grant(path: Path, *, expected: Binding, now: int | None = None) -> MutationGrant:
    """Validate a regular owner-only, secret-free grant and its exact tuple."""
    observed_now = int(time.time()) if now is None else now
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ContractDenied("mutation grant must be a regular non-symlink file")
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise ContractDenied("mutation grant ownership or mode is unsafe")
    raw = path.read_bytes()
    value = json.loads(raw)
    forbidden = {"token", "secret", "private_key", "authorization", "password"}
    if forbidden.intersection(value):
        raise ContractDenied("mutation grant contains a forbidden credential field")
    grant_binding = Binding(**value["binding"])
    if grant_binding != expected:
        raise ContractDenied("mutation grant tuple mismatch")
    expected.validate()
    allowed = tuple(value["allowed_operations"])
    if set(allowed) != {"create_ref", "push", "create_draft_pr"}:
        raise ContractDenied("mutation grant operations are not exact")
    if value["maximum_pull_requests"] != 1:
        raise ContractDenied("mutation grant PR budget must equal one")
    if int(value["expires_at"]) <= observed_now:
        raise ContractDenied("mutation grant expired")
    if not value.get("issuer") or not value.get("reviewer") or value["issuer"] == value["reviewer"]:
        raise ContractDenied("grant issuer/reviewer separation required")
    return MutationGrant(
        grant_id=value["grant_id"],
        issuer=value["issuer"],
        reviewer=value["reviewer"],
        expires_at=int(value["expires_at"]),
        maximum_pull_requests=1,
        allowed_operations=allowed,
        binding=grant_binding,
        digest=f"sha256:{sha256(raw).hexdigest()}",
    )


def claim_grant(grant: MutationGrant, claim_directory: Path) -> Path:
    """Atomically and durably claim a unique grant across workers."""
    claim_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    claim = claim_directory / f"{grant.grant_id}.claim"
    payload = json.dumps(
        {"grant_id": grant.grant_id, "grant_hash": grant.digest, "binding_hash": grant.binding.digest()},
        sort_keys=True,
    ).encode()
    try:
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ContractDenied("mutation grant already claimed") from exc
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    return claim


def require_accepted_upstream(upstream: dict[str, object]) -> None:
    """Reject missing, unreviewed, versionless, or hashless sandbox evidence."""
    hashes = upstream.get("hashes", {})
    if (
        upstream.get("state") != "accepted-live"
        or upstream.get("review_verdict") != "accepted"
        or not upstream.get("reviewed_commit")
        or not isinstance(hashes, dict)
        or not all(hashes.get(name) for name in ("matrix_scope", "matrix", "versions", "fixtures"))
        or not upstream.get("consumed_rows")
    ):
        raise ContractDenied("accepted sandbox/proxy evidence is absent")
