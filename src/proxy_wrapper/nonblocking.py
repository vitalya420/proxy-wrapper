from collections.abc import Callable
from functools import partial, wraps

from proxy_wrapper.base import BaseProxiedSocket
from proxy_wrapper.callbacks_handler import cb_handler
from proxy_wrapper.enums import ProxyProtocol
from proxy_wrapper.exceptions import WantWriteError, _UncompletedRecv, WantReadError
from proxy_wrapper.protocols import ImplementsProxyProtocolsMixin
from proxy_wrapper.protocols.socks5.enums import ReplyStatus
from proxy_wrapper.proxy import Proxy


class _NonBlockingProxiedSocket(BaseProxiedSocket, ImplementsProxyProtocolsMixin):
    """
    Behavior if sock.getblocking() == False.
    Do not create instances of this class directly.
    Instead, use ProxiedSocket it inherits it.
    """

    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        super().__init__(family, type, proto, fileno)

        self._last_connect_cb: Callable | None = None
        self._last_connect_to_proxy_cb: Callable | None = None
        self._last_perform_cb: Callable | None = None

    def connect(self, address, /):
        if self._last_connect_cb:
            self._last_connect_cb()
            self._last_connect_cb = None
            return

        if self.in_command_mode:
            if self.does_user_called_connect():
                try:
                    self._connect_to_target_according_protocol(address)
                except _UncompletedRecv as e:
                    self._last_connect_cb = e.callback
                    raise WantReadError("Need to read data from proxy sever", callback=self._last_connect_cb)
            else:
                return self._connect_according_to_protocol(address)
        super().connect(address)

    def connect_to_proxy(self, proxy: Proxy):
        self.connecting_to_proxy = True
        self.proxy_to_connect = proxy

        try:
            self.connect(proxy.address)
            self._on_connected_and_raised_for_next_connection(proxy)
        except BlockingIOError:
            raise WantWriteError(message=".connect() called. Got BlockingIOError. Need to be writeable",
                                 callback=partial(self._on_connected_and_raised_for_next_connection, proxy))
        except _UncompletedRecv as e:
            def _continue_proxy_connection(cb):
                @wraps(cb)
                def inner():
                    cb()
                    self._on_connected_and_raised_for_next_connection(proxy)

                return inner

            raise WantReadError("", callback=_continue_proxy_connection(e.callback))

    @cb_handler
    def perform_connection(self):
        return self._raise_for_next_connection()

    def _connect_to_next_proxy(self):
        proxy = self.proxy_queue.get_nowait()
        self.connect_to_proxy(proxy)

    def _raise_for_next_connection(self):
        """
        Socket must be writeable.
        """
        if not self.proxy_queue.empty():
            raise WantWriteError("Socket must be writeable to connect to next proxy",
                                 callback=self._connect_to_next_proxy)

    def _on_connected_and_raised_for_next_connection(self, proxy: Proxy):
        self._on_connected_to_proxy(proxy)

    def _on_connected_to_proxy(self, proxy: Proxy):
        def _after_handshake(proxy_: Proxy):
            self.in_command_mode = True
            self.connecting_to_proxy = False
            self.proxy_to_connect = None
            self.proxy_chain.append(proxy_)

        def _socks5_cb(proxy_: Proxy):
            _after_handshake(proxy_)
            self._raise_for_next_connection()

        if proxy.protocol == ProxyProtocol.SOCKS5:
            return self.socks5_handshake(proxy.credentials, non_blocking_callback=partial(
                _socks5_cb, proxy_=proxy
            ))
        if proxy.protocol in (ProxyProtocol.HTTP, ProxyProtocol.HTTPS):
            _after_handshake(proxy)
            self._raise_for_next_connection()

    def _connect_according_to_protocol(self, address, to_target: bool = False):
        last_proxy = self.proxy_chain[-1]
        last_protocol_in_chain = last_proxy.protocol
        credentials = last_proxy.credentials

        if last_protocol_in_chain in (ProxyProtocol.HTTP, ProxyProtocol.HTTPS):
            return self.http_connect(address, credentials,
                                     partial(self._on_connected_via_http_proxy, to_target=to_target))
        if last_protocol_in_chain == ProxyProtocol.SOCKS5:
            return self.socks5_connect(address,
                                       partial(self._on_connected_via_socks5_proxy, to_target=to_target))

    def _connect_to_target_according_protocol(self, address):
        if self.connected_to_target:
            raise RuntimeError("Already connected to target")
        if not self.proxy_queue.empty():
            raise RuntimeError("Can't connect to target while proxy queue is not empty")
        self._connect_according_to_protocol(address, to_target=True)

    def _on_connected_via_http_proxy(self, success: bool, reason: str = '', to_target: bool = False):
        if not success:
            raise ConnectionError(f"HTTP proxy connection to {self.proxy_to_connect.address} failed. Reason: {reason}")

        if to_target:
            self.connected_to_target = True
            self.in_command_mode = False

    def _on_connected_via_socks5_proxy(self, success: bool, reason: ReplyStatus = '', to_target: bool = False):
        if not success:
            raise ConnectionError(
                f"SOCKS5 proxy connection to {self.proxy_to_connect.address} failed. Reason: {reason}")

        if to_target:
            self.connected_to_target = True
            self.in_command_mode = False
