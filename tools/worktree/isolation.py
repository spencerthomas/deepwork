"""Deterministic, fail-closed namespace isolation primitives.

The module is intentionally standard-library only.  It does not start processes,
open sockets, connect to a database, or contact a provider.  Product-demo
orchestration must supply those capabilities through a separately reviewed
driver.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping


MANIFEST_VERSION = 1
NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MAX_NAMESPACE_LENGTH = 48
DEFAULT_STATE_DIR = Path("/tmp").resolve() / "deepwork-worktree-harness-v1"
PORT_BASE = 20_000
PORT_SPAN = 12_000
PORT_BLOCK_SIZE = 4
RESOURCE_FIELDS = (
    "workspace_path",
    "ports",
    "database",
    "schema",
    "object_prefix",
    "browser",
    "telemetry",
    "logs_path",
    "proof_path",
    "process_identities",
)
FORBIDDEN_EVIDENCE_KEYS = {
    "authorization",
    "authref",
    "credential",
    "credentials",
    "cookie",
    "customer",
    "environment",
    "password",
    "provider_payload",
    "provider_response",
    "raw_payload",
    "raw_response",
    "response_payload",
    "secret",
    "teardown_token",
    "tenant",
    "token",
    "upstream_payload",
    "upstream_response",
}
FORBIDDEN_EVIDENCE_PATTERNS = (
    re.compile(r"(?i)\b(?:authorization|password|secret|token)\s*[:=]"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class IsolationError(RuntimeError):
    """Base error for a rejected isolation operation."""


class UnsafeNamespace(IsolationError):
    """The requested namespace is not explicit and safely bounded."""


class ReservationConflict(IsolationError):
    """A namespace or one of its resources is already reserved."""


class OwnershipError(IsolationError):
    """The caller cannot operate on the requested namespace."""


class EvidenceError(IsolationError):
    """Evidence is unsafe, incomplete, or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class TeardownResult:
    namespace: str
    state: str
    removed_fixture_paths: tuple[str, ...] = ()


def validate_namespace(namespace: str) -> str:
    """Return a safe namespace or raise without normalization."""

    if not isinstance(namespace, str):
        raise UnsafeNamespace("namespace must be an explicit string")
    if not namespace or len(namespace) > MAX_NAMESPACE_LENGTH:
        raise UnsafeNamespace(
            f"namespace length must be between 1 and {MAX_NAMESPACE_LENGTH}"
        )
    if not NAMESPACE_RE.fullmatch(namespace):
        raise UnsafeNamespace(
            "namespace must match ^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
        )
    return namespace


def canonical_root(root: str | Path) -> Path:
    """Resolve an existing directory without accepting broad roots."""

    candidate = Path(root).expanduser().resolve(strict=True)
    if not candidate.is_dir():
        raise IsolationError(f"workspace root is not a directory: {candidate}")
    if candidate == Path(candidate.anchor):
        raise IsolationError("filesystem root is not a valid workspace")
    if candidate == Path.home().resolve():
        raise IsolationError("home directory is not a valid workspace")
    return candidate


def _digest(namespace: str) -> str:
    return hashlib.sha256(f"deepwork-worktree-v1:{namespace}".encode()).hexdigest()


def _safe_component(namespace: str) -> str:
    return namespace.replace("-", "_")


