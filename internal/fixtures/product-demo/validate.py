#!/usr/bin/env python3
"""Read-only deterministic validation for the private product-demo corpus."""

import argparse
import ast
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EPOCH = "2026-07-23T00:00:00Z"
TICK_MS = 250
FORMAT_VERSION = "1.0.0"
MAX_DOCUMENT_DEPTH = 64
TOOL_SUMMARY_MAX_CHARS = 160
TOOL_SAFE_SUMMARY = "Synthetic result with no external content."
EXPECTED_ID_POLICY = {
    "prefix": "fx_",
    "qualifiedThreadTemplate": "{sourceId}:{threadId}",
    "qualifiedRunTemplate": "{sourceId}:{threadId}:{runId}",
}
SEMANTIC_MATRIX_PATH = "negative/semantic-matrix.json"
EXPECTED_SEMANTIC_PROBE_COUNT = 141
SEMANTIC_MATRIX_SHA256 = (
    "c4fa961807d465bb57a253c88648442678088a28f79b35946889a00bb3ff3a6d"
)
EXPECTED_CASE_PATHS = [
    "cases/start.json",
    "cases/content.json",
    "cases/tool.json",
    "cases/ordered-interrupt.json",
    "cases/checkpoint.json",
    "cases/reconnect.json",
    "cases/replay.json",
    "cases/logical-delay.json",
    "cases/completion.json",
    "cases/unknown.json",
    "cases/malformed-input.json",
    "cases/partial-failure.json",
    "cases/source-collision.json",
]
EXPECTED_CATEGORIES = [
    "start",
    "content",
    "tool",
    "ordered-interrupt",
    "checkpoint",
    "reconnect",
    "replay",
    "logical-delay",
    "completion",
    "unknown",
    "malformed-input",
    "partial-failure",
    "source-collision",
]
EXPECTED_NEGATIVE_PATHS = [
    "negative/invalid-schema.json",
    "negative/invalid-schema-expected-type.json",
    "negative/invalid-schema-payload-type.json",
    "negative/invalid-schema-semantic-list.json",
    "negative/invalid-schema-unhashable-decision.json",
    "negative/invalid-schema-semantic-required.json",
    "negative/invalid-schema-clock-range.json",
    "negative/invalid-id.json",
    "negative/invalid-record-source-scope.json",
    "negative/invalid-record-thread-scope.json",
    "negative/invalid-record-run-scope.json",
    "negative/invalid-clock.json",
    "negative/invalid-order.json",
    "negative/invalid-capability.json",
    "negative/invalid-tool-trust.json",
    "negative/invalid-tool-bounded.json",
    "negative/invalid-tool-correlation.json",
    "negative/invalid-tool-expected-correlation.json",
    "negative/invalid-tool-raw-expectation.json",
    "negative/invalid-tool-raw-body.json",
    "negative/invalid-interrupt.json",
    "negative/invalid-interrupt-decisions-present.json",
    "negative/invalid-interrupt-resume-payload.json",
    "negative/invalid-interrupt-accepted.json",
    "negative/invalid-interrupt-approved-alias.json",
    "negative/invalid-interrupt-selected-option.json",
    "negative/invalid-interrupt-decision.json",
    "negative/invalid-interrupt-decision-order.json",
    "negative/invalid-interrupt-decision-split.json",
    "negative/invalid-source-collision.json",
    "negative/invalid-partial-source-qualification.json",
    "negative/invalid-hash.json",
    "negative/invalid-scrub.json",
    "negative/invalid-scrub-endpoint.json",
    "negative/invalid-scrub-api-key.json",
    "negative/invalid-scrub-secret.json",
    "negative/invalid-scrub-basic.json",
    "negative/invalid-scrub-basic-short.json",
    "negative/invalid-scrub-basic-unpadded.json",
    "negative/invalid-scrub-path.json",
    "negative/invalid-scrub-identity.json",
    "negative/invalid-scrub-actor.json",
    "negative/invalid-scrub-current-actor.json",
    "negative/invalid-scrub-requested-actor.json",
    "negative/invalid-scrub-identity-field.json",
    "negative/invalid-scrub-repository.json",
    "negative/invalid-network.json",
    "negative/invalid-network-host.json",
    "negative/invalid-network-ip.json",
    "negative/invalid-network-exempt-descendant.json",
    "negative/invalid-network-exempt-case-path.json",
    "negative/invalid-network-exempt-schema-enum.json",
    "negative/invalid-expectation.json",
    "negative/invalid-logical-delay.json",
    "negative/invalid-logical-delay-visibility.json",
]
EXPECTED_RULE_CODES = [
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_ID_PREFIX",
    "FIXTURE_ID_QUALIFICATION",
    "FIXTURE_ID_QUALIFICATION",
    "FIXTURE_ID_QUALIFICATION",
    "FIXTURE_CLOCK_DERIVATION",
    "FIXTURE_ORDER_SEQUENCE",
    "FIXTURE_CAPABILITY_EVIDENCE",
    "FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY",
    "FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY",
    "FIXTURE_EXPECTATION_TOOL_CORRELATION",
    "FIXTURE_EXPECTATION_TOOL_CORRELATION",
    "FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY",
    "FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_DECISION_VALUE",
    "FIXTURE_INTERRUPT_DECISION_VALUE",
    "FIXTURE_INTERRUPT_DECISION_VALUE",
    "FIXTURE_ID_SOURCE_COLLISION",
    "FIXTURE_EXPECTATION_PARTIAL_FAILURE",
    "FIXTURE_HASH_MISMATCH",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_UNSAFE_PATH",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_EXPECTATION_REPLAY_DEDUPE",
    "FIXTURE_CLOCK_DELAY_MISMATCH",
    "FIXTURE_EXPECTATION_DELAY_VISIBILITY",
]
SCHEMA_PATHS = [
    "schema/fixture-envelope.json",
    "schema/capability-manifest.json",
]
MANIFEST_PATHS = [
    "manifests/fixture-source.json",
    "manifests/gated-runtimes.json",
]
EXPECTED_CAPABILITY_NAMES = {
    "fx_manifest_fixture_source": [
        "normalized-presentation",
        "replay-presentation",
        "interrupt-submission",
        "checkpoint-fork",
        "cancellation",
        "specialized-subagents",
        "artifact-operations",
    ],
    "fx_manifest_gated_runtimes": [
        "classic-stream-contract",
        "mda-runtime",
        "fleet-runtime",
        "browser-direct-stream",
        "permission-probe-example",
    ],
}
VALID_CAPABILITY_STATES = {
    "available",
    "unavailable",
    "gated",
    "permission-denied",
    "unknown",
}
VALIDATOR_IMPORT_ALLOWLIST = [
    "argparse",
    "ast",
    "copy",
    "hashlib",
    "json",
    "pathlib",
    "re",
    "sys",
    "unicodedata",
]
PURITY_WRITE_CALLS = {
    "chmod",
    "hardlink_to",
    "link_to",
    "lchmod",
    "mkdir",
    "open",
    "remove",
    "rename",
    "rmdir",
    "symlink_to",
    "touch",
    "unlink",
    "write",
    "write_bytes",
    "write_text",
    "writelines",
}
PURITY_PROCESS_CALLS = {
    "__import__",
    "call",
    "check_call",
    "check_output",
    "compile",
    "eval",
    "exec",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "fork",
    "popen",
    "Popen",
    "posix_spawn",
    "posix_spawnp",
    "run",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "system",
}
PURITY_PROCESS_IMPORTS = {
    "asyncio",
    "multiprocessing",
    "os",
    "pty",
    "subprocess",
}
PURITY_DYNAMIC_CALLS = {
    "delattr",
    "getattr",
    "globals",
    "locals",
    "setattr",
    "vars",
}
PURITY_DYNAMIC_ATTRIBUTES = {
    "__class__",
    "__dict__",
    "__getattr__",
    "__getattribute__",
    "__globals__",
    "__mro__",
    "__subclasses__",
}
PURITY_NETWORK_CALLS = {
    "connect",
    "connect_ex",
    "create_connection",
    "create_server",
    "open_connection",
    "request",
    "send",
    "sendall",
    "socket",
    "start_server",
    "urlopen",
}
PURITY_NETWORK_IMPORTS = {
    "aiohttp",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "smtplib",
    "socket",
    "telnetlib",
    "urllib",
}
PURITY_ENVIRONMENT_CALLS = {
    "expanduser",
    "getenv",
    "get_exec_path",
    "home",
}
PURITY_WALL_CLOCK_CALLS = {
    "ctime",
    "gmtime",
    "localtime",
    "monotonic",
    "monotonic_ns",
    "now",
    "perf_counter",
    "perf_counter_ns",
    "sleep",
    "strftime",
    "time",
    "time_ns",
    "today",
    "utcnow",
    "wait",
    "wait_for",
}
FORBIDDEN_FIELD_FRAGMENTS = (
    "accesskey",
    "apikey",
    "authref",
    "authorization",
    "callbackurl",
    "cookie",
    "credential",
    "endpoint",
    "hostname",
    "password",
    "privatekey",
    "repository",
    "secret",
    "serviceurl",
    "signedurl",
    "token",
    "webhookurl",
)
IDENTITY_FIELD_FRAGMENTS = ("actor", "email", "identity", "owner", "user")
EXTERNAL_SCHEME_RE = re.compile(
    r"(?<![a-z0-9_])[a-z][a-z0-9+.-]*://",
    re.IGNORECASE,
)
GENERIC_URI_SCHEME_RE = re.compile(
    r"(?<![a-z0-9_])[a-z][a-z0-9+.-]*:",
    re.IGNORECASE,
)
EXTERNAL_HOST_RE = re.compile(
    r"(?<![a-z0-9_@-])"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}(?::[0-9]{1,5})?(?![a-z0-9_-])",
    re.IGNORECASE,
)
IP_ADDRESS_RE = re.compile(
    r"(?<![a-z0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![a-z0-9])|"
    r"(?<![a-z0-9])(?:[a-f0-9]{0,4}:){2,}[a-f0-9]{0,4}(?![a-z0-9])",
    re.IGNORECASE,
)
LOCAL_OR_NUMERIC_HOST_RE = re.compile(
    r"(?<![a-z0-9_-])(?:"
    r"localhost\.?(?::[0-9]{1,5})?"
    r"|0x[0-9a-f]{7,8}(?::[0-9]{1,5})?"
    r"|0[0-7]{10,11}(?::[0-9]{1,5})?"
    r"|[0-9]{8,10}(?::[0-9]{1,5})?"
    r")(?=[/:]|$)",
    re.IGNORECASE,
)
ABBREVIATED_OR_OCTAL_IP_RE = re.compile(
    r"(?<![a-z0-9])(?:"
    r"(?:[0-9]{1,3}\.){1,2}[0-9]{1,3}"
    r"|(?:[0-9]{1,4}\.){3}[0-9]{1,4}"
    r")(?=[:/])",
    re.IGNORECASE,
)
UNSAFE_PATH_RE = re.compile(
    r"(?:^|[\\/])\.\.(?:[\\/]|$)|^(?:~[\\/]|/|[a-z]:[\\/]|\\\\)",
    re.IGNORECASE,
)
REAL_IDENTITY_RE = re.compile(
    r"(?:[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|"
    r"(?:git@|github(?:usercontent)?\.com|gitlab\.com|bitbucket\.org))",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?:basic\s+[a-z0-9+/]{2,}={0,2}(?![a-z0-9+/=])|"
    r"bearer\s+[a-z0-9._~+/-]+=*|"
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----|"
    r"(?:sk(?:-proj)?[-_]|gh[opsu][-_]|xox[abprs][-_])[a-z0-9_-]{8,}|"
    r"github_pat_[a-z0-9_]{8,}|"
    r"AKIA[A-Z0-9]{16}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,})",
    re.IGNORECASE,
)
VALID_HITL_DECISIONS = ("approve", "edit", "reject", "respond")
EXPECTED_SCOPE_IDENTITIES = {
    "start": ("fx_source_alpha", "fx_thread_start", "fx_run_start"),
    "content": ("fx_source_alpha", "fx_thread_content", "fx_run_content"),
    "tool": ("fx_source_alpha", "fx_thread_tool", "fx_run_tool"),
    "ordered-interrupt": (
        "fx_source_alpha",
        "fx_thread_interrupt",
        "fx_run_interrupt",
    ),
    "checkpoint": (
        "fx_source_alpha",
        "fx_thread_checkpoint",
        "fx_run_checkpoint",
    ),
    "reconnect": (
        "fx_source_alpha",
        "fx_thread_reconnect",
        "fx_run_reconnect",
    ),
    "replay": ("fx_source_alpha", "fx_thread_replay", "fx_run_replay"),
    "logical-delay": ("fx_source_alpha", "fx_thread_delay", "fx_run_delay"),
    "completion": (
        "fx_source_alpha",
        "fx_thread_completion",
        "fx_run_completion",
    ),
    "unknown": ("fx_source_alpha", "fx_thread_unknown", "fx_run_unknown"),
    "malformed-input": (
        "fx_source_alpha",
        "fx_thread_malformed",
        "fx_run_malformed",
    ),
    "partial-failure": (
        "fx_source_alpha",
        "fx_thread_partial",
        "fx_run_partial",
    ),
    "source-collision": (
        "fx_source_alpha",
        "fx_thread_shared_external",
        "fx_run_shared_external",
    ),
}


