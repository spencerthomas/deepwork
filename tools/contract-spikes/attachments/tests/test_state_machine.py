from __future__ import annotations

import hashlib
import socket
from dataclasses import replace

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


def test_store_enforces_per_task_count_and_duplicate_hash() -> None:
    store = FakeObjectStore()
    for index in range(4):
        store.create(
            actor_id="actor-synthetic",
            workspace_id="workspace-synthetic",
            task_id="task-synthetic",
            media_class="bounded-text-file",
            filename=f"notes-{index}.txt",
            declared_type="text/plain",
            content=f"synthetic content {index}\n".encode(),
        )
    with pytest.raises(ContractError, match="count"):
        store.create(
            actor_id="actor-synthetic",
            workspace_id="workspace-synthetic",
            task_id="task-synthetic",
            media_class="bounded-text-file",
            filename="notes-5.txt",
            declared_type="text/plain",
            content=b"fifth synthetic content\n",
        )

    duplicate_store = FakeObjectStore()
    duplicate_store.create(
        actor_id="actor-synthetic",
        workspace_id="workspace-synthetic",
        task_id="task-synthetic",
        media_class="bounded-text-file",
        filename="notes-a.txt",
        declared_type="text/plain",
        content=TEXT,
    )
    with pytest.raises(ContractError, match="duplicate"):
        duplicate_store.create(
            actor_id="actor-synthetic",
            workspace_id="workspace-synthetic",
            task_id="task-synthetic",
            media_class="bounded-text-file",
            filename="notes-b.txt",
            declared_type="text/plain",
            content=TEXT,
        )


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
        idempotency_key="intent-key-1",
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
        idempotency_key="intent-key-1",
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
        ({"now": 160}, "stale-grant"),
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
        idempotency_key="intent-key-1",
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


def test_intent_creation_is_idempotent_and_rejects_changed_payload() -> None:
    _store, attachment, runtime = clean_attachment()
    arguments = {
        "actor_id": attachment.actor_id,
        "workspace_id": attachment.workspace_id,
        "task_id": attachment.task_id,
        "destination": runtime.DESTINATION,
        "representation": "standard-content-inline-base64",
        "idempotency_key": "intent-key-1",
        "now": 100,
    }
    first = runtime.create_intent(attachment, **arguments)
    replay = runtime.create_intent(attachment, **arguments)
    assert replay == first
    assert attachment.audit.count("transfer-intent") == 1
    with pytest.raises(ContractError, match="idempotency-conflict"):
        runtime.create_intent(
            attachment,
            **{**arguments, "representation": "standard-content-url-reference"},
        )


def test_runtime_rejects_capability_mismatch_and_source_failure() -> None:
    _store, attachment, runtime = clean_attachment()
    with pytest.raises(ContractError, match="capability-mismatch"):
        runtime.create_intent(
            attachment,
            actor_id=attachment.actor_id,
            workspace_id=attachment.workspace_id,
            task_id=attachment.task_id,
            destination=runtime.DESTINATION,
            representation="fleet-arbitrary-unsupported",
            idempotency_key="intent-key-1",
            now=100,
        )

    _store, attachment, unavailable = clean_attachment()
    unavailable.available = False
    with pytest.raises(ContractError, match="source-unavailable"):
        unavailable.create_intent(
            attachment,
            actor_id=attachment.actor_id,
            workspace_id=attachment.workspace_id,
            task_id=attachment.task_id,
            destination=unavailable.DESTINATION,
            representation="standard-content-inline-base64",
            idempotency_key="intent-key-2",
            now=100,
        )

    _store, attachment, failed = clean_attachment()
    failed.failure_mode = "synthetic"
    with pytest.raises(ContractError, match="source-error-synthetic"):
        failed.create_intent(
            attachment,
            actor_id=attachment.actor_id,
            workspace_id=attachment.workspace_id,
            task_id=attachment.task_id,
            destination=failed.DESTINATION,
            representation="standard-content-inline-base64",
            idempotency_key="intent-key-3",
            now=100,
        )


