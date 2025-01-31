import asyncio
import socket

from proxy_wrapper.exceptions import CannotWrapSocket, WantWriteError, WantReadError
from proxy_wrapper.mixins.base import BaseProxiedSocketMixin
from proxy_wrapper.utils import parse_proxy_string
from .proxied_socket import ProxiedSocket


def wrap_socket(sock: socket.socket, *proxy_strings: str) -> ProxiedSocket:
    """
    Wraps a socket with proxy support but does not perform the connection immediately.
    After wrapping, `perform_connection()` must be called to establish the connection.

    If the socket is in blocking mode, `perform_connection()` will complete synchronously.
    If the socket is non-blocking, it may raise `WantReadError` or `WantWriteError`,
    which should be handled using a preferred event loop mechanism (e.g., `select.select()`,
    `epoll()`, or `selectors`).

    Adding multiple proxies results in proxy chaining, where each request is routed through
    multiple proxy servers sequentially.

    Parameters:
        sock (socket.socket): The socket to wrap.
        proxy_strings (str): One or more proxy URLs (e.g., "socks5://127.0.0.1:9050").

    Returns:
        ProxiedSocket: A wrapped socket with proxy support.

    Raises:
        CannotWrapSocket: If the socket is already connected.

    Example (blocking mode):
        ```python
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxied = wrap_socket(sock, "socks5://127.0.0.1:9050")
        proxied.perform_connection()
        ```

    Example (non-blocking mode):
        ```python
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        proxied = wrap_socket(sock, "socks5://127.0.0.1:9050")

        try:
            proxied.perform_connection()
        except WantWriteError:
            # Handle using select(), epoll(), or selectors
        except WantReadError:
            # Handle using select(), epoll(), or selectors
        ```
    """
    if not isinstance(sock, BaseProxiedSocketMixin):
        try:
            sock.getpeername()
            raise CannotWrapSocket("Can not wrap a socket that is already connected")
        except OSError:
            pass
    proxied = sock if isinstance(sock, ProxiedSocket) else ProxiedSocket.from_socket(sock)
    for proxy_string in proxy_strings:
        proxied.add_proxy(parse_proxy_string(proxy_string))
    return proxied


async def wrap_socket_async(sock: socket.socket, *proxy_strings: str) -> ProxiedSocket:
    """
    Asynchronously wraps a socket with proxy support and performs the connection.

    This function ensures the socket is non-blocking and handles `WantWriteError` and
    `WantReadError` exceptions using the asyncio event loop.

    Parameters:
        sock (socket.socket): The socket to wrap.
        proxy_strings (str): One or more proxy URLs (e.g., "socks5://127.0.0.1:9050").

    Returns:
        ProxiedSocket: A wrapped socket with proxy support after a successful connection.

    Example:
        ```python
        async def main():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxied = await wrap_socket_async(sock, "socks5://127.0.0.1:9050")
            # Use the connected proxy socket
        ```
    """
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    sock = wrap_socket(sock, *proxy_strings)

    if sock.getblocking():
        sock.setblocking(False)

    def remove_reader_and_continue():
        nonlocal loop
        loop.remove_reader(sock.fileno())
        _continue_performing_connection()

    def remove_writer_and_continue():
        nonlocal loop
        loop.remove_writer(sock.fileno())
        _continue_performing_connection()

    def _continue_performing_connection():
        nonlocal loop, sock, fut

        try:
            sock.perform_connection()
            fut.set_result(sock)
        except WantWriteError:
            loop.add_writer(sock.fileno(), remove_writer_and_continue)
        except WantReadError:
            loop.add_reader(sock.fileno(), remove_reader_and_continue)

    _continue_performing_connection()
    return await fut


async def connect_socket_to_address_async(sock: ProxiedSocket, address: tuple[str, int]):
    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    def remove_reader_and_continue():
        nonlocal loop
        loop.remove_reader(sock.fileno())
        _continue_connecting()

    def remove_writer_and_continue():
        nonlocal loop
        loop.remove_writer(sock.fileno())
        _continue_connecting()

    def _continue_connecting():
        nonlocal loop, sock, fut
        try:
            sock.connect(address)
            fut.set_result(None)
        except WantWriteError:
            loop.add_writer(sock.fileno(), remove_writer_and_continue)
        except WantReadError:
            loop.add_reader(sock.fileno(), remove_reader_and_continue)

    _continue_connecting()
    return await fut