class DuplicateKeyError(ValueError):
    pass


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def read_bytes(relative_path):
    path = ROOT / relative_path
    resolved = path.resolve()
    if ROOT != resolved and ROOT not in resolved.parents:
        raise ValueError(f"path escapes corpus root: {relative_path}")
    return path.read_bytes()


def read_json(relative_path):
    return json.loads(
        read_bytes(relative_path).decode("utf-8"),
        object_pairs_hook=_object_no_duplicates,
    )


def canonical_json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _strict_json_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return (
            set(left) == set(right)
            and all(_strict_json_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, list):
        return (
            len(left) == len(right)
            and all(
                _strict_json_equal(left_item, right_item)
                for left_item, right_item in zip(left, right)
            )
        )
    return left == right


def _normalize_security_text(value):
    return unicodedata.normalize("NFKC", value).translate(
        str.maketrans(
            {
                "\u200b": None,
                "\u200c": None,
                "\u200d": None,
                "\u2060": None,
                "\ufeff": None,
                "\u2010": "-",
                "\u2011": "-",
                "\u2012": "-",
                "\u2013": "-",
                "\u2014": "-",
                "\u2212": "-",
                "\u2044": "/",
                "\u2215": "/",
                "\u29f5": "\\",
                "\u3002": ".",
                "\uff0e": ".",
                "\uff61": ".",
            }
        )
    )


def tick_timestamp(tick):
    total_ms = tick * TICK_MS
    seconds, milliseconds = divmod(total_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours >= 24:
        raise ValueError("fixture tick exceeds supported deterministic day")
    return f"2026-07-23T{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}Z"


def _walk(value, path=""):
    stack = [(path, value)]
    while stack:
        current_path, current = stack.pop()
        yield current_path, current
        if isinstance(current, dict):
            for key in sorted(current, reverse=True):
                stack.append((f"{current_path}/{key}", current[key]))
        elif isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append((f"{current_path}/{index}", current[index]))


def _exceeds_max_document_depth(value):
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_DOCUMENT_DEPTH:
            return True
        if isinstance(current, dict):
            stack.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
    return False


def scrub_diagnostics(value):
    diagnostics = []
    for path, item in _walk(value):
        if isinstance(item, dict):
            for key, child in item.items():
                normalized_key = unicodedata.normalize("NFKC", key).casefold()
                normalized = re.sub(r"[^a-z0-9]", "", normalized_key)
                if not key.isascii():
                    diagnostics.append(("FIXTURE_SCRUB_REAL_IDENTITY", f"{path}/{key}"))
                if any(fragment in normalized for fragment in FORBIDDEN_FIELD_FRAGMENTS):
                    diagnostics.append(("FIXTURE_SCRUB_FORBIDDEN_FIELD", f"{path}/{key}"))
                if (
                    any(fragment in normalized for fragment in IDENTITY_FIELD_FRAGMENTS)
                    and (
                        not isinstance(child, str)
                        or not child.startswith("fx_")
                    )
                ):
                    diagnostics.append(("FIXTURE_SCRUB_REAL_IDENTITY", f"{path}/{key}"))
        elif isinstance(item, str):
            normalized_item = _normalize_security_text(item)
            if SECRET_VALUE_RE.search(normalized_item):
                diagnostics.append(("FIXTURE_SCRUB_SECRET_VALUE", path))
            if UNSAFE_PATH_RE.search(normalized_item):
                diagnostics.append(("FIXTURE_SCRUB_UNSAFE_PATH", path))
            if REAL_IDENTITY_RE.search(normalized_item):
                diagnostics.append(("FIXTURE_SCRUB_REAL_IDENTITY", path))
    return diagnostics


def _expected_hashed_assets():
    return {
        "corpus.json",
        "validate.py",
        "negative/matrix.json",
        SEMANTIC_MATRIX_PATH,
        *SCHEMA_PATHS,
        *MANIFEST_PATHS,
        *EXPECTED_CASE_PATHS,
        *EXPECTED_NEGATIVE_PATHS,
    }


def _is_allowed_internal_reference(path, value):
    if path == "/$id":
        return value in {
            "urn:deep-work:fixture:product-demo:envelope:1",
            "urn:deep-work:fixture:product-demo:capability-manifest:1",
        }
    if path == "/negativeMatrixPath":
        return value == "negative/matrix.json"
    if path == "/semanticMatrixPath":
        return value == SEMANTIC_MATRIX_PATH
    if path == "/capabilityManifestRef":
        return value in MANIFEST_PATHS
    indexed_references = (
        (r"/casePaths/[0-9]+", EXPECTED_CASE_PATHS),
        (r"/schemaPaths/[0-9]+", SCHEMA_PATHS),
        (r"/manifestPaths/[0-9]+", MANIFEST_PATHS),
        (r"/hashedAssets/[0-9]+", _expected_hashed_assets()),
        (r"/negativePaths/[0-9]+", EXPECTED_NEGATIVE_PATHS),
        (r"/properties/capabilityManifestRef/enum/[0-9]+", MANIFEST_PATHS),
    )
    return any(
        re.fullmatch(pattern, path) is not None and value in allowed
        for pattern, allowed in indexed_references
    )


def network_diagnostics(value):
    diagnostics = []
    for path, item in _walk(value):
        if not isinstance(item, str):
            continue
        if _is_allowed_internal_reference(path, item):
            continue
        normalized_item = _normalize_security_text(item)
        if (
            EXTERNAL_SCHEME_RE.search(normalized_item)
            or GENERIC_URI_SCHEME_RE.search(normalized_item)
            or EXTERNAL_HOST_RE.search(normalized_item)
            or IP_ADDRESS_RE.search(normalized_item)
            or LOCAL_OR_NUMERIC_HOST_RE.search(normalized_item)
            or ABBREVIATED_OR_OCTAL_IP_RE.search(normalized_item)
        ):
            diagnostics.append(("FIXTURE_NETWORK_EXTERNAL_URL", path))
    return diagnostics


def _matches_schema_type(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def structural_schema_diagnostics(value, schema, path="$"):
    diagnostics = []
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_schema_type(value, expected_type):
        return [f"{path}:type"]
    if "const" in schema and not _strict_json_equal(value, schema["const"]):
        diagnostics.append(f"{path}:const")
    if "enum" in schema and not any(
        _strict_json_equal(value, member) for member in schema["enum"]
    ):
        diagnostics.append(f"{path}:enum")
    if isinstance(value, str) and "pattern" in schema:
        if re.fullmatch(schema["pattern"], value) is None:
            diagnostics.append(f"{path}:pattern")
    if isinstance(value, dict):
        required = schema.get("required", [])
        diagnostics.extend(
            f"{path}/{key}:required" for key in required if key not in value
        )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            diagnostics.extend(
                f"{path}/{key}:additional" for key in value if key not in properties
            )
        for key, child_schema in properties.items():
            if key in value:
                diagnostics.extend(
                    structural_schema_diagnostics(
                        value[key],
                        child_schema,
                        f"{path}/{key}",
                    )
                )
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            diagnostics.append(f"{path}:minItems")
        if schema.get("uniqueItems") and len({canonical_json_bytes(item) for item in value}) != len(value):
            diagnostics.append(f"{path}:uniqueItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                diagnostics.extend(
                    structural_schema_diagnostics(
                        item,
                        item_schema,
                        f"{path}/{index}",
                    )
                )
    return diagnostics


def _has_unsafe_structural_shape(diagnostics):
    return any(
        diagnostic.endswith((":type", ":required", ":additional", ":minItems"))
        for diagnostic in diagnostics
    )


def _required_case_fields():
    return {
        "formatVersion",
        "caseId",
        "category",
        "synthetic",
        "evidenceClass",
        "clock",
        "scope",
        "capabilityManifestRef",
        "records",
        "expected",
        "provenance",
    }


def _validate_manifest(manifest):
    if _exceeds_max_document_depth(manifest):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_diagnostics = structural_schema_diagnostics(
        manifest,
        read_json("schema/capability-manifest.json"),
    )
    if _has_unsafe_structural_shape(structural_diagnostics):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_invalid = bool(structural_diagnostics)
    required = {
        "formatVersion",
        "manifestId",
        "synthetic",
        "runtimeKind",
        "capabilities",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if manifest["formatVersion"] != FORMAT_VERSION or manifest["synthetic"] is not True:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if not isinstance(manifest["manifestId"], str) or not manifest["manifestId"].startswith("fx_manifest_"):
        return ["FIXTURE_ID_PREFIX"]
    diagnostics = []
    expected_names = EXPECTED_CAPABILITY_NAMES.get(manifest["manifestId"])
    observed_names = [
        capability.get("name") if isinstance(capability, dict) else None
        for capability in manifest["capabilities"]
    ]
    if observed_names != expected_names:
        diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
    seen = set()
    capability_required = {
        "name",
        "state",
        "observedAt",
        "adapterVersion",
        "contractVersion",
        "evidenceClass",
        "reason",
    }
    for capability in manifest["capabilities"]:
        if not isinstance(capability, dict) or set(capability) != capability_required:
            diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
            continue
        name = capability["name"]
        if name in seen:
            diagnostics.append("FIXTURE_CAPABILITY_DUPLICATE")
        seen.add(name)
        if capability["state"] not in VALID_CAPABILITY_STATES:
            diagnostics.append("FIXTURE_CAPABILITY_STATE")
        if capability["observedAt"] != tick_timestamp(0):
            diagnostics.append("FIXTURE_CLOCK_DERIVATION")
        if capability["evidenceClass"] != "fixture":
            diagnostics.append("FIXTURE_CAPABILITY_EVIDENCE")
        if capability["state"] == "available" and manifest["runtimeKind"] != "fixture":
            diagnostics.append("FIXTURE_CAPABILITY_RUNTIME_AUTHORITY")
        if capability["state"] != "available" and not capability["reason"]:
            diagnostics.append("FIXTURE_CAPABILITY_REASON")
    diagnostics.extend(code for code, _ in scrub_diagnostics(manifest))
    diagnostics.extend(code for code, _ in network_diagnostics(manifest))
    if structural_invalid and not diagnostics:
        diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
    return sorted(set(diagnostics))


def validate_manifest(manifest):
    try:
        return _validate_manifest(manifest)
    except (
        AttributeError,
        IndexError,
        KeyError,
        OverflowError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]


def _validate_scope(scope):
    required = {
        "tenantId",
        "workspaceId",
        "sourceId",
        "threadId",
        "runId",
        "qualifiedThreadKey",
        "qualifiedRunKey",
    }
    if not isinstance(scope, dict) or set(scope) != required:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if any(not isinstance(scope[key], str) or not scope[key].startswith("fx_") for key in ("tenantId", "workspaceId", "sourceId", "threadId", "runId")):
        return ["FIXTURE_ID_PREFIX"]
    expected_thread = f"{scope['sourceId']}:{scope['threadId']}"
    expected_run = f"{expected_thread}:{scope['runId']}"
    if scope["qualifiedThreadKey"] != expected_thread or scope["qualifiedRunKey"] != expected_run:
        return ["FIXTURE_ID_QUALIFICATION"]
    return []


def _validate_fixed_case_identity(case):
    category = case["category"]
    expected_case_id = f"fx_case_{str.replace(category, '-', '_')}"
    expected_identity = EXPECTED_SCOPE_IDENTITIES.get(category)
    if expected_identity is None or case["caseId"] != expected_case_id:
        return ["FIXTURE_ID_FIXED"]
    source_id, thread_id, run_id = expected_identity
    expected_scope = {
        "tenantId": "fx_tenant_alpha",
        "workspaceId": "fx_workspace_alpha",
        "sourceId": source_id,
        "threadId": thread_id,
        "runId": run_id,
        "qualifiedThreadKey": f"{source_id}:{thread_id}",
        "qualifiedRunKey": f"{source_id}:{thread_id}:{run_id}",
    }
    if not _strict_json_equal(case["scope"], expected_scope):
        return ["FIXTURE_ID_FIXED"]
    return []


def _canonical_record(
    case,
    *,
    record_id,
    durable_event_id,
    sequence,
    tick,
    kind,
    payload,
    identity=None,
):
    source_id, thread_id, run_id = identity or (
        case["scope"]["sourceId"],
        case["scope"]["threadId"],
        case["scope"]["runId"],
    )
    return {
        "recordId": record_id,
        "durableEventId": durable_event_id,
        "sequence": sequence,
        "tick": tick,
        "observedAt": tick_timestamp(tick),
        "kind": kind,
        "sourceId": source_id,
        "threadId": thread_id,
        "runId": run_id,
        "payload": payload,
    }


def _validate_start_case(case):
    records = case["records"]
    expected = case["expected"]
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_start",
            durable_event_id="fx_event_start",
            sequence=1,
            tick=1,
            kind="fixture-start",
            payload={"status": "active"},
        )
    ]
    canonical_expected = {
        "orderedRecordIds": ["fx_record_start"],
        "status": "active",
        "providerCreateCall": False,
    }
    if (
        not _strict_json_equal(records, canonical_records)
        or not _strict_json_equal(expected, canonical_expected)
        or case["clock"]["observedTick"] != 1
    ):
        return ["FIXTURE_EXPECTATION_START"]
    return []


def _validate_content_case(case):
    records = case["records"]
    expected = case["expected"]
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_content_a",
            durable_event_id="fx_event_content_a",
            sequence=1,
            tick=2,
            kind="fixture-content",
            payload={
                "chunkIndex": 0,
                "text": "Synthetic visible content.",
                "trust": "untrusted",
            },
        ),
        _canonical_record(
            case,
            record_id="fx_record_content_b",
            durable_event_id="fx_event_content_b",
            sequence=2,
            tick=3,
            kind="fixture-content",
            payload={
                "chunkIndex": 1,
                "text": "Synthetic bounded continuation.",
                "trust": "untrusted",
            },
        ),
    ]
    canonical_expected = {
        "orderedRecordIds": [
            "fx_record_content_a",
            "fx_record_content_b",
        ],
        "visibleTextOrder": [
            "Synthetic visible content.",
            "Synthetic bounded continuation.",
        ],
        "privateReasoningPresent": False,
    }
    if (
        not _strict_json_equal(records, canonical_records)
        or not _strict_json_equal(expected, canonical_expected)
        or case["clock"]["observedTick"] != 3
    ):
        return ["FIXTURE_EXPECTATION_CONTENT"]
    return []


