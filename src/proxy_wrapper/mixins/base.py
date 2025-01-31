import socket
from abc import ABC
from collections import deque
from queue import Queue

from proxy_wrapper.enums import ProxySocketState
from proxy_wrapper.proxy import Proxy
from proxy_wrapper.mixins.abc import AbstractProxiedSocket
from .socks5_sock import Socks5SocketMixin
from ..http.https_sock import HTTPSocketMixin


class BaseProxiedSocketMixin(AbstractProxiedSocket, Socks5SocketMixin, HTTPSocketMixin, ABC):
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        super().__init__(family, type, proto, fileno)

        self.proxy_chain: deque[Proxy] = deque()
        self.proxy_queue: Queue[Proxy] = Queue()
        self.state: ProxySocketState = ProxySocketState.INITIALIZED
        self.connecting_to_proxy = False

        self._last_callback = None
        self._last_connect_cb = None

    @classmethod
    def from_socket(cls, sock: socket.socket):
        instance = cls(sock.family, sock.type, sock.proto, sock.fileno())
        instance.setblocking(sock.getblocking())
        sock.detach()
        return instance

    def add_proxy(self, proxy: Proxy, *, perform_connection: bool | None = None):
        if perform_connection is not None:
            if self.getblocking():
                return self.connect_to_proxy(proxy)
            raise NotImplementedError("Non-blocking mode is not supported yet")
        self.proxy_queue.put(proxy)

    @property
    def proxy_connection_completed(self):
        return self.proxy_queue.empty()
