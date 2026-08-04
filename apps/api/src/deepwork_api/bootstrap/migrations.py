"""Explicit PostgreSQL migration entry point."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from alembic import command
from alembic.config import Config


def _config() -> Config:
    package_root = Path(__file__).resolve().parents[1]
    config = Config()
    config.set_main_option("script_location", str(package_root / "bootstrap" / "alembic"))
    config.set_main_option("prepend_sys_path", str(package_root.parent))
    return config


def main(argv: Sequence[str] | None = None) -> int:
    """Upgrade the configured PostgreSQL database or report its current revision."""

    parser = argparse.ArgumentParser(description="Manage the Deep Work PostgreSQL schema.")
    parser.add_argument("action", choices=("current", "upgrade"))
    args = parser.parse_args(argv)
    if args.action == "current":
        command.current(_config(), check_heads=True)
    else:
        command.upgrade(_config(), "head")
    return 0
