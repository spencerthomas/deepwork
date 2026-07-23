"""Deterministic fake adapters that prove fallbacks and negative boundaries only."""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from typing import Any

from coding_review_surface_spikes.contracts import (
    normalize_relative_path,
    reject_ambiguous_listing,
    validate_display_path,
)

ESCAPE = re.compile(
    r"(?:"
    r"\x1b(?:\][^\x07]*(?:\x07|\x1b\\)|\[[0-?]*[ -/]*[@-~])"
    r"|\x9b[0-?]*[ -/]*[@-~]"
    r"|\x9d[^\x9c]*(?:\x9c|$)"
    r")"
)
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
ACTIVE_MARKUP = re.compile(r"(?i)<\s*(?:script|iframe|object|embed|svg|html)\b")
BIDI = re.compile(r"[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]")


@dataclass(frozen=True)
class FileSnapshot:
    path: str
    version: str
    payload: bytes

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


class FakeFileAdapter:
    """A root-bound store with stable pages and version-checked reads."""

    def __init__(self, files: dict[str, FileSnapshot], symlinks: dict[str, str] | None = None):
        reject_ambiguous_listing(list(files), case_sensitive=False)
        self._files = {validate_display_path(path): value for path, value in files.items()}
        self._symlinks = symlinks or {}

    def list_page(self, *, cursor: int = 0, limit: int = 2) -> dict[str, Any]:
        names = sorted(self._files)
        selected = names[cursor : cursor + limit]
        next_cursor = cursor + len(selected)
        return {
            "items": [{"path": name, "checksum": self._files[name].checksum} for name in selected],
            "next_cursor": next_cursor if next_cursor < len(names) else None,
        }

    def read(self, path: str, expected_version: str) -> FileSnapshot:
        normalized = normalize_relative_path(path)
        if normalized in self._symlinks:
            raise ValueError("symlink content is never followed by the fake human-file adapter")
        snapshot = self._files[normalized]
        if snapshot.version != expected_version:
            raise RuntimeError("stale_file_version")
        return snapshot

    def replace(self, path: str, replacement: FileSnapshot) -> None:
        self._files[normalize_relative_path(path)] = replacement


def bounded_safe_text(payload: bytes, *, maximum_bytes: int) -> dict[str, Any]:
    if len(payload) > maximum_bytes:
        return {
            "mode": "metadata_only",
            "truncated": True,
            "total_bytes": len(payload),
            "returned_bytes": 0,
        }
    try:
        decoded = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "mode": "metadata_only",
            "truncated": False,
            "total_bytes": len(payload),
            "returned_bytes": 0,
        }
    if ACTIVE_MARKUP.search(decoded):
        return {
            "mode": "metadata_only",
            "truncated": False,
            "total_bytes": len(payload),
            "returned_bytes": 0,
            "reason": "active_markup_blocked",
        }
    safe = CONTROL.sub("\ufffd", decoded)
    safe = BIDI.sub("[bidi-control-removed]", safe)
    safe = html.escape(safe, quote=False)
    return {
        "mode": "escaped_text",
        "truncated": False,
        "total_bytes": len(payload),
        "returned_bytes": len(payload),
        "text": safe,
    }


def sanitize_transcript(payload: str, *, maximum_characters: int) -> dict[str, Any]:
    without_escapes = ESCAPE.sub("[terminal-control-removed]", payload)
    safe = CONTROL.sub("\ufffd", without_escapes)
    safe = BIDI.sub("[bidi-control-removed]", safe)
    truncated = len(safe) > maximum_characters
    rendered = safe[:maximum_characters]
    return {
        "rendering": "escaped_plain_text",
        "text": rendered,
        "truncated": truncated,
        "returned_characters": len(rendered),
        "omitted_characters": max(0, len(safe) - len(rendered)),
        "active_links": 0,
    }
