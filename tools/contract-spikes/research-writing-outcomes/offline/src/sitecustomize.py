"""Process-wide network denial for every Python launched from the offline venv."""

from __future__ import annotations

import builtins
import sys


DENIED_EVENTS = {
    "socket.__new__",
    "socket.bind",
    "socket.connect",
    "socket.getaddrinfo",
    "socket.gethostbyaddr",
    "socket.gethostbyname",
    "socket.gethostbyname_ex",
    "socket.gethostname",
    "socket.getnameinfo",
    "socket.sendto",
}


def _deny_network(event: str, _args: tuple[object, ...]) -> None:
    if event in DENIED_EVENTS:
        raise RuntimeError(f"offline Python runtime denied audit event: {event}")


sys.addaudithook(_deny_network)
builtins.DW_OFFLINE_NETWORK_GUARD = "audit-hook-v1"