def _validate_checkpoint_case(case):
    records = case["records"]
    expected = case["expected"]
    checkpoint_id = "fx_checkpoint_alpha"
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_checkpoint",
            durable_event_id="fx_event_checkpoint",
            sequence=1,
            tick=12,
            kind="fixture-checkpoint-observed",
            payload={
                "checkpointId": checkpoint_id,
                "qualifiedCheckpointKey": (
                    f"{case['scope']['sourceId']}:{case['scope']['threadId']}:"
                    f"{checkpoint_id}"
                ),
            },
        )
    ]
    canonical_expected = {
        "orderedRecordIds": ["fx_record_checkpoint"],
        "checkpointId": checkpoint_id,
        "forkCapabilityState": "gated",
        "forkPerformed": False,
    }
    if (
        not _strict_json_equal(records, canonical_records)
        or not _strict_json_equal(expected, canonical_expected)
        or case["clock"]["observedTick"] != 12
    ):
        return ["FIXTURE_EXPECTATION_CHECKPOINT"]
    return []


def _validate_reconnect_case(case):
    records = case["records"]
    expected = case["expected"]
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_reconnect_durable",
            durable_event_id="fx_event_reconnect_durable",
            sequence=1,
            tick=18,
            kind="fixture-content",
            payload={
                "text": "Last durable synthetic projection.",
                "trust": "untrusted",
            },
        ),
        _canonical_record(
            case,
            record_id="fx_record_reconnect_boundary",
            durable_event_id="fx_event_reconnect_boundary",
            sequence=2,
            tick=20,
            kind="fixture-recovery-boundary",
            payload={
                "freshness": "reconnecting",
                "applicationRecoveryMarker": "fx_recovery_boundary_alpha",
            },
        ),
    ]
    canonical_expected = {
        "orderedRecordIds": [
            "fx_record_reconnect_durable",
            "fx_record_reconnect_boundary",
        ],
        "retainedRecordIds": ["fx_record_reconnect_durable"],
        "freshness": "reconnecting",
        "terminalInferred": False,
        "cancelInferred": False,
        "providerRecoveryMechanism": "unspecified",
    }
    if (
        not _strict_json_equal(records, canonical_records)
        or not _strict_json_equal(expected, canonical_expected)
        or case["clock"]["observedTick"] != 20
    ):
        return ["FIXTURE_EXPECTATION_RECONNECT"]
    return []


