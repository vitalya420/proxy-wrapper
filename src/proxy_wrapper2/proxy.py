from dataclasses import dataclass
from typing import Literal, Tuple

from proxy_wrapper2.enums import ProxyProtocol

_ProtocolLike = ProxyProtocol | Literal["socks5", "socks4", "http"]
_ProxyTuple = Tuple[_ProtocolLike, Tuple[str, int], Tuple[str, str] | Tuple[None, None] | None]


@dataclass
class Proxy:
    protocol: _ProtocolLike
    address: Tuple[str, int]
    credentials: Tuple[str, str] | Tuple[None, None] | None = None

    def __post_init__(self):
        if isinstance(self.protocol, str):
            self.protocol = ProxyProtocol(self.protocol)

        if isinstance(self.credentials, Tuple):
            if self.credentials[0] is None and self.credentials[1] is None:
                self.credentials = None

    @classmethod
    def from_tuple(cls, proxy: _ProxyTuple):
        return cls(*proxy)
