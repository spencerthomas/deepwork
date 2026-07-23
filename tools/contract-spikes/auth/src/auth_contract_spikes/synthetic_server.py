"""Loopback-only synthetic upstream used by the offline contract tests."""

from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator

from .policy import sanitize_headers


class _Handler(BaseHTTPRequestHandler):
    server_version = "AuthContractSynthetic/1"
    sys_version = ""

    def _respond(self) -> None:
        api_key = self.headers.get("X-Api-Key")
        tenant = self.headers.get("X-Tenant-Id")
        if not api_key:
            status, payload = 401, {"detail": "synthetic missing authorization"}
        elif tenant == "wrong-workspace":
            status, payload = 403, {"detail": "synthetic inaccessible workspace"}
        else:
            status, payload = 200, {
                "ok": True,
                "observed_headers": sanitize_headers(dict(self.headers)),
                "redirected": False,
            }
        encoded = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    do_GET = _respond
    do_POST = _respond

    def log_message(self, format: str, *args: object) -> None:
        # Never emit request metadata or header-bearing access logs.
        return


@contextmanager
def synthetic_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
