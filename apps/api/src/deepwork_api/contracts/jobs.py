"""Public safe durable-job wire contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepwork_api.domain import JobAcceptance, JobKind, JobRecord, JobStatus


class _WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class JobResponse(_WireModel):
    """Credential-free, tenant-opaque local proof projection."""

    job_id: str = Field(alias="jobId")
    kind: JobKind
    status: JobStatus
    attempts: int
    max_attempts: int = Field(alias="maxAttempts")
    duplicate: bool = False
    safe_error: str | None = Field(default=None, alias="safeError")
    durability: Literal["local-sqlite-proof"] = "local-sqlite-proof"

    @classmethod
    def from_record(
        cls,
        record: JobRecord,
        *,
        duplicate: bool = False,
    ) -> "JobResponse":
        return cls(
            job_id=record.job_id,
            kind=record.kind,
            status=record.status,
            attempts=record.attempts,
            max_attempts=record.max_attempts,
            duplicate=duplicate,
            # Repository errors are worker-internal. Public reads expose only a
            # stable generic failure so tenant identifiers, credentials, or
            # untrusted exception text can never be reflected.
            safe_error="Job execution failed." if record.safe_error is not None else None,
        )

    @classmethod
    def from_acceptance(cls, acceptance: JobAcceptance) -> "JobResponse":
        return cls.from_record(acceptance.job, duplicate=acceptance.duplicate)
