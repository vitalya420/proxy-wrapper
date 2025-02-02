from abc import ABC, abstractmethod


class AbstractProxyProtocol(ABC):
    """Anything that can .recv() and .send() can be using for proxying."""

    @abstractmethod
    def recv(self, n: int) -> bytes: ...

    @abstractmethod
    def send(self, data: bytes) -> int: ...

    @abstractmethod
    def getblocking(self) -> bool: ...
