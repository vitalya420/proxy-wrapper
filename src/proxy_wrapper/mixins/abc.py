import socket
from abc import ABC, abstractmethod

from proxy_wrapper.proxy import Proxy


class AbstractProxiedSocket(ABC):


    @classmethod
    @abstractmethod
    def from_socket(cls, sock: socket.socket):
        pass

    @abstractmethod
    def add_proxy(self, proxy: Proxy, *, perform_connection: bool | None = None):
        pass

    @abstractmethod
    def connect_to_proxy(self, proxy: Proxy):
        pass

    @abstractmethod
    def perform_connection(self):
        pass
