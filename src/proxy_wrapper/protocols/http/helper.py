import base64
from typing import Tuple


def proxy_auth_header(username: str, password: str) -> str:
    return f"Proxy-Authorization: Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}\r\n"


def craft_connect_request(address: Tuple[str, int], credentials: Tuple[str, str] | None = None,
                          http_version: str = "HTTP/1.1"):
    return (
            f'CONNECT {address[0]}:{address[1]} {http_version}\r\n'
            + f"Host: {address[0]}:{address[1]}\r\n"
            + (f'{proxy_auth_header(*credentials)}' if credentials else '')
            + '\r\n'
    ).encode()
