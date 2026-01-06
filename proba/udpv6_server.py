import socket
import select

UDP_PORT = 5005


def process_server(sock):
    sel = select.select([sock], [sock], [sock], 0.1)

    name = "server"

    if len(sel[2]) != 0:
        print(f'{name}: error')
        exit(1)

    if len(sel[0]) != 0:
        data, addr = sock.recvfrom(50)
        print(f"{name}: recvfrom() {addr=}: {data.decode()}")

        if len(sel[1]) != 0:
            sock.sendto(name.encode('utf-8'), addr)


if __name__ == "__main__":

    sock_server = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock_server.bind(("", UDP_PORT))
    sock_server.setblocking(False)

    while True:
        process_server(sock_server)
