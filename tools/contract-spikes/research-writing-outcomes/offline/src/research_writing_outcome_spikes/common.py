"""Shared, dependency-free evidence helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = (
    "tenant_id",
    "workspace_id",
    "source_id",
    "actor_id",
    "task_id",
    "run_id",
    "attempt_id",
)

STREAMS = ("artifact", "subagent", "rubric", "verification")
BLOCKED_UPSTREAM = (
    "SPIKE-COMPOSE-001",
    "SPIKE-CONFIG-001",
    "SPIKE-STREAM-003",
    "SPIKE-HITL-001",
)
SUPPORTED_ACCEPTANCE = {
    "AC-DW-TASK-005-01",
    "AC-DW-TASK-005-02",
    "AC-DW-TASK-005-03",
    "AC-DW-HITL-002-01",
    "AC-DW-HITL-002-02",
    "AC-DW-HITL-002-03",
    "AC-DW-HITL-002-04",
}


class ValidationError(ValueError):
    """Raised when retained evidence fails closed."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON at {path}: {exc}") from exc


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def exact_identity(value: Any, *, label: str) -> dict[str, str]:
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == set(IDENTITY_FIELDS), f"{label} identity fields drifted")
    for field in IDENTITY_FIELDS:
        require(isinstance(value[field], str) and value[field], f"{label}.{field} missing")
    return value
