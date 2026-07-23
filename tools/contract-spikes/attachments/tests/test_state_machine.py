from __future__ import annotations

import hashlib
import socket

import pytest

from attachment_contract_spikes.state_machine import (
    ContractError,
    FakeClassicRuntime,
    FakeObjectStore,
    FakeScanner,
    State,
    Verdict,
    apply_scanner_result,
    validate_preflight,
)


TEXT = b"Synthetic bounded text attachment.\n"
PNG = b"\x89PNG\r\n\x1a\n"
PDF = b"%PDF-1.4\n% harmless synthetic fixture\n"
CODE = b"result = 2 + 2  # inert text fixture\n"


@pytest.mark.parametrize(
    ("media_class", "filename", "declared_type", "content"),
    [
        ("bounded-text-file", "notes.txt", "text/plain", TEXT),
        ("image", "pixel.png", "image/png", PNG),
        ("pdf", "document.pdf", "application/pdf", PDF),
        ("code", "example.py.txt", "text/plain", CODE),
    ],
)
def test_safe_media_preflight(
    media_class: str, filename: str, declared_type: str, content: bytes
) -> None:
    assert validate_preflight(
        media_class=media_class,
        filename=filename,
        declared_type=declared_type,
        content=content,
    ) == hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"count": 5}, "count"),
        ({"declared_type": "application/pdf"}, "declared-type"),
        ({"content": b""}, "empty"),
        ({"filename": "../notes.txt"}, "unsafe-filename"),
        ({"filename": "folder/notes.txt"}, "unsafe-filename"),
        ({"expected_hash": "0" * 64}, "hash-mismatch"),
        ({"media_class": "archive"}, "unsupported-media"),
    ],
)
def test_preflight_rejections(overrides: dict[str, object], reason: str) -> None:
    values: dict[str, object] = {
        "media_class": "bounded-text-file",
        "filename": "notes.txt",
        "declared_type": "text/plain",
        "content": TEXT,
    }
    values.update(overrides)
    with pytest.raises(ContractError, match=reason):
        validate_preflight(**values)  # type: ignore[arg-type]


def test_preflight_rejects_size_duplicate_and_detected_type() -> None:
    digest = hashlib.sha256(TEXT).hexdigest()
    with pytest.raises(ContractError, match="size"):
        validate_preflight(
            media_class="bounded-text-file",
            filename="notes.txt",
            declared_type="text/plain",
            content=b"x" * (64 * 1024 + 1),
        )
    with pytest.raises(ContractError, match="duplicate"):
        validate_preflight(
            media_class="bounded-text-file",
            filename="notes.txt",
            declared_type="text/plain",
            content=TEXT,
            existing_hashes={digest},
        )
    with pytest.raises(ContractError, match="detected-type-mismatch"):
        validate_preflight(
            media_class="pdf",
            filename="document.pdf",
            declared_type="application/pdf",
            content=TEXT,
        )


def make_attachment() -> tuple[FakeObjectStore, object]:
    store = FakeObjectStore()
    attachment = store.create(
        actor_id="actor-synthetic",
        workspace_id="workspace-synthetic",
        task_id="task-synthetic",
        media_class="bounded-text-file",
        filename="notes.txt",
        declared_type="text/plain",
        content=TEXT,
    )
    return store, attachment


def test_quarantine_binds_identity_and_denies_agent_bytes() -> None:
    store, attachment = make_attachment()
    assert attachment.state is State.QUARANTINED
    assert attachment.agent_visible is False
    assert store.verify_integrity(attachment.object_id)
    with pytest.raises(ContractError, match="agent-visibility-denied"):
        store.bytes_for_transfer(attachment.object_id)