def _validate_logical_delay(case):
    expected = case["expected"]
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_delay_start",
            durable_event_id="fx_event_delay_start",
            sequence=1,
            tick=40,
            kind="fixture-start",
            payload={"status": "active"},
        ),
        _canonical_record(
            case,
            record_id="fx_record_delay_content",
            durable_event_id="fx_event_delay_content",
            sequence=2,
            tick=44,
            kind="fixture-content",
            payload={
                "text": "Synthetic logically delayed content.",
                "trust": "untrusted",
            },
        ),
        _canonical_record(
            case,
            record_id="fx_record_delay_complete",
            durable_event_id="fx_event_delay_complete",
            sequence=3,
            tick=45,
            kind="fixture-completion",
            payload={"status": "completed", "authoritative": "fixture"},
        ),
    ]
    if (
        not _strict_json_equal(case["records"], canonical_records)
        or case["clock"]["observedTick"] != 45
    ):
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    exact_tick_contract = {
        "enqueueTick": 41,
        "delayTicks": 3,
        "lastPreReleaseTick": 43,
        "releaseTick": 44,
        "completionTick": 45,
    }
    if any(
        type(expected.get(field)) is not int
        or expected[field] != exact_value
        for field, exact_value in exact_tick_contract.items()
    ):
        return ["FIXTURE_CLOCK_DELAY_MISMATCH"]
    if expected["enqueueTick"] + expected["delayTicks"] != expected["releaseTick"]:
        return ["FIXTURE_CLOCK_DELAY_MISMATCH"]
    if expected["lastPreReleaseTick"] != expected["releaseTick"] - 1:
        return ["FIXTURE_CLOCK_DELAY_MISMATCH"]
    timestamp_fields = {
        "enqueueAt": expected["enqueueTick"],
        "lastPreReleaseAt": expected["lastPreReleaseTick"],
        "releaseAt": expected["releaseTick"],
        "completionAt": expected["completionTick"],
    }
    if any(expected[field] != tick_timestamp(tick) for field, tick in timestamp_fields.items()):
        return ["FIXTURE_CLOCK_DERIVATION"]
    visibility = expected["visibleRecordIdsByTick"]
    exact_visibility = {
        "40": ["fx_record_delay_start"],
        "43": ["fx_record_delay_start"],
        "44": ["fx_record_delay_start", "fx_record_delay_content"],
        "45": [
            "fx_record_delay_start",
            "fx_record_delay_content",
            "fx_record_delay_complete",
        ],
    }
    if visibility != exact_visibility:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["releaseOrder"] != exact_visibility["45"]:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["contentVisibleExactlyOnceAtRelease"] is not True:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["wallClockClaim"] is not False:
        return ["FIXTURE_CLOCK_WALL_TIME_CLAIM"]
    canonical_expected = {
        "enqueueTick": 41,
        "delayTicks": 3,
        "lastPreReleaseTick": 43,
        "releaseTick": 44,
        "completionTick": 45,
        "enqueueAt": "2026-07-23T00:00:10.250Z",
        "lastPreReleaseAt": "2026-07-23T00:00:10.750Z",
        "releaseAt": "2026-07-23T00:00:11.000Z",
        "completionAt": "2026-07-23T00:00:11.250Z",
        "visibleRecordIdsByTick": exact_visibility,
        "releaseOrder": exact_visibility["45"],
        "contentVisibleExactlyOnceAtRelease": True,
        "wallClockClaim": False,
    }
    if not _strict_json_equal(expected, canonical_expected):
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    return []


def _validate_tool_case(case):
    records = case["records"]
    expected = case["expected"]
    if (
        len(records) != 2
        or [record["kind"] for record in records]
        != ["fixture-tool-start", "fixture-tool-result"]
        or set(expected)
        != {
            "orderedRecordIds",
            "correlatedToolCallId",
            "rawToolBodyPresent",
        }
    ):
        return ["FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY"]
    start_payload = records[0]["payload"]
    result_payload = records[1]["payload"]
    if (
        not isinstance(start_payload, dict)
        or set(start_payload) != {"toolCallId", "displayName", "trust"}
        or not isinstance(result_payload, dict)
        or set(result_payload)
        != {"toolCallId", "summary", "trust", "bounded"}
        or not isinstance(start_payload["displayName"], str)
        or not start_payload["displayName"]
        or not isinstance(result_payload["summary"], str)
        or not result_payload["summary"]
        or len(result_payload["summary"]) > TOOL_SUMMARY_MAX_CHARS
        or result_payload["summary"] != TOOL_SAFE_SUMMARY
        or result_payload["summary"].lstrip().startswith(("{", "["))
        or start_payload["trust"] != "untrusted"
        or result_payload["trust"] != "untrusted"
        or result_payload["bounded"] is not True
        or expected["rawToolBodyPresent"] is not False
    ):
        return ["FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY"]
    correlation_ids = (
        start_payload["toolCallId"],
        result_payload["toolCallId"],
        expected["correlatedToolCallId"],
    )
    if (
        any(
            not isinstance(value, str) or not value.startswith("fx_")
            for value in correlation_ids
        )
        or len(set(correlation_ids)) != 1
    ):
        return ["FIXTURE_EXPECTATION_TOOL_CORRELATION"]
    canonical_records = [
        _canonical_record(
            case,
            record_id="fx_record_tool_start",
            durable_event_id="fx_event_tool_start",
            sequence=1,
            tick=4,
            kind="fixture-tool-start",
            payload={
                "toolCallId": "fx_tool_call_alpha",
                "displayName": "Synthetic lookup",
                "trust": "untrusted",
            },
        ),
        _canonical_record(
            case,
            record_id="fx_record_tool_result",
            durable_event_id="fx_event_tool_result",
            sequence=2,
            tick=5,
            kind="fixture-tool-result",
            payload={
                "toolCallId": "fx_tool_call_alpha",
                "summary": TOOL_SAFE_SUMMARY,
                "trust": "untrusted",
                "bounded": True,
            },
        ),
    ]
    if (
        not _strict_json_equal(records, canonical_records)
        or case["clock"]["observedTick"] != 5
    ):
        return ["FIXTURE_EXPECTATION_TOOL_TRUST_BOUNDARY"]
    return []


