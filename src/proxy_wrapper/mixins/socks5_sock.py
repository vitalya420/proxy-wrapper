import socket
from typing import Tuple, Callable

import proxy_wrapper.socks5.helper as socks5_helper
from proxy_wrapper.socks5.enums import ATYP
from proxy_wrapper.socks5.exceptions import ProxyError
from proxy_wrapper.decorators import recv_non_blocking


class Socks5SocketMixin(socket.socket):

    def send_socks5_handshake(self, credentials: Tuple[str, int] = None, non_blocking_callback: Callable | None = None):
        hello_message = socks5_helper.craft_hello_message(credentials)

        def send_hello():
            nonlocal hello_message
            self.send(hello_message.to_bytes())
            read_reply()

        @recv_non_blocking
        def read_reply():
            reply = socks5_helper.loads_hello_response(self.recv(2))
            if reply.requires_credentials():
                raise NotImplementedError("Later")


            nonlocal non_blocking_callback
            if non_blocking_callback:
                non_blocking_callback()

        send_hello()

    def socks5_connect(self, address: Tuple[str, int], on_completed: Callable | None = None):
        connect_message = socks5_helper.request_to_connect_to_remote_address(address)
        initial_reply = b""

        def send_connect():
            nonlocal connect_message
            print(connect_message)
            self.send(connect_message.to_bytes())

            check_connect_reply()

        @recv_non_blocking
        def check_connect_reply():
            nonlocal initial_reply, address
            initial_reply = self.recv(4)

            if len(initial_reply) < 4:
                raise ValueError("Incomplete SOCKS5 reply header received.")
            atyp = ATYP(initial_reply[3])
            if atyp == ATYP.IPV4:
                return read_remaining(6)
            elif atyp == ATYP.DOMAIN_NAME:
                return read_domain_len()
            elif atyp == ATYP.IPV6:
                return read_remaining(18)
            else:
                raise ValueError("Invalid address type.")

        @recv_non_blocking
        def read_domain_len():
            domain_length_byte = self.recv(1)
            domain_length = domain_length_byte[0] if domain_length_byte else 0
            return read_remaining(1 + domain_length + 2)

        @recv_non_blocking
        def read_remaining(size: int):
            nonlocal initial_reply
            remaining_data = self.recv(size)
            full_reply = initial_reply + remaining_data
            reply = socks5_helper.loads_reply(full_reply)

            nonlocal address
            if reply.is_ok():
                nonlocal on_completed
                if on_completed:
                    on_completed()
            else:
                raise ProxyError("Error occurred during connection.")

        send_connect()
