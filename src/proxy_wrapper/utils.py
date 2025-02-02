from functools import wraps
from urllib.parse import urlparse, unquote

from proxy_wrapper.enums import ProxyProtocol
from proxy_wrapper.proxy import Proxy


def parse_proxy_string(proxy_string: str) -> Proxy:
    parsed = urlparse(proxy_string)

    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    host = parsed.hostname
    port = parsed.port

    return Proxy(ProxyProtocol(parsed.scheme), (host, port), (username, password) if username or password else None)


__all__ = ("parse_proxy_string",)
