import weakref
from collections import deque
from functools import wraps
from typing import Dict, Callable

from proxy_wrapper.exceptions import WantReadError, WantWriteError, _UncompletedRecv, _UncompletedSend


class CallbacksHandler:
    def __init__(self):
        self.callbacks: Dict[weakref.ref, deque] = {}

    def __call__(self, func: Callable):
        @wraps(func)
        def inner(sock, *args, **kwargs):
            sock_ref = weakref.ref(sock)

            try:
                if sock_ref in self.callbacks and self.callbacks[sock_ref]:
                    callback = self.callbacks[sock_ref].popleft()
                    return callback()

                return func(sock, *args, **kwargs)
            except (WantReadError, WantWriteError) as e:
                self.callbacks.setdefault(sock_ref, deque()).append(e.callback)
                raise
            except _UncompletedRecv as e:
                self.callbacks.setdefault(sock_ref, deque()).append(e.callback)
                raise WantReadError(message=f"{func.__name__} called .recv() but io was not ready yet. Call callback ",
                                    callback=e.callback)
            except _UncompletedSend as e:
                self.callbacks.setdefault(sock_ref, deque()).append(e.callback)
                raise WantWriteError(message=f"{func.__name__} called .send() but io was not ready yet. Call callback ",
                                     callback=e.callback)

        return inner


cb_handler = CallbacksHandler()
