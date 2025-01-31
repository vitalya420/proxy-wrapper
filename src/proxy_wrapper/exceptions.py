from typing import Callable


class ProxyWrapperException(Exception):
    pass


class CannotWrapSocket(ProxyWrapperException):
    pass


class WantWriteError(ProxyWrapperException):
    def __init__(self, message: str = "", callback: Callable = None):
        super().__init__(message)
        self.callback = callback


class WantReadError(ProxyWrapperException):
    def __init__(self, message: str = "", callback: Callable = None):
        super().__init__(message)
        self.callback = callback


class _UncompletedRecv(ProxyWrapperException):
    def __init__(self, callback: Callable, message: str):
        self.callback = callback
        self.message = message
        super().__init__(message)


class _UncompletedSend(ProxyWrapperException):
    def __init__(self, callback: Callable, message: str):
        self.callback = callback
        self.message = message
        super().__init__(message)
