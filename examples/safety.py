import socket
from threading import Thread


def create_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 5555))
    s.listen(1)
    client, _ = s.accept()
    client.send(b"1")
    client.recv(1024)
    return s


def create_client():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 5555))
    s.setblocking(False)
    return s


def main():
    server_thread = Thread(target=create_server)
    server_thread.start()

    client = create_client()
    print(client.recv(1))


main()