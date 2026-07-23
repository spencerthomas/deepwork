"""Credential-free local persistence adapters."""

from deepwork_api.adapters.persistence.sqlite import (
    SQLiteTaskRepository,
    SQLiteTaskRepositoryClosedError,
    SQLiteTaskRepositoryDataError,
    SQLiteTaskRepositoryError,
    SQLiteTaskRepositoryPathError,
    SQLiteTaskRepositorySchemaError,
)

__all__ = [
    "SQLiteTaskRepository",
    "SQLiteTaskRepositoryClosedError",
    "SQLiteTaskRepositoryDataError",
    "SQLiteTaskRepositoryError",
    "SQLiteTaskRepositoryPathError",
    "SQLiteTaskRepositorySchemaError",
]
