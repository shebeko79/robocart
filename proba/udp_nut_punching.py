import socket
import select
import stun

UDP_PORT1 = 5005
UDP_PORT2 = 5006

STUN_SERVER = "stun.l.google.com"
#STUN_SERVER = "stun.nextcloud.com"
#STUN_SERVER = "stun4.l.google.com"

def process(name, sock, remote_addr):
    sel = select.select([sock], [sock], [sock], 0.5)

    if len(sel[2]) != 0:
        print(f'{name}: error')
        exit(1)

    if len(sel[0]) != 0:
        data, addr = sock.recvfrom(10)
        print(f"{name}: recvfrom() {addr=}: {data.decode()}")

    if len(sel[1]) != 0:
        print(f"{name}: sendto() {remote_addr=}: {name.encode('utf-8')}")
        sock.sendto(name.encode('utf-8'), remote_addr)


if __name__ == "__main__":

    nat_type, external_ip1, external_port1 = stun.get_ip_info("0.0.0.0", UDP_PORT1, stun_host=STUN_SERVER)
    print(f'{nat_type=} {external_ip1=} {external_port1=}')

    nat_type, external_ip2, external_port2 = stun.get_ip_info("0.0.0.0", UDP_PORT2, stun_host=STUN_SERVER)
    print(f'{nat_type=} {external_ip2=} {external_port2=}')

    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.bind(('0.0.0.0', UDP_PORT1))
    sock1.setblocking(False)

    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.bind(('0.0.0.0', UDP_PORT2))
    #sock2.bind(('192.168.45.55', UDP_PORT2))
    sock2.setblocking(False)

    while True:
        process("sock1", sock1, (external_ip2, external_port2))
        process("sock2", sock2, (external_ip1, external_port1))
