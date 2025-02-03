import asyncio
import select
import socket
import ssl

from proxy_wrapper.exceptions import WantReadError, WantWriteError
from proxy_wrapper.protocols.http.reader import read_http_response
from proxy_wrapper.wrapper import wrap_socket


def create_proxied_socket():
    sock = socket.socket()
    # sock.connect(("127.0.0.1", 9050))
    sock.setblocking(False)
    wrapped = wrap_socket(sock, "socks5://127.0.0.1:9050",
                          "https://49.0.91.7:8080")  # "https://36.103.167.209:7890"
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
            proxied.connect(("54.209.95.91", 443))
            print("Connected2", proxied.connected_to_target)
            connected = True
        except WantReadError as e:
            select.select([proxied], [], [])
        except WantWriteError as e:
            # print(e)
            select.select([], [proxied], [])

    ctx = ssl.create_default_context()

    # proxied.connect(("54.209.95.91", 443))
    #
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    as_sock = proxied.to_socket()
    as_sock.setblocking(True)
    print(as_sock)
    as_sock = ctx.wrap_socket(as_sock, do_handshake_on_connect=False)
    # proxied.connect(("54.209.95.91", 80))
    as_sock.send(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
    res = read_http_response(as_sock)
    print(res)


if __name__ == '__main__':
    asyncio.run(main())
