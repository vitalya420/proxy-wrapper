from abc import ABC
from typing import Tuple, Callable, Any

from proxy_wrapper.protocols.base import AbstractProxyProtocol


class Socks5ProxyProtocol(AbstractProxyProtocol, ABC):
    def _send_socks5_handshake_nonblocking(self, credentials: Tuple[str, str] | None = None,
                                           on_completed: Callable[[], Any] | None = None):
        pass

    def _send_socks5_handshake_blocking(self, credentials: Tuple[str, str] | None = None):
        print("sending socks5 handshake")

    def _send_socks5_connect_nonblocking(self, address: Tuple[str, int], on_completed: Callable[[], Any] | None = None):
        pass

    def _send_socks5_connect_blocking(self, address: Tuple[str, int]):
        pass

    def socks5_handshake(self, credentials: Tuple[str, str] | None = None,
                         on_completed: Callable[[], Any] | None = None):
        if self.getblocking():
            return self._send_socks5_handshake_blocking(credentials)
        return self._send_socks5_handshake_nonblocking(credentials, on_completed)
