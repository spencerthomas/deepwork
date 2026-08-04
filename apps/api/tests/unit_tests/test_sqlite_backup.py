"""Verified local backup and restore tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from deepwork_api.adapters.recovery import (
    BackupBundleError,
    create_backup_bundle,
    restore_backup_bundle,
)


def _database(path: Path, *, table: str, values: tuple[str, ...]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany(
            f"INSERT INTO {table} (value) VALUES (?)", ((value,) for value in values)
        )
        connection.execute("PRAGMA user_version = 7")
        connection.commit()


def _rows(path: Path, table: str) -> list[tuple[int, str]]:
    with sqlite3.connect(path) as connection:
        return list(connection.execute(f"SELECT id, value FROM {table} ORDER BY id"))


def test_bundle_round_trips_both_databases_with_verified_reports(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    _database(tasks, table="tasks", values=("one", "two"))
    _database(settings, table="settings", values=("prompt",))

    bundle = tmp_path / "bundle"
    manifest = create_backup_bundle(
        task_database=tasks,
        settings_database=settings,
        output_directory=bundle.resolve(),
    )
    restored = tmp_path / "restored"
    report = restore_backup_bundle(
        bundle_directory=bundle,
        output_directory=restored.resolve(),
    )

    assert manifest["format"] == "deepwork-local-sqlite-backup-v1"
    assert report["status"] == "verified"
    assert _rows(restored / "tasks.sqlite3", "tasks") == [(1, "one"), (2, "two")]
    assert _rows(restored / "settings.sqlite3", "settings") == [(1, "prompt")]


def test_restore_rejects_tampering_before_creating_output(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    _database(tasks, table="tasks", values=("one",))
    _database(settings, table="settings", values=("prompt",))
    bundle = tmp_path / "bundle"
    create_backup_bundle(
        task_database=tasks,
        settings_database=settings,
        output_directory=bundle.resolve(),
    )
    with sqlite3.connect(bundle / "tasks.sqlite3") as connection:
        connection.execute("UPDATE tasks SET value = 'tampered'")
        connection.commit()

    output = tmp_path / "restored"
    with pytest.raises(BackupBundleError, match="verification failed"):
        restore_backup_bundle(bundle_directory=bundle, output_directory=output.resolve())
    assert not output.exists()


def test_backup_and_restore_refuse_existing_output(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    _database(tasks, table="tasks", values=("one",))
    _database(settings, table="settings", values=("prompt",))
    existing = tmp_path / "existing"
    existing.mkdir()

    with pytest.raises(BackupBundleError, match="refusing to overwrite"):
        create_backup_bundle(
            task_database=tasks,
            settings_database=settings,
            output_directory=existing.resolve(),
        )


def test_restore_rejects_symbolic_link_assets(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    _database(tasks, table="tasks", values=("one",))
    _database(settings, table="settings", values=("prompt",))
    bundle = tmp_path / "bundle"
    create_backup_bundle(
        task_database=tasks,
        settings_database=settings,
        output_directory=bundle.resolve(),
    )
    (bundle / "tasks.sqlite3").unlink()
    (bundle / "tasks.sqlite3").symlink_to(tasks)

    with pytest.raises(BackupBundleError, match="symbolic link"):
        restore_backup_bundle(
            bundle_directory=bundle,
            output_directory=(tmp_path / "restored").resolve(),
        )


def test_backup_refuses_a_broken_output_symlink(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    _database(tasks, table="tasks", values=("one",))
    _database(settings, table="settings", values=("prompt",))
    output = tmp_path / "output"
    output.symlink_to(tmp_path / "missing")

    with pytest.raises(BackupBundleError, match="refusing to overwrite"):
        create_backup_bundle(
            task_database=tasks,
            settings_database=settings,
            output_directory=output,
        )
