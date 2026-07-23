"""Install the built wheel into a clean consumer and verify public package proof."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_EXPORTS = {
    "CONFIG_CONTRACT_GATE",
    "AgentPackageConfig",
    "RuntimeAvailability",
    "RuntimeCapabilityUnavailable",
    "UnavailableAgentState",
    "create_graph",
    "initial_unavailable_state",
    "runtime_availability",
}


def _sha256(path: Path) -> str:
    """Return a reproducible artifact digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    # Commands are fixed local Python/pip invocations assembled by this script.
    subprocess.run(command, check=True, env=environment)  # noqa: S603


def main() -> int:
    """Verify wheel contents and import behavior without an index or repository path."""
    wheels = sorted((PACKAGE_ROOT / "dist").glob("deepwork_agent-*.whl"))
    source_distributions = sorted((PACKAGE_ROOT / "dist").glob("deepwork_agent-*.tar.gz"))
    if len(wheels) != 1:
        msg = f"expected exactly one wheel, found {len(wheels)}"
        raise RuntimeError(msg)
    if len(source_distributions) != 1:
        msg = f"expected exactly one source distribution, found {len(source_distributions)}"
        raise RuntimeError(msg)
    wheel = wheels[0]
    source_distribution = source_distributions[0]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    marker = "deepwork_agent/py.typed"
    if marker not in names:
        msg = f"built wheel does not contain {marker}"
        raise RuntimeError(msg)

    with tempfile.TemporaryDirectory(prefix="deepwork-agent-consumer-") as temporary:
        environment_root = Path(temporary) / "venv"
        _run([sys.executable, "-m", "venv", str(environment_root)])
        python = environment_root / "bin" / "python"
        pip = environment_root / "bin" / "pip"
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        environment["PIP_NO_CACHE_DIR"] = "1"
        _run(
            [str(pip), "install", "--no-index", "--no-deps", str(wheel)],
            environment=environment,
        )
        consumer = (
            "import json; import deepwork_agent as package; "
            "from importlib.resources import files; "
            "assert files('deepwork_agent').joinpath('py.typed').is_file(); "
            f"assert set(package.__all__) == {EXPECTED_EXPORTS!r}; "
            "availability = package.runtime_availability(); "
            "assert availability.available is False; "
            "assert availability.contract_gate == 'SPIKE-CONFIG-001'; "
            "print(json.dumps({'exports': sorted(package.__all__), "
            "'gate': availability.contract_gate, 'network': 'not-used'}))"
        )
        _run([str(python), "-I", "-c", consumer], environment=environment)

    evidence = {
        "wheel": wheel.name,
        "wheel_sha256": _sha256(wheel),
        "source_distribution": source_distribution.name,
        "source_distribution_sha256": _sha256(source_distribution),
        "py_typed": True,
        "public_exports": sorted(EXPECTED_EXPORTS),
        "runtime_available": False,
        "contract_gate": "SPIKE-CONFIG-001",
        "install_index": "disabled",
    }
    evidence_path = PACKAGE_ROOT / "evidence" / "DW-M1-AGENT-001" / "artifacts.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(evidence, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
