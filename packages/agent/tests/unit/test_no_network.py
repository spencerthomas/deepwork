"""Direct proof that the default unit suite denies outbound sockets."""

import socket

import pytest
from pytest_socket import SocketBlockedError


def test_outbound_socket_is_blocked() -> None:
    """The pytest socket policy rejects even a loopback connection attempt."""
    with (
        pytest.warns(UserWarning, match="tried to use socket.socket"),
        pytest.raises(SocketBlockedError),
    ):
        socket.socket()
