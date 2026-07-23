#!/usr/bin/env python3
"""Deep Work worktree isolation harness.

Fixture self-tests prove the allocator and ownership controls only.  The
``exercise`` command deliberately refuses to claim product-demo acceptance until
both checked-out roots expose the separately owned product-demo driver contract.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

from isolation import (
    EvidenceError,
    IsolationError,
    OwnershipError,
    RESOURCE_FIELDS,
    ReservationStore,
    allocate_manifest,
    assert_distinct,
    canonical_root,
    differing_dimensions,
    public_manifest,
    validate_evidence,
    validate_namespace,
    write_evidence,
)


EXIT_INVALID = 2
EXIT_BLOCKED = 3
EXIT_VERIFY_FAILED = 4
PRODUCT_DEMO_DRIVER = Path("tools/product_demo/worktree_driver.py")
PRODUCT_DEMO_CONTRACT = Path("tools/product_demo/worktree-driver-contract.json")
PRODUCT_DEMO_CONTRACT_VERSION = 1
PRODUCT_DEMO_PROTOCOL = "deepwork-dual-product-demo-v1"
CONTRACT_KEYS = {
    "components",
    "contract_version",
    "credential_free",
    "driver_path",
    "driver_sha256",
    "loopback_only",
    "protocol",
    "reviewed_repository_commit",
}
REQUIRED_PRODUCT_DEMO_COMPONENTS = {
    "web",
    "api",
    "worker",
    "postgres",
    "object",
    "telemetry",
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
SYNTHETIC_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
RUN_NONCE_RE = re.compile(r"^[a-f0-9]{32,64}$")
PRODUCT_EVIDENCE_KEYS = {
    "acceptance",
    "allocation_digests",
    "concurrency",
    "contract_semantic_sha256",
    "cross_observations",
    "driver_revision",
    "driver_sha256",
    "evidence_class",
    "exercise_id",
    "manifests",
    "namespaces",
    "restarts",
    "run_nonce",
    "schema_version",
    "status",
    "teardown",
}
PUBLIC_MANIFEST_KEYS = {
    "browser",
    "database",
    "logs_id",
    "manifest_version",
    "namespace",
    "object_prefix",
    "ports",
    "process_identities",
    "proof_id",
    "restart_rule",
    "schema",
    "telemetry",
    "workspace_id",
}
PUBLIC_MANIFEST_SCHEMA = {
    "browser": {"origin": str, "storage_key": str},
    "database": str,
    "logs_id": str,
    "manifest_version": int,
    "namespace": str,
    "object_prefix": str,
    "ports": {"api": int, "telemetry": int, "web": int, "worker": int},
    "process_identities": {
        "api": {"identity": str, "namespace": str},
        "web": {"identity": str, "namespace": str},
        "worker": {"identity": str, "namespace": str},
    },
    "proof_id": str,
    "restart_rule": str,
    "schema": str,
    "telemetry": {
        "resource_attributes": {
            "deepwork.namespace": str,
            "deployment.mode": str,
            "service.namespace": str,
        }
    },
    "workspace_id": str,
}
BLOCKER_KEYS = {
    "acceptance",
    "command",
    "evidence_class",
    "namespaces",
    "processes_started",
    "reasons",
    "recovery",
    "recovery_context",
    "resources_reserved",
    "retryable",
    "schema_version",
    "spike",
    "status",
}
SELF_TEST_KEYS = {
    "acceptance",
    "checks",
    "command",
    "dimension_comparison",
    "evidence_class",
    "limitations",
    "manifests",
    "namespaces",
    "schema_version",
    "spike",
    "status",
}
RECEIPT_KEYS = {
    "contract_semantic_sha256",
    "driver_revision",
    "driver_sha256",
    "evidence_sha256",
    "exercise_id",
    "namespaces",
    "receipt_class",
    "receipt_hmac",
    "reservation_release",
    "run_nonce",
    "schema_version",
}
CLEANUP_EVIDENCE_KEYS = {
    "contract_semantic_sha256",
    "driver_revision",
    "driver_sha256",
    "evidence_class",
    "namespaces",
    "records",
    "run_nonce",
    "schema_version",
    "status",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Allocate and verify isolated Deep Work fixture namespaces."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="check harness prerequisites")
    doctor.add_argument("--root", required=True)

    self_test = subparsers.add_parser(
        "self-test", help="run synthetic allocator and ownership proof"
    )
    self_test.add_argument("--root", required=True)
    self_test.add_argument("--fixtures", required=True)
    self_test.add_argument("--evidence-dir", required=True)

    exercise = subparsers.add_parser(
        "exercise", help="run the separately owned dual product-demo matrix"
    )
    exercise.add_argument("--root", required=True)
    exercise.add_argument("--peer-root", required=True)
    exercise.add_argument("--namespace-a", required=True)
    exercise.add_argument("--namespace-b", required=True)
    exercise.add_argument("--evidence-dir", required=True)

    verify = subparsers.add_parser(
        "verify", help="verify retained product-demo exercise evidence"
    )
    verify.add_argument("--evidence-dir", required=True)
    verify.add_argument("--require-no-cross-observation", action="store_true")
    verify.add_argument("--require-clean-teardown", action="store_true")

    recover = subparsers.add_parser(
        "recover", help="retry reviewed cleanup for retained exact reservations"
    )
    recover.add_argument("--root", required=True)
    recover.add_argument("--peer-root", required=True)
    recover.add_argument("--namespace-a", required=True)
    recover.add_argument("--namespace-b", required=True)
    recover.add_argument("--evidence-dir", required=True)
    return parser


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _display_path(path: Path) -> str:
    """Render a log-safe path without exposing a local absolute prefix."""

    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.name


def _exact_keys(value: Any, expected: set[str], context: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{context} must be an object"]
    missing = sorted(expected.difference(value))
    unknown = sorted(set(value).difference(expected))
    failures = []
    if missing:
        failures.append(f"{context} missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{context} contains unknown fields: {', '.join(unknown)}")
    return failures


def _type_failure(value: Any, expected: type, context: str) -> list[str]:
    if expected is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
    else:
        valid = isinstance(value, expected)
    return [] if valid else [f"{context} has invalid type"]


def _shape_failures(value: Any, shape: dict[str, Any], context: str) -> list[str]:
    failures = _exact_keys(value, set(shape), context)
    if not isinstance(value, dict):
        return failures
    for field, expected in shape.items():
        nested = value.get(field)
        if isinstance(expected, dict):
            failures.extend(
                _shape_failures(nested, expected, f"{context}.{field}")
            )
        else:
            failures.extend(
                _type_failure(nested, expected, f"{context}.{field}")
            )
    return failures


def _blocker_schema_failures(evidence: Any) -> list[str]:
    failures = _exact_keys(evidence, BLOCKER_KEYS, "blocker evidence")
    if failures or not isinstance(evidence, dict):
        return failures
    failures.extend(
        _type_failure(
            evidence.get("schema_version"), int, "blocker schema_version"
        )
    )
    for field in (
        "acceptance",
        "command",
        "evidence_class",
        "recovery",
        "spike",
        "status",
    ):
        failures.extend(
            _type_failure(evidence.get(field), str, f"blocker {field}")
        )
    namespaces = evidence.get("namespaces")
    if not isinstance(namespaces, list) or not all(
        isinstance(namespace, str) for namespace in namespaces
    ):
        failures.append("blocker namespaces have invalid type")
    reasons = evidence.get("reasons")
    if not isinstance(reasons, list) or not all(
        isinstance(reason, str) for reason in reasons
    ):
        failures.append("blocker reasons have invalid type")
    processes_started = evidence.get("processes_started")
    if not (
        (
            isinstance(processes_started, int)
            and not isinstance(processes_started, bool)
        )
        or processes_started == "unknown"
    ):
        failures.append("blocker processes_started has invalid type")
    failures.extend(
        _type_failure(
            evidence.get("resources_reserved"),
            int,
            "blocker resources_reserved",
        )
    )
    failures.extend(
        _type_failure(evidence.get("retryable"), bool, "blocker retryable")
    )
    context = evidence.get("recovery_context")
    if context is not None:
        failures.extend(
            _shape_failures(
                context,
                {
                    "contract_semantic_sha256": str,
                    "driver_revision": str,
                    "driver_sha256": str,
                    "run_nonce": str,
                },
                "blocker recovery context",
            )
        )
    return failures


def _product_schema_failures(evidence: Any) -> list[str]:
    failures = _exact_keys(evidence, PRODUCT_EVIDENCE_KEYS, "product evidence")
    if failures or not isinstance(evidence, dict):
        return failures
    for field in (
        "acceptance",
        "contract_semantic_sha256",
        "driver_revision",
        "driver_sha256",
        "evidence_class",
        "exercise_id",
        "run_nonce",
        "status",
    ):
        failures.extend(_type_failure(evidence.get(field), str, field))
    failures.extend(_type_failure(evidence.get("schema_version"), int, "schema_version"))
    if not isinstance(evidence.get("namespaces"), list):
        failures.append("namespaces must be a list")
    if not isinstance(evidence.get("manifests"), list):
        failures.append("manifests must be a list")
    else:
        for index, manifest in enumerate(evidence["manifests"]):
            failures.extend(
                _shape_failures(
                    manifest, PUBLIC_MANIFEST_SCHEMA, f"manifest[{index}]"
                )
            )
            failures.extend(
                _exact_keys(manifest, PUBLIC_MANIFEST_KEYS, f"manifest[{index}]")
            )
            if isinstance(manifest, dict):
                failures.extend(
                    _type_failure(
                        manifest.get("manifest_version"),
                        int,
                        f"manifest[{index}].manifest_version",
                    )
                )
                for field in (
                    "database",
                    "logs_id",
                    "namespace",
                    "object_prefix",
                    "proof_id",
                    "restart_rule",
                    "schema",
                    "workspace_id",
                ):
                    failures.extend(
                        _type_failure(
                            manifest.get(field), str, f"manifest[{index}].{field}"
                        )
                    )
                failures.extend(
                    _exact_keys(
                        manifest.get("ports"),
                        {"api", "telemetry", "web", "worker"},
                        f"manifest[{index}].ports",
                    )
                )
                ports = manifest.get("ports")
                if isinstance(ports, dict):
                    for name, port in ports.items():
                        failures.extend(
                            _type_failure(
                                port, int, f"manifest[{index}].ports.{name}"
                            )
                        )
                failures.extend(
                    _exact_keys(
                        manifest.get("browser"),
                        {"origin", "storage_key"},
                        f"manifest[{index}].browser",
                    )
                )
                browser = manifest.get("browser")
                if isinstance(browser, dict):
                    for name, value in browser.items():
                        failures.extend(
                            _type_failure(
                                value, str, f"manifest[{index}].browser.{name}"
                            )
                        )
                failures.extend(
                    _exact_keys(
                        manifest.get("telemetry"),
                        {"resource_attributes"},
                        f"manifest[{index}].telemetry",
                    )
                )
                telemetry = manifest.get("telemetry")
                if isinstance(telemetry, dict):
                    failures.extend(
                        _exact_keys(
                            telemetry.get("resource_attributes"),
                            {
                                "deepwork.namespace",
                                "deployment.mode",
                                "service.namespace",
                            },
                            f"manifest[{index}].telemetry.resource_attributes",
                        )
                    )
                    attributes = telemetry.get("resource_attributes")
                    if isinstance(attributes, dict):
                        for name, value in attributes.items():
                            failures.extend(
                                _type_failure(
                                    value,
                                    str,
                                    f"manifest[{index}].telemetry.resource_attributes.{name}",
                                )
                            )
                failures.extend(
                    _exact_keys(
                        manifest.get("process_identities"),
                        {"api", "web", "worker"},
                        f"manifest[{index}].process_identities",
                    )
                )
                identities = manifest.get("process_identities")
                if isinstance(identities, dict):
                    for name, identity in identities.items():
                        failures.extend(
                            _exact_keys(
                                identity,
                                {"identity", "namespace"},
                                f"manifest[{index}].process_identities.{name}",
                            )
                        )
                        if isinstance(identity, dict):
                            for field, value in identity.items():
                                failures.extend(
                                    _type_failure(
                                        value,
                                        str,
                                        f"manifest[{index}].process_identities.{name}.{field}",
                                    )
                                )
    failures.extend(
        _exact_keys(
            evidence.get("concurrency"),
            {
                "a_ready_at",
                "a_started_at",
                "a_stopped_at",
                "b_ready_at",
                "b_started_at",
                "b_stopped_at",
            },
            "concurrency",
        )
    )
    concurrency = evidence.get("concurrency")
    if isinstance(concurrency, dict):
        for field, value in concurrency.items():
            failures.extend(_type_failure(value, str, f"concurrency.{field}"))
    record_schemas = (
        (
            "cross_observations",
            {
                "dimension",
                "probe_id",
                "result",
                "result_digest",
                "source_namespace",
                "target_namespace",
            },
        ),
        (
            "restarts",
            {
                "allocation_fingerprint_after",
                "allocation_fingerprint_before",
                "namespace",
                "process_identity_after",
                "process_identity_before",
                "restart_digest",
                "rule",
            },
        ),
        (
            "teardown",
            {
                "cleanup_digest",
                "namespace",
                "order",
                "peer_survived_after",
                "reservation_absent",
                "resources_absent",
            },
        ),
    )
    for field, keys in record_schemas:
        records = evidence.get(field)
        if not isinstance(records, list):
            failures.append(f"{field} must be a list")
            continue
        for index, record in enumerate(records):
            failures.extend(_exact_keys(record, keys, f"{field}[{index}]"))
            if not isinstance(record, dict):
                continue
            if field in {"cross_observations", "restarts"}:
                for name, value in record.items():
                    failures.extend(
                        _type_failure(value, str, f"{field}[{index}].{name}")
                    )
            else:
                failures.extend(
                    _type_failure(
                        record.get("namespace"), str, f"teardown[{index}].namespace"
                    )
                )
                failures.extend(
                    _type_failure(
                        record.get("order"), int, f"teardown[{index}].order"
                    )
                )
                for name in ("peer_survived_after", "reservation_absent"):
                    failures.extend(
                        _type_failure(
                            record.get(name), bool, f"teardown[{index}].{name}"
                        )
                    )
                failures.extend(
                    _type_failure(
                        record.get("cleanup_digest"),
                        str,
                        f"teardown[{index}].cleanup_digest",
                    )
                )
                resources = record.get("resources_absent")
                if not isinstance(resources, list) or not all(
                    isinstance(item, str) for item in resources
                ):
                    failures.append(
                        f"teardown[{index}].resources_absent has invalid type"
                    )
    if not isinstance(evidence.get("allocation_digests"), dict):
        failures.append("allocation_digests must be an object")
    elif not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in evidence["allocation_digests"].items()
    ):
        failures.append("allocation_digests keys and values must be strings")
    if isinstance(evidence.get("namespaces"), list) and not all(
        isinstance(namespace, str) for namespace in evidence["namespaces"]
    ):
        failures.append("namespaces entries must be strings")
    return failures


def _ensure_schema(value: Any, keys: set[str], context: str) -> None:
    failures = _exact_keys(value, keys, context)
    if failures:
        raise EvidenceError("; ".join(failures))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reviewed_commit_is_ancestor(root: Path, reviewed_commit: str) -> bool:
    if not COMMIT_RE.fullmatch(reviewed_commit):
        return False
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", reviewed_commit, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _git_blob(root: Path, commit: str, relative: Path) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative.as_posix()}"],
            cwd=root,
            check=False,
            capture_output=True,
            timeout=10,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or len(result.stdout) > 1024 * 1024:
        return None
    return result.stdout


def _contract_semantics(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in contract.items()
        if key != "reviewed_repository_commit"
    }


def _semantic_digest(value: Any) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _receipt_hmac(
    *,
    receipt_key_hex: str,
    evidence: dict[str, Any],
    receipt: dict[str, Any],
) -> str:
    payload = {
        "authority": "tools/worktree/harness.py",
        "evidence": evidence,
        "receipt": receipt,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    try:
        key = bytes.fromhex(receipt_key_hex)
    except ValueError as error:
        raise EvidenceError("private receipt authority key is invalid") from error
    if len(key) != 32:
        raise EvidenceError("private receipt authority key is invalid")
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


def _driver_status(root: Path) -> dict[str, Any]:
    agents_marker = root / "AGENTS.md"
    git_marker = root / ".git"
    if (
        not agents_marker.is_file()
        or agents_marker.is_symlink()
        or not git_marker.exists()
        or git_marker.is_symlink()
    ):
        return {
            "available": False,
            "reason": "repository identity markers are absent",
        }
    contract_path = root / PRODUCT_DEMO_CONTRACT
    driver = root / PRODUCT_DEMO_DRIVER
    if (
        not contract_path.is_file()
        or contract_path.is_symlink()
        or not driver.is_file()
        or driver.is_symlink()
    ):
        return {
            "available": False,
            "reason": (
                "missing static reviewed product-demo contract or driver: "
                f"{PRODUCT_DEMO_CONTRACT}"
            ),
        }
    try:
        if contract_path.stat().st_size > 32 * 1024:
            return {"available": False, "reason": "static driver contract is oversized"}
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "reason": "static driver contract is invalid"}
    if not isinstance(contract, dict):
        return {"available": False, "reason": "static driver contract is not an object"}
    if set(contract) != CONTRACT_KEYS:
        return {"available": False, "reason": "static driver contract schema is not exact"}
    raw_components = contract.get("components")
    if not isinstance(raw_components, list) or not all(
        isinstance(component, str) for component in raw_components
    ):
        return {"available": False, "reason": "driver contract components are invalid"}
    components = set(raw_components)
    if contract.get("contract_version") != PRODUCT_DEMO_CONTRACT_VERSION:
        return {"available": False, "reason": "unsupported driver contract version"}
    if contract.get("protocol") != PRODUCT_DEMO_PROTOCOL:
        return {"available": False, "reason": "unsupported driver protocol"}
    if contract.get("driver_path") != PRODUCT_DEMO_DRIVER.as_posix():
        return {"available": False, "reason": "driver contract path is not canonical"}
    missing = sorted(REQUIRED_PRODUCT_DEMO_COMPONENTS.difference(components))
    if missing:
        return {
            "available": False,
            "reason": "driver contract missing components: " + ", ".join(missing),
        }
    if contract.get("credential_free") is not True:
        return {"available": False, "reason": "driver is not credential-free"}
    if contract.get("loopback_only") is not True:
        return {"available": False, "reason": "driver is not loopback-only"}
    driver_sha256 = contract.get("driver_sha256")
    if not isinstance(driver_sha256, str) or not SHA256_RE.fullmatch(driver_sha256):
        return {"available": False, "reason": "driver SHA-256 pin is invalid"}
    if not secrets.compare_digest(_sha256_file(driver), driver_sha256):
        return {"available": False, "reason": "driver content does not match static SHA-256 pin"}
    reviewed_commit = contract.get("reviewed_repository_commit")
    if not isinstance(reviewed_commit, str) or not _reviewed_commit_is_ancestor(
        root, reviewed_commit
    ):
        return {
            "available": False,
            "reason": "reviewed repository commit is invalid or not an ancestor",
        }
    reviewed_driver = _git_blob(root, reviewed_commit, PRODUCT_DEMO_DRIVER)
    reviewed_contract_raw = _git_blob(root, reviewed_commit, PRODUCT_DEMO_CONTRACT)
    if reviewed_driver is None or reviewed_contract_raw is None:
        return {
            "available": False,
            "reason": "reviewed commit lacks immutable driver or contract blobs",
        }
    if not secrets.compare_digest(
        hashlib.sha256(reviewed_driver).hexdigest(), driver_sha256
    ) or reviewed_driver != driver.read_bytes():
        return {
            "available": False,
            "reason": "current driver does not match immutable reviewed Git blob",
        }
    try:
        reviewed_contract = json.loads(reviewed_contract_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"available": False, "reason": "reviewed contract Git blob is invalid"}
    if (
        not isinstance(reviewed_contract, dict)
        or set(reviewed_contract) != CONTRACT_KEYS
        or _contract_semantics(reviewed_contract) != _contract_semantics(contract)
    ):
        return {
            "available": False,
            "reason": "current contract semantics do not match reviewed Git blob",
        }
    contract_semantic_sha256 = _semantic_digest(_contract_semantics(contract))
    return {
        "available": True,
        "reason": "static-contract-ready",
        "driver_sha256": driver_sha256,
        "reviewed_repository_commit": reviewed_commit,
        "contract_semantic_sha256": contract_semantic_sha256,
        "protocol": PRODUCT_DEMO_PROTOCOL,
    }


def doctor(args: argparse.Namespace) -> int:
    root = canonical_root(args.root)
    fixture_path = root / "internal/fixtures/worktree/scenarios.json"
    status = {
        "command": "doctor",
        "harness": "ready" if fixture_path.is_file() else "blocked",
        "python": {
            "implementation": platform.python_implementation(),
            "supported": sys.version_info >= (3, 11),
        },
        "root": {
            "canonical": root == Path(args.root).expanduser().resolve(),
            "repository_markers": all(
                (root / marker).exists() for marker in ("AGENTS.md", ".git")
            ),
        },
        "fixtures": {"available": fixture_path.is_file()},
        "product_demo": _driver_status(root),
        "spike_worktree_001": "implemented-not-accepted",
    }
    ok = (
        status["python"]["supported"]
        and status["root"]["repository_markers"]
        and status["fixtures"]["available"]
    )
    _emit(status)
    return 0 if ok else EXIT_INVALID


def _load_scenarios(fixtures: Path) -> dict[str, Any]:
    path = fixtures / "scenarios.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise IsolationError(f"cannot load fixture scenarios: {path}") from error
    if not isinstance(value, dict):
        raise IsolationError("fixture scenarios must be a JSON object")
    return value


def self_test(args: argparse.Namespace) -> int:
    root = canonical_root(args.root)
    fixtures = Path(args.fixtures).expanduser().resolve(strict=True)
    evidence_dir = Path(args.evidence_dir).expanduser().resolve(strict=False)
    scenario = _load_scenarios(fixtures)
    namespace_a = validate_namespace(scenario["namespace_a"])
    namespace_b = validate_namespace(scenario["namespace_b"])
    if namespace_a == namespace_b:
        raise IsolationError("fixture namespaces must differ")
    if set(scenario.get("required_dimensions", ())) != set(RESOURCE_FIELDS):
        raise IsolationError("fixture required dimensions do not match the manifest")
    invalid_namespaces_rejected = True
    for unsafe in scenario.get("invalid_namespaces", ()):
        try:
            validate_namespace(unsafe)
        except IsolationError:
            continue
        invalid_namespaces_rejected = False
        break

    with tempfile.TemporaryDirectory(prefix="dw-worktree-self-test-") as temporary:
        sandbox = Path(temporary).resolve()
        root_a = sandbox / "checkout-a"
        root_b = sandbox / "checkout-b"
        root_a.mkdir()
        root_b.mkdir()
        store = ReservationStore(sandbox / "reservations")
        manifest_a = allocate_manifest(
            root=root_a,
            namespace=namespace_a,
            evidence_dir=sandbox / "proof",
        )
        manifest_b = allocate_manifest(
            root=root_b,
            namespace=namespace_b,
            evidence_dir=sandbox / "proof",
        )
        assert_distinct(manifest_a, manifest_b)
        store.reserve(manifest_a)
        store.reserve(manifest_b)

        duplicate_rejected = False
        try:
            store.reserve(manifest_a)
        except IsolationError:
            duplicate_rejected = True

        peer_restart_rejected = False
        try:
            store.restart(
                namespace=namespace_b,
                teardown_token=manifest_a["teardown_token"],
                root=root_b,
            )
        except OwnershipError:
            peer_restart_rejected = True

        restarted = store.restart(
            namespace=namespace_a,
            teardown_token=manifest_a["teardown_token"],
            root=root_a,
        )
        restart_reused = public_manifest(restarted) == public_manifest(manifest_a)

        first_teardown = store.teardown(
            namespace=namespace_a,
            teardown_token=manifest_a["teardown_token"],
            root=root_a,
        )
        peer_survived = namespace_b in store.active_namespaces()
        second_teardown = store.teardown(
            namespace=namespace_a,
            teardown_token=manifest_a["teardown_token"],
            root=root_a,
        )
        final_teardown = store.teardown(
            namespace=namespace_b,
            teardown_token=manifest_b["teardown_token"],
            root=root_b,
        )
        cleanup_verified = store.active_namespaces() == ()

    checks = {
        "all_dimensions_distinct": all(
            differing_dimensions(manifest_a, manifest_b).values()
        ),
        "invalid_namespaces_rejected": invalid_namespaces_rejected,
        "atomic_duplicate_rejected": duplicate_rejected,
        "peer_restart_rejected": peer_restart_rejected,
        "restart_reused_recorded_resources": restart_reused,
        "scoped_teardown_preserved_peer": peer_survived,
        "teardown_idempotent": (
            first_teardown.state == "released"
            and second_teardown.state == "already-absent"
        ),
        "cleanup_verified": (
            final_teardown.state == "released" and cleanup_verified
        ),
    }
    if not all(checks.values()):
        raise IsolationError("synthetic self-test failed")
    evidence = {
        "schema_version": 1,
        "evidence_class": "synthetic-fixture",
        "command": "self-test",
        "status": "passed",
        "acceptance": "implemented-not-accepted",
        "spike": "SPIKE-WORKTREE-001",
        "namespaces": [namespace_a, namespace_b],
        "manifests": [public_manifest(manifest_a), public_manifest(manifest_b)],
        "dimension_comparison": differing_dimensions(manifest_a, manifest_b),
        "checks": checks,
        "limitations": [
            "synthetic fixtures do not prove product-demo isolation",
            "dual product-demo acceptance requires the separately owned driver",
        ],
    }
    _ensure_schema(evidence, SELF_TEST_KEYS, "self-test evidence")
    _ensure_schema(
        evidence["checks"],
        {
            "all_dimensions_distinct",
            "atomic_duplicate_rejected",
            "cleanup_verified",
            "invalid_namespaces_rejected",
            "peer_restart_rejected",
            "restart_reused_recorded_resources",
            "scoped_teardown_preserved_peer",
            "teardown_idempotent",
        },
        "self-test checks",
    )
    _ensure_schema(
        evidence["dimension_comparison"],
        set(RESOURCE_FIELDS),
        "self-test dimension comparison",
    )
    for field in ("acceptance", "command", "evidence_class", "spike", "status"):
        if not isinstance(evidence[field], str):
            raise EvidenceError(f"self-test {field} has invalid type")
    if not isinstance(evidence["schema_version"], int) or isinstance(
        evidence["schema_version"], bool
    ):
        raise EvidenceError("self-test schema_version has invalid type")
    if not all(isinstance(value, bool) for value in evidence["checks"].values()):
        raise EvidenceError("self-test checks must be booleans")
    if not all(
        isinstance(value, bool)
        for value in evidence["dimension_comparison"].values()
    ):
        raise EvidenceError("self-test dimensions must be booleans")
    if not all(isinstance(value, str) for value in evidence["namespaces"]):
        raise EvidenceError("self-test namespaces must be strings")
    if not all(isinstance(value, str) for value in evidence["limitations"]):
        raise EvidenceError("self-test limitations must be strings")
    for index, manifest in enumerate(evidence["manifests"]):
        failures = _shape_failures(
            manifest,
            PUBLIC_MANIFEST_SCHEMA,
            f"self-test manifest[{index}]",
        )
        if failures:
            raise EvidenceError("; ".join(failures))
    write_evidence(evidence_dir / "self-test.json", evidence)
    _emit(
        {
            "command": "self-test",
            "status": "passed",
            "acceptance": "implemented-not-accepted",
            "evidence": _display_path(evidence_dir / "self-test.json"),
            "checks": checks,
        }
    )
    return 0


def _blocker_evidence(
    *,
    evidence_dir: Path,
    namespace_a: str,
    namespace_b: str,
    reasons: list[str],
    processes_started: int | str = 0,
    resources_reserved: int = 0,
    recovery: str = "not-required",
    retryable: bool = True,
    recovery_context: dict[str, str] | None = None,
) -> None:
    evidence = {
        "schema_version": 1,
        "evidence_class": "product-demo-blocker",
        "command": "exercise",
        "status": "blocked",
        "acceptance": "implemented-not-accepted",
        "spike": "SPIKE-WORKTREE-001",
        "namespaces": [namespace_a, namespace_b],
        "reasons": reasons,
        "processes_started": processes_started,
        "resources_reserved": resources_reserved,
        "recovery": recovery,
        "recovery_context": recovery_context,
        "retryable": retryable,
    }
    failures = _blocker_schema_failures(evidence)
    if failures:
        raise EvidenceError("; ".join(failures))
    write_evidence(evidence_dir / "exercise.json", evidence)


def _cleanup_evidence_failures(
    evidence: Any,
    *,
    namespaces: list[str],
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
    contract_semantic_sha256: str,
) -> list[str]:
    failures = _exact_keys(
        evidence, CLEANUP_EVIDENCE_KEYS, "recovery cleanup evidence"
    )
    if failures or not isinstance(evidence, dict):
        return failures
    for field in (
        "contract_semantic_sha256",
        "driver_revision",
        "driver_sha256",
        "evidence_class",
        "run_nonce",
        "status",
    ):
        failures.extend(
            _type_failure(evidence.get(field), str, f"cleanup evidence {field}")
        )
    failures.extend(
        _type_failure(
            evidence.get("schema_version"),
            int,
            "cleanup evidence schema_version",
        )
    )
    if not isinstance(evidence.get("namespaces"), list) or not all(
        isinstance(namespace, str) for namespace in evidence.get("namespaces", ())
    ):
        failures.append("cleanup evidence namespaces have invalid type")
    expected_identity = {
        "evidence_class": "product-demo-cleanup",
        "status": "clean",
        "run_nonce": run_nonce,
        "driver_revision": driver_revision,
        "driver_sha256": driver_sha256,
        "contract_semantic_sha256": contract_semantic_sha256,
        "namespaces": namespaces,
        "schema_version": 1,
    }
    for field, expected in expected_identity.items():
        if evidence.get(field) != expected:
            failures.append(f"cleanup evidence identity mismatch: {field}")
    records = evidence.get("records")
    if not isinstance(records, list) or len(records) != 2:
        failures.append("cleanup evidence requires exactly two records")
        return failures
    if {
        record.get("namespace") for record in records if isinstance(record, dict)
    } != set(namespaces):
        failures.append("cleanup records do not match namespaces")
    for index, record in enumerate(records):
        failures.extend(
            _exact_keys(
                record,
                {
                    "cleanup_digest",
                    "namespace",
                    "process_identity_verified",
                    "resources_absent",
                },
                f"cleanup record[{index}]",
            )
        )
        if not isinstance(record, dict):
            continue
        failures.extend(
            _type_failure(
                record.get("namespace"), str, f"cleanup record[{index}].namespace"
            )
        )
        failures.extend(
            _type_failure(
                record.get("process_identity_verified"),
                bool,
                f"cleanup record[{index}].process_identity_verified",
            )
        )
        failures.extend(
            _type_failure(
                record.get("cleanup_digest"),
                str,
                f"cleanup record[{index}].cleanup_digest",
            )
        )
        if not isinstance(record.get("resources_absent"), list) or not all(
            isinstance(resource, str)
            for resource in record.get("resources_absent", ())
        ):
            failures.append(
                f"cleanup record[{index}].resources_absent has invalid type"
            )
        if record.get("process_identity_verified") is not True:
            failures.append("cleanup did not verify exact process identity")
        if set(record.get("resources_absent", ())) != TEARDOWN_RESOURCES:
            failures.append("cleanup resource absence matrix is incomplete")
        payload = {
            key: value
            for key, value in record.items()
            if key != "cleanup_digest"
        }
        expected_digest = _bound_digest(
            kind="recovery-cleanup",
            payload=payload,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
        if not isinstance(record.get("cleanup_digest"), str) or not secrets.compare_digest(
            record["cleanup_digest"], expected_digest
        ):
            failures.append("cleanup digest does not bind cleanup record")
    return failures


def _attempt_reviewed_cleanup(
    *,
    root: Path,
    peer_root: Path,
    namespace_a: str,
    namespace_b: str,
    evidence_dir: Path,
    store: ReservationStore,
    manifest_path_a: Path,
    manifest_path_b: Path,
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
    contract_semantic_sha256: str,
) -> bool:
    command = [
        sys.executable,
        str(root / PRODUCT_DEMO_DRIVER),
        "cleanup",
        "--root",
        str(root),
        "--peer-root",
        str(peer_root),
        "--manifest-a",
        str(manifest_path_a),
        "--manifest-b",
        str(manifest_path_b),
        "--evidence-dir",
        str(evidence_dir),
        "--run-nonce",
        run_nonce,
        "--driver-revision",
        driver_revision,
        "--driver-sha256",
        driver_sha256,
        "--contract-semantic-sha256",
        contract_semantic_sha256,
        "--recovery-reason",
        "driver-failure",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONIOENCODING": "utf-8",
                "LC_ALL": "C",
            },
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    cleanup_path = evidence_dir / "recovery-cleanup.json"
    try:
        if (
            cleanup_path.is_symlink()
            or not cleanup_path.is_file()
            or cleanup_path.stat().st_size > 512 * 1024
        ):
            return False
        cleanup = json.loads(cleanup_path.read_text(encoding="utf-8"))
        validate_evidence(cleanup)
    except (OSError, json.JSONDecodeError, EvidenceError):
        return False
    failures = _cleanup_evidence_failures(
        cleanup,
        namespaces=[namespace_a, namespace_b],
        run_nonce=run_nonce,
        driver_revision=driver_revision,
        driver_sha256=driver_sha256,
        contract_semantic_sha256=contract_semantic_sha256,
    )
    if failures:
        return False
    try:
        store.release_pair(
            release_id=run_nonce,
            namespace_a=namespace_a,
            teardown_token_a=manifest_a["teardown_token"],
            root_a=root,
            namespace_b=namespace_b,
            teardown_token_b=manifest_b["teardown_token"],
            root_b=peer_root,
        )
    except (OSError, IsolationError):
        return False
    return True


def _finish_failed_exercise(
    *,
    reason: str,
    root: Path,
    peer_root: Path,
    namespace_a: str,
    namespace_b: str,
    evidence_dir: Path,
    store: ReservationStore,
    manifest_path_a: Path,
    manifest_path_b: Path,
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
    contract_semantic_sha256: str,
) -> int:
    cleaned = _attempt_reviewed_cleanup(
        root=root,
        peer_root=peer_root,
        namespace_a=namespace_a,
        namespace_b=namespace_b,
        evidence_dir=evidence_dir,
        store=store,
        manifest_path_a=manifest_path_a,
        manifest_path_b=manifest_path_b,
        manifest_a=manifest_a,
        manifest_b=manifest_b,
        run_nonce=run_nonce,
        driver_revision=driver_revision,
        driver_sha256=driver_sha256,
        contract_semantic_sha256=contract_semantic_sha256,
    )
    if cleaned:
        resources_reserved = 0
    else:
        try:
            active = set(store.active_namespaces())
            resources_reserved = sum(
                namespace in active for namespace in (namespace_a, namespace_b)
            )
        except IsolationError:
            resources_reserved = 2
    _blocker_evidence(
        evidence_dir=evidence_dir,
        namespace_a=namespace_a,
        namespace_b=namespace_b,
        reasons=[reason],
        processes_started="unknown",
        resources_reserved=resources_reserved,
        recovery="cleanup-proven" if cleaned else "reservation-retained",
        retryable=True,
        recovery_context={
            "run_nonce": run_nonce,
            "driver_revision": driver_revision,
            "driver_sha256": driver_sha256,
            "contract_semantic_sha256": contract_semantic_sha256,
        },
    )
    _emit(
        {
            "command": "exercise",
            "status": "blocked",
            "acceptance": "implemented-not-accepted",
            "recovery": "cleanup-proven" if cleaned else "reservation-retained",
            "retryable": True,
            "reasons": [reason],
        }
    )
    return EXIT_BLOCKED


def exercise(args: argparse.Namespace) -> int:
    root = canonical_root(args.root)
    try:
        peer_root = canonical_root(args.peer_root)
    except (FileNotFoundError, IsolationError) as error:
        namespace_a = validate_namespace(args.namespace_a)
        namespace_b = validate_namespace(args.namespace_b)
        evidence_dir = Path(args.evidence_dir).expanduser().resolve(strict=False)
        reason = f"peer checkout unavailable: {type(error).__name__}"
        _blocker_evidence(
            evidence_dir=evidence_dir,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            reasons=[reason],
        )
        _emit(
            {
                "command": "exercise",
                "status": "blocked",
                "acceptance": "implemented-not-accepted",
                "reasons": [reason],
            }
        )
        return EXIT_BLOCKED

    namespace_a = validate_namespace(args.namespace_a)
    namespace_b = validate_namespace(args.namespace_b)
    if namespace_a == namespace_b:
        raise IsolationError("exercise namespaces must differ")
    evidence_dir = Path(args.evidence_dir).expanduser().resolve(strict=False)
    if root == peer_root:
        reason = "peer checkout aliases the primary checkout"
        _blocker_evidence(
            evidence_dir=evidence_dir,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            reasons=[reason],
        )
        _emit(
            {
                "command": "exercise",
                "status": "blocked",
                "acceptance": "implemented-not-accepted",
                "reasons": [reason],
            }
        )
        return EXIT_BLOCKED
    statuses = {"root": _driver_status(root), "peer": _driver_status(peer_root)}
    reasons = [
        f"{name}: {status['reason']}"
        for name, status in statuses.items()
        if not status["available"]
    ]
    if reasons:
        _blocker_evidence(
            evidence_dir=evidence_dir,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            reasons=reasons,
        )
        _emit(
            {
                "command": "exercise",
                "status": "blocked",
                "acceptance": "implemented-not-accepted",
                "reasons": reasons,
            }
        )
        return EXIT_BLOCKED

    root_status = statuses["root"]
    peer_status = statuses["peer"]
    if (
        root_status["driver_sha256"] != peer_status["driver_sha256"]
        or root_status["reviewed_repository_commit"]
        != peer_status["reviewed_repository_commit"]
    ):
        reason = "primary and peer static driver pins do not match"
        _blocker_evidence(
            evidence_dir=evidence_dir,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            reasons=[reason],
        )
        _emit(
            {
                "command": "exercise",
                "status": "blocked",
                "acceptance": "implemented-not-accepted",
                "reasons": [reason],
            }
        )
        return EXIT_BLOCKED

    run_nonce = secrets.token_hex(16)
    driver_revision = root_status["reviewed_repository_commit"]
    driver_sha256 = root_status["driver_sha256"]
    contract_semantic_sha256 = root_status["contract_semantic_sha256"]
    manifest_a = allocate_manifest(
        root=root,
        namespace=namespace_a,
        evidence_dir=evidence_dir,
    )
    manifest_b = allocate_manifest(
        root=peer_root,
        namespace=namespace_b,
        evidence_dir=evidence_dir,
    )
    assert_distinct(manifest_a, manifest_b)
    store = ReservationStore()
    receipt_record = store.create_receipt_record(
        run_nonce=run_nonce,
        driver_revision=driver_revision,
        driver_sha256=driver_sha256,
        contract_semantic_sha256=contract_semantic_sha256,
        namespaces=[namespace_a, namespace_b],
    )
    reserved_a = False
    reserved_b = False
    try:
        store.reserve(manifest_a)
        reserved_a = True
        store.reserve(manifest_b)
        reserved_b = True
    except IsolationError as error:
        if reserved_a and not reserved_b:
            store.teardown(
                namespace=namespace_a,
                teardown_token=manifest_a["teardown_token"],
                root=root,
            )
        reason = f"atomic allocation preflight failed: {type(error).__name__}"
        _blocker_evidence(
            evidence_dir=evidence_dir,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            reasons=[reason],
        )
        _emit(
            {
                "command": "exercise",
                "status": "blocked",
                "acceptance": "implemented-not-accepted",
                "reasons": [reason],
            }
        )
        return EXIT_BLOCKED

    manifest_path_a = store.owned_manifest_path(
        namespace=namespace_a,
        teardown_token=manifest_a["teardown_token"],
        root=root,
    )
    manifest_path_b = store.owned_manifest_path(
        namespace=namespace_b,
        teardown_token=manifest_b["teardown_token"],
        root=peer_root,
    )
    command = [
        sys.executable,
        str(root / PRODUCT_DEMO_DRIVER),
        "dual-exercise",
        "--root",
        str(root),
        "--peer-root",
        str(peer_root),
        "--manifest-a",
        str(manifest_path_a),
        "--manifest-b",
        str(manifest_path_b),
        "--evidence-dir",
        str(evidence_dir),
        "--run-nonce",
        run_nonce,
        "--driver-revision",
        driver_revision,
        "--driver-sha256",
        driver_sha256,
        "--contract-semantic-sha256",
        contract_semantic_sha256,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=600,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONIOENCODING": "utf-8",
                "LC_ALL": "C",
            },
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        reason = f"reviewed product-demo driver failed: {type(error).__name__}"
        return _finish_failed_exercise(
            reason=reason,
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            contract_semantic_sha256=contract_semantic_sha256,
        )
    if result.returncode != 0:
        reason = f"reviewed product-demo driver exited {result.returncode}"
        return _finish_failed_exercise(
            reason=reason,
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            contract_semantic_sha256=contract_semantic_sha256,
        )

    evidence_path = evidence_dir / "exercise.json"
    try:
        if (
            evidence_path.is_symlink()
            or not evidence_path.is_file()
            or evidence_path.stat().st_size > 3 * 1024 * 1024
        ):
            raise EvidenceError("driver evidence is absent, symlinked, or oversized")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if not isinstance(evidence, dict):
            raise EvidenceError("driver evidence is not an object")
        validate_evidence(evidence)
    except (OSError, json.JSONDecodeError, EvidenceError) as error:
        reason = f"reviewed driver evidence failed validation: {type(error).__name__}"
        return _finish_failed_exercise(
            reason=reason,
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            contract_semantic_sha256=contract_semantic_sha256,
        )
    identity_matches = (
        evidence.get("run_nonce") == run_nonce
        and evidence.get("driver_revision") == driver_revision
        and evidence.get("driver_sha256") == driver_sha256
        and evidence.get("contract_semantic_sha256")
        == contract_semantic_sha256
        and evidence.get("namespaces") == [namespace_a, namespace_b]
        and evidence.get("manifests")
        == [public_manifest(manifest_a), public_manifest(manifest_b)]
    )
    failures = _product_demo_failures(
        evidence,
        require_no_cross_observation=True,
        require_clean_teardown=False,
    )
    failures.extend(
        _teardown_failures(
            evidence.get("teardown"),
            [namespace_a, namespace_b],
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            require_reservation_absent=False,
        )
    )
    if not identity_matches:
        failures.append("driver evidence does not match the invoked reviewed run")
    if failures:
        reason = "reviewed driver evidence is incomplete or inconsistent"
        return _finish_failed_exercise(
            reason=reason,
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            contract_semantic_sha256=contract_semantic_sha256,
        )

    try:
        store.release_pair(
            release_id=run_nonce,
            namespace_a=namespace_a,
            teardown_token_a=manifest_a["teardown_token"],
            root_a=root,
            namespace_b=namespace_b,
            teardown_token_b=manifest_b["teardown_token"],
            root_b=peer_root,
        )
    except (OSError, IsolationError) as error:
        return _finish_failed_exercise(
            reason=f"reservation release failed: {type(error).__name__}",
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
            contract_semantic_sha256=contract_semantic_sha256,
        )
    for record in evidence["teardown"]:
        record["reservation_absent"] = True
        payload = {
            key: nested
            for key, nested in record.items()
            if key != "cleanup_digest"
        }
        record["cleanup_digest"] = _bound_digest(
            kind="cleanup",
            payload=payload,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
    final_failures = _product_demo_failures(
        evidence,
        require_no_cross_observation=True,
        require_clean_teardown=True,
    )
    if final_failures:
        raise EvidenceError("final product-demo evidence failed after reservation release")
    write_evidence(evidence_path, evidence)
    receipt = _build_receipt(
        evidence=evidence,
        evidence_path=evidence_path,
        receipt_record=receipt_record,
        reservation_release=[
            {"namespace": namespace_a, "state": "released"},
            {"namespace": namespace_b, "state": "released"},
        ],
    )
    write_evidence(evidence_dir / "receipt.json", receipt)
    _emit(
        {
            "command": "exercise",
            "status": "passed",
            "acceptance": "accepted",
            "evidence": _display_path(evidence_path),
        }
    )
    return 0


def recover(args: argparse.Namespace) -> int:
    root = canonical_root(args.root)
    peer_root = canonical_root(args.peer_root)
    namespace_a = validate_namespace(args.namespace_a)
    namespace_b = validate_namespace(args.namespace_b)
    if root == peer_root or namespace_a == namespace_b:
        raise IsolationError("recovery requires distinct roots and namespaces")
    evidence_dir = Path(args.evidence_dir).expanduser().resolve(strict=True)
    blocker_path = evidence_dir / "exercise.json"
    try:
        blocker = json.loads(blocker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError("recovery requires retained blocker evidence") from error
    failures = _blocker_schema_failures(blocker)
    if failures or not isinstance(blocker, dict):
        raise EvidenceError("; ".join(failures))
    expected_identity = {
        "acceptance": "implemented-not-accepted",
        "command": "exercise",
        "evidence_class": "product-demo-blocker",
        "namespaces": [namespace_a, namespace_b],
        "recovery": "reservation-retained",
        "retryable": True,
        "schema_version": 1,
        "spike": "SPIKE-WORKTREE-001",
        "status": "blocked",
    }
    if any(blocker.get(field) != value for field, value in expected_identity.items()):
        raise EvidenceError("recovery requires an exact retained-reservation blocker")
    if blocker.get("resources_reserved") not in {1, 2}:
        raise EvidenceError("recovery requires retained reservation state")
    context = blocker.get("recovery_context")
    _ensure_schema(
        context,
        {
            "contract_semantic_sha256",
            "driver_revision",
            "driver_sha256",
            "run_nonce",
        },
        "blocker recovery context",
    )
    statuses = [_driver_status(root), _driver_status(peer_root)]
    if not all(status.get("available") for status in statuses):
        raise IsolationError("reviewed cleanup driver provenance is unavailable")
    primary = statuses[0]
    for field in (
        "contract_semantic_sha256",
        "driver_sha256",
        "reviewed_repository_commit",
    ):
        context_field = (
            "driver_revision"
            if field == "reviewed_repository_commit"
            else field
        )
        if primary[field] != context[context_field] or statuses[1][field] != primary[field]:
            raise IsolationError("recovery context does not match immutable driver provenance")
    store = ReservationStore()
    if store.release_pair_pending(release_id=context["run_nonce"]):
        try:
            store.commit_pair_release(release_id=context["run_nonce"])
            cleaned = True
        except (OSError, IsolationError):
            cleaned = False
    else:
        manifest_path_a, manifest_a = store.recovery_manifest(
            namespace=namespace_a, root=root
        )
        manifest_path_b, manifest_b = store.recovery_manifest(
            namespace=namespace_b, root=peer_root
        )
        cleaned = _attempt_reviewed_cleanup(
            root=root,
            peer_root=peer_root,
            namespace_a=namespace_a,
            namespace_b=namespace_b,
            evidence_dir=evidence_dir,
            store=store,
            manifest_path_a=manifest_path_a,
            manifest_path_b=manifest_path_b,
            manifest_a=manifest_a,
            manifest_b=manifest_b,
            run_nonce=context["run_nonce"],
            driver_revision=context["driver_revision"],
            driver_sha256=context["driver_sha256"],
            contract_semantic_sha256=context["contract_semantic_sha256"],
        )
    if cleaned:
        resources_reserved = 0
    else:
        try:
            active = set(store.active_namespaces())
            resources_reserved = sum(
                namespace in active for namespace in (namespace_a, namespace_b)
            )
        except IsolationError:
            resources_reserved = 2
    _blocker_evidence(
        evidence_dir=evidence_dir,
        namespace_a=namespace_a,
        namespace_b=namespace_b,
        reasons=["reviewed recovery retry completed" if cleaned else "reviewed recovery retry failed"],
        processes_started=0 if cleaned else "unknown",
        resources_reserved=resources_reserved,
        recovery="cleanup-proven" if cleaned else "reservation-retained",
        retryable=True,
        recovery_context=context,
    )
    _emit(
        {
            "command": "recover",
            "status": "passed" if cleaned else "blocked",
            "recovery": "cleanup-proven" if cleaned else "reservation-retained",
            "retryable": True,
        }
    )
    return 0 if cleaned else EXIT_BLOCKED


def _build_receipt(
    *,
    evidence: dict[str, Any],
    evidence_path: Path,
    receipt_record: dict[str, Any],
    reservation_release: list[dict[str, str]],
) -> dict[str, Any]:
    expected_authority = {
        "run_nonce": evidence["run_nonce"],
        "driver_revision": evidence["driver_revision"],
        "driver_sha256": evidence["driver_sha256"],
        "contract_semantic_sha256": evidence["contract_semantic_sha256"],
        "namespaces": evidence["namespaces"],
    }
    if any(
        receipt_record.get(field) != value
        for field, value in expected_authority.items()
    ):
        raise EvidenceError(
            "private receipt authority does not match reviewed exercise"
        )
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "receipt_class": "worktree-harness-receipt",
        "exercise_id": evidence["exercise_id"],
        "run_nonce": evidence["run_nonce"],
        "driver_revision": evidence["driver_revision"],
        "driver_sha256": evidence["driver_sha256"],
        "contract_semantic_sha256": evidence["contract_semantic_sha256"],
        "namespaces": list(evidence["namespaces"]),
        "evidence_sha256": _sha256_file(evidence_path),
        "reservation_release": reservation_release,
    }
    receipt["receipt_hmac"] = _receipt_hmac(
        receipt_key_hex=receipt_record["receipt_key_hex"],
        evidence=evidence,
        receipt=receipt,
    )
    _ensure_schema(receipt, RECEIPT_KEYS, "harness receipt")
    for index, record in enumerate(reservation_release):
        _ensure_schema(
            record,
            {"namespace", "state"},
            f"harness receipt reservation_release[{index}]",
        )
    return receipt


def _receipt_failures(
    *,
    evidence_dir: Path,
    evidence: dict[str, Any],
    store: ReservationStore | None = None,
) -> list[str]:
    receipt_path = evidence_dir / "receipt.json"
    try:
        if (
            receipt_path.is_symlink()
            or not receipt_path.is_file()
            or receipt_path.stat().st_size > 128 * 1024
        ):
            return ["independent harness receipt is absent, symlinked, or oversized"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["independent harness receipt is unreadable"]
    failures = _exact_keys(receipt, RECEIPT_KEYS, "harness receipt")
    if failures or not isinstance(receipt, dict):
        return failures
    failures.extend(
        _type_failure(receipt.get("schema_version"), int, "receipt schema_version")
    )
    for field in (
        "contract_semantic_sha256",
        "driver_revision",
        "driver_sha256",
        "evidence_sha256",
        "exercise_id",
        "receipt_class",
        "receipt_hmac",
        "run_nonce",
    ):
        failures.extend(
            _type_failure(receipt.get(field), str, f"receipt {field}")
        )
    if not isinstance(receipt.get("namespaces"), list) or not all(
        isinstance(namespace, str) for namespace in receipt.get("namespaces", ())
    ):
        failures.append("receipt namespaces have invalid type")
    release = receipt.get("reservation_release")
    if not isinstance(release, list) or len(release) != 2:
        failures.append("harness receipt must contain two reservation releases")
    else:
        for index, record in enumerate(release):
            failures.extend(
                _exact_keys(
                    record,
                    {"namespace", "state"},
                    f"harness receipt reservation_release[{index}]",
                )
            )
            if isinstance(record, dict) and not all(
                isinstance(value, str) for value in record.values()
            ):
                failures.append(
                    f"harness receipt reservation_release[{index}] has invalid types"
                )
        if any(
            not isinstance(record, dict)
            or record.get("state") != "released"
            for record in release
        ):
            failures.append("harness receipt does not prove reservation release")
        released_namespaces = {
            record.get("namespace")
            for record in release
            if isinstance(record, dict)
        }
        if released_namespaces != set(receipt.get("namespaces", ())):
            failures.append(
                "harness receipt releases do not match evidence namespaces"
            )
    try:
        evidence_sha256 = _sha256_file(evidence_dir / "exercise.json")
    except OSError:
        failures.append("exercise evidence cannot be hashed for receipt")
    else:
        if receipt.get("evidence_sha256") != evidence_sha256:
            failures.append("harness receipt does not bind exercise evidence")
    for field in (
        "exercise_id",
        "run_nonce",
        "driver_revision",
        "driver_sha256",
        "contract_semantic_sha256",
        "namespaces",
    ):
        if receipt.get(field) != evidence.get(field):
            failures.append(f"harness receipt does not bind evidence field: {field}")
    authority_store = store or ReservationStore()
    try:
        authority = authority_store.receipt_record(
            run_nonce=evidence.get("run_nonce", "")
        )
    except IsolationError:
        failures.append("private harness receipt authority is unavailable")
        authority = None
    if authority is not None:
        authority_fields = {
            "run_nonce": evidence.get("run_nonce"),
            "driver_revision": evidence.get("driver_revision"),
            "driver_sha256": evidence.get("driver_sha256"),
            "contract_semantic_sha256": evidence.get(
                "contract_semantic_sha256"
            ),
            "namespaces": evidence.get("namespaces"),
        }
        if any(
            authority.get(field) != value
            for field, value in authority_fields.items()
        ):
            failures.append(
                "private harness receipt authority does not match evidence"
            )
        receipt_hmac = receipt.get("receipt_hmac")
        unsigned = {
            key: value for key, value in receipt.items() if key != "receipt_hmac"
        }
        try:
            expected_hmac = _receipt_hmac(
                receipt_key_hex=authority.get("receipt_key_hex", ""),
                evidence=evidence,
                receipt=unsigned,
            )
        except EvidenceError:
            failures.append("private harness receipt authority is invalid")
        else:
            if not isinstance(receipt_hmac, str) or not hmac.compare_digest(
                receipt_hmac, expected_hmac
            ):
                failures.append(
                    "harness receipt HMAC does not prove reviewed execution"
                )
    driver_status = _driver_status(Path.cwd().resolve())
    if not driver_status.get("available"):
        failures.append("immutable reviewed driver/contract provenance is unavailable")
    else:
        provenance = {
            "driver_revision": "reviewed_repository_commit",
            "driver_sha256": "driver_sha256",
            "contract_semantic_sha256": "contract_semantic_sha256",
        }
        for receipt_field, status_field in provenance.items():
            if receipt.get(receipt_field) != driver_status.get(status_field):
                failures.append(
                    f"harness receipt provenance mismatch: {receipt_field}"
                )
    return failures


def verify(args: argparse.Namespace) -> int:
    evidence_dir = Path(args.evidence_dir).expanduser().resolve(strict=True)
    path = evidence_dir / "exercise.json"
    try:
        if path.is_symlink() or path.stat().st_size > 3 * 1024 * 1024:
            raise EvidenceError("exercise evidence is symlinked or oversized")
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"cannot read exercise evidence: {path}") from error
    validate_evidence(evidence)
    failures = _product_demo_failures(
        evidence,
        require_no_cross_observation=args.require_no_cross_observation,
        require_clean_teardown=args.require_clean_teardown,
    )
    failures.extend(_receipt_failures(evidence_dir=evidence_dir, evidence=evidence))
    result = {
        "command": "verify",
        "status": "failed" if failures else "passed",
        "failures": failures,
    }
    _emit(result)
    return EXIT_VERIFY_FAILED if failures else 0


def _product_demo_failures(
    evidence: dict[str, Any],
    *,
    require_no_cross_observation: bool,
    require_clean_teardown: bool,
) -> list[str]:
    failures = _product_schema_failures(evidence)
    if failures:
        return failures
    if evidence.get("schema_version") != 1:
        failures.append("unsupported evidence schema")
    if evidence.get("evidence_class") != "product-demo":
        failures.append("evidence is not a real product-demo exercise")
    if evidence.get("status") != "passed":
        failures.append("exercise status is not passed")
    if evidence.get("acceptance") != "accepted":
        failures.append("exercise is not accepted")
    exercise_id = evidence.get("exercise_id")
    if not isinstance(exercise_id, str) or not SYNTHETIC_ID_RE.fullmatch(exercise_id):
        failures.append("synthetic exercise id is absent or invalid")
    run_nonce = evidence.get("run_nonce")
    if not isinstance(run_nonce, str) or not RUN_NONCE_RE.fullmatch(run_nonce):
        failures.append("run nonce is absent or invalid")
        run_nonce = ""
    driver_revision = evidence.get("driver_revision")
    if not isinstance(driver_revision, str) or not COMMIT_RE.fullmatch(driver_revision):
        failures.append("reviewed driver revision is absent or invalid")
        driver_revision = ""
    driver_sha256 = evidence.get("driver_sha256")
    if not isinstance(driver_sha256, str) or not SHA256_RE.fullmatch(driver_sha256):
        failures.append("reviewed driver SHA-256 is absent or invalid")
        driver_sha256 = ""
    contract_semantic_sha256 = evidence.get("contract_semantic_sha256")
    if (
        not isinstance(contract_semantic_sha256, str)
        or not SHA256_RE.fullmatch(contract_semantic_sha256)
    ):
        failures.append("reviewed contract semantic SHA-256 is absent or invalid")

    namespaces = evidence.get("namespaces")
    if (
        not isinstance(namespaces, list)
        or len(namespaces) != 2
        or not all(isinstance(namespace, str) for namespace in namespaces)
        or len(set(namespaces)) != 2
    ):
        failures.append("exactly two distinct namespaces are required")
        namespaces = []
    else:
        try:
            for namespace in namespaces:
                validate_namespace(namespace)
        except (TypeError, IsolationError):
            failures.append("evidence contains an unsafe namespace")

    manifests = evidence.get("manifests")
    if not isinstance(manifests, list) or len(manifests) != 2:
        failures.append("exactly two public manifests are required")
    else:
        failures.extend(_public_manifest_failures(manifests, namespaces))
        failures.extend(
            _allocation_digest_failures(
                manifests,
                evidence.get("allocation_digests"),
                run_nonce=run_nonce,
                driver_revision=driver_revision,
                driver_sha256=driver_sha256,
            )
        )

    failures.extend(_concurrency_failures(evidence.get("concurrency")))

    if require_no_cross_observation:
        failures.extend(
            _cross_observation_failures(
                evidence.get("cross_observations"),
                namespaces,
                run_nonce=run_nonce,
                driver_revision=driver_revision,
                driver_sha256=driver_sha256,
            )
        )
    failures.extend(
        _restart_failures(
            evidence.get("restarts"),
            namespaces,
            evidence.get("allocation_digests"),
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
    )
    if require_clean_teardown:
        failures.extend(
            _teardown_failures(
                evidence.get("teardown"),
                namespaces,
                run_nonce=run_nonce,
                driver_revision=driver_revision,
                driver_sha256=driver_sha256,
            )
        )
    return failures


def _bound_digest(
    *,
    kind: str,
    payload: Any,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
) -> str:
    bound = {
        "kind": kind,
        "run_nonce": run_nonce,
        "driver_revision": driver_revision,
        "driver_sha256": driver_sha256,
        "payload": payload,
    }
    canonical = json.dumps(
        bound, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _allocation_digest_failures(
    manifests: list[Any],
    digests: Any,
    *,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
) -> list[str]:
    if not isinstance(digests, dict):
        return ["allocation digest map is absent"]
    if not all(
        isinstance(manifest, dict)
        and isinstance(manifest.get("namespace"), str)
        for manifest in manifests
    ):
        return ["allocation manifests cannot be digested"]
    expected_namespaces = {
        manifest.get("namespace") for manifest in manifests if isinstance(manifest, dict)
    }
    if set(digests) != expected_namespaces:
        return ["allocation digest map does not match manifests"]
    for manifest in manifests:
        namespace = manifest["namespace"]
        expected = _bound_digest(
            kind="allocation",
            payload=manifest,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
        actual = digests.get(namespace)
        if not isinstance(actual, str) or not secrets.compare_digest(actual, expected):
            return [f"allocation digest does not bind manifest: {namespace}"]
    return []


def _public_manifest_failures(
    manifests: list[Any], namespaces: list[str]
) -> list[str]:
    failures: list[str] = []
    if not all(isinstance(manifest, dict) for manifest in manifests):
        return ["public manifests must be objects"]
    manifest_namespaces = [manifest.get("namespace") for manifest in manifests]
    if set(manifest_namespaces) != set(namespaces):
        failures.append("public manifests do not match exercise namespaces")
    required = {
        "namespace",
        "ports",
        "database",
        "schema",
        "object_prefix",
        "browser",
        "telemetry",
        "process_identities",
        "workspace_id",
        "logs_id",
        "proof_id",
        "restart_rule",
    }
    for manifest in manifests:
        missing = sorted(required.difference(manifest))
        if missing:
            failures.append("public manifest missing: " + ", ".join(missing))
    if failures:
        return failures

    left, right = manifests
    left_ports = left.get("ports", {})
    right_ports = right.get("ports", {})
    if not isinstance(left_ports, dict) or not isinstance(right_ports, dict):
        failures.append("public manifest ports must be objects")
    elif not set(left_ports.values()).isdisjoint(right_ports.values()):
        failures.append("product-demo ports overlap")
    for field in (
        "database",
        "schema",
        "object_prefix",
        "browser",
        "telemetry",
        "process_identities",
        "workspace_id",
        "logs_id",
        "proof_id",
    ):
        if left.get(field) == right.get(field):
            failures.append(f"product-demo dimension is shared: {field}")
    return failures


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _concurrency_failures(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["structured concurrency evidence is absent"]
    keys = (
        "a_started_at",
        "b_started_at",
        "a_ready_at",
        "b_ready_at",
        "a_stopped_at",
        "b_stopped_at",
    )
    parsed = {key: _parse_time(value.get(key)) for key in keys}
    if any(item is None for item in parsed.values()):
        return ["concurrency timestamps are incomplete or invalid"]
    if parsed["a_started_at"] > parsed["a_ready_at"]:
        return ["namespace A readiness precedes startup"]
    if parsed["b_started_at"] > parsed["b_ready_at"]:
        return ["namespace B readiness precedes startup"]
    first_stop = min(parsed["a_stopped_at"], parsed["b_stopped_at"])
    if max(parsed["a_ready_at"], parsed["b_ready_at"]) >= first_stop:
        return ["product-demo stacks were not concurrently ready"]
    return []


def _cross_observation_failures(
    value: Any,
    namespaces: list[str],
    *,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
) -> list[str]:
    if not isinstance(value, list):
        return ["structured cross-observation evidence is absent"]
    if len(namespaces) != 2:
        return ["cross-observation namespaces cannot be validated"]
    expected = {
        (source, target, dimension)
        for source, target in (
            (namespaces[0], namespaces[1]),
            (namespaces[1], namespaces[0]),
        )
        for dimension in PROBE_DIMENSIONS
    }
    observed: set[tuple[str, str, str]] = set()
    for record in value:
        if not isinstance(record, dict):
            return ["cross-observation record is not an object"]
        key = (
            record.get("source_namespace"),
            record.get("target_namespace"),
            record.get("dimension"),
        )
        if key in observed:
            return ["duplicate cross-observation record"]
        observed.add(key)
        if record.get("result") != "not-observed":
            return ["cross-observation probe did not deny peer visibility"]
        probe_id = record.get("probe_id")
        digest = record.get("result_digest")
        if not isinstance(probe_id, str) or not SYNTHETIC_ID_RE.fullmatch(probe_id):
            return ["cross-observation probe id is invalid"]
        payload = {key: nested for key, nested in record.items() if key != "result_digest"}
        expected_digest = _bound_digest(
            kind="cross-observation",
            payload=payload,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
        if not isinstance(digest, str) or not secrets.compare_digest(
            digest, expected_digest
        ):
            return ["cross-observation result digest does not bind the record"]
    if observed != expected:
        return ["bidirectional cross-observation matrix is incomplete"]
    return []


def _restart_failures(
    value: Any,
    namespaces: list[str],
    allocation_digests: Any,
    *,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
) -> list[str]:
    if not isinstance(value, list) or len(value) != 2:
        return ["exactly two structured restart records are required"]
    if {record.get("namespace") for record in value if isinstance(record, dict)} != set(
        namespaces
    ):
        return ["restart records do not match exercise namespaces"]
    for record in value:
        if not isinstance(record, dict):
            return ["restart record is not an object"]
        if record.get("rule") != "reuse-reserved-resources-with-exact-teardown-token":
            return ["restart rule is absent or changed"]
        namespace = record.get("namespace")
        expected_allocation = (
            allocation_digests.get(namespace)
            if isinstance(allocation_digests, dict)
            else None
        )
        if (
            record.get("allocation_fingerprint_before") != expected_allocation
            or record.get("allocation_fingerprint_after") != expected_allocation
        ):
            return ["restart silently rotated allocated resources"]
        if record.get("process_identity_before") == record.get(
            "process_identity_after"
        ):
            return ["restart did not record a new process identity"]
        digest = record.get("restart_digest")
        payload = {key: nested for key, nested in record.items() if key != "restart_digest"}
        expected_digest = _bound_digest(
            kind="restart",
            payload=payload,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
        if not isinstance(digest, str) or not secrets.compare_digest(
            digest, expected_digest
        ):
            return ["restart digest does not bind the record"]
    return []


def _teardown_failures(
    value: Any,
    namespaces: list[str],
    *,
    run_nonce: str,
    driver_revision: str,
    driver_sha256: str,
    require_reservation_absent: bool = True,
) -> list[str]:
    if not isinstance(value, list) or len(value) != 2:
        return ["exactly two structured teardown records are required"]
    ordered = sorted(
        (record for record in value if isinstance(record, dict)),
        key=lambda record: record.get("order", 0),
    )
    if len(ordered) != 2 or [record.get("order") for record in ordered] != [1, 2]:
        return ["teardown order is absent or invalid"]
    if {record.get("namespace") for record in ordered} != set(namespaces):
        return ["teardown records do not match exercise namespaces"]
    if ordered[0].get("peer_survived_after") is not True:
        return ["first scoped teardown did not prove peer survival"]
    for record in ordered:
        if set(record.get("resources_absent", ())) != TEARDOWN_RESOURCES:
            return ["teardown resource cleanup matrix is incomplete"]
        if require_reservation_absent and record.get("reservation_absent") is not True:
            return ["reservation cleanup proof is absent"]
        digest = record.get("cleanup_digest")
        payload = {key: nested for key, nested in record.items() if key != "cleanup_digest"}
        expected_digest = _bound_digest(
            kind="cleanup",
            payload=payload,
            run_nonce=run_nonce,
            driver_revision=driver_revision,
            driver_sha256=driver_sha256,
        )
        if not isinstance(digest, str) or not secrets.compare_digest(
            digest, expected_digest
        ):
            return ["teardown cleanup digest does not bind the record"]
    return []


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    commands = {
        "doctor": doctor,
        "self-test": self_test,
        "exercise": exercise,
        "recover": recover,
        "verify": verify,
    }
    try:
        return commands[args.command](args)
    except (EvidenceError, IsolationError, KeyError, TypeError, ValueError) as error:
        _emit(
            {
                "command": args.command,
                "status": "error",
                "error": str(error),
            }
        )
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
