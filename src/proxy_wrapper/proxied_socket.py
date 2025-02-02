from functools import partial, wraps
from typing import Callable, Dict, Tuple

from proxy_wrapper.enums import ProxySocketState, ProxyProtocol
from proxy_wrapper.proxy import Proxy
from proxy_wrapper.exceptions import WantWriteError, WantReadError, _UncompletedRecv
from proxy_wrapper.mixins.base import BaseProxiedSocketMixin


class CallbackHandler(Dict[Callable, Callable]):

    def __call__(self, func: Callable):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                if func in self:
                    callback = self.pop(func)
                    return callback()
                return func(*args, **kwargs)
            except (WantWriteError, WantReadError) as e:
                self[func] = e.callback
                raise

        return inner


callback_handler = CallbackHandler()


class _NonBlockingProxiedSocket(BaseProxiedSocketMixin):
    """Default behaviour"""

    def _connect_according_to_protocol(self, address: Tuple[str, int]):
        try:
            meth = getattr(self, f"{self.proxy_chain[-1].protocol.value}_connect")
            return meth(address)
        except AttributeError:
            print(self.proxy_chain)
            raise ValueError(f"Unknown protocol: {self.proxy_chain[-1].protocol.value}")

    def connect(self, address, /):
        if self.state == ProxySocketState.IN_COMMAND_MODE:
            if self.proxy_connection_completed and not self.connecting_to_proxy:
                # User called .connect()
                try:
                    if self._last_connect_cb:
                        self._last_connect_cb()
                        self._last_connect_cb = None
                        return
                    return self._connect_according_to_protocol(address)
                except _UncompletedRecv as e:
                    self._last_connect_cb = e.callback
                    raise WantReadError("I need to read  some data", callback=e.callback)
            return self._connect_according_to_protocol(address)
        super().connect(address)

    def on_handshake_completed(self, proxy: Proxy):
        self.proxy_chain.append(proxy)
        self.state = ProxySocketState.IN_COMMAND_MODE
        self.connecting_to_proxy = False
        if not self.proxy_queue.empty():
            raise WantWriteError("Handshake is completed", callback=self._connect_to_next_proxy)

    def on_connected_to_proxy(self, proxy: Proxy):
        try:
            if proxy.protocol == ProxyProtocol.SOCKS5:
                self.send_socks5_handshake(proxy.credentials, partial(self.on_handshake_completed, proxy))
            elif proxy.protocol in (ProxyProtocol.HTTP, ProxyProtocol.HTTPS):
                self.on_handshake_completed(proxy)
        except _UncompletedRecv as e:
            raise WantReadError("I need to read  some data", callback=e.callback)

    def connect_to_proxy(self, proxy: Proxy):
        self.connecting_to_proxy = True
        try:
            self.connect(proxy.address)
            self.on_connected_to_proxy(proxy)
        except BlockingIOError:
            raise WantWriteError("Connection to proxy is not completed yet",
                                 callback=partial(self.on_connected_to_proxy, proxy))
        except _UncompletedRecv as e:
            def create_continuation(cb):
                def inner():
                    cb()
                    self.on_connected_to_proxy(proxy)

                return inner

            raise WantReadError("I need to read  some data", callback=create_continuation(e.callback))

    def _connect_to_next_proxy(self):
        if self.proxy_queue.empty():
            return
        proxy = self.proxy_queue.get_nowait()
        self.proxy_queue.task_done()
        self.connect_to_proxy(proxy)

    def perform_connection(self):
        try:
            if self._last_callback:
                self._last_callback()
                self._last_callback = None
                return
            self._connect_to_next_proxy()
        except (WantWriteError, WantReadError) as e:
            self._last_callback = e.callback
            raise


class ProxiedSocket(_NonBlockingProxiedSocket):
    def connect_to_proxy(self, proxy: Proxy):
        if not self.getblocking():
            return super().connect_to_proxy(proxy)
        print("connecting to proxy in blocking mode")

    def perform_connection(self):
        if not self.getblocking():
            return super().perform_connection()
        print("performing in blocking mode")
