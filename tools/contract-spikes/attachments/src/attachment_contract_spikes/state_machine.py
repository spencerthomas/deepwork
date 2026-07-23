"""Network-free quarantine, scanner, transfer, and lifecycle fakes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, replace
from enum import StrEnum


class ContractError(ValueError):
    """A fail-closed contract rejection."""


class State(StrEnum):
    QUARANTINED = "quarantined"
    CLEAN = "clean"
    UNSAFE = "unsafe"
    SCAN_ERROR = "scan-error"
    SCAN_TIMEOUT = "scan-timeout"
    SCAN_UNAVAILABLE = "scan-unavailable"
    TRANSFER_READY = "transfer-ready"
    TRANSFERRED = "transferred"
    REMOVED = "removed"
    DELETION_PENDING = "deletion-pending"
    DELETED = "deleted"


class Verdict(StrEnum):
    CLEAN = "clean"
    UNSAFE = "unsafe"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"


SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,119}$")
MAX_COUNT = 4
MAX_BYTES = {
    "bounded-text-file": 64 * 1024,
    "image": 2 * 1024 * 1024,
    "pdf": 5 * 1024 * 1024,
    "code": 128 * 1024,
}
DECLARED_TYPES = {
    "bounded-text-file": "text/plain",
    "image": "image/png",
    "pdf": "application/pdf",
    "code": "text/plain",
}


def detect_media_type(content: bytes) -> str:
    """Detect only the harmless fixture types needed by the spike."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if b"\x00" not in content:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            return "application/octet-stream"
        return "text/plain"
    return "application/octet-stream"


def validate_preflight(
    *,
    media_class: str,
    filename: str,
    declared_type: str,
    content: bytes,
    count: int = 1,
    expected_hash: str | None = None,
    existing_hashes: set[str] | None = None,
) -> str:
    """Apply deterministic count, media, size, name, and integrity policy."""
    if media_class not in MAX_BYTES:
        raise ContractError("unsupported-media")
    if count < 1 or count > MAX_COUNT:
        raise ContractError("count")
    if not content:
        raise ContractError("empty")
    if len(content) > MAX_BYTES[media_class]:
        raise ContractError("size")
    if (
        not SAFE_NAME.fullmatch(filename)
        or "/" in filename
        or "\\" in filename
        or filename in {".", ".."}
        or ".." in filename.split(".")
    ):
        raise ContractError("unsafe-filename")
    if declared_type != DECLARED_TYPES[media_class]:
        raise ContractError("declared-type")
    digest = hashlib.sha256(content).hexdigest()
    if expected_hash is not None and expected_hash != digest:
        raise ContractError("hash-mismatch")
    if existing_hashes is not None and digest in existing_hashes:
        raise ContractError("duplicate")
    detected = detect_media_type(content)
    if detected != declared_type:
        raise ContractError("detected-type-mismatch")
    return digest


@dataclass
class Attachment:
    """Durable metadata used by the deterministic lifecycle."""

    object_id: str
    actor_id: str
    workspace_id: str
    task_id: str
    media_class: str
    filename: str
    declared_type: str
    detected_type: str
    sha256: str
    size: int
    state: State = State.QUARANTINED
    agent_visible: bool = False
    audit: list[str] = field(default_factory=lambda: ["quarantine-created"])


@dataclass(frozen=True)
class TransferIntent:
    """A short-lived, destination-bound fake transfer authority."""

    intent_id: str
    object_id: str
    actor_id: str
    workspace_id: str
    task_id: str
    destination: str
    representation: str
    sha256: str
    size: int
    expires_at: int


@dataclass(frozen=True)
class TransferReceipt:
    """A hash- and size-bound fake transfer receipt."""

    receipt_id: str
    intent_id: str
    object_id: str
    sha256: str
    size: int


class FakeObjectStore:
    """An in-memory object store that never exposes quarantined bytes."""

    def __init__(self) -> None:
        self._bytes: dict[str, bytes] = {}
        self._objects: dict[str, Attachment] = {}
        self._sequence = 0

    def create(
        self,
        *,
        actor_id: str,
        workspace_id: str,
        task_id: str,
        media_class: str,
        filename: str,
        declared_type: str,
        content: bytes,
    ) -> Attachment:
        if not actor_id or not workspace_id or not task_id:
            raise ContractError("missing-binding")
        digest = validate_preflight(
            media_class=media_class,
            filename=filename,
            declared_type=declared_type,
            content=content,
        )
        self._sequence += 1
        object_id = f"obj-{self._sequence:04d}"
        attachment = Attachment(
            object_id=object_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            task_id=task_id,
            media_class=media_class,
            filename=filename,
            declared_type=declared_type,
            detected_type=detect_media_type(content),
            sha256=digest,
            size=len(content),
        )
        self._bytes[object_id] = bytes(content)
        self._objects[object_id] = attachment
        return attachment

    def metadata(self, object_id: str) -> Attachment:
        return self._objects[object_id]

    def bytes_for_scanner(self, object_id: str) -> bytes:
        attachment = self.metadata(object_id)
        if attachment.state is not State.QUARANTINED:
            raise ContractError("scanner-read-state")
        return self._bytes[object_id]

    def bytes_for_transfer(self, object_id: str) -> bytes:
        attachment = self.metadata(object_id)
        if attachment.state not in {State.TRANSFER_READY, State.TRANSFERRED}:
            raise ContractError("agent-visibility-denied")
        return self._bytes[object_id]

    def verify_integrity(self, object_id: str) -> bool:
        attachment = self.metadata(object_id)
        content = self._bytes[object_id]
        return (
            hashlib.sha256(content).hexdigest() == attachment.sha256
            and len(content) == attachment.size
            and detect_media_type(content) == attachment.detected_type
        )

    def remove(self, object_id: str) -> None:
        attachment = self.metadata(object_id)
        attachment.state = State.REMOVED
        attachment.agent_visible = False
        attachment.audit.append("removed")

    def delete(self, object_id: str, *, provider_failure: bool = False) -> None:
        attachment = self.metadata(object_id)
        if provider_failure:
            attachment.state = State.DELETION_PENDING
            attachment.audit.append("provider-deletion-unverified")
            return
        attachment.state = State.DELETED
        attachment.agent_visible = False
        attachment.audit.append("deleted")
        self._bytes.pop(object_id, None)

    def retry_delete(self, object_id: str) -> None:
        attachment = self.metadata(object_id)
        if attachment.state is not State.DELETION_PENDING:
            raise ContractError("delete-retry-state")
        self.delete(object_id)

    def recover(self, object_id: str) -> Attachment:
        """Return a process-restart copy without changing verdict or visibility."""
        attachment = self.metadata(object_id)
        recovered = replace(attachment, audit=list(attachment.audit))
        if recovered.state in {
            State.UNSAFE,
            State.SCAN_ERROR,
            State.SCAN_TIMEOUT,
            State.SCAN_UNAVAILABLE,
            State.QUARANTINED,
        }:
            recovered.agent_visible = False
        return recovered


