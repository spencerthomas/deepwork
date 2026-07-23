"""Dependency-free PEP 517 backend for the offline probe package."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import zipfile
from pathlib import Path

NAME = "deepwork_langchain_contract_spikes"
VERSION = "0.1.0"
WHEEL = f"{NAME}-{VERSION}-py3-none-any.whl"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"


def _record_line(path: str, data: bytes) -> tuple[str, str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return path, f"sha256={digest}", str(len(data))


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    del config_settings, metadata_directory
    root = Path(__file__).parent
    files: dict[str, bytes] = {}
    for path in sorted((root / "src/langchain_contract_spikes").glob("*.py")):
        files[f"langchain_contract_spikes/{path.name}"] = path.read_bytes()
    files[f"{DIST_INFO}/METADATA"] = (
        "Metadata-Version: 2.3\n"
        "Name: deepwork-langchain-contract-spikes\n"
        f"Version: {VERSION}\n"
        "Requires-Python: >=3.11,<3.15\n"
    ).encode()
    files[f"{DIST_INFO}/WHEEL"] = (
        "Wheel-Version: 1.0\n"
        "Generator: deepwork-offline-build-backend\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode()
    files[f"{DIST_INFO}/entry_points.txt"] = (
        "[console_scripts]\n"
        "pytest = langchain_contract_spikes.pytest_runner:main\n"
    ).encode()
    rows = [_record_line(path, data) for path, data in files.items()]
    rows.append((f"{DIST_INFO}/RECORD", "", ""))
    record = io.StringIO()
    csv.writer(record, lineterminator="\n").writerows(rows)
    files[f"{DIST_INFO}/RECORD"] = record.getvalue().encode()

    wheel_path = Path(wheel_directory) / WHEEL
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            archive.writestr(path, data)
    return WHEEL


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    del config_settings
    path = Path(metadata_directory) / DIST_INFO
    path.mkdir(parents=True, exist_ok=True)
    (path / "METADATA").write_text(
        "Metadata-Version: 2.3\n"
        "Name: deepwork-langchain-contract-spikes\n"
        f"Version: {VERSION}\n"
        "Requires-Python: >=3.11,<3.15\n",
        encoding="utf-8",
    )
    (path / "WHEEL").write_text(
        "Wheel-Version: 1.0\n"
        "Generator: deepwork-offline-build-backend\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n",
        encoding="utf-8",
    )
    return DIST_INFO


def build_editable(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    """Install the small probe package as a regular pure-Python wheel."""
    return build_wheel(wheel_directory, config_settings, metadata_directory)


def prepare_metadata_for_build_editable(metadata_directory: str, config_settings=None) -> str:
    """Reuse wheel metadata for the editable installation request."""
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)
