"""Pure errors for the source-backed schedule (recurring run) registry.

Deep Work owns no schedule storage: a "schedule" is a LangGraph Cron already
registered on the configured task source. This module holds only the safe
error the transport boundary maps, matching the source-owned truth instead
of inventing a local copy.
"""

from __future__ import annotations


class ScheduleDomainError(Exception):
    """Base error mapped safely at the transport boundary."""


class ScheduleRegistryUnavailableError(ScheduleDomainError):
    """No real task source is configured, so there is no schedule registry.

    Fixture mode makes no provider calls and owns no schedule storage of its
    own, so this reports an honest unavailable state instead of a fabricated
    empty or default schedule list.
    """
