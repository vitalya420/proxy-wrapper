from functools import partial, wraps
from typing import Callable

from proxy_wrapper.exceptions import _UncompletedRecv, _UncompletedSend, WantReadError, WantWriteError


def recv_non_blocking(func: Callable):
    """
    Decorator to handle non-blocking I/O operations for functions that call .recv().

    This decorator is designed to wrap functions that perform non-blocking
    socket operations using the .recv() method. When the I/O source is
    non-blocking and the .recv() call raises a BlockingIOError, this
    decorator will catch the exception and raise a custom
    _UncompletedRecv exception. This exception includes a callback that
    allows the original function to be retried once the I/O source is ready.

    Note:
        - Ensure that the decorated function contains only one call to .recv().
        - The callback provided in the _UncompletedRecv exception can be used
          to retry the function when the I/O operation can proceed.

    Args:
        func (Callable): The function to be decorated, which is expected to
                         call .recv().

    Returns:
        Callable: A wrapped version of the input function that handles
                   BlockingIOError exceptions and raises _UncompletedRecv.

    Raises:
        _UncompletedRecv: If a BlockingIOError is encountered, indicating
                          that the .recv() call could not be completed
                          because the I/O source was not ready.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BlockingIOError:
            wrapped_again = recv_non_blocking(func)
            raise _UncompletedRecv(message=f"{func.__name__} called .recv() but io was not ready yet. Call callback "
                                           f"to recall this function", callback=partial(wrapped_again, *args, **kwargs))

    return wrapper


def send_non_blocking(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BlockingIOError:
            wrapped_again = recv_non_blocking(func)
            raise _UncompletedSend(message=f"{func.__name__} called .recv() but io was not ready yet. Call callback "
                                           f"to recall this function", callback=partial(wrapped_again, *args, **kwargs))

    return wrapper


def uncompleted2want(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except _UncompletedRecv as e:
            return WantReadError(message=f"{func.__name__} called .recv() but io was not ready yet. Call callback "
                                         f"to recall this function", callback=e.callback)
        except _UncompletedSend as e:
            return WantWriteError(message=f"{func.__name__} called .send() but io was not ready yet. Call callback ",
                                  callback=e.callback)

    return wrapper
