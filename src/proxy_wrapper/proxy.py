from typing import NamedTuple, Tuple

from proxy_wrapper.enums import ProxyProtocol


class Proxy(NamedTuple):
    protocol: ProxyProtocol
    address: Tuple[str, int]
    credentials: Tuple[str, str] | None = None

