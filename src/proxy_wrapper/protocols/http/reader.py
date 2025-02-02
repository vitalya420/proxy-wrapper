import asyncio
import json
import socket
from dataclasses import dataclass
from functools import partial
from typing import Callable, Dict, Any

from proxy_wrapper.callbacks_handler import cb_handler
from proxy_wrapper.exceptions import _UncompletedRecv


@dataclass
class HTTPResponse:
    http_version: str
    status_code: int
    status_phrase: str
    headers: Dict[str, str]
    body: bytes

    def json(self):
        return json.loads(self.body)


async def read_http_response_async(sock: socket.socket):
    loop = asyncio.get_event_loop()
    fut = loop.create_future()

    def handle_done(response: HTTPResponse):
        if not fut.done():
            fut.set_result(response)

    def continue_reading():
        nonlocal loop
        loop.remove_reader(sock.fileno())
        _continue_reading()

    def _continue_reading():
        try:
            read_http_response_continuable(sock, handle_done)
        except _UncompletedRecv:
            loop.add_reader(sock.fileno(), continue_reading)

    _continue_reading()
    return await fut


@cb_handler
def read_http_response_continuable(sock: socket.socket,
                                   non_blocking_callback: Callable[[
                                       HTTPResponse], Any] | None = None) -> HTTPResponse | None:
    return read_http_response(sock, non_blocking_callback)


def read_http_response(sock: socket.socket,
                       non_blocking_callback: Callable[[HTTPResponse], Any] | None = None) -> HTTPResponse | None:
    """
    Returns HTTPResponse in blocking mode else calls non_blocking_callback and passes HTTPResponse as first
    argument
    """
    status_line = b''
    headers = b''
    headers_dict: Dict[str, str] = {}
    http_version = ''
    status_code = -1
    status_phrase = ''
    body = b''
    bytes_read = 0

    def read_status_line():
        nonlocal status_line

        while not status_line.endswith(b'\r\n'):
            try:
                byte_ = sock.recv(1)
                if not byte_:
                    raise ConnectionError("Server closed connection")
                status_line += byte_
            except BlockingIOError:
                raise _UncompletedRecv(message="Reading status line does not completed.", callback=read_status_line)
        return read_headers()

    def read_headers():
        nonlocal headers

        while not headers.endswith(b'\r\n\r\n'):
            try:
                byte_ = sock.recv(1)
                if not byte_:
                    raise ConnectionError("Server closed connection")
                headers += byte_
                if headers == b'\r\n':
                    break
            except BlockingIOError:
                raise _UncompletedRecv(message="Reading headers does not completed.", callback=read_headers)

        return parse()

    def parse():
        nonlocal status_line, headers, headers_dict, status_code, status_phrase, http_version

        status_line = status_line.removesuffix(b'\r\n').decode('utf-8')
        headers = headers.decode('utf-8')

        http_version, status_code, *status_phrase = status_line.split(" ")
        status_code = int(status_code)
        status_phrase = " ".join(status_phrase)

        for line in headers.split('\r\n'):
            if not line or ": " not in line:
                continue
            key, value = line.split(": ", 1)
            headers_dict[key.lower()] = value

        is_chunked = headers_dict.get("transfer-encoding", "").lower() == "chunked"
        content_length = int(headers_dict.get("content-length", 0))

        if is_chunked or content_length:
            return read_body(content_length, is_chunked)
        else:
            return call_callback_or_return()

    def call_callback_or_return():
        nonlocal http_version, status_code, status_phrase, headers_dict, body
        nonlocal non_blocking_callback
        res = HTTPResponse(http_version, status_code, status_phrase, headers_dict, body)
        if not sock.getblocking() and non_blocking_callback:
            return non_blocking_callback(res)
        return res

    def read_body(length: int | None, is_chunked: bool = False):
        if length and is_chunked:
            raise ValueError("Cannot read body with both content-length and transfer-encoding")
        if length:
            return read_content_length(length)
        if is_chunked:
            return read_chunked()

    def read_chunked():
        """
        Will implement later
        """
        raise NotImplementedError("Chunked transfer encoding is not implemented yet")

    def read_content_length(length):
        nonlocal bytes_read, body
        while bytes_read < length:
            chunk_size = min(4096, length - bytes_read)
            try:
                chunk = sock.recv(chunk_size)
                if not chunk:
                    raise ConnectionError("Server closed connection")
                body += chunk
                bytes_read += len(chunk)
            except BlockingIOError:
                raise _UncompletedRecv(message="Reding body does not completed.",
                                       callback=partial(read_content_length, length))

        return call_callback_or_return()

    return read_status_line()
