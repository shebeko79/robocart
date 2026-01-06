import socket
import select

IP = "2a00:f41:908f:d834:fd7e:a3b2:62da:794e"
UDP_PORT = 5005


def process_client(sock, remote_addr):
    sel = select.select([sock], [sock], [sock], 0.1)

    name = "client"

    if len(sel[2]) != 0:
        print(f'{name}: error')
        exit(1)

    if len(sel[0]) != 0:
        data, addr = sock.recvfrom(50)
        print(f"{name}: recvfrom() {addr=}: {data.decode()}")

    if len(sel[1]) != 0:
        #print(f"{name}: sendto() {remote_addr=}: {name.encode('utf-8')}")
        sock.sendto(name.encode('utf-8'), remote_addr)


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

    sock_client = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock_client.bind(("", UDP_PORT+1))
    sock_client.setblocking(False)

    sock_server = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock_server.bind((IP, UDP_PORT))
    sock_server.setblocking(False)

    while True:
        process_client(sock_client, (IP, UDP_PORT))
        process_server(sock_server)