def _semantic_diagnostics(case):
    category = case["category"]
    expected = case["expected"]
    records = case["records"]
    if category == "start":
        return _validate_start_case(case)
    if category == "content":
        return _validate_content_case(case)
    if category == "tool":
        return _validate_tool_case(case)
    if category == "ordered-interrupt":
        if len(records) != 1 or records[0]["kind"] != "fixture-interrupt":
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        payload = records[0]["payload"]
        expected_fields = {
            "orderedRecordIds",
            "actionRequestOrder",
            "reviewConfigOrder",
            "positionalAlignment",
            "repeatedActionNamesPreserved",
            "documentedDecisionVocabulary",
            "acceptedDecisionPresent",
            "resumePayloadPresent",
            "submissionCapabilityState",
        }
        payload_fields = {
            "interruptId",
            "version",
            "actionRequests",
            "reviewConfigs",
        }
        if (
            not isinstance(payload, dict)
            or not payload_fields.issubset(payload)
            or not isinstance(expected, dict)
            or not expected_fields.issubset(expected)
        ):
            return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
        if (
            set(payload) != payload_fields
            or set(expected) != expected_fields
            or payload["interruptId"] != "fx_interrupt_alpha"
            or payload["version"] != "fx_interrupt_version_3"
            or records[0]["recordId"] != "fx_record_interrupt"
            or records[0]["durableEventId"] != "fx_event_interrupt"
            or records[0]["tick"] != 8
            or case["clock"]["observedTick"] != 8
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        requests = payload["actionRequests"]
        configs = payload["reviewConfigs"]
        if not isinstance(requests, list) or not isinstance(configs, list):
            return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
        if any(
            not isinstance(request, dict)
            or set(request) != {"name", "args", "description"}
            or not isinstance(request["name"], str)
            or not isinstance(request["description"], str)
            or not request["description"]
            or not isinstance(request["args"], dict)
            or set(request["args"]) != {"subject"}
            or not isinstance(request["args"]["subject"], str)
            or not request["args"]["subject"].startswith("fx_")
            for request in requests
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        if any(
            not isinstance(config, dict)
            or set(config) != {"actionName", "allowedDecisions"}
            for config in configs
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        request_names = [item.get("name") for item in requests]
        config_names = [item.get("actionName") for item in configs]
        if (
            not requests
            or len(requests) != len(configs)
            or request_names != config_names
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        if request_names != ["review", "review"]:
            return ["FIXTURE_INTERRUPT_REPEATED_NAME"]
        request_subjects = [item["args"]["subject"] for item in requests]
        if (
            expected["actionRequestOrder"] != request_names
            or expected["reviewConfigOrder"] != config_names
            or expected["positionalAlignment"] is not True
            or expected["repeatedActionNamesPreserved"] != request_names
            or request_subjects != ["fx_change_a", "fx_change_b"]
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        for config in configs:
            decisions = config["allowedDecisions"]
            if (
                not isinstance(decisions, list)
                or any(not isinstance(decision, str) for decision in decisions)
            ):
                return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
            if decisions != list(VALID_HITL_DECISIONS):
                return ["FIXTURE_INTERRUPT_DECISION_VALUE"]
        if (
            expected["documentedDecisionVocabulary"]
            != list(VALID_HITL_DECISIONS)
        ):
            return ["FIXTURE_INTERRUPT_DECISION_VALUE"]
        if (
            expected["acceptedDecisionPresent"] is not False
            or expected["resumePayloadPresent"] is not False
            or expected["submissionCapabilityState"] != "gated"
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        canonical_requests = [
            {
                "name": "review",
                "args": {"subject": "fx_change_a"},
                "description": "Review synthetic change A.",
            },
            {
                "name": "review",
                "args": {"subject": "fx_change_b"},
                "description": "Review synthetic change B.",
            },
        ]
        if requests != canonical_requests:
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
    elif category == "checkpoint":
        return _validate_checkpoint_case(case)
    elif category == "reconnect":
        return _validate_reconnect_case(case)
    elif category == "replay":
        seen = set()
        visible = []
        durable = []
        ignored = []
        for record in records:
            event_id = record["durableEventId"]
            if event_id in seen:
                ignored.append(record["recordId"])
            else:
                seen.add(event_id)
                durable.append(event_id)
                visible.append(record["recordId"])
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_replay_a",
                durable_event_id="fx_event_replay_a",
                sequence=1,
                tick=21,
                kind="fixture-content",
                payload={"text": "Synthetic replay item A.", "trust": "untrusted"},
            ),
            _canonical_record(
                case,
                record_id="fx_record_replay_a_duplicate",
                durable_event_id="fx_event_replay_a",
                sequence=2,
                tick=22,
                kind="fixture-content",
                payload={"text": "Synthetic replay item A.", "trust": "untrusted"},
            ),
            _canonical_record(
                case,
                record_id="fx_record_replay_b",
                durable_event_id="fx_event_replay_b",
                sequence=3,
                tick=24,
                kind="fixture-content",
                payload={"text": "Synthetic replay item B.", "trust": "untrusted"},
            ),
        ]
        canonical_expected = {
            "inputRecordIds": [
                "fx_record_replay_a",
                "fx_record_replay_a_duplicate",
                "fx_record_replay_b",
            ],
            "deduplicatedDurableEventIds": [
                "fx_event_replay_a",
                "fx_event_replay_b",
            ],
            "ignoredRecordIds": ["fx_record_replay_a_duplicate"],
            "visibleRecordIds": [
                "fx_record_replay_a",
                "fx_record_replay_b",
            ],
        }
        if (
            not _strict_json_equal(records, canonical_records)
            or not _strict_json_equal(expected, canonical_expected)
            or case["clock"]["observedTick"] != 24
            or expected["deduplicatedDurableEventIds"] != durable
            or expected["ignoredRecordIds"] != ignored
            or expected["visibleRecordIds"] != visible
        ):
            return ["FIXTURE_EXPECTATION_REPLAY_DEDUPE"]
    elif category == "logical-delay":
        return _validate_logical_delay(case)
    elif category == "completion":
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_completion",
                durable_event_id="fx_event_completion",
                sequence=1,
                tick=30,
                kind="fixture-completion",
                payload={"status": "completed", "authoritative": "fixture"},
            )
        ]
        canonical_expected = {
            "orderedRecordIds": ["fx_record_completion"],
            "terminalStatus": "completed",
            "terminalAuthorityRecordId": "fx_record_completion",
            "absenceInfersTerminal": False,
            "timeoutInfersTerminal": False,
            "disconnectInfersTerminal": False,
        }
        if (
            not _strict_json_equal(records, canonical_records)
            or not _strict_json_equal(expected, canonical_expected)
            or case["clock"]["observedTick"] != 30
        ):
            return ["FIXTURE_EXPECTATION_TERMINAL_AUTHORITY"]
    elif category == "source-collision":
        if len(records) != 2:
            return ["FIXTURE_ID_SOURCE_COLLISION"]
        source_ids = [record["sourceId"] for record in records]
        thread_ids = [record["threadId"] for record in records]
        run_ids = [record["runId"] for record in records]
        qualified_threads = [
            f"{record['sourceId']}:{record['threadId']}" for record in records
        ]
        qualified_runs = [
            f"{record['sourceId']}:{record['threadId']}:{record['runId']}"
            for record in records
        ]
        canonical_expected = {
            "orderedRecordIds": [
                "fx_record_collision_alpha",
                "fx_record_collision_beta",
            ],
            "sharedThreadId": "fx_thread_shared_external",
            "sharedRunId": "fx_run_shared_external",
            "distinctQualifiedThreadKeys": qualified_threads,
            "distinctQualifiedRunKeys": qualified_runs,
        }
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_collision_alpha",
                durable_event_id="fx_event_collision_alpha",
                sequence=1,
                tick=38,
                kind="fixture-source-result",
                payload={
                    "qualifiedThreadKey": (
                        "fx_source_alpha:fx_thread_shared_external"
                    ),
                    "qualifiedRunKey": (
                        "fx_source_alpha:fx_thread_shared_external:"
                        "fx_run_shared_external"
                    ),
                },
                identity=(
                    "fx_source_alpha",
                    "fx_thread_shared_external",
                    "fx_run_shared_external",
                ),
            ),
            _canonical_record(
                case,
                record_id="fx_record_collision_beta",
                durable_event_id="fx_event_collision_beta",
                sequence=2,
                tick=39,
                kind="fixture-source-result",
                payload={
                    "qualifiedThreadKey": (
                        "fx_source_beta:fx_thread_shared_external"
                    ),
                    "qualifiedRunKey": (
                        "fx_source_beta:fx_thread_shared_external:"
                        "fx_run_shared_external"
                    ),
                },
                identity=(
                    "fx_source_beta",
                    "fx_thread_shared_external",
                    "fx_run_shared_external",
                ),
            ),
        ]
        if (
            not _strict_json_equal(records, canonical_records)
            or case["clock"]["observedTick"] != 39
            or len(set(source_ids)) != 2
            or [record["kind"] for record in records]
            != ["fixture-source-result", "fixture-source-result"]
            or set(thread_ids) != {expected["sharedThreadId"]}
            or set(run_ids) != {expected["sharedRunId"]}
            or not _strict_json_equal(expected, canonical_expected)
            or expected["distinctQualifiedThreadKeys"] != qualified_threads
            or expected["distinctQualifiedRunKeys"] != qualified_runs
            or any(
                record["payload"]
                != {
                    "qualifiedThreadKey": qualified_threads[index],
                    "qualifiedRunKey": qualified_runs[index],
                }
                for index, record in enumerate(records)
            )
            or case["scope"]["sourceId"] != source_ids[0]
            or case["scope"]["threadId"] != thread_ids[0]
            or case["scope"]["runId"] != run_ids[0]
            or case["scope"]["qualifiedThreadKey"] != qualified_threads[0]
            or case["scope"]["qualifiedRunKey"] != qualified_runs[0]
        ):
            return ["FIXTURE_ID_SOURCE_COLLISION"]
    elif category == "malformed-input":
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_malformed",
                durable_event_id="fx_event_malformed",
                sequence=1,
                tick=34,
                kind="fixture-malformed-input",
                payload={
                    "input": {"upstreamLikeValue": ["unexpected", 7, False]},
                    "safeClassification": "malformed-input",
                    "safeErrorCode": "FIXTURE_INPUT_MALFORMED",
                    "rawBodyRetained": False,
                },
            )
        ]
        canonical_expected = {
            "orderedRecordIds": ["fx_record_malformed"],
            "classification": "malformed-input",
            "safeErrorCode": "FIXTURE_INPUT_MALFORMED",
            "envelopeValid": True,
        }
        if (
            not _strict_json_equal(records, canonical_records)
            or not _strict_json_equal(expected, canonical_expected)
            or case["clock"]["observedTick"] != 34
        ):
            return ["FIXTURE_EXPECTATION_MALFORMED_CLASSIFICATION"]
    elif category == "partial-failure":
        expected_fields = {
            "orderedRecordIds",
            "healthyRecordIds",
            "partialErrorRecordIds",
            "aggregateUsable",
            "failedSourceId",
            "failedThreadId",
            "failedRunId",
            "failedQualifiedThreadKey",
            "failedQualifiedRunKey",
        }
        if len(records) != 2 or set(expected) != expected_fields:
            return ["FIXTURE_EXPECTATION_PARTIAL_FAILURE"]
        healthy, failed = records
        failed_thread_key = f"{failed['sourceId']}:{failed['threadId']}"
        failed_run_key = f"{failed_thread_key}:{failed['runId']}"
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_partial_healthy",
                durable_event_id="fx_event_partial_healthy",
                sequence=1,
                tick=36,
                kind="fixture-source-result",
                payload={
                    "result": "Synthetic healthy source result.",
                    "trust": "untrusted",
                },
            ),
            _canonical_record(
                case,
                record_id="fx_record_partial_error",
                durable_event_id="fx_event_partial_error",
                sequence=2,
                tick=37,
                kind="fixture-source-error",
                payload={
                    "safeErrorCode": "SOURCE_UNAVAILABLE",
                    "safeSummary": "Synthetic source is unavailable.",
                    "sourceQualified": True,
                },
                identity=(
                    "fx_source_beta",
                    "fx_thread_partial_beta",
                    "fx_run_partial_beta",
                ),
            ),
        ]
        if (
            not _strict_json_equal(records, canonical_records)
            or case["clock"]["observedTick"] != 37
            or healthy["kind"] != "fixture-source-result"
            or (
                healthy["sourceId"],
                healthy["threadId"],
                healthy["runId"],
            )
            != (
                case["scope"]["sourceId"],
                case["scope"]["threadId"],
                case["scope"]["runId"],
            )
            or healthy["payload"]
            != {
                "result": "Synthetic healthy source result.",
                "trust": "untrusted",
            }
            or failed["kind"] != "fixture-source-error"
            or failed["sourceId"] != expected["failedSourceId"]
            or failed["threadId"] != expected["failedThreadId"]
            or failed["runId"] != expected["failedRunId"]
            or failed_thread_key != expected["failedQualifiedThreadKey"]
            or failed_run_key != expected["failedQualifiedRunKey"]
            or failed["payload"]
            != {
                "safeErrorCode": "SOURCE_UNAVAILABLE",
                "safeSummary": "Synthetic source is unavailable.",
                "sourceQualified": True,
            }
            or expected["healthyRecordIds"] != [healthy["recordId"]]
            or expected["partialErrorRecordIds"] != [failed["recordId"]]
            or expected["aggregateUsable"] is not True
            or (
                failed["sourceId"],
                failed["threadId"],
                failed["runId"],
            )
            == (
                healthy["sourceId"],
                healthy["threadId"],
                healthy["runId"],
            )
        ):
            return ["FIXTURE_EXPECTATION_PARTIAL_FAILURE"]
    elif category == "unknown":
        canonical_records = [
            _canonical_record(
                case,
                record_id="fx_record_unknown",
                durable_event_id="fx_event_unknown",
                sequence=1,
                tick=32,
                kind="fixture-unknown",
                payload={
                    "originalKind": "fx_unrecognized_kind",
                    "safeSummary": "Unsupported synthetic content preserved as unknown.",
                    "trust": "untrusted",
                },
            )
        ]
        canonical_expected = {
            "orderedRecordIds": ["fx_record_unknown"],
            "classification": "unknown",
            "observable": True,
            "promotedDiscriminator": False,
        }
        if (
            not _strict_json_equal(records, canonical_records)
            or not _strict_json_equal(expected, canonical_expected)
            or case["clock"]["observedTick"] != 32
        ):
            return ["FIXTURE_EXPECTATION_UNKNOWN"]
    else:
        return ["FIXTURE_SCHEMA_CASE_COVERAGE"]
    return []


