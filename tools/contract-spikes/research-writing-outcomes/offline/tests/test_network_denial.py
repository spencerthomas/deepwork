from __future__ import annotations

import socket
from urllib.request import urlopen

from support import OfflineTestCase


class NetworkDenialTests(OfflineTestCase):
    def test_socket_and_dns_are_globally_denied(self) -> None:
        with self.assertRaisesRegex(AssertionError, "network access"):
            socket.create_connection(("example.invalid", 443))
        with self.assertRaisesRegex(AssertionError, "network access"):
            socket.getaddrinfo("example.invalid", 443)

    def test_standard_library_http_is_denied(self) -> None:
        with self.assertRaises(AssertionError):
            urlopen("https://example.invalid", timeout=1)
