"""Unit coverage for SSE replay-cursor parsing at the transport boundary."""

from __future__ import annotations

import pytest

from deepwork_api.domain import InvalidEventCursorError
from deepwork_api.transport.tasks import _parse_event_cursor


def test_parse_event_cursor_rejects_overlong_digit_string() -> None:
    # More than Python's 4300-digit int(str) limit: must be a domain
    # InvalidEventCursorError (→ 409), never a ValueError (→ unhandled 500).
    with pytest.raises(InvalidEventCursorError):
        _parse_event_cursor("1" * 5_000)


def test_parse_event_cursor_preserves_existing_bounds() -> None:
    assert _parse_event_cursor(None) == 0
    assert _parse_event_cursor("") == 0
    assert _parse_event_cursor("0") == 0
    assert _parse_event_cursor("2147483647") == 2_147_483_647
    for bad in ("2147483648", "not-an-id", "-1", "1.0"):
        with pytest.raises(InvalidEventCursorError):
            _parse_event_cursor(bad)
