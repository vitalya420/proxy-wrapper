import socket
from abc import abstractmethod, ABC
from collections import deque
from queue import Queue

from proxy_wrapper.proxy import Proxy


class AbstractProxiedSocket(socket.socket):

    @classmethod
    @abstractmethod
    def from_socket(cls, sock: socket.socket): ...

    @abstractmethod
    def to_socket(self) -> socket.socket: ...

    @abstractmethod
    def add_proxy(self, proxy: Proxy): ...

    @abstractmethod
    def connect_to_proxy(self, proxy: Proxy): ...

    @abstractmethod
    def perform_connection(self): ...


class BaseProxiedSocket(AbstractProxiedSocket, ABC):
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        super().__init__(family, type, proto, fileno)

        self.proxy_chain: deque[Proxy] = deque()
        self.proxy_queue: Queue[Proxy] = Queue()
        self.in_command_mode: bool = False  # call socket's connect() or send connect message
        self.connecting_to_proxy: bool = False
        self.proxy_to_connect: Proxy | None = None
        self.connected_to_target: bool = False  # When user called .connect() then adding proxy will be disallowed

    @classmethod
    def from_socket(cls, sock: socket.socket):
        instance = cls(sock.family, sock.type, sock.proto, sock.fileno())
        instance.setblocking(sock.getblocking())
        sock.detach()
        return instance

    def to_socket(self, *, force: bool = False) -> socket.socket:
        if self.in_command_mode:
            raise RuntimeError("Socket is in command mode. Use force=True you know what you are doing.")
        s = socket.fromfd(self.fileno(), self.family, self.type, self.proto)
        s.setblocking(self.getblocking())
        return s

    def add_proxy(self, proxy: Proxy):
        if self.connected_to_target:
            raise RuntimeError("Adding proxy to connected socket is not allowed.")
        self.proxy_queue.put(proxy)

    def does_user_called_connect(self):
        return not self.connecting_to_proxy
