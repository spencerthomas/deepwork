"""Credential-free local persistence adapters."""

from deepwork_api.adapters.persistence.postgres_jobs import (
    PostgresJobRepository,
    PostgresJobRepositoryError,
)
from deepwork_api.adapters.persistence.sqlite import (
    SQLiteTaskRepository,
    SQLiteTaskRepositoryClosedError,
    SQLiteTaskRepositoryDataError,
    SQLiteTaskRepositoryError,
    SQLiteTaskRepositoryPathError,
    SQLiteTaskRepositorySchemaError,
)
from deepwork_api.adapters.persistence.sqlite_jobs import (
    SQLiteJobRepository,
    SQLiteJobRepositoryError,
)

__all__ = [
    "PostgresJobRepository",
    "PostgresJobRepositoryError",
    "SQLiteJobRepository",
    "SQLiteJobRepositoryError",
    "SQLiteTaskRepository",
    "SQLiteTaskRepositoryClosedError",
    "SQLiteTaskRepositoryDataError",
    "SQLiteTaskRepositoryError",
    "SQLiteTaskRepositoryPathError",
    "SQLiteTaskRepositorySchemaError",
]
