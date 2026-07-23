"""Verify the built wheel from a clean, offline Python environment."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _wheel() -> Path:
    wheels = sorted((PROJECT_ROOT / "dist").glob("deepwork_api-*.whl"))
    if len(wheels) != 1:
        message = f"expected one wheel, found {len(wheels)}"
        raise RuntimeError(message)
    return wheels[0]


def _inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        entry_points_name = next(
            (name for name in names if name.endswith(".dist-info/entry_points.txt")),
            None,
        )
        entry_points = archive.read(entry_points_name).decode() if entry_points_name else ""
    if "deepwork_api/py.typed" not in names:
        raise RuntimeError("wheel does not contain deepwork_api/py.typed")
    if "deepwork-api" not in entry_points or "deepwork-worker" not in entry_points:
        raise RuntimeError("wheel does not contain both declared console entry points")
    forbidden = ("tests/", "evidence/", ".artifacts/", ".uv-cache/", ".venv/")
    leaked = sorted(name for name in names if name.startswith(forbidden))
    if leaked:
        message = f"wheel contains repository-only files: {leaked}"
        raise RuntimeError(message)


def main() -> int:
    wheel = _wheel()
    _inspect_wheel(wheel)
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="deepwork-api-wheel-") as directory:
        consumer = Path(directory)
        target = consumer / "site"
        _run(
            ["uv", "pip", "install", "--offline", "--no-deps", "--target", str(target), str(wheel)],
            cwd=consumer,
            env=env,
        )
        smoke = (
            "import sys; from pathlib import Path; "
            f"sys.path.insert(0, {str(target)!r}); "
            "from importlib.resources import files; import deepwork_api; "
            "from deepwork_api import create_app; "
            f"assert Path(deepwork_api.__file__).is_relative_to(Path({str(target)!r})); "
            "assert create_app().title == 'Deep Work API fixture scaffold'; "
            "assert files('deepwork_api').joinpath('py.typed').is_file()"
        )
        _run([sys.executable, "-c", smoke], cwd=consumer, env=env)
        worker_smoke = (
            "import sys; "
            f"sys.path.insert(0, {str(target)!r}); "
            "from deepwork_api.bootstrap.worker import main; "
            "raise SystemExit(main(['--check']))"
        )
        _run([sys.executable, "-c", worker_smoke], cwd=consumer, env=env)
    print(f"verified clean wheel: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
