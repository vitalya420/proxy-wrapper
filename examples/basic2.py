import asyncio
import select
import socket

from proxy_wrapper.exceptions import WantReadError, WantWriteError
from proxy_wrapper2.wrapper import wrap_socket


def create_proxied_socket():
    sock = socket.socket()
    # sock.connect(("127.0.0.1", 9050))
    # sock.setblocking(False)
    wrapped = wrap_socket(sock, "https://15.235.141.213:10002")
    return wrapped


def on_read(res):
    print(res)


async def create_socket():
    loop = asyncio.get_running_loop()

    sock = socket.socket()
    sock.setblocking(False)
    await loop.sock_connect(sock, ("httpbin.org", 80))
    await loop.sock_sendall(sock, b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")

    return sock


async def main():
    proxied = create_proxied_socket()

    connected = False
    while not connected:
        try:
            proxied.perform_connection()
            print("Connected", proxied.proxy_chain)
            connected = True
        except WantReadError as e:
            select.select([proxied], [], [])
        except WantWriteError as e:
            # print(e)
            select.select([], [proxied], [])

    connected = False
    while not connected:
        try:
            proxied.connect(("54.209.95.91", 80))
            print("Connected2", proxied.connected_to_target)
            connected = True
        except WantReadError as e:
            select.select([proxied], [], [])
        except WantWriteError as e:
            # print(e)
            select.select([], [proxied], [])

    as_sock = proxied.to_socket()
    as_sock.setblocking(True)
    # proxied.connect(("54.209.95.91", 80))
    as_sock.send(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
    print(as_sock.recv(4096))


if __name__ == '__main__':
    asyncio.run(main())
