from abc import ABC

from proxy_wrapper.protocols.http import HTTPProxyProtocol
from proxy_wrapper.protocols.socks5 import Socks5ProxyProtocol


class ImplementsProxyProtocolsMixin(
    Socks5ProxyProtocol, HTTPProxyProtocol, ABC
):
    pass


__all__ = [
    'ImplementsProxyProtocolsMixin',
    'HTTPProxyProtocol',
    'Socks5ProxyProtocol'
]
