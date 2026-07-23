"""Execute and record the packet's exact no-index command set.

This helper is an authoring utility, not an extra acceptance command. It runs the
fixed commands without accepting user-provided shell content, records their real
exit statuses, then reruns scrub/hash/evidence after the command record changes so
the retained freshness and closure are final.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from .validate_evidence import REQUIRED_COMMANDS


REFRESH_INDICES = (6, 7, 8)


def _run(command: str, root: Path) -> int:
    result = subprocess.run(
        command,
        cwd=root,
        shell=True,
        executable="/bin/sh",
        check=False,
        timeout=180,
    )
    return result.returncode


def _write(path: Path, statuses: list[int]) -> None:
    lines = ["# execution-derived exit-status<TAB>exact-command"]
    lines.extend(
        f"{status}\t{command}"
        for status, command in zip(statuses, REQUIRED_COMMANDS, strict=True)
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output",
        default="docs/references/research/research-writing-outcomes/commands.txt",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    output = root / args.output
    statuses: list[int] = []
    for command in REQUIRED_COMMANDS:
        status = _run(command, root)
        statuses.append(status)
        if status != 0:
            _write(output, statuses + [127] * (len(REQUIRED_COMMANDS) - len(statuses)))
            return status
    _write(output, statuses)
    for index in REFRESH_INDICES:
        status = _run(REQUIRED_COMMANDS[index], root)
        if status != 0:
            return status
    print(f"recorded {len(statuses)} execution-derived command statuses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
