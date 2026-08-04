#!/usr/bin/env python3
"""Run two credential-free, loopback-only Deep Work product-demo cells.

The repository harness owns allocation, reservations, receipt authority and final
verification. This driver owns the real processes and writes only the strict
evidence document requested by that harness.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import http.cookiejar
import http.server
import json
import os
import pwd
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

WORKTREE_TOOLS = Path(__file__).resolve().parents[1] / "worktree"
sys.path.insert(0, str(WORKTREE_TOOLS))

from isolation import (  # noqa: E402
    IsolationError,
    canonical_root,
    public_manifest,
    validate_namespace,
    write_evidence,
)


TEARDOWN_RESOURCES = {
    "processes",
    "ports",
    "database",
    "schema",
    "objects",
    "browser_storage",
    "telemetry",
    "logs",
    "proof",
}
PROBE_DIMENSIONS = {
    "database",
    "schema",
    "object_prefix",
    "browser_storage",
    "telemetry",
    "logs",
    "proof",
    "process_control",
}
RUN_NONCE_RE = re.compile(r"^[a-f0-9]{32,64}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
STATE_FILE = "product-demo-state.json"
ACCESS_KEYS = ("deepwork-product-demo-a", "deepwork-product-demo-b")
NEXT_ENV_MAX_BYTES = 64 * 1024


class DriverError(RuntimeError):
    """Fail-closed product-demo driver error."""


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _bound_digest(
    kind: str,
    payload: Any,
    *,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
) -> str:
    value = {
        "kind": kind,
        "run_nonce": run_nonce,
        "driver_revision": driver_revision,
        "driver_sha256": driver_sha256,
        "payload": payload,
    }
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


def _load_manifest(path: Path, root: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise DriverError("private allocation manifest is absent, linked, or oversized")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise DriverError("private allocation manifest is not an object")
    namespace = validate_namespace(manifest.get("namespace"))
    workspace = Path(str(manifest.get("workspace_path", ""))).resolve(strict=False)
    expected = root / ".deepwork" / "worktrees" / namespace
    if workspace != expected or workspace == root:
        raise DriverError("allocation workspace does not belong to the requested root")
    if (
        manifest.get("restart_rule")
        != "reuse-reserved-resources-with-exact-teardown-token"
    ):
        raise DriverError("allocation restart rule is not supported")
    ports = manifest.get("ports")
    if not isinstance(ports, dict) or set(ports) != {
        "api",
        "web",
        "worker",
        "telemetry",
    }:
        raise DriverError("allocation port schema is not exact")
    if any(
        not isinstance(port, int) or not 1024 <= port <= 65535
        for port in ports.values()
    ):
        raise DriverError("allocation ports are invalid")
    return manifest


def _find_executable(name: str) -> Path:
    found = shutil.which(name)
    if found:
        return Path(found).resolve()
    for prefix in (Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        candidate = prefix / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise DriverError(f"required local executable is unavailable: {name}")


def _node_version(node: Path) -> tuple[int, int, int] | None:
    result = subprocess.run(
        [str(node), "--version"], check=False, capture_output=True, text=True, timeout=5
    )
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)\s*", result.stdout)
    return (
        tuple(int(value) for value in match.groups())
        if result.returncode == 0 and match
        else None
    )


def _find_node() -> Path:
    candidates: list[Path] = []
    found = shutil.which("node")
    if found:
        candidates.append(Path(found))
    candidates.extend(
        sorted(
            (Path.home() / ".nvm/versions/node").glob("v24.*/bin/node"), reverse=True
        )
    )
    for candidate in candidates:
        if candidate.is_file() and (version := _node_version(candidate)) is not None:
            if (24, 14, 0) <= version < (25, 0, 0):
                return candidate.resolve()
    raise DriverError("Node.js >=24.14.0 <25 is required")


def _wait_url(url: str, *, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310 - validated loopback
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    raise DriverError(
        f"service readiness timed out: {urllib.parse.urlsplit(url).path or '/'}"
    )


def _port_closed(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, Any]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise DriverError("product-demo HTTP is loopback-only")
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    client = opener or urllib.request.build_opener()
    try:
        with client.open(request, timeout=10) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


def _write_private_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.chmod(0o600)
    temporary.replace(path)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _capture_next_env(root: Path, workspace: Path) -> dict[str, Any]:
    source = root / "apps/web/next-env.d.ts"
    if source.is_symlink() or not source.is_file():
        raise DriverError("tracked Next.js environment declaration is unsafe")
    metadata = source.stat()
    if metadata.st_size > NEXT_ENV_MAX_BYTES:
        raise DriverError("tracked Next.js environment declaration is oversized")
    contents = source.read_bytes()
    snapshot = workspace / "runtime-snapshots" / "next-env.d.ts"
    snapshot.parent.mkdir(parents=True, mode=0o700)
    snapshot.write_bytes(contents)
    snapshot.chmod(0o600)
    return {
        "path": str(snapshot),
        "sha256": _sha256_bytes(contents),
        "mode": stat.S_IMODE(metadata.st_mode),
    }


def _restore_next_env(root: Path, workspace: Path, record: Any) -> None:
    if not isinstance(record, dict) or set(record) != {"path", "sha256", "mode"}:
        raise DriverError("persisted Next.js environment snapshot is invalid")
    expected_snapshot = workspace / "runtime-snapshots" / "next-env.d.ts"
    snapshot = Path(str(record["path"]))
    if snapshot != expected_snapshot or snapshot.is_symlink() or not snapshot.is_file():
        raise DriverError("persisted Next.js environment snapshot is unsafe")
    if snapshot.stat().st_size > NEXT_ENV_MAX_BYTES:
        raise DriverError("persisted Next.js environment snapshot is oversized")
    expected_sha = record["sha256"]
    mode = record["mode"]
    if not isinstance(expected_sha, str) or not SHA_RE.fullmatch(expected_sha):
        raise DriverError("persisted Next.js environment digest is invalid")
    if not isinstance(mode, int) or mode < 0 or mode > 0o777:
        raise DriverError("persisted Next.js environment mode is invalid")
    contents = snapshot.read_bytes()
    if _sha256_bytes(contents) != expected_sha:
        raise DriverError("persisted Next.js environment snapshot changed")
    destination = root / "apps/web/next-env.d.ts"
    if destination.parent.is_symlink() or not destination.parent.is_dir():
        raise DriverError("Next.js environment destination is unsafe")
    if destination.is_symlink():
        raise DriverError("Next.js environment destination is linked")
    temporary = destination.parent / f".next-env.d.ts.deepwork-{workspace.name}.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise DriverError("Next.js environment restore temporary already exists")
    try:
        temporary.write_bytes(contents)
        temporary.chmod(mode)
        temporary.replace(destination)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
    if (
        destination.is_symlink()
        or not destination.is_file()
        or _sha256_bytes(destination.read_bytes()) != expected_sha
    ):
        raise DriverError("Next.js environment restoration could not be verified")


def _postgres_is_running(pg_ctl: Path, pg_data: Path, env: dict[str, str]) -> bool:
    result = subprocess.run(
        [str(pg_ctl), "-D", str(pg_data), "status"],
        check=False,
        capture_output=True,
        timeout=10,
        env=env,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 3:
        return False
    raise DriverError("PostgreSQL status could not be verified")


def _socket_is_closed(socket_dir: Path) -> bool:
    socket_path = socket_dir / ".s.PGSQL.5432"
    if not socket_path.exists():
        return True
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(str(socket_path)) != 0


def _stop_postgres(
    pg_ctl: Path, pg_data: Path, socket_dir: Path, env: dict[str, str]
) -> None:
    if pg_data.is_dir() and _postgres_is_running(pg_ctl, pg_data, env):
        result = subprocess.run(
            [str(pg_ctl), "-D", str(pg_data), "-m", "fast", "-w", "stop"],
            check=False,
            capture_output=True,
            timeout=20,
            env=env,
        )
        if result.returncode != 0:
            raise DriverError("PostgreSQL shutdown failed")
    if pg_data.is_dir() and _postgres_is_running(pg_ctl, pg_data, env):
        raise DriverError("PostgreSQL remains active after shutdown")
    if not _socket_is_closed(socket_dir):
        raise DriverError("PostgreSQL socket remains active after shutdown")


@dataclass
class OwnedProcess:
    name: str
    process: subprocess.Popen[bytes]
    log_file: Any
    command_marker: str


@dataclass
class Stack:
    root: Path
    manifest: dict[str, Any]
    access_key: str
    node: Path
    api_bin: Path
    postgres_bins: dict[str, Path]
    processes: list[OwnedProcess] = field(default_factory=list)
    started_at: str = ""
    ready_at: str = ""
    stopped_at: str = ""
    api_restart_before: str = ""
    api_restart_after: str = ""
    next_env_snapshot: dict[str, Any] | None = None

    @property
    def namespace(self) -> str:
        return str(self.manifest["namespace"])

    @property
    def workspace(self) -> Path:
        return Path(self.manifest["workspace_path"])

    @property
    def ports(self) -> dict[str, int]:
        return self.manifest["ports"]

    @property
    def socket_dir(self) -> Path:
        digest = hashlib.sha256(self.namespace.encode()).hexdigest()[:16]
        return Path("/tmp") / f"deepwork-pg-{digest}"

    @property
    def pg_data(self) -> Path:
        return self.workspace / "postgres-data"

    @property
    def database_url(self) -> str:
        user = urllib.parse.quote(pwd.getpwuid(os.getuid()).pw_name, safe="")
        database = urllib.parse.quote(str(self.manifest["database"]), safe="")
        host = urllib.parse.quote(str(self.socket_dir), safe="")
        search_path = urllib.parse.quote(
            f"-csearch_path={self.manifest['schema']}", safe=""
        )
        return (
            f"postgresql+psycopg://{user}@/{database}?host={host}&options={search_path}"
        )

    @property
    def logs(self) -> Path:
        return Path(self.manifest["logs_path"])

    def _env(self) -> dict[str, str]:
        allowed = {
            key: os.environ[key] for key in ("PATH", "TMPDIR") if key in os.environ
        }
        allowed.update(
            {
                "LC_ALL": "C",
                "PYTHONIOENCODING": "utf-8",
                "PYTHONPATH": str(self.root / "apps/api/src"),
                "DEEPWORK_DATABASE_URL": self.database_url,
                "DEEPWORK_ACCESS_KEY": self.access_key,
                "DEEPWORK_WEB_ORIGINS": f"http://127.0.0.1:{self.ports['web']}",
            }
        )
        return allowed

    def prepare(self) -> None:
        if self.workspace.exists():
            raise DriverError(f"allocated workspace already exists: {self.namespace}")
        self.workspace.mkdir(parents=True, mode=0o700)
        (self.workspace / "home").mkdir(mode=0o700)
        self.logs.mkdir(mode=0o700)
        ownership_log = self.logs / "ownership.log"
        ownership_log.write_text(f"namespace={self.namespace}\n", encoding="utf-8")
        ownership_log.chmod(0o600)
        if self.socket_dir.exists() or self.socket_dir.is_symlink():
            raise DriverError(
                f"PostgreSQL socket allocation already exists: {self.namespace}"
            )
        self.socket_dir.mkdir(mode=0o700)
        for port in self.ports.values():
            if not _port_closed(port):
                raise DriverError(f"allocated port is already in use: {self.namespace}")
        next_executable = self.root / "apps/web/node_modules/next/dist/bin/next"
        if not next_executable.is_file():
            raise DriverError(f"web dependencies are absent in {self.namespace} root")
        self.next_env_snapshot = _capture_next_env(self.root, self.workspace)
        self._persist_state()
        self._init_postgres()
        self._migrate()

    def _init_postgres(self) -> None:
        env = self._env()
        subprocess.run(
            [
                str(self.postgres_bins["initdb"]),
                "-D",
                str(self.pg_data),
                "--auth=trust",
                "--encoding=UTF8",
                "--no-locale",
                "--username",
                pwd.getpwuid(os.getuid()).pw_name,
            ],
            check=True,
            capture_output=True,
            timeout=60,
            env=env,
        )
        subprocess.run(
            [
                str(self.postgres_bins["pg_ctl"]),
                "-D",
                str(self.pg_data),
                "-l",
                str(self.logs / "postgres.log"),
                "-o",
                f"-h '' -k {self.socket_dir} -p 5432",
                "-w",
                "start",
            ],
            check=True,
            capture_output=True,
            timeout=60,
            env=env,
        )
        subprocess.run(
            [
                str(self.postgres_bins["createdb"]),
                "-h",
                str(self.socket_dir),
                "-p",
                "5432",
                str(self.manifest["database"]),
            ],
            check=True,
            capture_output=True,
            timeout=30,
            env=env,
        )
        schema = str(self.manifest["schema"])
        if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", schema):
            raise DriverError("allocated PostgreSQL schema is unsafe")
        subprocess.run(
            [
                str(self.postgres_bins["psql"]),
                "-h",
                str(self.socket_dir),
                "-p",
                "5432",
                "-d",
                str(self.manifest["database"]),
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'CREATE SCHEMA "{schema}"',
            ],
            check=True,
            capture_output=True,
            timeout=30,
            env=env,
        )

    def _migrate(self) -> None:
        subprocess.run(
            [str(self.api_bin / "deepwork-migrate"), "upgrade"],
            cwd=self.root / "apps/api",
            env=self._env(),
            check=True,
            capture_output=True,
            timeout=60,
        )

    def _start_process(
        self,
        name: str,
        command: list[str],
        *,
        extra_env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> OwnedProcess:
        log_path = self.logs / f"{name}.log"
        log_file = log_path.open("ab", buffering=0)
        env = self._env()
        if extra_env:
            env.update(extra_env)
        process = subprocess.Popen(
            command,
            cwd=cwd or self.root,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        owned = OwnedProcess(
            name=name,
            process=process,
            log_file=log_file,
            command_marker=str(command[0]),
        )
        self.processes.append(owned)
        self._persist_state()
        return owned

    def _persist_state(self) -> None:
        state = {
            "namespace": self.namespace,
            "processes": [
                {
                    "name": item.name,
                    "pid": item.process.pid,
                    "marker": item.command_marker,
                }
                for item in self.processes
                if item.process.poll() is None
            ],
            "postgres_data": str(self.pg_data),
            "next_env": self.next_env_snapshot,
        }
        _write_private_json(self.workspace / STATE_FILE, state)

    def start(self) -> None:
        self.started_at = _now()
        driver = Path(__file__).resolve()
        self._start_process(
            "telemetry",
            [
                str(self.api_bin / "python"),
                str(driver),
                "fixture-service",
                "--kind",
                "telemetry",
                "--port",
                str(self.ports["telemetry"]),
                "--namespace",
                self.namespace,
                "--data-root",
                str(self.workspace / "telemetry"),
            ],
        )
        self._start_process(
            "worker",
            [
                str(self.api_bin / "python"),
                str(driver),
                "fixture-service",
                "--kind",
                "worker-object",
                "--port",
                str(self.ports["worker"]),
                "--namespace",
                self.namespace,
                "--data-root",
                str(self.workspace / "objects"),
                "--object-prefix",
                str(self.manifest["object_prefix"]),
                "--telemetry-url",
                f"http://127.0.0.1:{self.ports['telemetry']}",
                "--api-python",
                str(self.api_bin / "deepwork-worker"),
                "--api-root",
                str(self.root / "apps/api/src"),
            ],
        )
        self._start_api()
        next_executable = self.root / "apps/web/node_modules/next/dist/bin/next"
        self._start_process(
            "web",
            [
                str(self.node),
                str(next_executable),
                "dev",
                "--webpack",
                "--hostname",
                "127.0.0.1",
                "--port",
                str(self.ports["web"]),
            ],
            extra_env={
                "NEXT_PUBLIC_API_BASE_URL": "",
                "DEEPWORK_API_ORIGIN": f"http://127.0.0.1:{self.ports['api']}",
                "NEXT_TELEMETRY_DISABLED": "1",
            },
            cwd=self.root / "apps/web",
        )
        _wait_url(f"http://127.0.0.1:{self.ports['telemetry']}/health")
        _wait_url(f"http://127.0.0.1:{self.ports['worker']}/health")
        _wait_url(f"http://127.0.0.1:{self.ports['api']}/health")
        _wait_url(f"http://127.0.0.1:{self.ports['web']}/login", timeout=90)
        self.ready_at = _now()

    def _start_api(self) -> OwnedProcess:
        owned = self._start_process(
            "api",
            [
                str(self.api_bin / "deepwork-api"),
                "--port",
                str(self.ports["api"]),
                "--task-database",
                str(self.workspace / "tasks.sqlite3"),
                "--settings-database",
                str(self.workspace / "settings.sqlite3"),
            ],
        )
        return owned

    def exercise_worker(self) -> str:
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        status, _ = _request_json(
            f"http://127.0.0.1:{self.ports['api']}/api/v1/auth/login",
            method="POST",
            payload={"accessKey": self.access_key},
            opener=opener,
        )
        if status != 200:
            raise DriverError("worker acceptance login failed")
        status, accepted = _request_json(
            f"http://127.0.0.1:{self.ports['api']}/api/v1/durable-jobs/fixture",
            method="POST",
            headers={"Idempotency-Key": f"product-demo-{self.namespace}"},
            opener=opener,
        )
        if status != 202 or not isinstance(accepted, dict):
            raise DriverError("durable job was not accepted")
        job_id = accepted.get("jobId")
        deadline = time.monotonic() + 20
        last_observation: tuple[int, Any] | None = None
        while time.monotonic() < deadline:
            status, job = _request_json(
                f"http://127.0.0.1:{self.ports['api']}/api/v1/durable-jobs/{job_id}",
                opener=opener,
            )
            last_observation = (status, job)
            if (
                status == 200
                and isinstance(job, dict)
                and job.get("status") == "succeeded"
            ):
                _wait_url(
                    f"http://127.0.0.1:{self.ports['worker']}/objects-ready/{job_id}"
                )
                return str(job_id)
            time.sleep(0.2)
        safe_state = (
            last_observation[1].get("status")
            if last_observation
            and isinstance(last_observation[1], dict)
            and isinstance(last_observation[1].get("status"), str)
            else "unavailable"
        )
        raise DriverError(
            f"durable worker did not complete the accepted job; last state={safe_state}"
        )

    def restart_api(self) -> None:
        api = next(
            item
            for item in reversed(self.processes)
            if item.name == "api" and item.process.poll() is None
        )
        self.api_restart_before = f"{self.namespace}:api:pid-{api.process.pid}"
        _stop_owned(api)
        restarted = self._start_api()
        _wait_url(f"http://127.0.0.1:{self.ports['api']}/health")
        self.api_restart_after = f"{self.namespace}:api:pid-{restarted.process.pid}"

    def stop(self) -> None:
        for owned in reversed(self.processes):
            _stop_owned(owned)
        self.processes.clear()
        _stop_postgres(
            self.postgres_bins["pg_ctl"], self.pg_data, self.socket_dir, self._env()
        )
        _restore_next_env(self.root, self.workspace, self.next_env_snapshot)
        proof = Path(self.manifest["proof_path"])
        if proof.exists() and proof.parent == Path(self.manifest["evidence_root"]):
            shutil.rmtree(proof)
        if (
            self.workspace.exists()
            and self.workspace.parent == self.root / ".deepwork" / "worktrees"
        ):
            shutil.rmtree(self.workspace)
        if self.socket_dir.is_dir() and not self.socket_dir.is_symlink():
            self.socket_dir.rmdir()
        _remove_empty_runtime_parents(self.root)
        self.stopped_at = _now()
        if not all(_port_closed(port) for port in self.ports.values()):
            raise DriverError(
                f"scoped ports remain open after teardown: {self.namespace}"
            )


def _stop_owned(owned: OwnedProcess) -> None:
    process = owned.process
    if process.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
    with contextlib.suppress(Exception):
        owned.log_file.close()


def _remove_empty_runtime_parents(root: Path) -> None:
    for path in (root / ".deepwork" / "worktrees", root / ".deepwork"):
        if path.is_dir() and not path.is_symlink():
            with contextlib.suppress(OSError):
                path.rmdir()


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    server: "_FixtureServer"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _json(self, status: int, value: Any) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/health":
            self._json(200, {"status": "ready", "kind": self.server.kind})
            return
        if self.server.kind == "telemetry" and parsed.path == "/events":
            requested = urllib.parse.parse_qs(parsed.query).get("namespace", [""])[0]
            events = [
                event
                for event in self.server.events
                if event.get("namespace") == requested
            ]
            self._json(200, {"events": events})
            return
        if self.server.kind == "worker-object" and parsed.path.startswith(
            "/objects-ready/"
        ):
            job_id = parsed.path.rsplit("/", 1)[-1]
            self._json(
                200 if job_id in self.server.completed_jobs else 404,
                {"ready": job_id in self.server.completed_jobs},
            )
            return
        if self.server.kind == "worker-object" and parsed.path.startswith("/objects/"):
            relative = urllib.parse.unquote(parsed.path.removeprefix("/objects/"))
            target = self.server.object_path(relative)
            if target is None or not target.is_file():
                self._json(404, {"found": False})
            else:
                self._json(200, json.loads(target.read_text(encoding="utf-8")))
            return
        self._json(404, {"found": False})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 64 * 1024:
            self._json(413, {"accepted": False})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"accepted": False})
            return
        if self.server.kind == "telemetry" and self.path == "/events":
            if (
                not isinstance(payload, dict)
                or payload.get("namespace") != self.server.namespace
            ):
                self._json(403, {"accepted": False})
                return
            self.server.events.append(payload)
            _write_private_json(
                self.server.data_root / "events.json", self.server.events
            )
            self._json(202, {"accepted": True})
            return
        self._json(404, {"accepted": False})


class _FixtureServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        *,
        kind: str,
        namespace: str,
        data_root: Path,
        object_prefix: str | None = None,
    ) -> None:
        super().__init__(address, _FixtureHandler)
        self.kind = kind
        self.namespace = namespace
        self.data_root = data_root
        self.object_prefix = object_prefix
        self.events: list[dict[str, Any]] = []
        self.completed_jobs: set[str] = set()
        data_root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def object_path(self, relative: str) -> Path | None:
        if self.object_prefix is None or not relative.startswith(self.object_prefix):
            return None
        if ".." in Path(relative).parts or Path(relative).is_absolute():
            return None
        resolved = (self.data_root / relative).resolve(strict=False)
        if self.data_root.resolve() not in resolved.parents:
            return None
        return resolved


def _worker_loop(
    server: _FixtureServer,
    *,
    worker_executable: Path,
    api_root: Path,
    telemetry_url: str,
) -> None:
    env = {
        key: os.environ[key]
        for key in os.environ
        if key in {"PATH", "LC_ALL", "PYTHONIOENCODING", "DEEPWORK_DATABASE_URL"}
    }
    env["PYTHONPATH"] = str(api_root)
    while not getattr(server, "stopping", False):
        result = subprocess.run(
            [
                str(worker_executable),
                "--once",
                "--worker-id",
                f"product-demo-{server.namespace}",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        _write_private_json(
            server.data_root / "worker-status.json",
            {
                "returncode": result.returncode,
                "stdout": result.stdout[-2_000:],
                "stderr": result.stderr[-2_000:],
            },
        )
        if result.returncode == 0:
            with contextlib.suppress(json.JSONDecodeError):
                payload = json.loads(result.stdout)
                job_id = payload.get("jobId")
                if payload.get("status") == "succeeded" and isinstance(job_id, str):
                    relative = f"{server.object_prefix}{job_id}.json"
                    target = server.object_path(relative)
                    if target is not None:
                        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                        _write_private_json(
                            target,
                            {
                                "jobId": job_id,
                                "namespace": server.namespace,
                                "status": "succeeded",
                            },
                        )
                        server.completed_jobs.add(job_id)
                        _request_json(
                            f"{telemetry_url}/events",
                            method="POST",
                            payload={
                                "namespace": server.namespace,
                                "event": "job.succeeded",
                                "jobId": job_id,
                            },
                        )
        time.sleep(0.2)


def fixture_service(args: argparse.Namespace) -> int:
    namespace = validate_namespace(args.namespace)
    data_root = Path(args.data_root).resolve(strict=False)
    server = _FixtureServer(
        ("127.0.0.1", args.port),
        kind=args.kind,
        namespace=namespace,
        data_root=data_root,
        object_prefix=args.object_prefix,
    )
    worker: threading.Thread | None = None
    if args.kind == "worker-object":
        if not all(
            (args.api_python, args.api_root, args.telemetry_url, args.object_prefix)
        ):
            raise DriverError("worker-object service configuration is incomplete")
        worker = threading.Thread(
            target=_worker_loop,
            args=(server,),
            kwargs={
                "worker_executable": Path(args.api_python),
                "api_root": Path(args.api_root),
                "telemetry_url": args.telemetry_url,
            },
            daemon=True,
        )
        worker.start()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.stopping = True
        server.server_close()
        if worker is not None:
            worker.join(timeout=2)
    return 0


def _write_proof_marker(stack: Stack, job_id: str) -> Path:
    proof = Path(stack.manifest["proof_path"])
    if proof.parent != Path(stack.manifest["evidence_root"]):
        raise DriverError("allocated proof path is outside its evidence root")
    marker = proof / f"synthetic-proof-{stack.namespace}.json"
    _write_private_json(
        marker,
        {"namespace": stack.namespace, "jobId": job_id, "status": "observed"},
    )
    return marker


def _probe_isolation(
    source: Stack,
    target: Stack,
    browser_report: dict[str, Any],
    job_ids: dict[str, str],
) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    psql = source.postgres_bins["psql"]
    env = source._env()
    database_result = subprocess.run(
        [
            str(psql),
            "-h",
            str(source.socket_dir),
            "-p",
            "5432",
            "-d",
            str(source.manifest["database"]),
            "-Atc",
            "SELECT current_database()",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    checks["database"] = (
        database_result.returncode == 0
        and database_result.stdout.strip() == source.manifest["database"]
        and target.manifest["database"] not in database_result.stdout
    )
    schema_result = subprocess.run(
        [
            str(psql),
            "-h",
            str(source.socket_dir),
            "-p",
            "5432",
            "-d",
            str(source.manifest["database"]),
            "-Atc",
            "SELECT schema_name FROM information_schema.schemata",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    schemas = set(schema_result.stdout.splitlines())
    checks["schema"] = (
        schema_result.returncode == 0
        and source.manifest["schema"] in schemas
        and target.manifest["schema"] not in schemas
    )
    target_relative = (
        f"{target.manifest['object_prefix']}{job_ids[target.namespace]}.json"
    )
    target_status, target_object = _request_json(
        f"http://127.0.0.1:{target.ports['worker']}/objects/{urllib.parse.quote(target_relative)}"
    )
    source_status, _ = _request_json(
        f"http://127.0.0.1:{source.ports['worker']}/objects/{urllib.parse.quote(target_relative)}"
    )
    checks["object_prefix"] = (
        target_status == 200
        and isinstance(target_object, dict)
        and target_object.get("namespace") == target.namespace
        and source_status == 404
    )
    journey = next(
        item
        for item in browser_report["journeys"]
        if item["label"]
        == ("stack-a" if source.access_key == ACCESS_KEYS[0] else "stack-b")
    )
    checks["browser_storage"] = journey.get("peerStorageObserved") is None
    own_status, own_telemetry = _request_json(
        f"http://127.0.0.1:{source.ports['telemetry']}/events?namespace={urllib.parse.quote(source.namespace)}"
    )
    status, telemetry = _request_json(
        f"http://127.0.0.1:{source.ports['telemetry']}/events?namespace={urllib.parse.quote(target.namespace)}"
    )
    checks["telemetry"] = (
        own_status == 200
        and isinstance(own_telemetry, dict)
        and any(
            event.get("namespace") == source.namespace
            for event in own_telemetry.get("events", [])
            if isinstance(event, dict)
        )
        and status == 200
        and telemetry == {"events": []}
    )
    log_contents = [
        path.read_text(encoding="utf-8", errors="replace")
        for path in source.logs.glob("*.log")
        if path.is_file() and not path.is_symlink()
    ]
    checks["logs"] = any(
        source.namespace in content for content in log_contents
    ) and all(target.namespace not in content for content in log_contents)
    source_proof_id = f"synthetic-proof-{source.namespace}.json"
    target_proof_id = f"synthetic-proof-{target.namespace}.json"
    source_proof = Path(source.manifest["proof_path"])
    checks["proof"] = (source_proof / source_proof_id).is_file() and not (
        source_proof / target_proof_id
    ).exists()
    return checks


def _live_api_pid(stack: Stack) -> int:
    candidates = [
        item.process.pid
        for item in stack.processes
        if item.name == "api" and item.process.poll() is None
    ]
    if not candidates:
        raise DriverError(f"live API process is absent: {stack.namespace}")
    return candidates[-1]


def _prove_process_control(source: Stack, target: Stack) -> bool:
    target_pid_before = _live_api_pid(target)
    source.restart_api()
    _wait_url(f"http://127.0.0.1:{target.ports['api']}/health", timeout=5)
    return (
        _live_api_pid(target) == target_pid_before
        and source.api_restart_before != source.api_restart_after
        and _live_api_pid(source) != target_pid_before
    )


def _browser_command(
    root: Path,
    node: Path,
    report: Path,
    stacks: tuple[Stack, Stack],
    *,
    reopen: tuple[str, str] | None = None,
) -> list[str]:
    command = [
        str(node),
        str(root / "tools/product_demo/browser_journey.mjs"),
        "--origin-a",
        f"http://127.0.0.1:{stacks[0].ports['web']}",
        "--origin-b",
        f"http://127.0.0.1:{stacks[1].ports['web']}",
        "--storage-a",
        stacks[0].manifest["browser"]["storage_key"],
        "--storage-b",
        stacks[1].manifest["browser"]["storage_key"],
        "--report",
        str(report),
    ]
    if reopen:
        command.extend(["--reopen-a", reopen[0], "--reopen-b", reopen[1]])
    return command


def _validate_invocation(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    root = canonical_root(args.root)
    peer = canonical_root(args.peer_root)
    if root == peer:
        raise DriverError("product-demo roots must differ")
    evidence = Path(args.evidence_dir).resolve(strict=False)
    if not RUN_NONCE_RE.fullmatch(args.run_nonce):
        raise DriverError("run nonce is invalid")
    if not COMMIT_RE.fullmatch(args.driver_revision):
        raise DriverError("driver revision is invalid")
    if not SHA_RE.fullmatch(args.driver_sha256) or not SHA_RE.fullmatch(
        args.contract_semantic_sha256
    ):
        raise DriverError("driver digest input is invalid")
    actual = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if actual != args.driver_sha256:
        raise DriverError("invoked driver bytes do not match the sealed digest")
    return root, peer, evidence


def _copy_failure_logs(stack: Stack, evidence_dir: Path) -> None:
    if not stack.logs.is_dir():
        return
    diagnostic_dir = evidence_dir / "failure-logs" / stack.namespace
    diagnostic_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    for log in stack.logs.glob("*.log"):
        if (
            log.is_file()
            and not log.is_symlink()
            and log.stat().st_size <= 2 * 1024 * 1024
        ):
            shutil.copy2(log, diagnostic_dir / log.name)


def _cleanup_remaining(
    stacks: Sequence[Stack], cleaned: set[str], evidence_dir: Path, *, passed: bool
) -> None:
    for stack in stacks:
        if stack.namespace in cleaned:
            continue
        try:
            if not passed:
                with contextlib.suppress(Exception):
                    _copy_failure_logs(stack, evidence_dir)
        finally:
            with contextlib.suppress(Exception):
                stack.stop()


def dual_exercise(args: argparse.Namespace) -> int:
    root, peer, evidence_dir = _validate_invocation(args)
    evidence_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest_a = _load_manifest(Path(args.manifest_a), root)
    manifest_b = _load_manifest(Path(args.manifest_b), peer)
    if manifest_a["namespace"] == manifest_b["namespace"]:
        raise DriverError("product-demo namespaces must differ")
    node = _find_node()
    api_bin = root / "apps/api/.venv/bin"
    if not all(
        (api_bin / name).is_file()
        for name in ("python", "deepwork-api", "deepwork-migrate", "deepwork-worker")
    ):
        raise DriverError("bootstrapped API entry points are unavailable")
    postgres_bins = {
        name: _find_executable(name)
        for name in ("initdb", "pg_ctl", "createdb", "psql")
    }
    stacks = (
        Stack(root, manifest_a, ACCESS_KEYS[0], node, api_bin, postgres_bins),
        Stack(peer, manifest_b, ACCESS_KEYS[1], node, api_bin, postgres_bins),
    )
    browser_root = evidence_dir / "browser"
    browser_report_path = browser_root / "journeys.json"
    reopen_report_path = browser_root / "reopen.json"
    cleaned: set[str] = set()
    passed = False
    try:
        for stack in stacks:
            stack.prepare()
        start_errors: list[BaseException] = []

        def start_stack(stack: Stack) -> None:
            try:
                stack.start()
            except BaseException as error:  # propagate thread failures to the owner
                start_errors.append(error)

        starters = [
            threading.Thread(target=start_stack, args=(stack,)) for stack in stacks
        ]
        for thread in starters:
            thread.start()
        for thread in starters:
            thread.join()
        if start_errors:
            first_error = start_errors[0]
            raise DriverError(
                "product-demo stack startup failed: "
                f"{type(first_error).__name__}: {first_error}"
            )
        if any(not stack.ready_at for stack in stacks):
            raise DriverError("one or more product-demo stacks did not become ready")
        job_ids_by_namespace = {
            stack.namespace: stack.exercise_worker() for stack in stacks
        }
        for stack in stacks:
            _write_proof_marker(stack, job_ids_by_namespace[stack.namespace])
        subprocess.run(
            _browser_command(root, node, browser_report_path, stacks),
            cwd=root,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
            check=True,
            timeout=180,
        )
        browser_report = json.loads(browser_report_path.read_text(encoding="utf-8"))
        if (
            not isinstance(browser_report, dict)
            or not isinstance(browser_report.get("journeys"), list)
            or len(browser_report.get("journeys", [])) != 2
            or not all(
                isinstance(journey, dict)
                for journey in browser_report.get("journeys", [])
            )
            or any(
                not journey.get("liveProgressObserved")
                or not journey.get("portableDownload")
                or not isinstance(journey.get("resultText"), str)
                or not isinstance(journey.get("prompt"), str)
                or journey.get("prompt") not in journey.get("resultText", "")
                or not isinstance(journey.get("sourceText"), str)
                or not journey.get("sourceText")
                or not isinstance(journey.get("retainedEventsText"), str)
                for journey in browser_report.get("journeys", [])
            )
        ):
            raise DriverError("browser journey report is incomplete")
        isolation = {
            (source.namespace, target.namespace): _probe_isolation(
                source, target, browser_report, job_ids_by_namespace
            )
            for source, target in ((stacks[0], stacks[1]), (stacks[1], stacks[0]))
        }
        isolation[(stacks[0].namespace, stacks[1].namespace)]["process_control"] = (
            _prove_process_control(stacks[0], stacks[1])
        )
        isolation[(stacks[1].namespace, stacks[0].namespace)]["process_control"] = (
            _prove_process_control(stacks[1], stacks[0])
        )
        if any(
            not passed for checks in isolation.values() for passed in checks.values()
        ):
            raise DriverError("one or more cross-stack isolation probes failed")
        task_paths = tuple(item["taskPath"] for item in browser_report["journeys"])
        subprocess.run(
            _browser_command(root, node, reopen_report_path, stacks, reopen=task_paths),
            cwd=root,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
            check=True,
            timeout=120,
        )
        reopen_report = json.loads(reopen_report_path.read_text(encoding="utf-8"))
        reopened = reopen_report.get("reopened", [])
        if (
            len(reopened) != 4
            or {
                (item.get("label"), item.get("viewport"))
                for item in reopened
                if isinstance(item, dict)
            }
            != {
                ("stack-a", "1440x900"),
                ("stack-a", "390x844"),
                ("stack-b", "1440x900"),
                ("stack-b", "390x844"),
            }
            or not all(item.get("reopenedAfterApiRestart") for item in reopened)
        ):
            raise DriverError(
                "desktop and phone fresh-browser reopen after API restart were not proven"
            )

        public = [public_manifest(manifest_a), public_manifest(manifest_b)]
        allocation_digests = {
            manifest["namespace"]: _bound_digest(
                "allocation",
                manifest,
                run_nonce=args.run_nonce,
                driver_revision=args.driver_revision,
                driver_sha256=args.driver_sha256,
            )
            for manifest in public
        }
        cross_observations: list[dict[str, Any]] = []
        for source, target in ((stacks[0], stacks[1]), (stacks[1], stacks[0])):
            for dimension in sorted(PROBE_DIMENSIONS):
                if not isolation[(source.namespace, target.namespace)][dimension]:
                    raise DriverError(f"failed isolation dimension: {dimension}")
                record = {
                    "source_namespace": source.namespace,
                    "target_namespace": target.namespace,
                    "dimension": dimension,
                    "result": "not-observed",
                    "probe_id": f"probe-{source.namespace[-1]}-{target.namespace[-1]}-{dimension.replace('_', '-')}",
                }
                record["result_digest"] = _bound_digest(
                    "cross-observation",
                    record,
                    run_nonce=args.run_nonce,
                    driver_revision=args.driver_revision,
                    driver_sha256=args.driver_sha256,
                )
                cross_observations.append(record)
        restarts: list[dict[str, Any]] = []
        for stack in stacks:
            record = {
                "namespace": stack.namespace,
                "rule": "reuse-reserved-resources-with-exact-teardown-token",
                "allocation_fingerprint_before": allocation_digests[stack.namespace],
                "allocation_fingerprint_after": allocation_digests[stack.namespace],
                "process_identity_before": stack.api_restart_before,
                "process_identity_after": stack.api_restart_after,
            }
            record["restart_digest"] = _bound_digest(
                "restart",
                record,
                run_nonce=args.run_nonce,
                driver_revision=args.driver_revision,
                driver_sha256=args.driver_sha256,
            )
            restarts.append(record)

        stacks[0].stop()
        cleaned.add(stacks[0].namespace)
        _wait_url(f"http://127.0.0.1:{stacks[1].ports['api']}/health", timeout=5)
        _wait_url(f"http://127.0.0.1:{stacks[1].ports['web']}/tasks", timeout=5)
        first_stopped = stacks[0].stopped_at
        stacks[1].stop()
        cleaned.add(stacks[1].namespace)
        teardown: list[dict[str, Any]] = []
        for order, stack in enumerate(stacks, start=1):
            record = {
                "namespace": stack.namespace,
                "order": order,
                "peer_survived_after": order == 1,
                "resources_absent": sorted(TEARDOWN_RESOURCES),
                "reservation_absent": False,
            }
            record["cleanup_digest"] = _bound_digest(
                "cleanup",
                record,
                run_nonce=args.run_nonce,
                driver_revision=args.driver_revision,
                driver_sha256=args.driver_sha256,
            )
            teardown.append(record)
        evidence = {
            "schema_version": 1,
            "evidence_class": "product-demo",
            "status": "passed",
            "acceptance": "accepted",
            "exercise_id": f"product-demo-{args.run_nonce[:16]}",
            "run_nonce": args.run_nonce,
            "driver_revision": args.driver_revision,
            "driver_sha256": args.driver_sha256,
            "contract_semantic_sha256": args.contract_semantic_sha256,
            "namespaces": [stack.namespace for stack in stacks],
            "manifests": public,
            "allocation_digests": allocation_digests,
            "concurrency": {
                "a_started_at": stacks[0].started_at,
                "b_started_at": stacks[1].started_at,
                "a_ready_at": stacks[0].ready_at,
                "b_ready_at": stacks[1].ready_at,
                "a_stopped_at": first_stopped,
                "b_stopped_at": stacks[1].stopped_at,
            },
            "cross_observations": cross_observations,
            "restarts": restarts,
            "teardown": teardown,
        }
        _write_private_json(
            evidence_dir / "product-demo-summary.json",
            {
                "schemaVersion": 1,
                "status": "passed",
                "components": [
                    "web",
                    "api",
                    "worker",
                    "postgres",
                    "object",
                    "telemetry",
                ],
                "jobs": [job_ids_by_namespace[stack.namespace] for stack in stacks],
                "browser": {
                    "journeys": 2,
                    "reopenedAfterApiRestart": 4,
                    "viewports": ["1440x900", "390x844"],
                },
                "isolationDimensions": sorted(PROBE_DIMENSIONS),
            },
        )
        write_evidence(evidence_dir / "exercise.json", evidence)
        passed = True
        return 0
    finally:
        _cleanup_remaining(stacks, cleaned, evidence_dir, passed=passed)


def _recover_stack(root: Path, manifest: dict[str, Any], pg_ctl: Path) -> bool:
    workspace = Path(manifest["workspace_path"])
    if not workspace.exists():
        socket_digest = hashlib.sha256(str(manifest["namespace"]).encode()).hexdigest()[
            :16
        ]
        socket_dir = Path("/tmp") / f"deepwork-pg-{socket_digest}"
        return (
            _socket_is_closed(socket_dir)
            and not socket_dir.exists()
            and all(_port_closed(port) for port in manifest["ports"].values())
        )
    if workspace.parent != root / ".deepwork" / "worktrees":
        return False
    state_path = workspace / STATE_FILE
    if state_path.is_symlink() or not state_path.is_file():
        return False
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if (
        not isinstance(state, dict)
        or state.get("namespace") != manifest["namespace"]
        or state.get("postgres_data") != str(workspace / "postgres-data")
        or not isinstance(state.get("processes"), list)
    ):
        return False
    verified = True
    for record in state["processes"]:
        if not isinstance(record, dict):
            verified = False
            continue
        pid = record.get("pid")
        marker = record.get("marker")
        if not isinstance(pid, int) or pid <= 1 or not isinstance(marker, str):
            verified = False
            continue
        try:
            if os.getpgid(pid) != pid:
                verified = False
                continue
            command = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout
            if marker not in command or (
                str(root) not in command and "worktree_driver.py" not in command
            ):
                verified = False
                continue
            os.killpg(pid, signal.SIGTERM)
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.1)
            else:
                os.killpg(pid, signal.SIGKILL)
                time.sleep(0.2)
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    verified = False
        except ProcessLookupError:
            pass
    pg_data = workspace / "postgres-data"
    socket_digest = hashlib.sha256(str(manifest["namespace"]).encode()).hexdigest()[:16]
    socket_dir = Path("/tmp") / f"deepwork-pg-{socket_digest}"
    try:
        recovery_env = {
            key: os.environ[key] for key in ("PATH", "TMPDIR") if key in os.environ
        }
        recovery_env["LC_ALL"] = "C"
        _stop_postgres(pg_ctl, pg_data, socket_dir, recovery_env)
        _restore_next_env(root, workspace, state.get("next_env"))
    except (DriverError, OSError, subprocess.SubprocessError):
        return False
    if not verified or not all(
        _port_closed(port) for port in manifest["ports"].values()
    ):
        return False
    if socket_dir.is_dir() and not socket_dir.is_symlink():
        try:
            socket_dir.rmdir()
        except OSError:
            return False
    if socket_dir.exists() or socket_dir.is_symlink():
        return False
    proof = Path(manifest["proof_path"])
    if proof.exists() and proof.parent == Path(manifest["evidence_root"]):
        shutil.rmtree(proof)
    shutil.rmtree(workspace)
    _remove_empty_runtime_parents(root)
    return (
        not workspace.exists()
        and not socket_dir.exists()
        and all(_port_closed(port) for port in manifest["ports"].values())
    )


def cleanup(args: argparse.Namespace) -> int:
    root, peer, evidence_dir = _validate_invocation(args)
    manifests = (
        _load_manifest(Path(args.manifest_a), root),
        _load_manifest(Path(args.manifest_b), peer),
    )
    pg_ctl = _find_executable("pg_ctl")
    records = []
    for workspace_root, manifest in ((root, manifests[0]), (peer, manifests[1])):
        try:
            verified = _recover_stack(workspace_root, manifest, pg_ctl)
        except (OSError, ValueError, subprocess.SubprocessError):
            verified = False
        record = {
            "namespace": manifest["namespace"],
            "process_identity_verified": verified,
            "resources_absent": sorted(TEARDOWN_RESOURCES),
        }
        record["cleanup_digest"] = _bound_digest(
            "recovery-cleanup",
            record,
            run_nonce=args.run_nonce,
            driver_revision=args.driver_revision,
            driver_sha256=args.driver_sha256,
        )
        records.append(record)
    evidence = {
        "schema_version": 1,
        "evidence_class": "product-demo-cleanup",
        "status": "clean"
        if all(record["process_identity_verified"] for record in records)
        else "failed",
        "run_nonce": args.run_nonce,
        "driver_revision": args.driver_revision,
        "driver_sha256": args.driver_sha256,
        "contract_semantic_sha256": args.contract_semantic_sha256,
        "namespaces": [manifest["namespace"] for manifest in manifests],
        "records": records,
    }
    write_evidence(evidence_dir / "recovery-cleanup.json", evidence)
    return 0 if evidence["status"] == "clean" else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    service = commands.add_parser("fixture-service")
    service.add_argument(
        "--kind", choices=("telemetry", "worker-object"), required=True
    )
    service.add_argument("--port", type=int, required=True)
    service.add_argument("--namespace", required=True)
    service.add_argument("--data-root", required=True)
    service.add_argument("--object-prefix")
    service.add_argument("--telemetry-url")
    service.add_argument("--api-python")
    service.add_argument("--api-root")
    for name in ("dual-exercise", "cleanup"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--peer-root", required=True)
        command.add_argument("--manifest-a", required=True)
        command.add_argument("--manifest-b", required=True)
        command.add_argument("--evidence-dir", required=True)
        command.add_argument("--run-nonce", required=True)
        command.add_argument("--driver-revision", required=True)
        command.add_argument("--driver-sha256", required=True)
        command.add_argument("--contract-semantic-sha256", required=True)
        if name == "cleanup":
            command.add_argument("--recovery-reason", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "fixture-service":
            return fixture_service(args)
        if args.command == "dual-exercise":
            return dual_exercise(args)
        return cleanup(args)
    except (
        DriverError,
        IsolationError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as error:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": type(error).__name__,
                    "message": str(error),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
