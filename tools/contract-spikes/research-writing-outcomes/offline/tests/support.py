"""Global network denial base class for every offline unittest."""

from __future__ import annotations

import socket
import unittest
from unittest.mock import patch


def deny_network(*_args, **_kwargs):
    raise AssertionError("offline spike attempted network access")


class OfflineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls._patchers = [
            patch.object(socket, "socket", side_effect=deny_network),
            patch.object(socket, "create_connection", side_effect=deny_network),
            patch.object(socket, "getaddrinfo", side_effect=deny_network),
        ]
        for patcher in cls._patchers:
            patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        for patcher in reversed(cls._patchers):
            patcher.stop()
        super().tearDownClass()
