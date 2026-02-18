import sys
import socket
import select


class Peer:
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.bind(('', port))
        self.sock.setblocking(False)

        self.data_to_send = None
        self.addr = None


if len(sys.argv) < 2:
    print(f"Use: {sys.argv[0]} <udp_port1> <udp_port2>")
    exit(1)

peer1 = Peer(int(sys.argv[1]))
peer2 = Peer(int(sys.argv[2]))


socks_array = [peer1.sock, peer2.sock]
read_array = []
write_array = []


def add_sock(send_peer, receive_peer):
    global socks_array
    global read_array
    global write_array

    if send_peer.data_to_send is not None:
        if send_peer.addr is not None:
            write_array.append(send_peer.sock)
    else:
        read_array.append(receive_peer.sock)


def do_receive(receive_peer, data_peer, read_sel):
    if receive_peer.sock in read_sel:
        data_peer.data_to_send, receive_peer.addr = receive_peer.sock.recvfrom(65535)


def do_send(peer, write_sel):
    if peer.sock in write_sel:
        peer.sock.sendto(peer.data_to_send, peer.addr)
        peer.data_to_send = None


while True:
    read_array = []
    write_array = []

    add_sock(peer1, peer2)
    add_sock(peer2, peer1)

    sel = select.select(read_array, write_array, socks_array, 1.0)

    if len(sel[2]) != 0:
        print(f'socket error')
        exit(1)

    do_receive(peer1, peer2, sel[0])
    do_receive(peer2, peer1, sel[0])

    do_send(peer1, sel[1])
    do_send(peer2, sel[1])
