"""Install the built wheel into a clean consumer and verify public package proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = PACKAGE_ROOT / "evidence" / "DW-M1-AGENT-001" / "artifacts.json"
EXPECTED_EXPORTS = {
    "DEEP_WORK_SYSTEM_PROMPT",
    "HARD_VERIFICATION_ITERATION_CAP",
    "PROTECTED_ACTION",
    "RUNTIME_MODE",
    "VERIFIER_REF",
    "AgentConfig",
    "AgentInput",
    "AgentOutput",
    "AgentState",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalResponse",
    "ArtifactClaim",
    "ArtifactKind",
    "ClaimBasis",
    "CriterionResult",
    "EvidenceReference",
    "JourneyArtifact",
    "JourneyArtifactDraft",
    "JourneyCapabilities",
    "JourneyKind",
    "JourneyOutput",
    "JourneyProfile",
    "JourneyState",
    "JourneySubagent",
    "RubricCriterion",
    "RubricSpec",
    "RuntimeCapabilities",
    "VerificationRecord",
    "VerificationVerdict",
    "create_graph",
    "create_journey_graph",
    "initial_state",
    "journey_capabilities",
    "render_rubric",
    "research_profile",
    "runtime_capabilities",
    "validate_approval_response",
    "validate_artifact",
    "validate_plan_edit",
    "writing_profile",
}
EXPECTED_REQUIREMENTS = {
    "deepagents<0.7.0,>=0.6.12",
    "langchain-core<2.0.0,>=1.5.0",
    "langgraph<2.0.0,>=1.2.9",
    "typing-extensions<5.0.0,>=4.16.0",
}


def _sha256(path: Path) -> str:
    """Return a reproducible artifact digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    # Commands are fixed local Python/pip invocations assembled by this script.
    subprocess.run(command, check=True, cwd=PACKAGE_ROOT, env=environment)  # noqa: S603


def _artifacts(directory: Path) -> tuple[Path, Path]:
    """Return the sole wheel and source distribution in a build directory."""
    wheels = sorted(directory.glob("deepwork_agent-*.whl"))
    source_distributions = sorted(directory.glob("deepwork_agent-*.tar.gz"))
    if len(wheels) != 1:
        msg = f"expected exactly one wheel, found {len(wheels)}"
        raise RuntimeError(msg)
    if len(source_distributions) != 1:
        msg = f"expected exactly one source distribution, found {len(source_distributions)}"
        raise RuntimeError(msg)
    return wheels[0], source_distributions[0]


def _manifest(wheel: Path, source_distribution: Path) -> dict[str, Any]:
    """Describe immutable artifact and public-contract evidence."""
    return {
        "wheel": wheel.name,
        "wheel_sha256": _sha256(wheel),
        "source_distribution": source_distribution.name,
        "source_distribution_sha256": _sha256(source_distribution),
        "reproducible_builds": 2,
        "py_typed": True,
        "public_exports": sorted(EXPECTED_EXPORTS),
        "runtime_mode": "local-runtime",
        "runtime_available": True,
        "managed_external_providers": "unavailable",
        "model_injection_required": True,
        "runtime_dependencies": sorted(EXPECTED_REQUIREMENTS),
        "install_index": "disabled",
    }


def _verify_wheel_contents(wheel: Path) -> None:
    """Verify required package data is present in the wheel."""
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1:
            msg = f"built wheel must contain one METADATA file; found {len(metadata_names)}"
            raise RuntimeError(msg)
        metadata = archive.read(metadata_names[0]).decode()
    marker = "deepwork_agent/py.typed"
    if marker not in names:
        msg = f"built wheel does not contain {marker}"
        raise RuntimeError(msg)
    requirements = {
        line.removeprefix("Requires-Dist: ")
        for line in metadata.splitlines()
        if line.startswith("Requires-Dist: ")
    }
    if requirements != EXPECTED_REQUIREMENTS:
        msg = f"wheel requirements {sorted(requirements)} != {sorted(EXPECTED_REQUIREMENTS)}"
        raise RuntimeError(msg)