def _validate_case(case):
    if _exceeds_max_document_depth(case):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_diagnostics = structural_schema_diagnostics(
        case,
        read_json("schema/fixture-envelope.json"),
    )
    if _has_unsafe_structural_shape(structural_diagnostics):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_invalid = bool(structural_diagnostics)
    if not isinstance(case, dict) or set(case) != _required_case_fields():
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if case["formatVersion"] != FORMAT_VERSION or case["synthetic"] is not True or case["evidenceClass"] != "fixture":
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if not isinstance(case["caseId"], str) or not case["caseId"].startswith("fx_case_"):
        return ["FIXTURE_ID_PREFIX"]
    scope_diagnostics = _validate_scope(case["scope"])
    if scope_diagnostics:
        return scope_diagnostics
    fixed_identity_diagnostics = _validate_fixed_case_identity(case)
    if fixed_identity_diagnostics:
        return fixed_identity_diagnostics
    if case["capabilityManifestRef"] not in MANIFEST_PATHS:
        return ["FIXTURE_CAPABILITY_REFERENCE"]
    clock = case["clock"]
    if set(clock) != {"tickEpoch", "tickDurationMs", "observedTick", "observedAt"}:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if clock["tickEpoch"] != EPOCH or clock["tickDurationMs"] != TICK_MS:
        return ["FIXTURE_CLOCK_POLICY"]
    if clock["observedAt"] != tick_timestamp(clock["observedTick"]):
        return ["FIXTURE_CLOCK_DERIVATION"]
    records = case["records"]
    if not isinstance(records, list) or not records:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    record_ids = []
    sequences = []
    prior_tick = -1
    diagnostics = []
    for record in records:
        required = {
            "recordId",
            "durableEventId",
            "sequence",
            "tick",
            "observedAt",
            "kind",
            "sourceId",
            "threadId",
            "runId",
            "payload",
        }
        if not isinstance(record, dict) or set(record) != required:
            diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
            continue
        for id_field in ("recordId", "durableEventId", "sourceId", "threadId", "runId"):
            if not isinstance(record[id_field], str) or not record[id_field].startswith("fx_"):
                diagnostics.append("FIXTURE_ID_PREFIX")
        record_ids.append(record["recordId"])
        sequences.append(record["sequence"])
        if record["tick"] < prior_tick:
            diagnostics.append("FIXTURE_ORDER_TICK")
        prior_tick = record["tick"]
        if record["observedAt"] != tick_timestamp(record["tick"]):
            diagnostics.append("FIXTURE_CLOCK_DERIVATION")
    if case["category"] not in {"partial-failure", "source-collision"} and any(
        (
            record["sourceId"],
            record["threadId"],
            record["runId"],
        )
        != (
            case["scope"]["sourceId"],
            case["scope"]["threadId"],
            case["scope"]["runId"],
        )
        for record in records
    ):
        diagnostics.append("FIXTURE_ID_QUALIFICATION")
    if len(record_ids) != len(set(record_ids)):
        diagnostics.append("FIXTURE_ID_DUPLICATE_RECORD")
    durable_event_ids = [
        record["durableEventId"]
        for record in records
        if isinstance(record, dict) and "durableEventId" in record
    ]
    if (
        case["category"] != "replay"
        and len(durable_event_ids) != len(set(durable_event_ids))
    ):
        diagnostics.append("FIXTURE_EXPECTATION_REPLAY_DEDUPE")
    if sequences != list(range(1, len(records) + 1)):
        diagnostics.append("FIXTURE_ORDER_SEQUENCE")
    if "orderedRecordIds" in case["expected"] and case["expected"]["orderedRecordIds"] != record_ids:
        diagnostics.append("FIXTURE_EXPECTATION_ORDER")
    scrub_codes = [code for code, _ in scrub_diagnostics(case)]
    network_codes = [code for code, _ in network_diagnostics(case)]
    diagnostics.extend(scrub_codes)
    diagnostics.extend(network_codes)
    if not diagnostics:
        diagnostics.extend(_semantic_diagnostics(case))
    if structural_invalid and not diagnostics:
        diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
    return sorted(set(diagnostics))


def validate_case(case):
    try:
        return _validate_case(case)
    except (
        AttributeError,
        IndexError,
        KeyError,
        OverflowError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]


def _validate_case_inventory(cases):
    case_ids = []
    record_ids = []
    for case in cases:
        if not isinstance(case, dict):
            return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
        case_ids.append(case.get("caseId"))
        records = case.get("records")
        if not isinstance(records, list):
            return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
        record_ids.extend(
            record.get("recordId")
            for record in records
            if isinstance(record, dict)
        )
    diagnostics = []
    if len(case_ids) != len(set(case_ids)):
        diagnostics.append("FIXTURE_ID_DUPLICATE_CASE")
    if len(record_ids) != len(set(record_ids)):
        diagnostics.append("FIXTURE_ID_DUPLICATE_RECORD")
    return diagnostics


def _validate_corpus_policy(corpus):
    if not isinstance(corpus, dict) or corpus.get("idPolicy") != EXPECTED_ID_POLICY:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    return []


def _apply_mutation(document, mutation):
    result = copy.deepcopy(document)
    parts = [
        str.replace(str.replace(part, "~1", "/"), "~0", "~")
        for part in mutation["path"].split("/")[1:]
    ]
    parent = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    key = parts[-1]
    if mutation["operation"] == "remove":
        if isinstance(parent, list):
            del parent[int(key)]
        else:
            del parent[key]
    elif mutation["operation"] in {"replace", "add"}:
        if isinstance(parent, list):
            index = int(key)
            if mutation["operation"] == "add" and index == len(parent):
                parent.append(mutation["value"])
            else:
                parent[index] = mutation["value"]
        else:
            parent[key] = mutation["value"]
    else:
        raise ValueError(f"unsupported mutation operation: {mutation['operation']}")
    return result


def _apply_mutations(document, mutations):
    result = document
    for mutation in mutations:
        result = _apply_mutation(result, mutation)
    return result


def diagnose_negative(negative):
    if "probe" in negative:
        probe = negative["probe"]
        if probe.get("kind") == "claimed-asset-hash":
            actual = hashlib.sha256(read_bytes(probe["assetPath"])).hexdigest()
            return [] if actual == probe["claimedSha256"] else ["FIXTURE_HASH_MISMATCH"]
        if probe.get("kind") == "network-diagnostic":
            return sorted({code for code, _ in network_diagnostics(probe["value"])})
        if probe.get("kind") == "scrub-diagnostic":
            return sorted({code for code, _ in scrub_diagnostics(probe["value"])})
        if probe.get("kind") == "validator-purity-snippet":
            purity = _validator_purity_from_source(
                probe["source"].encode("utf-8")
            )
            return _validator_purity_diagnostics(purity)
        if probe.get("kind") == "deep-nesting":
            nested = "fx_leaf"
            for _ in range(probe["depth"]):
                nested = {"child": nested}
            mutated = _apply_mutations(
                read_json(probe["basePath"]),
                [
                    {
                        "operation": "replace",
                        "path": probe["path"],
                        "value": nested,
                    }
                ],
            )
            return validate_case(mutated)
        if probe.get("kind") == "normalized-reverse-records":
            mutated = read_json(probe["basePath"])
            reversed_records = list(reversed(mutated["records"]))
            normalized_records = []
            ordered_ticks = sorted(record["tick"] for record in mutated["records"])
            for sequence, record in enumerate(reversed_records, 1):
                normalized_record = copy.deepcopy(record)
                normalized_record["sequence"] = sequence
                normalized_record["tick"] = ordered_ticks[sequence - 1]
                normalized_record["observedAt"] = tick_timestamp(
                    normalized_record["tick"]
                )
                normalized_records.append(normalized_record)
            mutated["records"] = normalized_records
            mutated["expected"]["orderedRecordIds"] = [
                record["recordId"] for record in normalized_records
            ]
            return validate_case(mutated)
        if probe.get("kind") == "corpus-record-id-collision":
            cases = [read_json(path) for path in EXPECTED_CASE_PATHS]
            target_index = EXPECTED_CASE_PATHS.index(probe["basePath"])
            cases[target_index] = _apply_mutations(
                cases[target_index],
                probe["mutations"],
            )
            return _validate_case_inventory(cases)
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    base_path = negative["basePath"]
    mutations = negative.get("mutations")
    if mutations is None:
        mutations = [negative["mutation"]]
    mutated = _apply_mutations(read_json(base_path), mutations)
    if base_path == "corpus.json":
        return _validate_corpus_policy(mutated)
    if base_path.startswith("manifests/"):
        return validate_manifest(mutated)
    return validate_case(mutated)


