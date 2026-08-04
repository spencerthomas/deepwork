"""SQLAlchemy metadata for the PostgreSQL job/outbox boundary."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

metadata = MetaData(
    naming_convention={
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "pk": "pk_%(table_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
    }
)

jobs = Table(
    "jobs",
    metadata,
    Column("sequence", BigInteger, primary_key=True, autoincrement=True),
    Column("job_id", String(28), nullable=False, unique=True),
    Column("tenant_id", String(200), nullable=False),
    Column("workspace_id", String(200), nullable=False),
    Column("actor_id", String(200), nullable=False),
    Column("kind", String(64), nullable=False),
    Column("status", String(16), nullable=False),
    Column("idempotency_key", String(200), nullable=False),
    Column("attempts", Integer, nullable=False),
    Column("max_attempts", Integer, nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("updated_at", BigInteger, nullable=False),
    Column("lease_owner", String(200)),
    Column("lease_token", String(96)),
    Column("lease_expires_at", BigInteger),
    Column("safe_error", String(100)),
    UniqueConstraint(
        "tenant_id",
        "workspace_id",
        "idempotency_key",
        name="job_scope_idempotency",
    ),
    CheckConstraint("attempts >= 0", name="attempts_nonnegative"),
    CheckConstraint("max_attempts BETWEEN 1 AND 10", name="max_attempts_bounded"),
    CheckConstraint(
        "status IN ('queued', 'leased', 'succeeded', 'dead')",
        name="status_known",
    ),
)

Index("jobs_queue_order", jobs.c.status, jobs.c.sequence)
Index("jobs_expired_leases", jobs.c.status, jobs.c.lease_expires_at)

job_outbox = Table(
    "job_outbox",
    metadata,
    Column("sequence", BigInteger, primary_key=True, autoincrement=True),
    Column("outbox_id", String(28), nullable=False, unique=True),
    Column(
        "job_id",
        String(28),
        ForeignKey("jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("status", String(16), nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("updated_at", BigInteger, nullable=False),
    Column("lease_owner", String(200)),
    Column("lease_token", String(96)),
    Column("lease_expires_at", BigInteger),
    Column("delivered_at", BigInteger),
    CheckConstraint(
        "status IN ('pending', 'leased', 'delivered', 'dead')",
        name="status_known",
    ),
)

Index("job_outbox_delivery_order", job_outbox.c.status, job_outbox.c.sequence)
Index("job_outbox_expired_leases", job_outbox.c.status, job_outbox.c.lease_expires_at)

ALEMBIC_HEAD = "20260804_0001"
