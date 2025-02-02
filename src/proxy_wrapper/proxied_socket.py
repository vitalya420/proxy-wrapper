import socket
from typing import Callable

from proxy_wrapper.enums import ProxyProtocol
from proxy_wrapper.nonblocking import _NonBlockingProxiedSocket
from proxy_wrapper.proxy import Proxy


def call_super_for_nonblocking(meth: Callable):
    def inner(self: socket.socket, *args, **kwargs):
        if self.getblocking():
            return meth(self, *args, **kwargs)
        return getattr(super(self.__class__, self), meth.__name__)(*args, **kwargs)

    return inner


class ProxiedSocket(_NonBlockingProxiedSocket):
    @call_super_for_nonblocking
    def connect(self, address, /):
        if self.in_command_mode:
            if self.does_user_called_connect():
                return self._connect_to_target_according_protocol(address)
            else:
                return self._connect_according_to_protocol(address)
        return super().connect(address)

    @call_super_for_nonblocking
    def connect_to_proxy(self, proxy: Proxy):
        self.connecting_to_proxy = True
        self.proxy_to_connect = proxy

        # Be sure that this function is calling in 'blocking' mode
        self.connect(proxy.address)
        self._on_connected_to_proxy(proxy)

    @call_super_for_nonblocking
    def perform_connection(self):
        while not self.proxy_queue.empty():
            self._connect_to_next_proxy()

    @call_super_for_nonblocking
    def _connect_to_next_proxy(self):
        proxy = self.proxy_queue.get_nowait()
        self.connect_to_proxy(proxy)

    @call_super_for_nonblocking
    def _on_connected_to_proxy(self, proxy: Proxy):
        self.in_command_mode = True
        self.connecting_to_proxy = False
        self.proxy_to_connect = None
        self.proxy_chain.append(proxy)

    @call_super_for_nonblocking
    def _connect_according_to_protocol(self, address):
        last_proxy = self.proxy_chain[-1]
        last_protocol_in_chain = last_proxy.protocol
        credentials = last_proxy.credentials

        if last_protocol_in_chain in (ProxyProtocol.HTTP, ProxyProtocol.HTTPS):
            success = self.http_connect(address, credentials)
            if not success:
                raise ConnectionError("HTTP proxy connection failed")

    @call_super_for_nonblocking
    def _connect_to_target_according_protocol(self, address):
        if self.connected_to_target:
            raise RuntimeError("Already connected to target")
        if not self.proxy_queue.empty():
            raise RuntimeError("Can't connect to target while proxy queue is not empty")
        self._connect_according_to_protocol(address)
        self.connected_to_target = True
        self.in_command_mode = False