class FakeScanner:
    """Return a configured untrusted verdict without network access."""

    def __init__(self, verdict: Verdict) -> None:
        self.verdict = verdict

    def scan(self, store: FakeObjectStore, object_id: str) -> Verdict:
        store.bytes_for_scanner(object_id)
        return self.verdict


def apply_scanner_result(attachment: Attachment, verdict: Verdict) -> None:
    """Fail closed; a clean verdict is necessary but cannot authorize transfer."""
    if attachment.state is not State.QUARANTINED:
        raise ContractError("scan-state")
    next_state = {
        Verdict.CLEAN: State.CLEAN,
        Verdict.UNSAFE: State.UNSAFE,
        Verdict.ERROR: State.SCAN_ERROR,
        Verdict.TIMEOUT: State.SCAN_TIMEOUT,
        Verdict.UNAVAILABLE: State.SCAN_UNAVAILABLE,
    }[verdict]
    attachment.state = next_state
    attachment.agent_visible = False
    attachment.audit.append(f"scan-{verdict.value}")


class FakeClassicRuntime:
    """A destination-bound fake; it is explicitly not Classic provider proof."""

    DESTINATION = "classic:assistant-synthetic"

    def __init__(self) -> None:
        self._sequence = 0
        self._receipts: dict[str, TransferReceipt] = {}

    def create_intent(
        self,
        attachment: Attachment,
        *,
        actor_id: str,
        workspace_id: str,
        task_id: str,
        destination: str,
        representation: str,
        now: int,
        ttl: int = 60,
    ) -> TransferIntent:
        if attachment.state is not State.CLEAN:
            raise ContractError("not-clean")
        if (
            actor_id != attachment.actor_id
            or workspace_id != attachment.workspace_id
            or task_id != attachment.task_id
        ):
            raise ContractError("binding-mismatch")
        if destination != self.DESTINATION:
            raise ContractError("destination")
        if ttl < 1 or ttl > 300:
            raise ContractError("expiry")
        self._sequence += 1
        attachment.state = State.TRANSFER_READY
        attachment.audit.append("transfer-intent")
        return TransferIntent(
            intent_id=f"intent-{self._sequence:04d}",
            object_id=attachment.object_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            task_id=task_id,
            destination=destination,
            representation=representation,
            sha256=attachment.sha256,
            size=attachment.size,
            expires_at=now + ttl,
        )

    def transfer(
        self,
        store: FakeObjectStore,
        attachment: Attachment,
        intent: TransferIntent,
        *,
        now: int,
        actor_id: str,
        workspace_id: str,
        task_id: str,
        destination: str,
        redirect: bool = False,
        partial: bool = False,
    ) -> TransferReceipt:
        if redirect:
            raise ContractError("redirect")
        if partial:
            raise ContractError("range-partial")
        if now > intent.expires_at:
            raise ContractError("stale-grant")
        if (
            actor_id != intent.actor_id
            or workspace_id != intent.workspace_id
            or task_id != intent.task_id
            or destination != intent.destination
        ):
            raise ContractError("intent-binding-mismatch")
        if attachment.state not in {State.TRANSFER_READY, State.TRANSFERRED}:
            raise ContractError("transfer-state")
        content = store.bytes_for_transfer(attachment.object_id)
        if hashlib.sha256(content).hexdigest() != intent.sha256:
            raise ContractError("hash-mismatch")
        if len(content) != intent.size:
            raise ContractError("size-mismatch")
        if intent.intent_id in self._receipts:
            return self._receipts[intent.intent_id]
        receipt = TransferReceipt(
            receipt_id=f"receipt-{intent.intent_id}",
            intent_id=intent.intent_id,
            object_id=attachment.object_id,
            sha256=intent.sha256,
            size=intent.size,
        )
        self._receipts[intent.intent_id] = receipt
        attachment.state = State.TRANSFERRED
        attachment.agent_visible = True
        attachment.audit.append("transfer-receipt")
        return receipt