@pytest.mark.parametrize(
    ("verdict", "state"),
    [
        (Verdict.CLEAN, State.CLEAN),
        (Verdict.UNSAFE, State.UNSAFE),
        (Verdict.ERROR, State.SCAN_ERROR),
        (Verdict.TIMEOUT, State.SCAN_TIMEOUT),
        (Verdict.UNAVAILABLE, State.SCAN_UNAVAILABLE),
    ],
)
def test_scanner_verdicts_fail_closed(verdict: Verdict, state: State) -> None:
    store, attachment = make_attachment()
    result = FakeScanner(verdict).scan(store, attachment.object_id)
    apply_scanner_result(attachment, result)
    assert attachment.state is state
    assert attachment.agent_visible is False
    with pytest.raises(ContractError, match="agent-visibility-denied"):
        store.bytes_for_transfer(attachment.object_id)


def clean_attachment() -> tuple[FakeObjectStore, object, FakeClassicRuntime]:
    store, attachment = make_attachment()
    apply_scanner_result(attachment, FakeScanner(Verdict.CLEAN).scan(store, attachment.object_id))
    return store, attachment, FakeClassicRuntime()


def test_clean_verdict_alone_cannot_transfer() -> None:
    store, attachment, _runtime = clean_attachment()
    assert attachment.state is State.CLEAN
    with pytest.raises(ContractError, match="agent-visibility-denied"):
        store.bytes_for_transfer(attachment.object_id)


def test_transfer_binding_receipt_and_idempotent_replay() -> None:
    store, attachment, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-inline-base64",
        now=100,
    )
    receipt = runtime.transfer(
        store,
        attachment,
        intent,
        now=101,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
    )
    replay = runtime.transfer(
        store,
        attachment,
        intent,
        now=102,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
    )
    assert replay == receipt
    assert attachment.state is State.TRANSFERRED
    assert attachment.agent_visible is True
    assert attachment.audit.count("transfer-receipt") == 1


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("actor_id", "wrong", "intent-binding-mismatch"),
        ("workspace_id", "wrong", "intent-binding-mismatch"),
        ("task_id", "wrong", "intent-binding-mismatch"),
        ("destination", "classic:wrong", "intent-binding-mismatch"),
    ],
)
def test_transfer_rejects_binding_mismatch(field: str, value: str, reason: str) -> None:
    store, attachment, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-url-reference",
        now=100,
    )
    args = {
        "now": 101,
        "actor_id": attachment.actor_id,
        "workspace_id": attachment.workspace_id,
        "task_id": attachment.task_id,
        "destination": runtime.DESTINATION,
    }
    args[field] = value
    with pytest.raises(ContractError, match=reason):
        runtime.transfer(store, attachment, intent, **args)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"now": 1000}, "stale-grant"),
        ({"redirect": True}, "redirect"),
        ({"partial": True}, "range-partial"),
    ],
)
def test_transfer_rejects_stale_redirect_and_partial(
    overrides: dict[str, object], reason: str
) -> None:
    store, attachment, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-url-reference",
        now=100,
    )
    args: dict[str, object] = {
        "now": 101,
        "actor_id": attachment.actor_id,
        "workspace_id": attachment.workspace_id,
        "task_id": attachment.task_id,
        "destination": runtime.DESTINATION,
    }
    args.update(overrides)
    with pytest.raises(ContractError, match=reason):
        runtime.transfer(store, attachment, intent, **args)  # type: ignore[arg-type]


def test_remove_delete_retry_and_recovery_preserve_safety() -> None:
    store, attachment = make_attachment()
    apply_scanner_result(attachment, Verdict.UNSAFE)
    recovered = store.recover(attachment.object_id)
    assert recovered.state is State.UNSAFE
    assert recovered.agent_visible is False

    store, clean, _runtime = clean_attachment()
    store.remove(clean.object_id)
    assert clean.state is State.REMOVED
    store.delete(clean.object_id, provider_failure=True)
    assert clean.state is State.DELETION_PENDING
    store.retry_delete(clean.object_id)
    assert clean.state is State.DELETED


def test_network_is_denied() -> None:
    with pytest.raises(AssertionError, match="network access denied"):
        socket.create_connection(("example.invalid", 443))
