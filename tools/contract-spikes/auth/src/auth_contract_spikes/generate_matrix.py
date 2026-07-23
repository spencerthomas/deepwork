"""Generate the deterministic matrix and synthetic fixture corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .catalog import (
    COLLECTED_AT,
    CONTEXT_CASES,
    FORBIDDEN_CALLER_HEADERS,
    KEY_CLASSES,
    OPERATIONS,
    REJECTED_CASES,
)

WORKSPACE_VALUE_CASES = {
    "valid-documented-workspace-context",
    "wrong-workspace-context",
    "conflicting-workspace-context",
    "inaccessible-workspace",
}
CONTROL_TENANT_CASES = {
    "valid-documented-workspace-context",
    "wrong-workspace-context",
    "conflicting-workspace-context",
    "unsupported-key-plane-combination",
    "caller-supplied-forwarding-headers",
    "permission-denied",
    "revoked-key",
    "inaccessible-workspace",
}
PROVIDER_OBSERVED_CASES = {
    "wrong-workspace-context",
    "missing-required-workspace-context",
    "unsupported-key-plane-combination",
    "permission-denied",
    "revoked-key",
    "inaccessible-workspace",
}


def is_locally_rejected(operation, context_case: str) -> bool:
    return context_case in REJECTED_CASES or (
        operation.plane == "control"
        and context_case
        in {
            "valid-no-workspace-context",
            "missing-required-workspace-context",
        }
    )


def selected_headers(operation, context_case: str) -> list[str]:
    """Return only headers documented for this exact operation and case."""

    selected = (
        [] if context_case == "missing-authorization" else ["X-Api-Key"]
    )
    if operation.plane == "platform" and context_case != "missing-authorization":
        if operation.operation in {"current-organization", "list-workspaces"}:
            selected.append("X-Organization-Id")
    elif operation.plane == "control" and context_case in CONTROL_TENANT_CASES:
        selected.append("X-Tenant-Id")
    return sorted(set(selected), key=str.lower)


def _row(operation, key_class: str, context_case: str) -> dict[str, object]:
    row_id = "::".join(
        (
            operation.method,
            operation.route_template,
            operation.service_host_class,
            operation.plane,
            operation.operation,
            key_class,
            context_case,
        )
    )
    rejected = is_locally_rejected(operation, context_case)
    exact_headers = list(operation.documented_headers)
    selected = selected_headers(operation, context_case)
    conflicts = []
    if operation.contract_limit:
        conflicts.append(
            {
                "id": "official-contract-incomplete",
                "tier": 2,
                "detail": operation.contract_limit,
                "resolved": False,
            }
        )
    if operation.plane == "data" and context_case == "valid-documented-workspace-context":
        conflicts.append(
            {
                "id": "workspace-selection-not-agent-header",
                "tier": 2,
                "detail": "Agent Server docs establish X-Api-Key but do not establish X-Tenant-Id or X-Organization-Id forwarding.",
                "resolved": False,
            }
        )
    conclusion = "rejected" if rejected else "blocked-live-evidence"
    blocker = (
        "The combination is denied by the fail-closed probe policy before dispatch."
        if rejected
        else "No sanctioned non-production classic account was supplied for exact provider confirmation."
    )
    fixture_payload = _fixture_payload(
        operation, context_case, selected, conclusion
    )
    fixture_path, fixture_sha256 = _fixture_record(
        operation, context_case, fixture_payload
    )
    workspace_value = _workspace_value(operation, context_case)
    return {
        "row_id": row_id,
        "method": operation.method,
        "official_route_template": operation.route_template,
        "service_host_class": operation.service_host_class,
        "plane": operation.plane,
        "operation": operation.operation,
        "key_class": key_class,
        "context_case": context_case,
        "evidence_context": {
            "package_versions": {
                "langsmith": "0.10.9",
                "langgraph-sdk": "0.4.2",
            },
            "server_revision": None,
            "account_tier": None,
            "region": None,
            "auth_context": "offline-synthetic-only",
            "date": COLLECTED_AT,
        },
        "exact_header_names": sorted(set(exact_headers), key=str.lower),
        "synthetic_selected_header_names": sorted(
            set(selected), key=str.lower
        ),
        "final_selected_header_names": None,
        "redacted_request_schema": {
            "credential": (
                None if context_case == "missing-authorization" else "<redacted>"
            ),
            "workspace": workspace_value,
            "organization": "<organization-id>"
            if "X-Organization-Id" in selected
            else None,
            "body": operation.request_schema,
        },
        "sanitized_response_or_error_schema": (
            {
                "code": "typed-source-error",
                "provider_body_retained": False,
                "provider_behavior_confirmed": False,
            }
            if rejected or context_case in PROVIDER_OBSERVED_CASES
            else {"shape": operation.response_schema, "provider_body_retained": False}
        ),
        "caller_headers_stripped_or_rejected": list(FORBIDDEN_CALLER_HEADERS),
        "observations": [
            {
                "evidence_id": f"official::{operation.operation}",
                "tier": 2,
                "evidence_class": "official-primary-documentation",
                "source_id": "official-source-inventory",
                "source": operation.source_url,
                "revision_or_version": f"accessed-{COLLECTED_AT}",
                "date": COLLECTED_AT,
                "claim": operation.source_claim,
                "fixture_sha256": None,
                "contradicts": [],
            },
            {
                "evidence_id": f"installed::{operation.operation}",
                "tier": 2,
                "evidence_class": "installed-public-api-and-generated-schema",
                "source_id": "installed-generated-inventory",
                "source": "installed-generated-inventory.md",
                "revision_or_version": (
                    "langsmith==0.10.9"
                    if operation.plane == "platform"
                    else "langgraph-sdk==0.4.2"
                ),
                "date": COLLECTED_AT,
                "claim": _installed_claim(operation.plane),
                "fixture_sha256": None,
                "contradicts": (
                    ["official::" + operation.operation]
                    if operation.operation in {"current-organization", "list-workspaces"}
                    else []
                ),
            },
            *_pinned_observations(operation),
            {
                "evidence_id": f"offline::{operation.operation}::{context_case}",
                "tier": 5,
                "evidence_class": "offline-synthetic-fixture",
                "source_id": f"fixture::{operation.operation}::{context_case}",
                "source": "fixtures/manifest.json",
                "revision_or_version": "auth-contract-spikes-0.1.0",
                "date": COLLECTED_AT,
                "claim": (
                    "The offline fixture proves local fail-closed rejection before dispatch."
                    if rejected
                    else "The offline fixture models the blocked disposition without claiming provider behavior."
                ),
                "fixture_path": fixture_path,
                "fixture_sha256": fixture_sha256,
                "contradicts": [],
            },
        ],
        "unresolved_conflicts": conflicts,
        "final_conclusion": conclusion,
        "owner": "runtime-contracts-and-security-reviewers",
        "blocker": blocker,
        "fallback": (
            "Reject before network dispatch with a typed explanation."
            if rejected
            else "Keep this operation unavailable; do not infer provider behavior from the synthetic model."
        ),
        "author_acceptance": False,
        "reviewer_status": "pending-independent-review",
        "downstream_acceptance_ids": [
            "AC-DW-ONB-001-01",
            "AC-DW-ONB-002-01",
            "AC-DW-FND-003-01",
            "AC-DW-FND-003-02",
            "AC-DW-FND-003-08",
            "AC-DW-QUAL-001-03",
            "AC-DW-QUAL-001-04",
        ],
    }


def _workspace_value(operation, context_case: str) -> str | None:
    if operation.plane == "control" and context_case in CONTROL_TENANT_CASES:
        return (
            "<wrong-workspace-id>"
            if context_case in {"wrong-workspace-context", "inaccessible-workspace"}
            else "<workspace-id>"
        )
    if operation.plane == "data" and context_case in WORKSPACE_VALUE_CASES:
        return (
            "<wrong-selector-workspace-id>"
            if context_case in {"wrong-workspace-context", "inaccessible-workspace"}
            else "<selector-only-workspace-id>"
        )
    return None


def _pinned_observations(operation) -> list[dict[str, object]]:
    observations = [
        {
            "evidence_id": f"pinned::SRC-LC::{operation.operation}",
            "tier": 4,
            "evidence_class": "pinned-reference-code-and-generated-contract",
            "source_id": "SRC-LC",
            "source": "pinned-source-inventory.md",
            "revision_or_version": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
            "date": COLLECTED_AT,
            "claim": operation.source_claim,
            "fixture_sha256": None,
            "contradicts": [],
        },
        {
            "evidence_id": f"pinned::SRC-LCPY::{operation.operation}",
            "tier": 4,
            "evidence_class": "pinned-reference-code-dependency-lead",
            "source_id": "SRC-LCPY",
            "source": "pinned-source-inventory.md",
            "revision_or_version": "592055e15e138f5369dce95dd049ce22430996e2",
            "date": COLLECTED_AT,
            "claim": "Pinned LangChain Python delegates to langsmith and does not implement a cross-plane header selector.",
            "fixture_sha256": None,
            "contradicts": [],
        },
    ]
    if operation.plane == "data":
        observations.append(
            {
                "evidence_id": f"pinned::SRC-LG::{operation.operation}",
                "tier": 4,
                "evidence_class": "pinned-reference-code-and-generated-contract",
                "source_id": "SRC-LG",
                "source": "pinned-source-inventory.md",
                "revision_or_version": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
                "date": COLLECTED_AT,
                "claim": "Pinned LangGraph SDK exposes this Agent Server plane and emits lowercase x-api-key while accepting broad custom headers.",
                "fixture_sha256": None,
                "contradicts": [],
            }
        )
    return observations


def build_matrix() -> dict[str, object]:
    rows = [
        _row(operation, key_class, context_case)
        for operation in OPERATIONS
        for key_class in KEY_CLASSES
        for context_case in CONTEXT_CASES
    ]
    return {
        "schema_version": 1,
        "gate": "SPIKE-AUTH-002",
        "generated_at": COLLECTED_AT,
        "evidence_precedence": [
            "accepted-live-contract-and-executable-fixtures",
            "installed-generated-and-official-primary-documentation",
            "accepted-deep-work-decisions-and-specifications",
            "pinned-research-and-reference-code",
            "prototype-mock-and-synthetic-fixture-only",
        ],
        "dimensions": {
            "operations": [operation.to_dict() for operation in OPERATIONS],
            "key_classes": list(KEY_CLASSES),
            "context_cases": list(CONTEXT_CASES),
        },
        "row_count": len(rows),
        "rows": rows,
        "overall_conclusion": "blocked-live-evidence",
        "overall_blocker": "No sanctioned non-production classic account was supplied.",
        "safe_fallback": "Enable no classic source combination until independent accepted-live evidence exists for that exact row.",
    }


def _installed_claim(plane: str) -> str:
    if plane == "platform":
        return (
            "langsmith 0.10.9 constructs x-api-key and adds X-Tenant-Id when "
            "workspace_id is configured; it does not resolve the key-class/live "
            "authorization matrix."
        )
    if plane == "data":
        return (
            "langgraph-sdk 0.4.2 constructs lowercase x-api-key and exposes the "
            "Agent Server route methods, while accepting arbitrary caller headers "
            "that this probe boundary must reject."
        )
    return (
        "The selected installed LangSmith and Agent Server SDKs do not provide a "
        "typed classic control-plane host/header selector; official and pinned "
        "control-plane evidence remains separate."
    )


def _fixture_payload(
    operation,
    context_case: str,
    selected_headers: list[str],
    conclusion: str,
) -> dict[str, object]:
    placeholder = {
        "X-Api-Key": "<redacted>",
        "X-Tenant-Id": (
            "<wrong-workspace-id>"
            if context_case in {"wrong-workspace-context", "inaccessible-workspace"}
            else "<workspace-id>"
        ),
        "X-Organization-Id": "<organization-id>",
    }
    headers = {name: placeholder[name] for name in selected_headers}
    if conclusion == "rejected":
        result = {
            "status": "local-policy-rejected",
            "code": context_case,
            "network_dispatched": False,
            "provider_body_retained": False,
        }
    elif context_case in PROVIDER_OBSERVED_CASES:
        result = {
            "status": "unconfirmed-provider-behavior",
            "case": context_case,
            "network_dispatched": False,
            "provider_body_retained": False,
        }
    else:
        result = {
            "status": "unconfirmed-live",
            "expected_shape": operation.response_schema,
            "network_dispatched": False,
            "provider_body_retained": False,
        }
    return {
        "schema_version": 1,
        "evidence_class": "offline-synthetic-fixture",
        "operation": operation.operation,
        "context_case": context_case,
        "modeled_key_classes": list(KEY_CLASSES),
        "request": {
            "method": operation.method,
            "route_template": operation.route_template,
            "host_class": operation.service_host_class,
            "headers": headers,
            "body_schema": operation.request_schema,
            "negative_input": _negative_input(operation, context_case),
        },
        "result": result,
        "scrub_attestation": "symbolic placeholders only",
    }


def _negative_input(operation, context_case: str) -> dict[str, object] | None:
    if context_case in {
        "valid-no-workspace-context",
        "valid-documented-workspace-context",
    }:
        return None
    if context_case == "missing-authorization":
        return {"authorization_state": "missing"}
    if context_case == "missing-required-workspace-context":
        return {"workspace_context": "missing"}
    if context_case == "wrong-workspace-context":
        return {"workspace_context": "<wrong-workspace-id>"}
    if context_case == "conflicting-workspace-context":
        return {
            "workspace_contexts": [
                "<workspace-id>",
                "<wrong-workspace-id>",
            ]
        }
    if context_case == "unsupported-key-plane-combination":
        return {
            "key_family": "<unsupported-key-family>",
            "plane": operation.plane,
        }
    if context_case == "caller-supplied-forwarding-headers":
        return {
            "attempted_header_names": list(FORBIDDEN_CALLER_HEADERS),
            "attempted_header_values": "<stripped>",
        }
    if context_case == "permission-denied":
        return {"provider_outcome": "permission-denied-unconfirmed"}
    if context_case == "revoked-key":
        return {"credential_state": "revoked-unconfirmed"}
    if context_case == "inaccessible-workspace":
        return {
            "workspace_context": "<wrong-workspace-id>",
            "provider_outcome": "inaccessible-workspace-unconfirmed",
        }
    raise ValueError(f"unsupported context case: {context_case}")


def _fixture_filename(operation, context_case: str) -> str:
    return f"{operation.operation}--{context_case}.json"


def _fixture_record(
    operation, context_case: str, payload: dict[str, object]
) -> tuple[str, str]:
    name = _fixture_filename(operation, context_case)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    return f"fixtures/{name}", hashlib.sha256(encoded).hexdigest()


def _fixture_payloads() -> dict[str, dict[str, object]]:
    payloads: dict[str, dict[str, object]] = {}
    for operation in OPERATIONS:
        for context_case in CONTEXT_CASES:
            selected = selected_headers(operation, context_case)
            rejected = is_locally_rejected(operation, context_case)
            conclusion = "rejected" if rejected else "blocked-live-evidence"
            payloads[_fixture_filename(operation, context_case)] = _fixture_payload(
                operation, context_case, selected, conclusion
            )
    return payloads


def write_outputs(output_dir: Path) -> None:
    fixture_dir = output_dir / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    for stale in fixture_dir.glob("*.json"):
        stale.unlink()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "generated_at": COLLECTED_AT,
        "scrub_attestation": "Synthetic placeholders only; no live credential, tenant, customer, or reusable endpoint values.",
        "fixtures": [],
    }
    for name, payload in sorted(_fixture_payloads().items()):
        encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
        (fixture_dir / name).write_bytes(encoded)
        manifest["fixtures"].append(
            {"path": name, "sha256": hashlib.sha256(encoded).hexdigest()}
        )
    (fixture_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "matrix.json").write_text(
        json.dumps(build_matrix(), indent=2, sort_keys=True) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    write_outputs(args.output_dir)


if __name__ == "__main__":
    main()
