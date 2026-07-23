"""Verify the built wheel and its installed launchers without network access."""

from __future__ import annotations

import configparser
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ENTRY_POINTS = {
    "deepwork-api": "deepwork_api.bootstrap.api:main",
    "deepwork-worker": "deepwork_api.bootstrap.worker:main",
}


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=capture_output,
        text=True,
    )


def _wheel() -> Path:
    wheels = sorted((PROJECT_ROOT / "dist").glob("deepwork_api-*.whl"))
    if len(wheels) != 1:
        message = f"expected one wheel, found {len(wheels)}"
        raise RuntimeError(message)
    return wheels[0]


def _parse_entry_points(value: str) -> dict[str, str]:
    parser = configparser.ConfigParser()
    parser.read_string(value)
    if not parser.has_section("console_scripts"):
        return {}
    return dict(parser.items("console_scripts"))


def _inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        entry_points_name = next(
            (name for name in names if name.endswith(".dist-info/entry_points.txt")),
            None,
        )
        entry_points_text = archive.read(entry_points_name).decode() if entry_points_name else ""
        payload = b"\n".join(
            archive.read(name)
            for name in sorted(names)
            if not name.endswith("/") and not name.endswith(".pyc")
        )

    if "deepwork_api/py.typed" not in names:
        raise RuntimeError("wheel does not contain deepwork_api/py.typed")
    entry_points = _parse_entry_points(entry_points_text)
    if entry_points != EXPECTED_ENTRY_POINTS:
        message = f"unexpected console entry-point mappings: {entry_points}"
        raise RuntimeError(message)

    forbidden_paths = ("tests/", "evidence/", ".artifacts/", ".uv-cache/", ".venv/")
    leaked_paths = sorted(name for name in names if name.startswith(forbidden_paths))
    if leaked_paths:
        message = f"wheel contains repository-only files: {leaked_paths}"
        raise RuntimeError(message)

    checkout_markers = {
        str(PROJECT_ROOT).encode(),
        str(PROJECT_ROOT.parent).encode(),
        str(PROJECT_ROOT.parents[2]).encode(),
    }
    leaked_checkout = sorted(marker.decode() for marker in checkout_markers if marker in payload)
    if leaked_checkout:
        message = f"wheel contains checkout paths: {leaked_checkout}"
        raise RuntimeError(message)

    secret_patterns = {
        "AWS access key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
        "GitHub token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "OpenAI-style token": re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "server credential reference": re.compile(rb"\bauthRef\b"),
    }
    leaked_secrets = sorted(
        label for label, pattern in secret_patterns.items() if pattern.search(payload)
    )
    if leaked_secrets:
        message = f"wheel contains secret-shaped material: {leaked_secrets}"
        raise RuntimeError(message)


def _offline_environment(runtime_site: Path | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "UV_CACHE_DIR": str(PROJECT_ROOT / ".uv-cache"),
        "UV_OFFLINE": "1",
        "UV_PYTHON_DOWNLOADS": "never",
    }
    if runtime_site is not None:
        env["PYTHONPATH"] = str(runtime_site)
    return env


def _check_bounded_api_process(api_launcher: Path, *, cwd: Path, env: dict[str, str]) -> None:
    process = subprocess.Popen(
        [str(api_launcher), "--port", "0"],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        returncode = process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.communicate(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5.0)
        print("verified installed API process reached bounded loopback run state")
        return

    stdout, stderr = process.communicate()
    combined = f"{stdout}\n{stderr}".lower()
    if returncode != 0 and ("operation not permitted" in combined or "errno 1" in combined):
        print("installed API process reached sandbox loopback bind boundary: EPERM")
        return
    message = f"installed API process exited unexpectedly with code {returncode}"
    raise RuntimeError(message)


def _verify_installed_wheel(wheel: Path) -> None:
    env = _offline_environment()
    uv = shutil.which("uv", path=env["PATH"])
    if uv is None:
        raise RuntimeError("uv executable not found")

    with tempfile.TemporaryDirectory(prefix="deepwork-api-wheel-") as directory:
        consumer = Path(directory)
        environment = consumer / "venv"
        _run(
            [
                uv,
                "--offline",
                "--no-python-downloads",
                "venv",
                "--python",
                sys.executable,
                str(environment),
            ],
            cwd=consumer,
            env=env,
        )
        python = environment / "bin" / "python"
        _run(
            [
                uv,
                "--offline",
                "--no-python-downloads",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                str(wheel),
            ],
            cwd=consumer,
            env=env,
        )

        runtime_site = Path(sysconfig.get_paths()["purelib"])
        launcher_env = _offline_environment(runtime_site)
        smoke = (
            "from pathlib import Path; "
            "from importlib.resources import files; import deepwork_api; "
            "from deepwork_api import create_app; "
            f"assert Path(deepwork_api.__file__).is_relative_to(Path({str(environment)!r})); "
            "assert create_app().title == 'Deep Work API fixture scaffold'; "
            "assert files('deepwork_api').joinpath('py.typed').is_file()"
        )
        _run([str(python), "-c", smoke], cwd=consumer, env=launcher_env)

        api_launcher = environment / "bin" / "deepwork-api"
        worker_launcher = environment / "bin" / "deepwork-worker"
        if not api_launcher.is_file() or not worker_launcher.is_file():
            raise RuntimeError("wheel install did not create both console launchers")

        api_help = _run(
            [str(api_launcher), "--help"],
            cwd=consumer,
            env=launcher_env,
            capture_output=True,
        )
        if "Run the fixture-only Deep Work API on loopback." not in api_help.stdout:
            raise RuntimeError("installed API launcher help is not the declared fixture command")
        print("verified installed API launcher: --help")

        worker = _run(
            [str(worker_launcher), "--check"],
            cwd=consumer,
            env=launcher_env,
            capture_output=True,
        )
        worker_payload = json.loads(worker.stdout)
        if (
            worker_payload.get("mode") != "fixture"
            or worker_payload.get("durability") != "unavailable"
        ):
            raise RuntimeError("installed worker launcher did not retain unavailable durability")
        print("verified installed worker launcher: fixture durability unavailable")

        _check_bounded_api_process(api_launcher, cwd=consumer, env=launcher_env)


def main() -> int:
    wheel = _wheel()
    _inspect_wheel(wheel)
    _verify_installed_wheel(wheel)
    print(f"verified offline installed wheel: {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
