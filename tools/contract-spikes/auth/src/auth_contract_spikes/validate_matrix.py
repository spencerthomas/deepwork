"""Validate the complete, precedence-aware SPIKE-AUTH-002 matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

from .catalog import (
    CONTEXT_CASES,
    FORBIDDEN_CALLER_HEADERS,
    KEY_CLASSES,
    OPERATIONS,
)
from .generate_matrix import (
    _fixture_payload,
    _workspace_value,
    is_locally_rejected,
    selected_headers,
)


class MatrixError(ValueError):
    pass


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MatrixError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise MatrixError(f"invalid JSON numeric constant: {value}")


def validate(
    path: Path,
    *,
    require_complete_cross_product: bool,
    reject_unresolved_precedence_conflicts: bool,
) -> None:
    data = json.loads(
        path.read_text(),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )
    if not isinstance(data, dict):
        raise MatrixError("matrix must be an object")
    if data.get("schema_version") != 1 or data.get("gate") != "SPIKE-AUTH-002":
        raise MatrixError("invalid matrix identity")
    expected_dimensions = json.loads(
        json.dumps(
            {
                "operations": [operation.to_dict() for operation in OPERATIONS],
                "key_classes": list(KEY_CLASSES),
                "context_cases": list(CONTEXT_CASES),
            }
        )
    )
    if data.get("dimensions") != expected_dimensions:
        raise MatrixError("matrix dimensions do not match catalog")
    if data.get("overall_conclusion") != "blocked-live-evidence":
        raise MatrixError("overall conclusion must remain blocked-live-evidence")
    if not data.get("overall_blocker") or not data.get("safe_fallback"):
        raise MatrixError("matrix requires overall blocker and fallback")
    rows = data.get("rows")
    if not isinstance(rows, list):
        raise MatrixError("rows must be a list")
    required = {
        (
            operation.method,
            operation.route_template,
            operation.service_host_class,
            operation.plane,
            operation.operation,
            key_class,
            context_case,
        )
        for operation, key_class, context_case in product(
            OPERATIONS, KEY_CLASSES, CONTEXT_CASES
        )
    }
    actual: set[tuple[str, ...]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise MatrixError("row must be an object")
        identity = (
            row["method"],
            row["official_route_template"],
            row["service_host_class"],
            row["plane"],
            row["operation"],
            row["key_class"],
            row["context_case"],
        )
        if identity in actual:
            raise MatrixError(f"duplicate row: {row['row_id']}")
        actual.add(identity)
        expected_row_id = "::".join(identity)
        if row.get("row_id") != expected_row_id:
            raise MatrixError(f"row_id mismatch: {row.get('row_id')}")
        if row["final_conclusion"] not in {
            "accepted-live",
            "blocked-live-evidence",
            "rejected",
            "unknown",
        }:
            raise MatrixError(f"invalid conclusion: {row['row_id']}")
        if not row.get("owner") or not row.get("blocker") or not row.get("fallback"):
            raise MatrixError(f"missing owner/blocker/fallback: {row['row_id']}")
        operation = next(
            (
                candidate
                for candidate in OPERATIONS
                if candidate.operation == row["operation"]
            ),
            None,
        )
        if operation is None:
            raise MatrixError(f"unknown operation: {row['row_id']}")
        expected_exact_headers = sorted(
            set(operation.documented_headers), key=str.lower
        )
        if row.get("exact_header_names") != expected_exact_headers:
            raise MatrixError(f"documented header mismatch: {row['row_id']}")
        expected_selected_headers = selected_headers(
            operation, row["context_case"]
        )
        if row.get("synthetic_selected_header_names") != expected_selected_headers:
            raise MatrixError(f"selected header mismatch: {row['row_id']}")
        if not set(expected_selected_headers).issubset(expected_exact_headers):
            raise MatrixError(f"selected undocumented header: {row['row_id']}")
        if row.get("caller_headers_stripped_or_rejected") != list(
            FORBIDDEN_CALLER_HEADERS
        ):
            raise MatrixError(f"caller-header policy mismatch: {row['row_id']}")
        evidence_context = row.get("evidence_context")
        if not isinstance(evidence_context, dict) or any(
            field not in evidence_context
            for field in (
                "package_versions",
                "server_revision",
                "account_tier",
                "region",
                "auth_context",
                "date",
            )
        ):
            raise MatrixError(f"invalid evidence context: {row['row_id']}")
        if evidence_context.get("package_versions") != {
            "langsmith": "0.10.9",
            "langgraph-sdk": "0.4.2",
        } or not evidence_context.get("date"):
            raise MatrixError(f"invalid evidence version context: {row['row_id']}")
        observations = row.get("observations", [])
        if not observations:
            raise MatrixError(f"missing observations: {row['row_id']}")
        for observation in observations:
            if not isinstance(observation, dict) or any(
                field not in observation
                for field in (
                    "evidence_id",
                    "tier",
                    "evidence_class",
                    "source_id",
                    "source",
                    "revision_or_version",
                    "date",
                    "claim",
                    "fixture_sha256",
                    "contradicts",
                )
            ):
                raise MatrixError(f"invalid observation schema: {row['row_id']}")
            if (
                not observation["evidence_id"]
                or observation["tier"] not in {1, 2, 3, 4, 5}
                or not observation["evidence_class"]
                or not observation["source_id"]
                or not observation["source"]
                or not observation["revision_or_version"]
                or not observation["date"]
                or not observation["claim"]
                or not isinstance(observation["contradicts"], list)
            ):
                raise MatrixError(f"invalid observation values: {row['row_id']}")
        if row["final_conclusion"] == "accepted-live":
            if row.get("author_acceptance") is not False:
                raise MatrixError(f"author cannot accept row: {row['row_id']}")
            if row.get("reviewer_status") != "accepted-independent-review":
                raise MatrixError(f"accepted row lacks independent review: {row['row_id']}")
            if not row.get("reviewed_by") or not row.get("reviewed_at"):
                raise MatrixError(f"accepted row lacks reviewer identity/date: {row['row_id']}")
            if not row.get("final_selected_header_names"):
                raise MatrixError(f"accepted row lacks final headers: {row['row_id']}")
            live_observations = [
                observation
                for observation in observations
                if observation.get("tier") == 1
                and observation.get("evidence_class")
                == "accepted-live-contract-and-executable-fixture"
                and observation.get("reviewer_decision") == "accepted"
                and observation.get("fixture_path")
                and observation.get("fixture_sha256")
            ]
            if len(live_observations) != 1:
                raise MatrixError(f"accepted row lacks reviewed tier-1 evidence: {row['row_id']}")
            if any(
                not evidence_context.get(field)
                for field in (
                    "server_revision",
                    "account_tier",
                    "region",
                    "auth_context",
                )
            ) or evidence_context.get("auth_context") == "offline-synthetic-only":
                raise MatrixError(f"accepted row lacks live context: {row['row_id']}")
            if not any(
                observation.get("tier") == 1
                and observation.get("evidence_class")
                == "accepted-live-contract-and-executable-fixture"
                for observation in observations
            ):
                raise MatrixError(f"accepted row lacks tier-1 evidence: {row['row_id']}")
            if reject_unresolved_precedence_conflicts and any(
                not conflict.get("resolved", False)
                and conflict.get("tier", 99) <= 1
                for conflict in row.get("unresolved_conflicts", [])
            ):
                raise MatrixError(
                    f"accepted row has unresolved precedence conflict: {row['row_id']}"
                )
        for header_name in row.get("exact_header_names", []):
            if (
                not header_name.isascii()
                or "\r" in header_name
                or "\n" in header_name
                or ":" in header_name
            ):
                raise MatrixError(f"invalid header name: {row['row_id']}")
        for observation in observations:
            fixture_path = observation.get("fixture_path")
            fixture_sha256 = observation.get("fixture_sha256")
            if fixture_path:
                relative = Path(fixture_path)
                if relative.is_absolute() or ".." in relative.parts:
                    raise MatrixError(f"unsafe fixture path: {row['row_id']}")
                resolved = path.parent / relative
                if not resolved.is_file() or resolved.is_symlink():
                    raise MatrixError(f"missing/unsafe fixture: {row['row_id']}")
                actual_hash = hashlib.sha256(resolved.read_bytes()).hexdigest()
                if actual_hash != fixture_sha256:
                    raise MatrixError(f"fixture hash mismatch: {row['row_id']}")
        if row["final_conclusion"] == "accepted-live":
            live_observation = live_observations[0]
            live_fixture = json.loads(
                (path.parent / live_observation["fixture_path"]).read_text(),
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
            if (
                live_fixture.get("evidence_class")
                != "accepted-live-contract-fixture"
                or live_fixture.get("reviewer_status")
                != "accepted-independent-review"
                or live_fixture.get("operation") != row["operation"]
                or live_fixture.get("context_case") != row["context_case"]
                or live_fixture.get("request", {}).get("method") != row["method"]
                or live_fixture.get("request", {}).get("route_template")
                != row["official_route_template"]
                or live_fixture.get("request", {}).get("host_class")
                != row["service_host_class"]
                or live_fixture.get("response", {}).get("sanitized") is not True
                or live_fixture.get("response", {}).get("provider_body_retained")
                is not False
            ):
                raise MatrixError(f"accepted row has invalid live fixture: {row['row_id']}")
            live_header_names = sorted(
                live_fixture.get("request", {}).get("header_names", []),
                key=str.lower,
            )
            final_header_names = sorted(
                row.get("final_selected_header_names", []), key=str.lower
            )
            if (
                live_header_names != final_header_names
                or not set(final_header_names).issubset(
                    set(row.get("exact_header_names", []))
                )
            ):
                raise MatrixError(
                    f"accepted row live/final header mismatch: {row['row_id']}"
                )
            live_context = live_fixture.get("evidence_context", {})
            row_context = row.get("evidence_context", {})
            if any(
                live_context.get(field) != row_context.get(field)
                for field in (
                    "server_revision",
                    "account_tier",
                    "region",
                    "auth_context",
                )
            ):
                raise MatrixError(
                    f"accepted row live context mismatch: {row['row_id']}"
                )
        values = row.get("redacted_request_schema", {})
        allowed_credential = (
            None
            if row["context_case"] == "missing-authorization"
            else "<redacted>"
        )
        if values.get("credential") != allowed_credential:
            raise MatrixError(f"credential not redacted: {row['row_id']}")
        expected_workspace = _workspace_value(operation, row["context_case"])
        if values.get("workspace") != expected_workspace:
            raise MatrixError(f"workspace schema mismatch: {row['row_id']}")
        expected_rejected = is_locally_rejected(operation, row["context_case"])
        if expected_rejected and row["final_conclusion"] != "rejected":
            raise MatrixError(f"conclusion/context mismatch: {row['row_id']}")
        if not expected_rejected and row["final_conclusion"] not in {
            "blocked-live-evidence",
            "accepted-live",
        }:
            raise MatrixError(f"conclusion/context mismatch: {row['row_id']}")
        if (
            row["final_conclusion"] != "accepted-live"
            and row.get("final_selected_header_names") is not None
        ):
            raise MatrixError(
                f"non-live row has final selected headers: {row['row_id']}"
            )
        fixture_observations = [
            observation
            for observation in observations
            if observation.get("evidence_class") == "offline-synthetic-fixture"
        ]
        if len(fixture_observations) != 1:
            raise MatrixError(f"expected one offline fixture: {row['row_id']}")
        fixture = json.loads(
            (path.parent / fixture_observations[0]["fixture_path"]).read_text(),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
        expected_offline_conclusion = (
            "rejected" if expected_rejected else "blocked-live-evidence"
        )
        expected_fixture = _fixture_payload(
            operation,
            row["context_case"],
            expected_selected_headers,
            expected_offline_conclusion,
        )
        if fixture != expected_fixture:
            raise MatrixError(f"fixture transcript mismatch: {row['row_id']}")
    if require_complete_cross_product:
        missing = required - actual
        extra = actual - required
        if missing or extra:
            raise MatrixError(
                f"cross product mismatch: missing={len(missing)} extra={len(extra)}"
            )
    if data.get("row_count") != len(rows):
        raise MatrixError("row_count does not match rows")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--require-complete-cross-product", action="store_true")
    parser.add_argument(
        "--reject-unresolved-precedence-conflicts", action="store_true"
    )
    args = parser.parse_args()
    validate(
        args.matrix,
        require_complete_cross_product=args.require_complete_cross_product,
        reject_unresolved_precedence_conflicts=args.reject_unresolved_precedence_conflicts,
    )
    print("matrix-valid")


if __name__ == "__main__":
    main()
