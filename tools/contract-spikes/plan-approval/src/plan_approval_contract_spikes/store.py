from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .errors import ContractViolation


@dataclass(frozen=True)
class StoredEvent:
    sequence: int
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str


class AppendOnlyCheckpointStore:
    """Deterministic JSONL event store with a corruption-detecting checksum chain.

    The unkeyed checksum is not authenticated storage and cannot prove resistance
    to an actor that can rewrite the whole file. Application authorization and
    durable storage integrity remain outside this offline harness.
    """

    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def _canonical(value: object) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _hash(
        cls, sequence: int, event_type: str, payload: dict[str, Any], previous_hash: str
    ) -> str:
        material = {
            "sequence": sequence,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        return hashlib.sha256(cls._canonical(material).encode()).hexdigest()

    def load(self) -> tuple[StoredEvent, ...]:
        if not self.path.exists():
            return ()
        events: list[StoredEvent] = []
        previous_hash = "GENESIS"
        for expected_sequence, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            raw = json.loads(line)
            event = StoredEvent(**raw)
            if event.sequence != expected_sequence:
                raise ContractViolation("append-only log sequence is invalid")
            if event.previous_hash != previous_hash:
                raise ContractViolation("append-only log hash chain is invalid")
            expected_hash = self._hash(
                event.sequence, event.event_type, event.payload, event.previous_hash
            )
            if event.event_hash != expected_hash:
                raise ContractViolation("append-only log content was modified")
            events.append(event)
            previous_hash = event.event_hash
        return tuple(events)

    def append(self, event_type: str, payload: dict[str, Any]) -> StoredEvent:
        events = self.load()
        sequence = len(events) + 1
        previous_hash = events[-1].event_hash if events else "GENESIS"
        event_hash = self._hash(sequence, event_type, payload, previous_hash)
        event = StoredEvent(
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(self._canonical(event.__dict__) + "\n")
        return event

    def event_types(self) -> Iterable[str]:
        return (event.event_type for event in self.load())
