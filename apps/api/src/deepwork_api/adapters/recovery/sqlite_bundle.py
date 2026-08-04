"""Verified, non-overwriting backup bundles for the local SQLite adapter pair."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

_FORMAT: Final = "deepwork-local-sqlite-backup-v1"
_DATABASE_FILES: Final = ("tasks.sqlite3", "settings.sqlite3")


class BackupBundleError(RuntimeError):
    """Raised when a local backup or restore cannot be proven safe."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: object) -> object:
    if isinstance(value, bytes):
        return {"base64": base64.b64encode(value).decode("ascii")}
    if value is None or isinstance(value, str | int | float):
        return value
    raise BackupBundleError(f"unsupported SQLite value type: {type(value).__name__}")


def _logical_snapshot(path: Path) -> tuple[str, int]:
    uri = f"{path.as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            integrity = cast(str, connection.execute("PRAGMA quick_check").fetchone()[0])
            if integrity != "ok":
                raise BackupBundleError(f"database integrity check failed: {path.name}")
            objects = [
                (cast(str, row[0]), cast(str, row[1]), cast(str | None, row[2]))
                for row in connection.execute(
                    "SELECT type, name, sql FROM sqlite_master "
                    "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
                )
            ]
            tables: dict[str, list[list[object]]] = {}
            row_count = 0
            for object_type, name, _sql in objects:
                if object_type != "table":
                    continue
                quoted = name.replace('"', '""')
                rows = [
                    [_json_value(value) for value in row]
                    for row in connection.execute(f'SELECT * FROM "{quoted}" ORDER BY rowid')
                ]
                tables[name] = rows
                row_count += len(rows)
            payload = {
                "applicationId": cast(
                    int, connection.execute("PRAGMA application_id").fetchone()[0]
                ),
                "objects": objects,
                "tables": tables,
                "userVersion": cast(int, connection.execute("PRAGMA user_version").fetchone()[0]),
            }
    except sqlite3.DatabaseError as error:
        raise BackupBundleError(f"database cannot be read safely: {path.name}") from error
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest(), row_count


def _copy_database(source: Path, destination: Path) -> None:
    uri = f"{source.as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as source_connection:
            with sqlite3.connect(destination) as destination_connection:
                source_connection.backup(destination_connection)
    except sqlite3.DatabaseError as error:
        raise BackupBundleError(f"database backup failed safely: {source.name}") from error


def _asset(path: Path) -> dict[str, object]:
    logical_sha256, rows = _logical_snapshot(path)
    return {
        "bytes": path.stat().st_size,
        "logicalSha256": logical_sha256,
        "rows": rows,
        "sha256": _sha256(path),
    }


def _safe_target(path: Path) -> Path:
    target = path.expanduser()
    if not target.is_absolute():
        raise BackupBundleError("output directory must be an absolute path")
    if target.exists() or target.is_symlink():
        raise BackupBundleError(f"refusing to overwrite existing output: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _safe_source(path: Path, *, label: str) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise BackupBundleError(f"{label} must not be a symbolic link")
    try:
        source = expanded.resolve(strict=True)
    except FileNotFoundError as error:
        raise BackupBundleError(f"{label} does not exist") from error
    if not source.is_file():
        raise BackupBundleError(f"{label} must be a regular file")
    return source


def create_backup_bundle(
    *,
    task_database: Path,
    settings_database: Path,
    output_directory: Path,
) -> Mapping[str, object]:
    """Snapshot both stopped local databases into a verified, immutable bundle."""

    sources = {
        "tasks.sqlite3": _safe_source(task_database, label="task database"),
        "settings.sqlite3": _safe_source(settings_database, label="settings database"),
    }
    target = _safe_target(output_directory)
    with tempfile.TemporaryDirectory(prefix="deepwork-backup-", dir=target.parent) as temporary:
        staged = Path(temporary) / "bundle"
        staged.mkdir()
        assets: dict[str, object] = {}
        for filename, source in sources.items():
            destination = staged / filename
            _copy_database(source, destination)
            assets[filename] = _asset(destination)
        manifest: dict[str, object] = {
            "assets": assets,
            "createdAt": datetime.now(UTC).isoformat(),
            "format": _FORMAT,
        }
        (staged / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staged, target)
    return manifest


def _load_manifest(bundle: Path) -> dict[str, object]:
    manifest_path = bundle / "manifest.json"
    if manifest_path.is_symlink():
        raise BackupBundleError("backup manifest must not be a symbolic link")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BackupBundleError("backup manifest is missing or invalid") from error
    if not isinstance(value, dict) or value.get("format") != _FORMAT:
        raise BackupBundleError("backup format is unsupported")
    assets = value.get("assets")
    if not isinstance(assets, dict) or set(assets) != set(_DATABASE_FILES):
        raise BackupBundleError("backup asset set is incomplete or unsupported")
    return value


def _verify_asset(path: Path, expected: object) -> dict[str, object]:
    if not isinstance(expected, dict):
        raise BackupBundleError(f"backup metadata is invalid: {path.name}")
    actual = _asset(path)
    for field in ("bytes", "logicalSha256", "rows", "sha256"):
        if actual[field] != expected.get(field):
            raise BackupBundleError(f"backup verification failed for {path.name}: {field}")
    return actual


def restore_backup_bundle(
    *, bundle_directory: Path, output_directory: Path
) -> Mapping[str, object]:
    """Verify and restore a bundle without overwriting any existing directory."""

    raw_bundle = bundle_directory.expanduser()
    if raw_bundle.is_symlink():
        raise BackupBundleError("backup bundle must not be a symbolic link")
    bundle = raw_bundle.resolve(strict=True)
    if not bundle.is_dir():
        raise BackupBundleError("backup bundle must be a directory")
    manifest = _load_manifest(bundle)
    assets = cast(dict[str, object], manifest["assets"])
    target = _safe_target(output_directory)
    with tempfile.TemporaryDirectory(prefix="deepwork-restore-", dir=target.parent) as temporary:
        staged = Path(temporary) / "restored"
        staged.mkdir()
        restored_assets: dict[str, object] = {}
        for filename in _DATABASE_FILES:
            source = _safe_source(bundle / filename, label=f"backup asset {filename}")
            _verify_asset(source, assets[filename])
            destination = staged / filename
            _copy_database(source, destination)
            restored_assets[filename] = _verify_asset(destination, assets[filename])
        report: dict[str, object] = {
            "assets": restored_assets,
            "format": _FORMAT,
            "sourceManifestSha256": _sha256(bundle / "manifest.json"),
            "status": "verified",
        }
        (staged / "restore-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staged, target)
    return report