def allocate_manifest(
    *,
    root: str | Path,
    namespace: str,
    evidence_dir: str | Path,
    teardown_token: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic resource manifest for an explicit namespace."""

    workspace_root = canonical_root(root)
    safe_namespace = validate_namespace(namespace)
    digest = _digest(safe_namespace)
    block = int(digest[:8], 16) % (PORT_SPAN // PORT_BLOCK_SIZE)
    first_port = PORT_BASE + block * PORT_BLOCK_SIZE
    short = digest[:12]
    component = _safe_component(safe_namespace)
    proof_dir = Path(evidence_dir).expanduser().resolve(strict=False)
    workspace = workspace_root / ".deepwork" / "worktrees" / safe_namespace
    token = teardown_token or secrets.token_urlsafe(32)

    return {
        "manifest_version": MANIFEST_VERSION,
        "namespace": safe_namespace,
        "workspace_path": str(workspace),
        "evidence_root": str(proof_dir),
        "ports": {
            "api": first_port,
            "web": first_port + 1,
            "worker": first_port + 2,
            "telemetry": first_port + 3,
        },
        "database": f"deepwork_{component}_{short}",
        "schema": f"dw_{component}_{short}",
        "object_prefix": f"worktrees/{safe_namespace}/{short}/",
        "browser": {
            "origin": f"http://127.0.0.1:{first_port + 1}",
            "storage_key": f"deepwork:isolation:{safe_namespace}:{short}",
        },
        "telemetry": {
            "resource_attributes": {
                "deepwork.namespace": safe_namespace,
                "service.namespace": f"deepwork-fixture-{short}",
                "deployment.mode": "fixture",
            }
        },
        "logs_path": str(workspace / "logs"),
        "proof_path": str(proof_dir / safe_namespace),
        "process_identities": {
            name: {
                "namespace": safe_namespace,
                "identity": f"{safe_namespace}:{name}:{short}",
                "pid": None,
            }
            for name in ("api", "web", "worker")
        },
        "restart_rule": "reuse-reserved-resources-with-exact-teardown-token",
        "teardown_token": token,
    }


def public_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return evidence-safe dimensions without local paths or ownership token."""

    namespace = str(manifest["namespace"])
    return {
        "manifest_version": manifest["manifest_version"],
        "namespace": namespace,
        "ports": dict(manifest["ports"]),
        "database": manifest["database"],
        "schema": manifest["schema"],
        "object_prefix": manifest["object_prefix"],
        "browser": dict(manifest["browser"]),
        "telemetry": json.loads(json.dumps(manifest["telemetry"])),
        "process_identities": {
            name: {"identity": value["identity"], "namespace": value["namespace"]}
            for name, value in manifest["process_identities"].items()
        },
        "restart_rule": manifest["restart_rule"],
        "workspace_id": f"synthetic-workspace-{namespace}",
        "logs_id": f"synthetic-logs-{namespace}",
        "proof_id": f"synthetic-proof-{namespace}",
    }


def differing_dimensions(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> dict[str, bool]:
    """Compare every required allocation dimension."""

    result = {
        field: left[field] != right[field] for field in RESOURCE_FIELDS
    }
    result["ports"] = set(left["ports"].values()).isdisjoint(
        right["ports"].values()
    )
    return result


def assert_distinct(left: Mapping[str, Any], right: Mapping[str, Any]) -> None:
    duplicates = [
        field for field, differs in differing_dimensions(left, right).items() if not differs
    ]
    if duplicates:
        raise ReservationConflict(
            "namespaces share required resources: " + ", ".join(duplicates)
        )


class ReservationStore:
    """Atomic manifest reservations serialized by an advisory file lock."""

    def __init__(self, state_dir: str | Path = DEFAULT_STATE_DIR) -> None:
        self.unresolved_state_dir = Path(state_dir).expanduser().absolute()
        for candidate in (
            self.unresolved_state_dir,
            *self.unresolved_state_dir.parents,
        ):
            if candidate.is_symlink():
                raise IsolationError("reservation state cannot traverse a symlink")
        self.state_dir = self.unresolved_state_dir.resolve(strict=False)
        if self.state_dir == Path(self.state_dir.anchor):
            raise IsolationError("reservation state cannot be filesystem root")
        if self.state_dir == Path.home().resolve():
            raise IsolationError("reservation state cannot be the home directory")
        if self.state_dir in {
            Path("/tmp").resolve(),
            Path("/var/tmp").resolve(),
        }:
            raise IsolationError("reservation state cannot be a broad temporary root")

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._validate_private_path(self.state_dir, directory=True)
        lock_path = self.state_dir / ".lock"
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(lock_path, flags, 0o600)
        except OSError as error:
            raise IsolationError("reservation lock is unsafe") from error
        try:
            lock_stat = os.fstat(descriptor)
            self._validate_private_stat(lock_stat, "reservation lock")
        except Exception:
            os.close(descriptor)
            raise
        with os.fdopen(descriptor, "a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _validate_private_path(self, path: Path, *, directory: bool = False) -> None:
        if path.is_symlink():
            raise IsolationError("private reservation path cannot be a symlink")
        try:
            path_stat = path.stat()
        except OSError as error:
            raise IsolationError("private reservation path is unavailable") from error
        if directory and not stat.S_ISDIR(path_stat.st_mode):
            raise IsolationError("reservation state is not a directory")
        self._validate_private_stat(path_stat, "reservation state")

    @staticmethod
    def _validate_private_stat(path_stat: os.stat_result, label: str) -> None:
        if path_stat.st_uid != os.geteuid():
            raise IsolationError(f"{label} is not owned by the current user")
        if stat.S_IMODE(path_stat.st_mode) & 0o077:
            raise IsolationError(f"{label} has group or world permissions")

    def _path(self, namespace: str) -> Path:
        return self.state_dir / f"{validate_namespace(namespace)}.json"

    def _receipt_path(self, run_nonce: str) -> Path:
        if not isinstance(run_nonce, str) or not re.fullmatch(
            r"[a-f0-9]{32,64}", run_nonce
        ):
            raise IsolationError("receipt run nonce is invalid")
        return self.state_dir / f".receipt-{run_nonce}.json"

    def _release_path(self, release_id: str) -> Path:
        if not isinstance(release_id, str) or not re.fullmatch(
            r"[a-f0-9]{32,64}", release_id
        ):
            raise IsolationError("release transaction identifier is invalid")
        return self.state_dir / f".release-{release_id}.json"

    def active_namespaces(self) -> tuple[str, ...]:
        """List identifiers only; private peer manifests never leave the store."""

        with self._locked():
            return tuple(
                sorted(str(manifest["namespace"]) for manifest in self._list_unlocked())
            )

    def owned_manifest_path(
        self, *, namespace: str, teardown_token: str, root: str | Path
    ) -> Path:
        """Return an owned private manifest path for a reviewed driver."""

        safe_namespace = validate_namespace(namespace)
        expected_root = canonical_root(root)
        with self._locked():
            path = self._path(safe_namespace)
            if not path.exists():
                raise OwnershipError(f"namespace is not reserved: {safe_namespace}")
            manifest = self._read_private_json(path)
            _require_owner(manifest, teardown_token, expected_root)
            return path

    def recovery_manifest(
        self, *, namespace: str, root: str | Path
    ) -> tuple[Path, dict[str, Any]]:
        """Load one private reservation for the reviewed recovery protocol."""

        safe_namespace = validate_namespace(namespace)
        expected_root = canonical_root(root)
        with self._locked():
            path = self._path(safe_namespace)
            if not path.exists():
                raise OwnershipError(f"namespace is not reserved: {safe_namespace}")
            manifest = self._read_private_json(path)
            workspace = Path(str(manifest["workspace_path"])).resolve(strict=False)
            expected_parent = expected_root / ".deepwork" / "worktrees"
            if (
                workspace.parent != expected_parent
                or workspace.name != safe_namespace
            ):
                raise OwnershipError(
                    "recovery reservation does not belong to requested workspace"
                )
            return path, manifest

    def create_receipt_record(
        self,
        *,
        run_nonce: str,
        driver_revision: str,
        driver_sha256: str,
        contract_semantic_sha256: str,
        namespaces: list[str],
    ) -> dict[str, Any]:
        """Create an unpredictable private authority record before driver execution."""

        path = self._receipt_path(run_nonce)
        safe_namespaces = [validate_namespace(namespace) for namespace in namespaces]
        if len(safe_namespaces) != 2 or len(set(safe_namespaces)) != 2:
            raise IsolationError("receipt authority requires two distinct namespaces")
        record = {
            "schema_version": 1,
            "run_nonce": run_nonce,
            "driver_revision": driver_revision,
            "driver_sha256": driver_sha256,
            "contract_semantic_sha256": contract_semantic_sha256,
            "namespaces": safe_namespaces,
            "receipt_key_hex": secrets.token_hex(32),
        }
        _validate_receipt_record(record)
        with self._locked():
            if path.exists():
                raise ReservationConflict("receipt authority already exists")
            _write_json_atomic(path, record, mode=0o600)
        return record

    def receipt_record(self, *, run_nonce: str) -> dict[str, Any]:
        """Load one private receipt authority record, failing closed if absent."""

        path = self._receipt_path(run_nonce)
        with self._locked():
            if not path.exists():
                raise OwnershipError("private receipt authority is unavailable")
            record = self._read_private_json(path)
            _validate_receipt_record(record)
            return record

    def release_pair(
        self,
        *,
        release_id: str,
        namespace_a: str,
        teardown_token_a: str,
        root_a: str | Path,
        namespace_b: str,
        teardown_token_b: str,
        root_b: str | Path,
    ) -> tuple[TeardownResult, TeardownResult]:
        """Stage both private release records, then delete both reservations."""

        transaction = {
            "schema_version": 1,
            "release_id": release_id,
            "state": "staged",
            "entries": [
                {
                    "namespace": validate_namespace(namespace_a),
                    "teardown_token": teardown_token_a,
                    "workspace_root": str(canonical_root(root_a)),
                },
                {
                    "namespace": validate_namespace(namespace_b),
                    "teardown_token": teardown_token_b,
                    "workspace_root": str(canonical_root(root_b)),
                },
            ],
        }
        _validate_release_transaction(transaction)
        path = self._release_path(release_id)
        with self._locked():
            if path.exists():
                existing = self._read_private_json(path)
                _validate_release_transaction(existing)
                if existing["entries"] != transaction["entries"]:
                    raise OwnershipError(
                        "release transaction does not match exact reservations"
                    )
            else:
                _write_json_atomic(path, transaction, mode=0o600)
        return self.commit_pair_release(release_id=release_id)

    def release_pair_pending(self, *, release_id: str) -> bool:
        """Return whether a private staged release can be resumed."""

        path = self._release_path(release_id)
        with self._locked():
            if not path.exists():
                return False
            transaction = self._read_private_json(path)
            _validate_release_transaction(transaction)
            return transaction["state"] != "released"

    def commit_pair_release(
        self, *, release_id: str
    ) -> tuple[TeardownResult, TeardownResult]:
        """Idempotently finish a staged two-reservation release transaction."""

        transaction_path = self._release_path(release_id)
        with self._locked():
            if not transaction_path.exists():
                raise OwnershipError("release transaction is unavailable")
            transaction = self._read_private_json(transaction_path)
            _validate_release_transaction(transaction)
            entries = transaction["entries"]
            staged: list[tuple[dict[str, Any], Path, Path, Path]] = []
            for entry in entries:
                namespace = entry["namespace"]
                expected_root = canonical_root(entry["workspace_root"])
                manifest_path = self._path(namespace)
                tombstone = self.state_dir / f"{namespace}.released.json"
                if manifest_path.exists():
                    manifest = self._read_private_json(manifest_path)
                    _require_owner(
                        manifest, entry["teardown_token"], expected_root
                    )
                elif tombstone.exists():
                    released = self._read_private_json(tombstone)
                    _require_released_owner(
                        released, entry["teardown_token"], expected_root
                    )
                    manifest = {}
                else:
                    raise OwnershipError(
                        f"release reservation state is unavailable: {namespace}"
                    )
                staged.append((entry, expected_root, manifest_path, tombstone))

            for entry, expected_root, manifest_path, tombstone in staged:
                if tombstone.exists():
                    released = self._read_private_json(tombstone)
                    _require_released_owner(
                        released, entry["teardown_token"], expected_root
                    )
                    continue
                manifest = self._read_private_json(manifest_path)
                released = {
                    "namespace": entry["namespace"],
                    "workspace_path": manifest["workspace_path"],
                    "teardown_token_digest": hashlib.sha256(
                        entry["teardown_token"].encode()
                    ).hexdigest(),
                }
                _write_json_atomic(tombstone, released, mode=0o600)

            transaction["state"] = "tombstones-staged"
            _write_json_atomic(transaction_path, transaction, mode=0o600)
            results: list[TeardownResult] = []
            for entry, _, manifest_path, _ in staged:
                if manifest_path.exists():
                    _unlink_reservation(manifest_path)
                    state = "released"
                else:
                    state = "already-absent"
                results.append(TeardownResult(entry["namespace"], state))
            transaction["state"] = "released"
            _write_json_atomic(transaction_path, transaction, mode=0o600)
            return results[0], results[1]

    def _list_unlocked(self) -> list[dict[str, Any]]:
        manifests = []
        for path in sorted(self.state_dir.glob("*.json")):
            if path.name.startswith(".") or path.name.endswith(".released.json"):
                continue
            manifests.append(self._read_private_json(path))
        return manifests

    def _read_private_json(self, path: Path) -> dict[str, Any]:
        self._validate_private_path(path)
        return _read_json(path)

    def reserve(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        namespace = validate_namespace(str(manifest.get("namespace", "")))
        _validate_manifest(manifest)
        path = self._path(namespace)
        with self._locked():
            if path.exists():
                raise ReservationConflict(f"namespace already reserved: {namespace}")
            for peer in self._list_unlocked():
                assert_distinct(manifest, peer)
            payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            try:
                descriptor = os.open(
                    path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
                )
            except FileExistsError as error:
                raise ReservationConflict(
                    f"namespace already reserved: {namespace}"
                ) from error
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
        return dict(manifest)

    def restart(
        self, *, namespace: str, teardown_token: str, root: str | Path
    ) -> dict[str, Any]:
        """Explicitly reattach only to an exactly owned reservation."""

        safe_namespace = validate_namespace(namespace)
        expected_root = canonical_root(root)
        with self._locked():
            path = self._path(safe_namespace)
            if not path.exists():
                raise OwnershipError(f"namespace is not reserved: {safe_namespace}")
            manifest = self._read_private_json(path)
            _require_owner(manifest, teardown_token, expected_root)
            return manifest

    def teardown(
        self,
        *,
        namespace: str,
        teardown_token: str,
        root: str | Path,
        remove_fixture_paths: bool = False,
    ) -> TeardownResult:
        """Release one exact reservation; repeated exact teardown is harmless."""

        safe_namespace = validate_namespace(namespace)
        expected_root = canonical_root(root)
        path = self._path(safe_namespace)
        tombstone = self.state_dir / f"{safe_namespace}.released.json"
        with self._locked():
            if not path.exists():
                if tombstone.exists():
                    released = self._read_private_json(tombstone)
                    _require_released_owner(released, teardown_token, expected_root)
                    return TeardownResult(safe_namespace, "already-absent")
                raise OwnershipError(f"namespace is not reserved: {safe_namespace}")
            manifest = self._read_private_json(path)
            _require_owner(manifest, teardown_token, expected_root)
            removed: list[str] = []
            if remove_fixture_paths:
                for field in ("logs_path", "proof_path"):
                    candidate = Path(manifest[field]).resolve(strict=False)
                    _remove_exact_fixture_path(
                        candidate=candidate,
                        namespace=safe_namespace,
                        manifest=manifest,
                    )
                    removed.append(field)
            released = {
                "namespace": safe_namespace,
                "workspace_path": manifest["workspace_path"],
                "teardown_token_digest": hashlib.sha256(
                    manifest["teardown_token"].encode()
                ).hexdigest(),
            }
            _write_json_atomic(tombstone, released, mode=0o600)
            path.unlink()
            return TeardownResult(
                safe_namespace, "released", tuple(sorted(removed))
            )


def _validate_receipt_record(record: Mapping[str, Any]) -> None:
    expected = {
        "contract_semantic_sha256",
        "driver_revision",
        "driver_sha256",
        "namespaces",
        "receipt_key_hex",
        "run_nonce",
        "schema_version",
    }
    if set(record) != expected or record.get("schema_version") != 1:
        raise IsolationError("private receipt authority schema is invalid")
    if not isinstance(record.get("namespaces"), list) or not all(
        isinstance(namespace, str) for namespace in record["namespaces"]
    ):
        raise IsolationError("private receipt namespaces are invalid")
    if len(record["namespaces"]) != 2 or len(set(record["namespaces"])) != 2:
        raise IsolationError("private receipt requires two distinct namespaces")
    for namespace in record["namespaces"]:
        validate_namespace(namespace)
    patterns = {
        "run_nonce": r"[a-f0-9]{32,64}",
        "driver_revision": r"[a-f0-9]{40}",
        "driver_sha256": r"[a-f0-9]{64}",
        "contract_semantic_sha256": r"[a-f0-9]{64}",
        "receipt_key_hex": r"[a-f0-9]{64}",
    }
    if any(
        not isinstance(record.get(field), str)
        or not re.fullmatch(pattern, record[field])
        for field, pattern in patterns.items()
    ):
        raise IsolationError("private receipt authority contains invalid values")


def _validate_release_transaction(transaction: Mapping[str, Any]) -> None:
    if set(transaction) != {"entries", "release_id", "schema_version", "state"}:
        raise IsolationError("private release transaction schema is invalid")
    if transaction.get("schema_version") != 1 or transaction.get("state") not in {
        "staged",
        "tombstones-staged",
        "released",
    }:
        raise IsolationError("private release transaction state is invalid")
    release_id = transaction.get("release_id")
    if not isinstance(release_id, str) or not re.fullmatch(
        r"[a-f0-9]{32,64}", release_id
    ):
        raise IsolationError("private release transaction identifier is invalid")
    entries = transaction.get("entries")
    if not isinstance(entries, list) or len(entries) != 2:
        raise IsolationError("private release transaction requires two entries")
    namespaces: list[str] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {
            "namespace",
            "teardown_token",
            "workspace_root",
        }:
            raise IsolationError("private release entry schema is invalid")
        namespace = validate_namespace(entry["namespace"])
        token = entry["teardown_token"]
        root = entry["workspace_root"]
        if (
            not isinstance(token, str)
            or len(token) < 32
            or not isinstance(root, str)
        ):
            raise IsolationError("private release entry values are invalid")
        canonical_root(root)
        namespaces.append(namespace)
    if len(set(namespaces)) != 2:
        raise IsolationError("private release namespaces must be distinct")


def _unlink_reservation(path: Path) -> None:
    """Single injection seam for crash-safe pair-release tests."""

    path.unlink()


def _require_owner(
    manifest: Mapping[str, Any], teardown_token: str, expected_root: Path
) -> None:
    if not teardown_token or not secrets.compare_digest(
        str(manifest.get("teardown_token", "")), teardown_token
    ):
        raise OwnershipError("exact teardown token is required")
    workspace = Path(str(manifest["workspace_path"])).resolve(strict=False)
    expected_parent = expected_root / ".deepwork" / "worktrees"
    if workspace.parent != expected_parent or workspace.name != manifest["namespace"]:
        raise OwnershipError("reservation does not belong to the requested workspace")


def _require_released_owner(
    released: Mapping[str, Any], teardown_token: str, expected_root: Path
) -> None:
    candidate_digest = hashlib.sha256(teardown_token.encode()).hexdigest()
    if not teardown_token or not secrets.compare_digest(
        str(released.get("teardown_token_digest", "")), candidate_digest
    ):
        raise OwnershipError("exact teardown token is required")
    workspace = Path(str(released["workspace_path"])).resolve(strict=False)
    expected_parent = expected_root / ".deepwork" / "worktrees"
    if workspace.parent != expected_parent or workspace.name != released["namespace"]:
        raise OwnershipError("release record does not belong to the requested workspace")


def _remove_exact_fixture_path(
    *, candidate: Path, namespace: str, manifest: Mapping[str, Any]
) -> None:
    """Remove only an exact manifest path containing the owned namespace."""

    allowed = {
        Path(str(manifest["logs_path"])).resolve(strict=False),
        Path(str(manifest["proof_path"])).resolve(strict=False),
    }
    if candidate not in allowed:
        raise OwnershipError("teardown path is not an exact manifest path")
    if namespace not in candidate.parts:
        raise OwnershipError("teardown path does not contain the exact namespace")
    if candidate == Path(candidate.anchor) or candidate == Path.home().resolve():
        raise OwnershipError("teardown refuses broad paths")
    workspace = Path(str(manifest["workspace_path"])).resolve(strict=False)
    evidence_root = Path(str(manifest["evidence_root"])).resolve(strict=False)
    allowed_relations = (
        candidate == workspace / "logs"
        or (
            candidate.parent == evidence_root
            and candidate.name == namespace
            and evidence_root not in {Path(evidence_root.anchor), Path.home().resolve()}
            and len(candidate.parts) >= 3
        )
    )
    if not allowed_relations:
        raise OwnershipError("teardown path is not safely contained")
    if candidate.exists():
        if candidate.is_symlink():
            raise OwnershipError("teardown refuses symlink paths")
        if not candidate.is_dir():
            raise OwnershipError("teardown path is not a directory")
        shutil.rmtree(candidate)


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    required = {
        "manifest_version",
        "namespace",
        *RESOURCE_FIELDS,
        "restart_rule",
        "teardown_token",
        "evidence_root",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        raise IsolationError("manifest is missing fields: " + ", ".join(missing))
    if manifest["manifest_version"] != MANIFEST_VERSION:
        raise IsolationError("unsupported manifest version")
    validate_namespace(str(manifest["namespace"]))
    token = manifest["teardown_token"]
    if not isinstance(token, str) or len(token) < 32:
        raise IsolationError("manifest teardown token is invalid")
    ports = manifest["ports"]
    if set(ports) != {"api", "web", "worker", "telemetry"}:
        raise IsolationError("manifest must allocate all four named ports")
    if len(set(ports.values())) != len(ports):
        raise IsolationError("manifest ports must be distinct")
    if not all(isinstance(port, int) and 1024 <= port <= 65535 for port in ports.values()):
        raise IsolationError("manifest contains an unsafe port")


def validate_evidence(value: Any) -> None:
    """Reject credential-like keys and values anywhere in evidence."""

    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in FORBIDDEN_EVIDENCE_KEYS):
                raise EvidenceError(f"forbidden evidence key: {key}")
            validate_evidence(nested)
    elif isinstance(value, list | tuple):
        for nested in value:
            validate_evidence(nested)
    elif isinstance(value, str):
        if value.startswith(("/", "~/")) or re.search(
            r"(?:^|[ =])(?:/Users/|/home/)", value
        ):
            raise EvidenceError("personal or absolute path rejected from evidence")
        for pattern in FORBIDDEN_EVIDENCE_PATTERNS:
            if pattern.search(value):
                raise EvidenceError("credential-like value rejected from evidence")


def write_evidence(path: str | Path, evidence: Mapping[str, Any]) -> None:
    validate_evidence(evidence)
    destination = Path(path).expanduser().resolve(strict=False)
    if destination == Path(destination.anchor):
        raise EvidenceError("evidence path cannot be filesystem root")
    unresolved = Path(path).expanduser().absolute()
    for candidate in (unresolved, *unresolved.parents):
        if candidate.is_symlink():
            raise EvidenceError("evidence path cannot traverse a symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(destination, evidence, mode=0o644)


def _write_json_atomic(
    path: Path, value: Mapping[str, Any], *, mode: int
) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise IsolationError(f"invalid reservation file: {path.name}") from error
    if not isinstance(value, dict):
        raise IsolationError(f"reservation is not an object: {path.name}")
    return value
