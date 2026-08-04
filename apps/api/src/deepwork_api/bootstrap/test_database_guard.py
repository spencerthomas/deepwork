"""Fail-closed guard for destructive disposable PostgreSQL integration tests."""

from __future__ import annotations

import ipaddress
import os

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


def validate_disposable_database_url(value: str) -> str:
    """Accept only a loopback PostgreSQL database with an explicit test name."""

    try:
        parsed = make_url(value)
        address = ipaddress.ip_address(parsed.host or "")
    except (ArgumentError, TypeError, ValueError):
        raise ValueError("test database URL must use a literal loopback IP address") from None
    database = parsed.database or ""
    if parsed.drivername != "postgresql+psycopg" or not address.is_loopback:
        raise ValueError("test database must use postgresql+psycopg on a loopback IP address")
    if parsed.query:
        raise ValueError("test database URL must not contain query overrides")
    if database != "deepwork_test" and not database.startswith("deepwork_test_"):
        raise ValueError("test database name must be deepwork_test or start with deepwork_test_")
    return value


def main() -> int:
    value = os.environ.get("DEEPWORK_TEST_DATABASE_URL")
    if not value:
        raise ValueError("DEEPWORK_TEST_DATABASE_URL is required")
    validate_disposable_database_url(value)
    print("validated disposable loopback PostgreSQL target")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
