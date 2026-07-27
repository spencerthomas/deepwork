"""The application's single wall-clock seam, modelled as an outbound port.

The API is otherwise time-free: task identity and ordering come from the
runner's monotonic sequence, not from timestamps. Task *creation time* is the
one genuinely time-derived fact we record, so it flows through this one
injectable port. Production uses :func:`system_clock`; tests pass a fixed clock
to keep task snapshots deterministic.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

# A clock returns an aware UTC ``datetime``. Repositories stamp task creation
# with ``clock().isoformat()`` so the recorded value is a real instant, never a
# fabricated or default-filled one.
Clock = Callable[[], datetime]


def system_clock() -> datetime:
    """Current wall-clock time in UTC — the only wall-clock read in the app."""

    return datetime.now(UTC)