def _verify_clean_consumer(wheel: Path) -> None:
    """Install the wheel without an index and exercise its public API."""
    with tempfile.TemporaryDirectory(prefix="deepwork-agent-consumer-") as temporary:
        environment_root = Path(temporary) / "venv"
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        environment["PIP_NO_CACHE_DIR"] = "1"
        environment["UV_PROJECT_ENVIRONMENT"] = str(environment_root)
        uv = shutil.which("uv")
        if uv is None:
            msg = "uv is required for the offline clean-wheel consumer"
            raise RuntimeError(msg)
        _run(
            [
                uv,
                "sync",
                "--project",
                str(PACKAGE_ROOT),
                "--frozen",
                "--offline",
                "--no-dev",
                "--no-install-project",
            ],
            environment=environment,
        )
        python = environment_root / "bin" / "python"
        _run(
            [
                uv,
                "pip",
                "install",
                "--offline",
                "--no-deps",
                "--reinstall",
                "--python",
                str(python),
                str(wheel),
            ],
            environment=environment,
        )
        consumer = (
            "import json; import deepwork_agent as package; "
            "from importlib.resources import files; "
            "assert files('deepwork_agent').joinpath('py.typed').is_file(); "
            f"assert set(package.__all__) == {EXPECTED_EXPORTS!r}; "
            "capabilities = package.runtime_capabilities(); "
            "assert capabilities.available is True; "
            "assert capabilities.runtime_mode == 'local-runtime'; "
            "assert capabilities.managed_external_providers == 'unavailable'; "
            "assert capabilities.model_injection_required is True; "
            "assert capabilities.hosted_deployment is False; "
            "journeys = package.journey_capabilities(); "
            "assert journeys.journeys == ('research', 'writing'); "
            "assert journeys.coding_journey == 'unavailable'; "
            "assert journeys.async_subagents == 'unavailable'; "
            "assert journeys.hosted_artifact_storage is False; "
            "assert journeys.artifact_transfer == 'unavailable'; "
            "assert journeys.verification_ground_truth is False; "
            "assert journeys.provider_credentials_managed is False; "
            "print(json.dumps({'exports': sorted(package.__all__), "
            "'runtime': capabilities.runtime_mode, 'network': 'not-used'}))"
        )
        _run([str(python), "-I", "-c", consumer], environment=environment)


def _repeat_build() -> tuple[Path, Path, tempfile.TemporaryDirectory[str]]:
    """Build a second artifact pair in a temporary directory."""
    temporary = tempfile.TemporaryDirectory(prefix="deepwork-agent-repeat-build-")
    destination = Path(temporary.name)
    _run(
        [
            sys.executable,
            "-m",
            "hatchling",
            "build",
            "--target",
            "sdist",
            "--target",
            "wheel",
            "--directory",
            str(destination),
        ]
    )
    wheel, source_distribution = _artifacts(destination)
    return wheel, source_distribution, temporary


def _assert_reproducible(
    evidence: dict[str, Any],
    repeat_wheel: Path,
    repeat_source_distribution: Path,
) -> None:
    """Require a second fresh build to produce the recorded filenames and hashes."""
    repeated = _manifest(repeat_wheel, repeat_source_distribution)
    if repeated != evidence:
        msg = (
            "consecutive builds are not reproducible:\n"
            f"first={json.dumps(evidence, sort_keys=True)}\n"
            f"second={json.dumps(repeated, sort_keys=True)}"
        )
        raise RuntimeError(msg)


def _verify_expected(evidence: dict[str, Any]) -> None:
    """Compare fresh evidence with the reviewed immutable manifest."""
    expected = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    if expected != evidence:
        msg = (
            f"artifact evidence does not match {EVIDENCE_PATH.relative_to(PACKAGE_ROOT)}; "
            "review the source change and run `make update-evidence` explicitly"
        )
        raise RuntimeError(msg)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-evidence",
        action="store_true",
        help="replace the reviewed artifact manifest after successful two-build verification",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Verify fresh artifacts or explicitly refresh their reviewed manifest."""
    arguments = _parser().parse_args(argv)
    wheel, source_distribution = _artifacts(PACKAGE_ROOT / "dist")
    _verify_wheel_contents(wheel)
    _verify_clean_consumer(wheel)
    evidence = _manifest(wheel, source_distribution)
    repeat_wheel, repeat_source_distribution, temporary = _repeat_build()
    try:
        _assert_reproducible(evidence, repeat_wheel, repeat_source_distribution)
    finally:
        temporary.cleanup()

    if arguments.update_evidence:
        EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        action = "updated"
    else:
        _verify_expected(evidence)
        action = "verified"
    sys.stdout.write(json.dumps(evidence, indent=2) + "\n")
    sys.stdout.write(f"{action} immutable evidence: {EVIDENCE_PATH.relative_to(PACKAGE_ROOT)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
