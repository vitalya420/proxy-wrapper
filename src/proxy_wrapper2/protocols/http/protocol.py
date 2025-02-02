import socket
from typing import Callable, Tuple, Any

from proxy_wrapper.exceptions import WantReadError, _UncompletedSend, _UncompletedRecv
from proxy_wrapper2.protocols.base import AbstractProxyProtocol
from proxy_wrapper2.protocols.http.helper import craft_connect_request
from proxy_wrapper2.protocols.http.reader import read_http_response, HTTPResponse


class HTTPProxyProtocol(socket.socket, AbstractProxyProtocol):
    def _send_connect_nonblocking(self, address: Tuple[str, int], credentials: Tuple[str, str] | None = None,
                                  on_completed: Callable[[bool], Any] | None = None):
        request = craft_connect_request(address, credentials)
        response: HTTPResponse | None = None

        def send_request():
            nonlocal request
            try:
                self.send(request)
            except BlockingIOError:
                raise _UncompletedSend(message="Sending request to connect", callback=send_request)

            return read_response()

        def read_response():
            nonlocal response
            try:
                response = read_http_response(self)
            except WantReadError as e:
                raise _UncompletedRecv(message="Reading response from connect", callback=read_response)

            return call_callback_or_return()

        def call_callback_or_return():
            nonlocal response, on_completed
            if not self.getblocking() and on_completed:
                return on_completed(response.status_code == 200)
            return response.status_code == 200

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
