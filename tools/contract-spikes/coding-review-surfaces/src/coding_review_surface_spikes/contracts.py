"""Fail-closed contract rules shared by tests and retained-evidence validators."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any

SPIKE_IDS = {"SPIKE-FILES-001", "SPIKE-TERMINAL-001", "SPIKE-BROWSER-001"}
ROW_STATES = {"accepted-live", "blocked-live-evidence", "rejected", "unknown"}
EVIDENCE_TIERS = {
    "accepted-live",
    "installed-public",
    "official-documented",
    "pinned-reference",
    "deterministic-fake",
    "unknown",
}
TERMINAL_MODES = {"interactive", "transcript", "none"}
COMMAND_INPUT_MODES = {"pty", "discrete_reviewed", "none"}
BROWSER_MODES = {"evidence", "service_url", "none"}
SURFACES = {"file", "diff", "terminal", "browser"}
SAFE_PATH_SEGMENT = re.compile(r"^[^\x00-\x1f\x7f]+$")
BIDI_CONTROLS = {
    "\u061c",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_without(document: Mapping[str, Any], key: str) -> str:
    return canonical_hash({name: value for name, value in document.items() if name != key})


def normalize_relative_path(raw: str) -> str:
    """Normalize a provider path without allowing authority to escape its root."""
    if not isinstance(raw, str) or not raw:
        raise ValueError("path must be a non-empty string")
    if "\x00" in raw:
        raise ValueError("NUL is forbidden")
    if "\\" in raw:
        raise ValueError("backslash paths are forbidden")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError("absolute paths are forbidden")
    raw_parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("dot and traversal segments are forbidden")
    parts = PurePosixPath(raw).parts
    if any(not SAFE_PATH_SEGMENT.match(part) for part in parts):
        raise ValueError("path contains control characters")
    normalized = posixpath.normpath(raw)
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError("path escapes root")
    return normalized


def validate_display_path(raw: str) -> str:
    """Reject ambiguous or direction-changing display paths."""
    normalized = normalize_relative_path(raw)
    if not unicodedata.is_normalized("NFC", normalized):
        raise ValueError("path must use NFC normalization")
    if any(character in BIDI_CONTROLS for character in normalized):
        raise ValueError("bidirectional control characters are forbidden")
    return normalized


def reject_ambiguous_listing(paths: Sequence[str], *, case_sensitive: bool) -> None:
    seen: dict[str, str] = {}
    for raw in paths:
        display = validate_display_path(raw)
        key = display if case_sensitive else display.casefold()
        if key in seen:
            raise ValueError(f"ambiguous listing collision: {seen[key]!r} and {display!r}")
        seen[key] = display


def validate_terminal_pair(terminal: str, command_input: str) -> None:
    if terminal not in TERMINAL_MODES or command_input not in COMMAND_INPUT_MODES:
        raise ValueError("noncanonical terminal capability")
    if terminal == "interactive" and command_input != "pty":
        raise ValueError("interactive terminal requires pty")
    if terminal == "transcript" and command_input not in {"discrete_reviewed", "none"}:
        raise ValueError("transcript cannot claim pty input")
    if terminal == "none" and command_input != "none":
        raise ValueError("terminal none requires command input none")


def validate_browser_mode(browser: str, evidence: Mapping[str, Any]) -> None:
    if browser not in BROWSER_MODES:
        raise ValueError("noncanonical browser capability")
    kind = evidence.get("kind")
    if browser == "none":
        if kind not in {None, "external_link"}:
            raise ValueError("browser none cannot retain browser evidence")
    elif browser == "evidence":
        if kind != "verified_evidence":
            raise ValueError("browser evidence requires verified evidence provenance")
        required = {
            "task_ref",
            "sandbox_ref",
            "actor_ref",
            "origin_ref",
            "captured_at",
            "expiry",
            "grant_hash",
            "screenshot_sha256",
        }
        if any(not evidence.get(key) for key in required):
            raise ValueError("browser evidence requires complete identity, provenance, expiry, grant, and media hash")
        if evidence.get("authorization_state") != "current":
            raise ValueError("browser evidence authority must be current")
        if evidence.get("auto_open") is not False:
            raise ValueError("browser evidence must not auto-open")
    elif browser == "service_url":
        if kind != "authorized_service_url":
            raise ValueError("service_url requires an authorized expiring binding")
        required = {
            "task_ref",
            "sandbox_ref",
            "actor_ref",
            "origin_ref",
            "audience_ref",
            "expiry",
            "grant_hash",
        }
        if any(not evidence.get(key) for key in required):
            raise ValueError("service_url requires complete identity, origin, audience, expiry, and grant")
        if not isinstance(evidence.get("allowed_port"), int):
            raise ValueError("service_url requires one exact allowed port")
        if evidence.get("authorization_state") != "current":
            raise ValueError("service_url authority must be current")
        if evidence.get("refresh") != "explicit" or evidence.get("revocation") != "supported":
            raise ValueError("service_url requires explicit refresh and revocation")
        if evidence.get("redirect_policy") != "same-origin-only":
            raise ValueError("service_url redirects must remain same-origin")
        if evidence.get("user_confirmation") is not True or evidence.get("auto_open") is not False:
            raise ValueError("service_url requires confirmation and no automatic open")


def validate_scope_document(scope: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if scope.get("schema_version") != "1.0":
        errors.append("scope schema_version must equal 1.0")
    if scope.get("scope_hash") != hash_without(scope, "scope_hash"):
        errors.append("scope_hash does not match canonical scope payload")
    required = scope.get("required_row_ids")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        errors.append("required_row_ids must be a non-empty unique list")
    if scope.get("terminal_modes") != ["interactive", "transcript", "none"]:
        errors.append("terminal_modes must retain the canonical ordered enum")
    if scope.get("command_input_modes") != ["pty", "discrete_reviewed", "none"]:
        errors.append("command_input_modes must retain the canonical ordered enum")
    if scope.get("browser_modes") != ["evidence", "service_url", "none"]:
        errors.append("browser_modes must retain the canonical ordered enum")
    pair = scope.get("assigned_checkout_pair", {})
    for key in ("base_sha", "seed_sha"):
        value = pair.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
            errors.append(f"assigned_checkout_pair.{key} must be a full SHA")
    return errors


def validate_upstream_lock(lock: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if lock.get("schema_version") != "1.0":
        errors.append("upstream lock schema_version must equal 1.0")
    dependencies = lock.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) != 2:
        return [*errors, "upstream lock must contain exactly two dependencies"]
    expected_ids = {
        "DW-EXT-W1-CODING-SANDBOX-CONTRACT-RESEARCH",
        "DW-EXT-W1-CODING-GITHUB-CONTRACT-RESEARCH",
    }
    observed_ids: set[str] = set()
    for index, item in enumerate(dependencies):
        label = f"dependencies[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        observed_ids.add(str(item.get("packet_id")))
        verdict = item.get("review_verdict")
        consumable = item.get("consumable")
        if verdict not in {"missing", "accepted"}:
            errors.append(f"{label} review_verdict must be missing or accepted")
        if verdict == "missing" and consumable is not False:
            errors.append(f"{label} missing evidence must not be consumable")
        if verdict == "accepted" and consumable is not True:
            errors.append(f"{label} accepted evidence must be consumable")
        if verdict == "accepted" and any(
            value is None for value in item.get("required_outputs", {}).values()
        ):
            errors.append(f"{label} accepted evidence requires every locked output hash")
        for required in ("observed_commit", "packet_sha256", "blocker"):
            if not item.get(required):
                errors.append(f"{label} missing {required}")
    if observed_ids != expected_ids:
        errors.append("upstream dependency identities do not match scope")
    if lock.get("lock_hash") != hash_without(lock, "lock_hash"):
        errors.append("upstream lock_hash does not match canonical payload")
    return errors


def validate_matrix_document(
    matrix: Mapping[str, Any],
    scope: Mapping[str, Any],
    upstream_lock: Mapping[str, Any],
) -> list[str]:
    errors = [*validate_scope_document(scope), *validate_upstream_lock(upstream_lock)]
    if matrix.get("schema_version") != "1.0":
        errors.append("matrix schema_version must equal 1.0")
    if matrix.get("scope_hash") != scope.get("scope_hash"):
        errors.append("matrix scope_hash does not match immutable scope")
    if matrix.get("upstream_lock_hash") != upstream_lock.get("lock_hash"):
        errors.append("matrix upstream_lock_hash does not match upstream lock")
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        return [*errors, "matrix rows must be a list"]
    dependencies = upstream_lock.get("dependencies", [])
    upstream_accepted = bool(dependencies) and all(
        item.get("review_verdict") == "accepted" and item.get("consumable") is True
        for item in dependencies
    )
    read_grant = upstream_lock.get("current_read_grant", {})
    terminal_grant = upstream_lock.get("current_terminal_grant", {})
    live_profile_allowed = upstream_lock.get("live_profile_allowed") is True
    required = set(scope.get("required_row_ids", []))
    seen: set[str] = set()
    for index, row in enumerate(rows):
        label = f"rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        row_id = row.get("row_id")
        if row_id in seen:
            errors.append(f"{label} duplicates row_id {row_id}")
        seen.add(str(row_id))
        for key in (
            "row_id",
            "spike_id",
            "surface",
            "source_identity",
            "authority",
            "freshness",
            "evidence_tier",
            "version",
            "observed_at",
            "schema_or_transcript",
            "checksum",
            "conclusion",
            "contradiction",
            "inherited_blocker",
            "owner",
            "fallback",
            "cleanup",
        ):
            if key not in row:
                errors.append(f"{label} missing {key}")
        if row.get("spike_id") not in SPIKE_IDS:
            errors.append(f"{label} has unknown spike_id")
        if row.get("surface") not in SURFACES:
            errors.append(f"{label} has unknown surface")
        if row.get("evidence_tier") not in EVIDENCE_TIERS:
            errors.append(f"{label} has invalid evidence_tier")
        conclusion = row.get("conclusion")
        if conclusion not in ROW_STATES:
            errors.append(f"{label} has invalid conclusion")
        if conclusion == "accepted-live" and row.get("evidence_tier") != "accepted-live":
            errors.append(f"{label} accepted-live requires accepted-live evidence")
        if conclusion == "accepted-live" and row.get("current_grant_hash") in {None, ""}:
            errors.append(f"{label} accepted-live requires a current grant hash")
        if conclusion == "accepted-live" and not upstream_accepted:
            errors.append(f"{label} accepted-live requires both accepted consumable upstream packets")
        if conclusion == "accepted-live" and not live_profile_allowed:
            errors.append(f"{label} accepted-live requires live_profile_allowed")
        if conclusion == "accepted-live" and (
            read_grant.get("present") is not True
            or row.get("current_grant_hash") != read_grant.get("grant_hash")
        ):
            errors.append(f"{label} accepted-live requires the exact current read grant")
        if conclusion == "accepted-live" and row.get("surface") == "terminal":
            if (
                terminal_grant.get("present") is not True
                or row.get("terminal_grant_hash") != terminal_grant.get("grant_hash")
            ):
                errors.append(f"{label} accepted-live terminal requires the exact terminal grant")
        if row.get("evidence_tier") == "deterministic-fake" and conclusion == "accepted-live":
            errors.append(f"{label} deterministic fake cannot promote a live capability")
        if conclusion == "blocked-live-evidence" and not row.get("fallback"):
            errors.append(f"{label} blocked row requires a fallback")
        if row.get("authoritative_bytes_from") not in {None, row.get("authority")}:
            errors.append(f"{label} mixes byte authority and asserted authority")
        if row.get("surface") == "terminal":
            try:
                validate_terminal_pair(row.get("terminal", ""), row.get("command_input", ""))
            except ValueError as exc:
                errors.append(f"{label} {exc}")
        if row.get("surface") == "browser":
            try:
                validate_browser_mode(row.get("browser", ""), row.get("browser_record", {}))
            except ValueError as exc:
                errors.append(f"{label} {exc}")
    if seen != required:
        errors.append(
            "matrix row cross-product mismatch: "
            f"missing={sorted(required - seen)} extra={sorted(seen - required)}"
        )
    dispositions = matrix.get("spike_dispositions", {})
    if set(dispositions) != SPIKE_IDS:
        errors.append("matrix must contain all three spike dispositions")
    for spike_id, disposition in dispositions.items():
        if disposition.get("state") == "accepted-live":
            accepted = [row for row in rows if row.get("spike_id") == spike_id and row.get("conclusion") == "accepted-live"]
            if not accepted:
                errors.append(f"{spike_id} cannot be accepted without accepted rows")
        if disposition.get("e2e_credit") != 0:
            errors.append(f"{spike_id} must contribute zero E2E credit")
    return errors


def exact_diff_errors(document: Mapping[str, Any], patch_bytes: bytes) -> list[str]:
    errors: list[str] = []
    digest = hashlib.sha256(patch_bytes).hexdigest()
    if document.get("patch_sha256") != digest:
        errors.append("diff patch_sha256 mismatch")
    try:
        patch_text = patch_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return [*errors, "diff patch must be UTF-8"]
    parsed, identities, parse_errors = _parse_unified_patch(patch_text)
    errors.extend(parse_errors)
    if identities.get("base_sha") != document.get("base_sha"):
        errors.append("diff base_sha does not match patch identity header")
    if identities.get("head_sha") != document.get("head_sha"):
        errors.append("diff head_sha does not match patch identity header")
    files = document.get("files")
    if not isinstance(files, list) or not files:
        return [*errors, "diff files must be a non-empty list"]
    seen: set[tuple[str, str]] = set()
    for item in files:
        key = (str(item.get("path")), str(item.get("status")))
        if key in seen:
            errors.append(f"duplicate diff file entry {key}")
        seen.add(key)
        if item.get("binary") and item.get("hunks"):
            errors.append(f"binary file {item.get('path')} cannot fabricate hunks")
        if item.get("status") in {"renamed", "copied"} and not item.get("previous_path"):
            errors.append(f"{item.get('status')} file requires previous_path")
        if item.get("status") == "deleted" and item.get("new_checksum") is not None:
            errors.append("deleted file must not have a new checksum")
    normalized = [
        {
            "path": item.get("path"),
            "previous_path": item.get("previous_path"),
            "status": item.get("status"),
            "additions": item.get("additions"),
            "deletions": item.get("deletions"),
            "binary": item.get("binary"),
            "hunks": item.get("hunks"),
        }
        for item in files
    ]
    if normalized != parsed:
        errors.append("normalized diff file/status/count/hunk facts do not match patch bytes")
    if document.get("document_sha256") != hash_without(document, "document_sha256"):
        errors.append("diff document_sha256 mismatch")
    return errors


def _parse_unified_patch(text: str) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    identities: dict[str, str] = {}
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None
    last_line_kind: str | None = None
    for line in text.splitlines():
        if line.startswith("X-DeepWork-Base-SHA: "):
            identities["base_sha"] = line.removeprefix("X-DeepWork-Base-SHA: ")
            continue
        if line.startswith("X-DeepWork-Head-SHA: "):
            identities["head_sha"] = line.removeprefix("X-DeepWork-Head-SHA: ")
            continue
        if line.startswith("diff --git a/"):
            match = re.fullmatch(r"diff --git a/(.+) b/(.+)", line)
            if not match:
                errors.append("malformed diff file header")
                current = None
                continue
            current = {
                "path": match.group(2),
                "previous_path": None,
                "status": "modified",
                "additions": 0,
                "deletions": 0,
                "binary": False,
                "hunks": [],
            }
            records.append(current)
            current_hunk = None
            continue
        if current is None:
            continue
        if line.startswith("new file mode "):
            current["status"] = "added"
        elif line.startswith("deleted file mode "):
            current["status"] = "deleted"
        elif line.startswith("rename from "):
            current["status"] = "renamed"
            current["previous_path"] = line.removeprefix("rename from ")
        elif line.startswith("rename to "):
            current["path"] = line.removeprefix("rename to ")
        elif line.startswith("Binary files "):
            current["binary"] = True
            current["additions"] = None
            current["deletions"] = None
        elif line.startswith("@@ "):
            match = re.match(
                r"@@ -(?P<old_start>\d+)(?:,(?P<old_lines>\d+))? "
                r"\+(?P<new_start>\d+)(?:,(?P<new_lines>\d+))? @@",
                line,
            )
            if not match:
                errors.append(f"malformed hunk header for {current['path']}")
                current_hunk = None
                continue
            current_hunk = {
                "header": line,
                "old_start": int(match.group("old_start")),
                "old_lines": int(match.group("old_lines") or 1),
                "new_start": int(match.group("new_start")),
                "new_lines": int(match.group("new_lines") or 1),
                "no_newline_old": False,
                "lines": [],
            }
            current["hunks"].append(current_hunk)
        elif current_hunk is not None and line.startswith("\\ No newline at end of file"):
            if last_line_kind == "deletion":
                current_hunk["no_newline_old"] = True
            elif last_line_kind == "addition":
                current_hunk["no_newline_new"] = True
        elif current_hunk is not None and line and line[0] in {" ", "+", "-"}:
            kind = {" ": "context", "+": "addition", "-": "deletion"}[line[0]]
            current_hunk["lines"].append({"kind": kind, "text": line[1:]})
            last_line_kind = kind
            if kind == "addition":
                current["additions"] += 1
            elif kind == "deletion":
                current["deletions"] += 1
    if not re.fullmatch(r"[0-9a-f]{40}", identities.get("base_sha", "")):
        errors.append("patch missing full base SHA identity header")
    if not re.fullmatch(r"[0-9a-f]{40}", identities.get("head_sha", "")):
        errors.append("patch missing full head SHA identity header")
    return records, identities, errors


def fixture_manifest_errors(root: Any, manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for item in manifest.get("files", []):
        path = root / item["path"]
        if not path.is_file():
            errors.append(f"fixture missing: {item['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            errors.append(f"fixture hash mismatch: {item['path']}")
    return errors