def test_transfer_rejects_cross_object_and_cross_workspace_substitution() -> None:
    store_a, attachment_a, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment_a,
        actor_id=attachment_a.actor_id,
        workspace_id=attachment_a.workspace_id,
        task_id=attachment_a.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-inline-base64",
        idempotency_key="intent-key-1",
        now=100,
    )
    store_b = FakeObjectStore()
    attachment_b = store_b.create(
        actor_id="actor-synthetic",
        workspace_id="workspace-b",
        task_id="task-synthetic",
        media_class="bounded-text-file",
        filename="other.txt",
        declared_type="text/plain",
        content=TEXT,
    )
    apply_scanner_result(attachment_b, Verdict.CLEAN)
    attachment_b.state = State.TRANSFER_READY
    with pytest.raises(ContractError, match="intent-object-binding-mismatch"):
        runtime.transfer(
            store_b,
            attachment_b,
            intent,
            now=101,
            actor_id=intent.actor_id,
            workspace_id=intent.workspace_id,
            task_id=intent.task_id,
            destination=intent.destination,
        )

    attachment_c = store_a.create(
        actor_id=attachment_a.actor_id,
        workspace_id=attachment_a.workspace_id,
        task_id=attachment_a.task_id,
        media_class="bounded-text-file",
        filename="different.txt",
        declared_type="text/plain",
        content=b"different synthetic content\n",
    )
    apply_scanner_result(attachment_c, Verdict.CLEAN)
    attachment_c.state = State.TRANSFER_READY
    with pytest.raises(ContractError, match="intent-object-binding-mismatch"):
        runtime.transfer(
            store_a,
            attachment_c,
            intent,
            now=101,
            actor_id=intent.actor_id,
            workspace_id=intent.workspace_id,
            task_id=intent.task_id,
            destination=intent.destination,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"intent_id": "forged-intent"},
        {"expires_at": 9999},
        {"sha256": "0" * 64},
    ],
)
def test_transfer_rejects_mutated_issued_intent(changes: dict[str, object]) -> None:
    store, attachment, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-inline-base64",
        idempotency_key="intent-key-1",
        now=100,
        ttl=1,
    )
    forged = replace(intent, **changes)
    with pytest.raises(ContractError, match="intent-mutation"):
        runtime.transfer(
            store,
            attachment,
            forged,
            now=500,
            actor_id=intent.actor_id,
            workspace_id=intent.workspace_id,
            task_id=intent.task_id,
            destination=intent.destination,
        )


def test_transfer_rejects_unissued_intent_key() -> None:
    store, attachment, runtime = clean_attachment()
    intent = runtime.create_intent(
        attachment,
        actor_id=attachment.actor_id,
        workspace_id=attachment.workspace_id,
        task_id=attachment.task_id,
        destination=runtime.DESTINATION,
        representation="standard-content-inline-base64",
        idempotency_key="intent-key-1",
        now=100,
    )
    forged = replace(intent, idempotency_key="unissued-key")
    with pytest.raises(ContractError, match="unissued-intent"):
        runtime.transfer(
            store,
            attachment,
            forged,
            now=101,
            actor_id=intent.actor_id,
            workspace_id=intent.workspace_id,
            task_id=intent.task_id,
            destination=intent.destination,
        )


def test_orphan_cleanup_is_scoped_and_idempotent() -> None:
    store = FakeObjectStore()
    orphan = store.create(
        actor_id="actor-synthetic",
        workspace_id="workspace-synthetic",
        task_id="task-orphan",
        media_class="bounded-text-file",
        filename="orphan.txt",
        declared_type="text/plain",
        content=b"orphan synthetic content\n",
    )
    active = store.create(
        actor_id="actor-synthetic",
        workspace_id="workspace-synthetic",
        task_id="task-active",
        media_class="bounded-text-file",
        filename="active.txt",
        declared_type="text/plain",
        content=b"active synthetic content\n",
    )
    assert store.cleanup_orphans(
        workspace_id="workspace-synthetic", active_task_ids={"task-active"}
    ) == [orphan.object_id]
    assert orphan.state is State.DELETED
    assert active.state is State.QUARANTINED
    assert (
        store.cleanup_orphans(
            workspace_id="workspace-synthetic", active_task_ids={"task-active"}
        )
        == []
    )


def test_network_is_denied() -> None:
    with pytest.raises(AssertionError, match="network access denied"):
        socket.create_connection(("example.invalid", 443))
