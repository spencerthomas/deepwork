"""Test-owned loopback API for browser tenant/workspace recovery acceptance."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from deepwork_api import create_app
from deepwork_api.domain import SecurityContext


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required test environment: {name}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-database", type=Path, required=True)
    parser.add_argument("--settings-database", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    shared_workspace = _required_environment("DEEPWORK_TEST_WORKSPACE")
    contexts = {
        _required_environment("DEEPWORK_TEST_ACCESS_KEY_A"): SecurityContext(
            tenant_id=_required_environment("DEEPWORK_TEST_TENANT_A"),
            workspace_id=shared_workspace,
            actor_id=_required_environment("DEEPWORK_TEST_ACTOR_A"),
        ),
        _required_environment("DEEPWORK_TEST_ACCESS_KEY_B"): SecurityContext(
            tenant_id=_required_environment("DEEPWORK_TEST_TENANT_B"),
            workspace_id=shared_workspace,
            actor_id=_required_environment("DEEPWORK_TEST_ACTOR_B"),
        ),
    }
    uvicorn.run(
        create_app(
            task_database_path=args.task_database,
            settings_database_path=args.settings_database,
            access_key_contexts=contexts,
        ),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
