"""Dependency-free PEP 517 backend used only by the offline spike project."""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


NAME = "research_writing_outcome_spikes"
VERSION = "0.1.0"


def _dist_info() -> str:
    return f"{NAME}-{VERSION}.dist-info"


def _metadata() -> bytes:
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {NAME.replace('_', '-')}\n"
        f"Version: {VERSION}\n"
        "Requires-Python: >=3.12\n\n"
    ).encode()


def _wheel() -> bytes:
    return b"Wheel-Version: 1.0\nGenerator: deepwork-offline\nRoot-Is-Purelib: true\nTag: py3-none-any\n"


def _record_line(path: str, content: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
    return f"{path},sha256={digest},{len(content)}"


def build_wheel(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    root = Path(__file__).parent
    filename = f"{NAME}-{VERSION}-py3-none-any.whl"
    destination = Path(wheel_directory) / filename
    entries: dict[str, bytes] = {}
    for source in sorted((root / "src" / NAME).glob("*.py")):
        entries[f"{NAME}/{source.name}"] = source.read_bytes()
    entries["sitecustomize.py"] = (root / "src" / "sitecustomize.py").read_bytes()
    entries[f"{_dist_info()}/METADATA"] = _metadata()
    entries[f"{_dist_info()}/WHEEL"] = _wheel()
    record_path = f"{_dist_info()}/RECORD"
    record = "\n".join(_record_line(path, data) for path, data in entries.items())
    entries[record_path] = (record + f"\n{record_path},,\n").encode()
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as wheel:
        for path, content in entries.items():
            info = ZipInfo(path, (2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            wheel.writestr(info, content)
    return filename


def get_requires_for_build_wheel(config_settings=None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(metadata_directory: str, config_settings=None) -> str:
    target = Path(metadata_directory) / _dist_info()
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA").write_bytes(_metadata())
    (target / "WHEEL").write_bytes(_wheel())
    return target.name


def build_editable(wheel_directory: str, config_settings=None, metadata_directory=None) -> str:
    return build_wheel(wheel_directory, config_settings, metadata_directory)


def get_requires_for_build_editable(config_settings=None) -> list[str]:
    return []


def prepare_metadata_for_build_editable(metadata_directory: str, config_settings=None) -> str:
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)
