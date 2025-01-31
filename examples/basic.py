import asyncio
import logging
import socket

from proxy_wrapper import wrap_socket, wrap_socket_async, connect_socket_to_address_async

logging.getLogger().setLevel(logging.DEBUG)


def create_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxied = wrap_socket(s, "socks5://127.0.0.1:9050")
    return proxied


async def create_socket_async():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxied = await wrap_socket_async(s, "socks5://127.0.0.1:9050", "http://123.16.135.43:10017")
    return proxied


async def recv_until_eof(sock):
    loop = asyncio.get_running_loop()

    total_data = b''

    while True:
        try:
            data = await loop.sock_recv(sock, 4096)
        except ConnectionResetError:
            break
        if not data:
            break
        total_data += data

    return total_data


async def main():
    loop = asyncio.get_running_loop()
    # socks = [create_socket() for _ in range(200)]
    # perform_connecting(socks)
    # print(socks)

    socks = await asyncio.gather(*(create_socket_async() for _ in range(1)))
    await asyncio.gather(*(connect_socket_to_address_async(s, ("httpbin.org", 80)) for s in socks))

    request = b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r"
    await asyncio.gather(*[loop.sock_sendall(s, request) for s in socks])
    await asyncio.gather(*[loop.sock_sendall(s, b"\n") for s in socks])
    results = await asyncio.gather(*(recv_until_eof(s) for s in socks))
    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
