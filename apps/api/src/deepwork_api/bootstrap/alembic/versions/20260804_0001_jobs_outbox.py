"""Create the durable PostgreSQL jobs and transactional outbox tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260804_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("sequence", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=28), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("workspace_id", sa.String(length=200), nullable=False),
        sa.Column("actor_id", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("lease_owner", sa.String(length=200), nullable=True),
        sa.Column("lease_token", sa.String(length=96), nullable=True),
        sa.Column("lease_expires_at", sa.BigInteger(), nullable=True),
        sa.Column("safe_error", sa.String(length=100), nullable=True),
        sa.CheckConstraint("attempts >= 0", name="ck_jobs_attempts_nonnegative"),
        sa.CheckConstraint(
            "max_attempts BETWEEN 1 AND 10",
            name="ck_jobs_max_attempts_bounded",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'leased', 'succeeded', 'dead')",
            name="ck_jobs_status_known",
        ),
        sa.PrimaryKeyConstraint("sequence", name="pk_jobs"),
        sa.UniqueConstraint("job_id", name="uq_jobs_job_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "workspace_id",
            "idempotency_key",
            name="job_scope_idempotency",
        ),
    )
    op.create_index("jobs_expired_leases", "jobs", ["status", "lease_expires_at"])
    op.create_index("jobs_queue_order", "jobs", ["status", "sequence"])
    op.create_table(
        "job_outbox",
        sa.Column("sequence", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("outbox_id", sa.String(length=28), nullable=False),
        sa.Column("job_id", sa.String(length=28), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("lease_owner", sa.String(length=200), nullable=True),
        sa.Column("lease_token", sa.String(length=96), nullable=True),
        sa.Column("lease_expires_at", sa.BigInteger(), nullable=True),
        sa.Column("delivered_at", sa.BigInteger(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'leased', 'delivered', 'dead')",
            name="ck_job_outbox_status_known",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
            name="fk_job_outbox_job_id_jobs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("sequence", name="pk_job_outbox"),
        sa.UniqueConstraint("job_id", name="uq_job_outbox_job_id"),
        sa.UniqueConstraint("outbox_id", name="uq_job_outbox_outbox_id"),
    )
    op.create_index(
        "job_outbox_delivery_order",
        "job_outbox",
        ["status", "sequence"],
    )
    op.create_index(
        "job_outbox_expired_leases",
        "job_outbox",
        ["status", "lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index("job_outbox_expired_leases", table_name="job_outbox")
    op.drop_index("job_outbox_delivery_order", table_name="job_outbox")
    op.drop_table("job_outbox")
    op.drop_index("jobs_queue_order", table_name="jobs")
    op.drop_index("jobs_expired_leases", table_name="jobs")
    op.drop_table("jobs")
