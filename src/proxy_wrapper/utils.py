import selectors
import time
from selectors import BaseSelector, DefaultSelector
from typing import Type, List
from urllib.parse import urlparse, unquote

from proxy_wrapper.enums import ProxyProtocol
from proxy_wrapper.exceptions import WantWriteError, WantReadError
from proxy_wrapper.proxied_socket import ProxiedSocket
from proxy_wrapper.proxy import Proxy


def parse_proxy_string(proxy: str):
    parsed = urlparse(proxy)

    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    host = parsed.hostname
    port = parsed.port

    return Proxy(ProxyProtocol(parsed.scheme), (host, port), (username, password) if username or password else None)


def perform_connecting(socks: List[ProxiedSocket], timeout: float | None = None,
                       selector_cls: Type[BaseSelector] = DefaultSelector):
    sel = selector_cls()

    for sock in socks:
        sock.setblocking(False)  # To be sure
        sel.register(sock, selectors.EVENT_WRITE, data=sock)

    total_sockets = len(socks)
    performed_connections = 0
    start_time = time.time()

    while performed_connections != total_sockets:
        current_time = time.time()
        elapsed_time = current_time - start_time

        if timeout is not None and elapsed_time >= timeout:
            raise TimeoutError(f"Connection timed out after {timeout} seconds")

        remaining_time = timeout - elapsed_time if timeout is not None else None

        events = sel.select(remaining_time)
        for selector_key, _ in events:
            try:
                selector_key.data.perform_connection()
                performed_connections += 1
            except WantWriteError:
                sel.modify(selector_key.fileobj, selectors.EVENT_WRITE, data=selector_key.data)
            except WantReadError:
                sel.modify(selector_key.fileobj, selectors.EVENT_READ, data=selector_key.data)

    return socks

