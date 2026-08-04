"""Pure durable application-job values and errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class JobKind(StrEnum):
    """Bounded job kinds supported by the local durability proof."""

    FIXTURE_NOOP = "fixture.noop"


class JobStatus(StrEnum):
    """Durable job lifecycle."""

    QUEUED = "queued"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    DEAD = "dead"

    @property
    def is_terminal(self) -> bool:
        return self in {self.SUCCEEDED, self.DEAD}


class JobDurability(StrEnum):
    """Truthful persistence class exposed by the configured job repository."""

    LOCAL_SQLITE_PROOF = "local-sqlite-proof"
    POSTGRES_OUTBOX = "postgres-outbox"


@dataclass(frozen=True, slots=True)
class JobRecord:
    """Internal tenant-scoped durable job record."""

    job_id: str
    tenant_id: str
    workspace_id: str
    actor_id: str
    kind: JobKind
    status: JobStatus
    attempts: int
    max_attempts: int
    created_at: int
    updated_at: int
    lease_expires_at: int | None
    safe_error: str | None


@dataclass(frozen=True, slots=True)
class JobAcceptance:
    """Result of idempotently accepting a job."""

    job: JobRecord
    duplicate: bool


@dataclass(frozen=True, slots=True)
class JobLease:
    """Worker-only lease material; never crosses the HTTP boundary."""

    job: JobRecord
    lease_token: str


class JobError(Exception):
    """Base durable-job error."""


class JobNotFoundError(JobError):
    """A job is absent or invisible to the authenticated tenant."""


class JobLeaseConflictError(JobError):
    """A worker attempted to finish a stale or foreign lease."""
