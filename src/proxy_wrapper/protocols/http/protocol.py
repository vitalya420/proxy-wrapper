import socket
from typing import Callable, Tuple, Any

from proxy_wrapper.decorators import send_non_blocking, recv_non_blocking
from proxy_wrapper.protocols.base import AbstractProxyProtocol
from proxy_wrapper.protocols.http.helper import craft_connect_request
from proxy_wrapper.protocols.http.reader import read_http_response, HTTPResponse


class HTTPProxyProtocol(socket.socket, AbstractProxyProtocol):
    def _send_connect_nonblocking(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None,
                                  on_completed: Callable[[bool, str], Any] | None = None):
        request = craft_connect_request(address, credentials)
        response: HTTPResponse | None = None

        @send_non_blocking
        def send_request():
            nonlocal request
            self.send(request)
            return read_response()

        @recv_non_blocking
        def read_response():
            nonlocal response
            read_http_response(self, on_response_read)

        def on_response_read(res: HTTPResponse):
            nonlocal on_completed
            if on_completed is not None:
                on_completed(res.status_code == 200, reason=res.status_phrase)

        return send_request()

    def _send_connect_blocking(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None):
        request = craft_connect_request(address, credentials)
        self.send(request)
        response = read_http_response(self)
        return response.status_code == 200

    def http_connect(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None,
                     non_blocking_callback: Callable | None = None):
        if self.getblocking():
            return self._send_connect_blocking(address, credentials)
        return self._send_connect_nonblocking(address, credentials, non_blocking_callback)
