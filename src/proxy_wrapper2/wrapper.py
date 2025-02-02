import errno
import socket
from typing import Sequence

from proxy_wrapper.exceptions import CannotWrapSocket
from proxy_wrapper2.base import BaseProxiedSocket
from proxy_wrapper2.proxied_socket import ProxiedSocket
from proxy_wrapper2.utils import parse_proxy_string


def wrap_socket(sock: socket.socket, *proxy_strings: str, perform_connection: bool | None = None):
    if not isinstance(sock, BaseProxiedSocket) and isinstance(sock, socket.socket):
        try:
            sock.getpeername()
            raise CannotWrapSocket("socket is already connected")
        except OSError as e:
            if e.errno != errno.ENOTCONN:
                raise e
    proxied = sock if isinstance(sock, ProxiedSocket) else ProxiedSocket.from_socket(sock)
    for proxy_string in proxy_strings:
        proxied.add_proxy(parse_proxy_string(proxy_string))

    if proxied.getblocking() and perform_connection is True:
        proxied.perform_connection()
    elif not proxied.getblocking() and perform_connection is True:
        raise ValueError("perform_connection=True is not allowed when the socket is in non-blocking mode")
    return proxied


async def wrap_socket_async(sock: socket.socket, *proxy_string: Sequence[str], perform_connection: bool | None = None):
    print(f"wrap sock, {proxy_string}, {perform_connection=}")