def render_hash_manifest():
    corpus = read_json("corpus.json")
    lines = []
    for relative_path in sorted(corpus["hashedAssets"]):
        digest = hashlib.sha256(read_bytes(relative_path)).hexdigest()
        lines.append(f"{digest}  {relative_path}\n")
    return "".join(lines).encode("utf-8")


def corpus_digest():
    return hashlib.sha256(render_hash_manifest()).hexdigest()


def _ast_qualified_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _ast_qualified_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _validator_purity_from_source(source):
    tree = ast.parse(source.decode("utf-8"))
    imports = set()
    import_violations = []
    write_calls = []
    write_references = []
    process_calls = []
    dynamic_accesses = []
    network_calls = []
    environment_reads = []
    wall_clock_reads = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
            if (
                len(node.names) != 1
                or node.names[0].asname is not None
                or "." in node.names[0].name
                or node.names[0].name
                not in set(VALIDATOR_IMPORT_ALLOWLIST) - {"pathlib"}
            ):
                import_violations.append(
                    {"line": node.lineno, "form": ast.dump(node)}
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
            if not (
                node.level == 0
                and node.module == "pathlib"
                and len(node.names) == 1
                and node.names[0].name == "Path"
                and node.names[0].asname is None
            ):
                import_violations.append(
                    {"line": node.lineno, "form": ast.dump(node)}
                )
        elif isinstance(node, ast.Attribute):
            qualified = _ast_qualified_name(node)
            final_name = qualified.rsplit(".", 1)[-1]
            if final_name in PURITY_WRITE_CALLS or (
                final_name == "replace" and qualified != "str.replace"
            ):
                write_references.append(
                    {"line": node.lineno, "reference": qualified}
                )
            if (
                final_name in PURITY_DYNAMIC_ATTRIBUTES
                or qualified == "sys.modules"
            ):
                dynamic_accesses.append(
                    {"line": node.lineno, "access": qualified}
                )
        elif isinstance(node, ast.Subscript):
            qualified = _ast_qualified_name(node.value)
            if qualified in {"environ", "os.environ"}:
                environment_reads.append(
                    {"line": node.lineno, "call": qualified + "[]"}
                )
            if qualified in {"__builtins__", "sys.modules"}:
                dynamic_accesses.append(
                    {"line": node.lineno, "access": qualified + "[]"}
                )
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id == "__builtins__" or node.id in PURITY_DYNAMIC_CALLS:
                dynamic_accesses.append(
                    {"line": node.lineno, "access": node.id}
                )
            if node.id in PURITY_WRITE_CALLS:
                write_references.append(
                    {"line": node.lineno, "reference": node.id}
                )
        if not isinstance(node, ast.Call):
            continue
        qualified = _ast_qualified_name(node.func)
        final_name = qualified.rsplit(".", 1)[-1]
        root_name = qualified.split(".", 1)[0]
        call = {"line": node.lineno, "call": qualified or final_name}
        if final_name in PURITY_WRITE_CALLS:
            write_calls.append(call)
        if (
            qualified in {"__import__", "compile", "eval", "exec"}
            or (
                root_name in PURITY_PROCESS_IMPORTS
                and final_name in PURITY_PROCESS_CALLS
            )
        ):
            process_calls.append(call)
        if final_name in PURITY_DYNAMIC_CALLS:
            dynamic_accesses.append(call)
        if (
            root_name in PURITY_NETWORK_IMPORTS
            and final_name in PURITY_NETWORK_CALLS
        ):
            network_calls.append(call)
        if (
            root_name == "os"
            and final_name in PURITY_ENVIRONMENT_CALLS
        ) or qualified in {"environ.get", "os.environ.get"}:
            environment_reads.append(call)
        if final_name in PURITY_WALL_CLOCK_CALLS:
            wall_clock_reads.append(call)
    process_imports = sorted(imports & PURITY_PROCESS_IMPORTS)
    network_imports = sorted(imports & PURITY_NETWORK_IMPORTS)
    return {
        "sourceSha256": hashlib.sha256(source).hexdigest(),
        "imports": sorted(imports),
        "importViolations": import_violations,
        "writeCalls": write_calls,
        "writeReferences": write_references,
        "processCalls": process_calls,
        "processImports": process_imports,
        "dynamicAccesses": dynamic_accesses,
        "networkCalls": network_calls,
        "networkImports": network_imports,
        "socketImportCount": int("socket" in imports),
        "environmentReads": environment_reads,
        "wallClockOrWaitCalls": wall_clock_reads,
    }


def validator_purity():
    return _validator_purity_from_source(read_bytes("validate.py"))


def validator_imports():
    return validator_purity()["imports"]


def _validator_purity_diagnostics(purity):
    forbidden_count = sum(
        (
            len(purity["writeCalls"]),
            len(purity["writeReferences"]),
            len(purity["importViolations"]),
            len(purity["processCalls"]),
            len(purity["processImports"]),
            len(purity["dynamicAccesses"]),
            len(purity["networkCalls"]),
            len(purity["networkImports"]),
            len(purity["environmentReads"]),
            len(purity["wallClockOrWaitCalls"]),
        )
    )
    return ["FIXTURE_SCHEMA_VALIDATOR_PURITY"] if forbidden_count else []


def _source_scan_assets(corpus):
    return (
        ["corpus.json"]
        + corpus["schemaPaths"]
        + corpus["manifestPaths"]
        + corpus["casePaths"]
        + ["negative/matrix.json"]
    )


def analyze_sources():
    corpus = read_json("corpus.json")
    purity = validator_purity()
    cases = [read_json(path) for path in corpus["casePaths"]]
    matrix = read_json(corpus["negativeMatrixPath"])
    semantic_matrix = read_json(matrix["semanticMatrixPath"])
    negative_results = {}
    negative_order = []
    for path in matrix["negativePaths"]:
        negative = read_json(path)
        negative_order.append(negative["negativeId"])
        negative_results[negative["negativeId"]] = {
            "path": path,
            "declaredRuleCode": negative["declaredRuleCode"],
            "observedRuleCodes": diagnose_negative(negative),
        }
    for probe in semantic_matrix["probes"]:
        negative_order.append(probe["negativeId"])
        negative_results[probe["negativeId"]] = {
            "path": SEMANTIC_MATRIX_PATH,
            "declaredRuleCode": probe["declaredRuleCode"],
            "observedRuleCodes": diagnose_negative(probe),
        }
    scrub_matches = []
    external_urls = []
    for path in _source_scan_assets(corpus):
        value = read_json(path)
        scrub_matches.extend((path, code, location) for code, location in scrub_diagnostics(value))
        external_urls.extend((path, code, location) for code, location in network_diagnostics(value))
    return {
        "corpus": corpus,
        "cases": cases,
        "matrix": matrix,
        "semanticMatrix": semantic_matrix,
        "negativeResults": negative_results,
        "negativeOrder": negative_order,
        "scrubMatches": scrub_matches,
        "externalUrls": external_urls,
        "imports": purity["imports"],
        "validatorPurity": purity,
        "corpusDigest": corpus_digest(),
    }


def render_validation_report(analysis=None):
    analysis = analysis or analyze_sources()
    purity = analysis["validatorPurity"]
    wait_call_count = sum(
        call["call"].rsplit(".", 1)[-1] in {"sleep", "wait", "wait_for"}
        for call in purity["wallClockOrWaitCalls"]
    )
    report = {
        "reportVersion": "1.0.0",
        "evidenceClass": "fixture",
        "authority": "corpus-validation-only",
        "corpusVersion": analysis["corpus"]["corpusVersion"],
        "corpusDigest": analysis["corpusDigest"],
        "caseIds": sorted(case["caseId"] for case in analysis["cases"]),
        "caseCategories": [case["category"] for case in analysis["cases"]],
        "fileNegativeCount": len(analysis["matrix"]["negativePaths"]),
        "semanticProbeCount": len(analysis["semanticMatrix"]["probes"]),
        "negativeCheckCount": len(analysis["negativeOrder"]),
        "semanticMatrixSha256": SEMANTIC_MATRIX_SHA256,
        "negativeRuleCodes": [
            analysis["negativeResults"][negative_id]["declaredRuleCode"]
            for negative_id in analysis["negativeOrder"]
        ],
        "structuralSchemaPaths": SCHEMA_PATHS,
        "structuralSchemaApplicationCount": len(analysis["cases"]) + len(MANIFEST_PATHS),
        "normalizedHitlDecisionVocabulary": list(VALID_HITL_DECISIONS),
        "scrubMatchCount": len(analysis["scrubMatches"]),
        "externalUrlHostCount": len(analysis["externalUrls"]),
        "validatorImportAllowlist": VALIDATOR_IMPORT_ALLOWLIST,
        "validatorImportsObserved": analysis["imports"],
        "validatorSourceSha256": purity["sourceSha256"],
        "validatorPurity": {
            "derivedBy": "stdlib-ast-source-inspection",
            "importViolationCount": len(purity["importViolations"]),
            "writeCallCount": len(purity["writeCalls"]),
            "writeReferenceCount": len(purity["writeReferences"]),
            "processCallCount": len(purity["processCalls"]),
            "processImportCount": len(purity["processImports"]),
            "dynamicAccessCount": len(purity["dynamicAccesses"]),
            "networkCallCount": len(purity["networkCalls"]),
            "networkImportCount": len(purity["networkImports"]),
            "environmentReadCount": len(purity["environmentReads"]),
            "wallClockOrWaitCallCount": len(
                purity["wallClockOrWaitCalls"]
            ),
        },
        "logicalDelay": {
            "tickEpoch": EPOCH,
            "tickDurationMs": TICK_MS,
            "enqueueTick": 41,
            "delayTicks": 3,
            "releaseTick": 44,
            "completionTick": 45,
            "equation": "41 + 3 = 44",
            "absentThroughTick": 43,
            "visibleExactlyOnceFromTick": 44,
            "wallClockReads": (
                len(purity["wallClockOrWaitCalls"]) - wait_call_count
            ),
            "waits": wait_call_count,
        },
    }
    return canonical_json_bytes(report)


def render_network_report(analysis=None):
    analysis = analysis or analyze_sources()
    purity = analysis["validatorPurity"]
    report = {
        "reportVersion": "1.0.0",
        "evidenceClass": "fixture",
        "authority": "validator-ast-and-corpus-source-inspection-only",
        "claimLimit": "Does not prove isolation for API, browser, provider, or future consumers.",
        "corpusDigest": analysis["corpusDigest"],
        "scannedAssetCount": len(_source_scan_assets(analysis["corpus"])),
        "externalUrlHostCount": len(analysis["externalUrls"]),
        "validatorSourceSha256": purity["sourceSha256"],
        "validatorPurityDerivedBy": "stdlib-ast-source-inspection",
        "validatorImportViolations": len(purity["importViolations"]),
        "validatorSubprocessCalls": len(purity["processCalls"]),
        "validatorProcessImports": len(purity["processImports"]),
        "validatorDynamicAccesses": len(purity["dynamicAccesses"]),
        "validatorSocketImports": purity["socketImportCount"],
        "validatorNetworkCalls": len(purity["networkCalls"]),
        "validatorNetworkImports": len(purity["networkImports"]),
        "validatorEnvironmentReads": len(purity["environmentReads"]),
        "validatorWallClockOrWaitCalls": len(
            purity["wallClockOrWaitCalls"]
        ),
        "validatorWrites": len(purity["writeCalls"]),
        "validatorWriteReferences": len(purity["writeReferences"]),
    }
    return canonical_json_bytes(report)


def _validate_index_and_closure(analysis):
    corpus = analysis["corpus"]
    diagnostics = []
    if corpus["corpusVersion"] != FORMAT_VERSION or corpus["fixtureSchemaVersion"] != FORMAT_VERSION:
        diagnostics.append("FIXTURE_SCHEMA_VERSION")
    if corpus["synthetic"] is not True or corpus["evidenceClass"] != "fixture" or corpus["authority"] != "private-fixture-only":
        diagnostics.append("FIXTURE_SCHEMA_AUTHORITY")
    if corpus["clock"] != {"tickEpoch": EPOCH, "tickDurationMs": TICK_MS}:
        diagnostics.append("FIXTURE_CLOCK_POLICY")
    diagnostics.extend(_validate_corpus_policy(corpus))
    if corpus["casePaths"] != EXPECTED_CASE_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_CASE_INDEX")
    if corpus["schemaPaths"] != SCHEMA_PATHS or corpus["manifestPaths"] != MANIFEST_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_ASSET_INDEX")
    matrix = analysis["matrix"]
    if matrix["negativePaths"] != EXPECTED_NEGATIVE_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_NEGATIVE_INDEX")
    if matrix.get("semanticMatrixPath") != SEMANTIC_MATRIX_PATH:
        diagnostics.append("FIXTURE_SCHEMA_NEGATIVE_INDEX")
    if matrix["expectedRuleCodes"] != EXPECTED_RULE_CODES:
        diagnostics.append("FIXTURE_SCHEMA_RULE_INDEX")
    semantic_matrix = analysis["semanticMatrix"]
    semantic_probes = semantic_matrix.get("probes")
    if (
        semantic_matrix.get("matrixVersion") != FORMAT_VERSION
        or not isinstance(semantic_probes, list)
        or len(semantic_probes) != EXPECTED_SEMANTIC_PROBE_COUNT
        or len(
            {
                probe.get("negativeId")
                for probe in semantic_probes
                if isinstance(probe, dict)
            }
        )
        != EXPECTED_SEMANTIC_PROBE_COUNT
        or hashlib.sha256(read_bytes(SEMANTIC_MATRIX_PATH)).hexdigest()
        != SEMANTIC_MATRIX_SHA256
    ):
        diagnostics.append("FIXTURE_SCHEMA_SEMANTIC_PROBE_INDEX")
    expected_assets = sorted(_expected_hashed_assets())
    if sorted(corpus["hashedAssets"]) != expected_assets or len(corpus["hashedAssets"]) != len(set(corpus["hashedAssets"])):
        diagnostics.append("FIXTURE_HASH_CLOSURE")
    categories = [case["category"] for case in analysis["cases"]]
    if categories != EXPECTED_CATEGORIES:
        diagnostics.append("FIXTURE_SCHEMA_CASE_COVERAGE")
    if len({case["caseId"] for case in analysis["cases"]}) != 13:
        diagnostics.append("FIXTURE_ID_DUPLICATE_CASE")
    return diagnostics


def _validate_hashes():
    expected = render_hash_manifest()
    try:
        actual = read_bytes("hashes.sha256")
    except FileNotFoundError:
        return ["FIXTURE_HASH_MANIFEST_MISSING"]
    return [] if actual == expected else ["FIXTURE_HASH_MISMATCH"]


def _validate_evidence(analysis):
    diagnostics = []
    targets = {
        "evidence/validation-report.json": render_validation_report(analysis),
        "evidence/no-external-network.json": render_network_report(analysis),
    }
    for path, expected in targets.items():
        try:
            actual = read_bytes(path)
        except FileNotFoundError:
            diagnostics.append("FIXTURE_HASH_EVIDENCE_MISSING")
            continue
        if actual != expected:
            diagnostics.append("FIXTURE_HASH_EVIDENCE_DRIFT")
    return diagnostics


def validate_all(require_evidence=True):
    analysis = analyze_sources()
    diagnostics = _validate_index_and_closure(analysis)
    for schema_path in SCHEMA_PATHS:
        schema = read_json(schema_path)
        if schema.get("schemaDialect") != "json-schema-2020-12" or schema.get("description", "").find("not") < 0:
            diagnostics.append("FIXTURE_SCHEMA_DOCUMENT")
        if (
            schema_path == "schema/fixture-envelope.json"
            and schema.get("properties", {})
            .get("capabilityManifestRef", {})
            .get("enum")
            != MANIFEST_PATHS
        ):
            diagnostics.append("FIXTURE_SCHEMA_DOCUMENT")
    for manifest_path in MANIFEST_PATHS:
        diagnostics.extend(validate_manifest(read_json(manifest_path)))
    for case in analysis["cases"]:
        diagnostics.extend(validate_case(case))
    diagnostics.extend(_validate_case_inventory(analysis["cases"]))
    for negative_id, result in sorted(analysis["negativeResults"].items()):
        if result["observedRuleCodes"] != [result["declaredRuleCode"]]:
            diagnostics.append(f"FIXTURE_EXPECTATION_NEGATIVE_SINGLE_CODE:{negative_id}")
    if analysis["scrubMatches"]:
        diagnostics.append("FIXTURE_SCRUB_ACTIVE_CORPUS")
    if analysis["externalUrls"]:
        diagnostics.append("FIXTURE_NETWORK_ACTIVE_CORPUS")
    if analysis["imports"] != VALIDATOR_IMPORT_ALLOWLIST:
        diagnostics.append("FIXTURE_SCHEMA_IMPORT_ALLOWLIST")
    diagnostics.extend(
        _validator_purity_diagnostics(analysis["validatorPurity"])
    )
    diagnostics.extend(_validate_hashes())
    if require_evidence:
        diagnostics.extend(_validate_evidence(analysis))
    return sorted(set(diagnostics)), analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    diagnostics, analysis = validate_all(require_evidence=True)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic, file=sys.stderr)
        return 1
    print(f"corpus_digest={analysis['corpusDigest']}")
    print("case_ids=" + ",".join(sorted(case["caseId"] for case in analysis["cases"])))
    print("case_categories=" + ",".join(case["category"] for case in analysis["cases"]))
    print(
        "negative_rule_codes="
        + ",".join(
            analysis["negativeResults"][negative_id]["declaredRuleCode"]
            for negative_id in analysis["negativeOrder"]
        )
    )
    print("scrub_match_count=0")
    print("external_url_host_count=0")
    print("logical_delay=enqueue:41,delay:3,release:44,completion:45")
    print("logical_delay_visibility=absent_through:43,visible_once_from:44")
    purity = analysis["validatorPurity"]
    print(f"validator_import_violations={len(purity['importViolations'])}")
    print(f"validator_subprocess_calls={len(purity['processCalls'])}")
    print(f"validator_process_imports={len(purity['processImports'])}")
    print(f"validator_dynamic_accesses={len(purity['dynamicAccesses'])}")
    print(f"validator_network_calls={len(purity['networkCalls'])}")
    print(f"validator_network_imports={len(purity['networkImports'])}")
    print(f"validator_environment_reads={len(purity['environmentReads'])}")
    print(
        "validator_wall_clock_or_wait_calls="
        + str(len(purity["wallClockOrWaitCalls"]))
    )
    print(f"validator_writes={len(purity['writeCalls'])}")
    print(f"validator_write_references={len(purity['writeReferences'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
