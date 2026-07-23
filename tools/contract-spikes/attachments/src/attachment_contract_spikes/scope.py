"""Immutable scope loading, hashing, and complete matrix identity derivation."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any


SCOPE_RELATIVE_PATH = Path(
    "docs/references/research/attachment-contract-spikes/matrix-scope.json"
)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object and reject non-object roots."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def scope_sha256(path: Path) -> str:
    """Return the immutable byte hash retained by every matrix row."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dimension_ids(scope: dict[str, Any], name: str) -> list[str]:
    """Return the ordered IDs for one declared dimension."""
    values = scope["matrix_dimensions"][name]
    ids = [item["id"] for item in values]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate IDs in scope dimension {name}")
    return ids


def derive_identities(scope: dict[str, Any]) -> list[dict[str, str]]:
    """Derive the complete immutable Cartesian product from the scope."""
    dimensions = scope["cartesian_product"]
    values = [dimension_ids(scope, name) for name in dimensions]
    identities = [
        dict(zip(dimensions, combination, strict=True))
        for combination in itertools.product(*values)
    ]
    declared = scope["expected_row_count"]
    if len(identities) != declared:
        raise ValueError(
            f"scope expected_row_count={declared}, derived={len(identities)}"
        )
    return identities


def row_id(identity: dict[str, str]) -> str:
    """Return a stable row ID independent of worker-selected ordering."""
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return f"ATTACH-{hashlib.sha256(canonical.encode()).hexdigest()[:20]}"


def scope_lookup(scope: dict[str, Any], dimension: str, item_id: str) -> dict[str, Any]:
    """Look up one scope item by ID."""
    for item in scope["matrix_dimensions"][dimension]:
        if item["id"] == item_id:
            return item
    raise KeyError(f"{dimension}: {item_id}")
