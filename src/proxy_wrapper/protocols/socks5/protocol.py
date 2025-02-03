from abc import ABC
from typing import Tuple, Callable, Any

from proxy_wrapper.decorators import send_non_blocking, recv_non_blocking
from proxy_wrapper.protocols.base import AbstractProxyProtocol
from proxy_wrapper.protocols.socks5.enums import ATYP
from proxy_wrapper.protocols.socks5.exceptions import ProxyConnectionClosed
from proxy_wrapper.protocols.socks5.helper import craft_hello_message, loads_hello_response, \
    craft_username_password_message, request_to_connect_to_remote_address, loads_reply


class Socks5ProxyProtocol(AbstractProxyProtocol, ABC):
    def _send_socks5_handshake_nonblocking(self, credentials: Tuple[str, str] | None = None,
                                           on_completed: Callable[[], Any] | None = None):
        hello = craft_hello_message(credentials)
        auth = craft_username_password_message(*credentials) if credentials else None

        @send_non_blocking
        def send_hello():
            nonlocal hello
            self.send(hello.to_bytes())
            read_hello_response()

        @recv_non_blocking
        def read_hello_response():
            data = self.recv(2)
            hello_response = loads_hello_response(data)

            if hello_response.requires_credentials():
                return send_auth()
            else:
                return call_callback()

        @send_non_blocking
        def send_auth():
            nonlocal auth
            self.send(auth.to_bytes())

        def call_callback():
            if on_completed is not None:
                on_completed()

        send_hello()

    def _send_socks5_handshake_blocking(self, credentials: Tuple[str, str] | None = None):
        print("sending socks5 handshake")

    def _send_socks5_connect_nonblocking(self, address: Tuple[str, int],
                                         on_completed: Callable[[bool, str], Any] | None = None):
        req = request_to_connect_to_remote_address(address)
        initial_reply = b''

        @send_non_blocking
        def send_req():
            nonlocal req
            self.send(req.to_bytes())
            read_response()

        @recv_non_blocking
        def read_response():
            nonlocal initial_reply
            initial_reply = self.recv(4)

            if not initial_reply:
                raise ProxyConnectionClosed(
                    "Proxy connection closed while waiting for initial response")
            atyp = initial_reply[3]
            if atyp == ATYP.IPV4:
                return read_remaining(6)
            if atyp == ATYP.DOMAIN_NAME:
                return read_domain()
            if atyp == ATYP.IPV6:
                return read_domain(18)
            raise ValueError(f"Unknown ATYP: {atyp}")

        @recv_non_blocking
        def read_remaining(length):
            remaining_data = self.recv(length)
            full_reply = initial_reply + remaining_data
            reply = loads_reply(full_reply)

            if on_completed is not None and callable(on_completed):
                on_completed(reply.is_ok(), reply.rep)

        @recv_non_blocking
        def read_domain():
            length = self.recv(1)
            domain_length = length[0] if length else 0
            remaining_length = 1 + domain_length + 2
            return read_remaining(remaining_length)

        send_req()

    def _send_socks5_connect_blocking(self, address: Tuple[str, int]):
        pass

    def socks5_handshake(self, credentials: Tuple[str, str] | None = None,
                         non_blocking_callback: Callable[[], Any] | None = None):
        if self.getblocking():
            return self._send_socks5_handshake_blocking(credentials)
        return self._send_socks5_handshake_nonblocking(credentials, non_blocking_callback)

    def socks5_connect(self, address: Tuple[str, int],
                       non_blocking_callback: Callable[[bool, str], Any] | None = None):
        if self.getblocking():
            return self._send_socks5_connect_blocking(address)
        return self._send_socks5_connect_nonblocking(address, non_blocking_callback)
