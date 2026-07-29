"""Shared wire-contract text validation helpers."""

from __future__ import annotations


def reject_unsafe_controls(value: str) -> str:
    """Reject C0 (< 0x20), DEL (0x7F), and C1 (0x80-0x9F) control characters.

    Keeps only tab/newline/carriage-return. Matches the endpoint validator in
    adapters/sources/classic/source.py, which already rejects DEL, so no
    request body can carry control bytes the source layer forbids.
    """
    if any(
        (ord(character) < 32 or 0x7F <= ord(character) <= 0x9F) and character not in "\t\n\r"
        for character in value
    ):
        raise ValueError("control characters are not allowed")
    return value
