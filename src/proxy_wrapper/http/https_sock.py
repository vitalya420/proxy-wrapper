import socket
from typing import Tuple

from .helper import craft_connect_request, read_http_response
from ..decorators import recv_non_blocking


class HTTPSocketMixin(socket.socket):
    """
    Mixin that implements the HTTP(s) proxy protocol.
    """

    def read_http_response(self):
        return read_http_response(self)

    def _http_connect_non_blocking(self, request: bytes):
        def send_request():
            nonlocal request
            print(f"http sending: {request}")
            self.send(request)
            read_response()

        @recv_non_blocking
        def read_response():
            response = self.read_http_response()
            print(f'{response=}')

        send_request()

    def _http_connect_blocking(self, request: bytes):
        self.sendall(request)
        response = self.read_http_response()
        print(f'{response=}')

    def http_connect(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None,
                     http_version: str = "HTTP/1.1"):
        req = craft_connect_request(address, credentials, http_version)
        if self.getblocking():
            return self._http_connect_blocking(req)
        return self._http_connect_non_blocking(req)

    def https_connect(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None):
        return self.http_connect(address, credentials, "HTTPS/1.1")
