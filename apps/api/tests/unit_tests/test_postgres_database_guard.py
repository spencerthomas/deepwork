"""Safety checks for the destructive PostgreSQL integration-test target."""

import pytest

from deepwork_api.bootstrap.test_database_guard import validate_disposable_database_url


def test_guard_accepts_only_explicit_loopback_test_database() -> None:
    value = "postgresql+psycopg://operator@127.0.0.1:5432/deepwork_test_slice"

    assert validate_disposable_database_url(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "postgresql+psycopg://operator@db.example.com/deepwork_test",
        "postgresql+psycopg://operator@localhost/deepwork_test",
        "postgresql+psycopg://operator@127.0.0.1/deepwork",
        "postgresql://operator@127.0.0.1/deepwork_test",
        "postgresql+psycopg://operator@127.0.0.1/deepwork_test?host=db.example.com",
        "postgresql+psycopg://operator@127.0.0.1/deepwork_test?dbname=production",
        "not-a-url",
    ],
)
def test_guard_rejects_ambiguous_remote_or_non_test_targets(value: str) -> None:
    with pytest.raises(ValueError, match="test database"):
        validate_disposable_database_url(value)
