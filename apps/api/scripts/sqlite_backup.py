#!/usr/bin/env python3
"""Create or restore a verified local Deep Work SQLite backup bundle."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from deepwork_api.adapters.recovery import (
    BackupBundleError,
    create_backup_bundle,
    restore_backup_bundle,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser(
        "backup", help="create a new verified bundle while the API is stopped"
    )
    backup.add_argument("--tasks", required=True, type=Path)
    backup.add_argument("--settings", required=True, type=Path)
    backup.add_argument("--output", required=True, type=Path)
    restore = commands.add_parser("restore", help="restore a verified bundle to a new directory")
    restore.add_argument("--bundle", required=True, type=Path)
    restore.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "backup":
            result = create_backup_bundle(
                task_database=args.tasks,
                settings_database=args.settings,
                output_directory=args.output,
            )
        else:
            result = restore_backup_bundle(
                bundle_directory=args.bundle,
                output_directory=args.output,
            )
    except (BackupBundleError, FileNotFoundError) as error:
        _parser().error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
