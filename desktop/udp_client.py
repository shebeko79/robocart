import socket
import select
import threading
import time
from packet_processor import PacketProcessor

CONNECTION_EXPIRE_TIMEOUT = 60
KEEP_ALIVE_PERIOD = 10


class UdpClient(PacketProcessor):
    def __init__(self, host_name, port, json_sig, jpeg_sig):
        super().__init__()
        self.sock: socket.socket = None
        self.host_name = host_name
        self.port = port
        self.addr = None
        self.json_sig = json_sig
        self.jpeg_sig = jpeg_sig
        self.last_received_packet_number = 0
        self.last_received_time = 0
        self.last_send_time = 0
        self.thr = None
        self.thread_alive = True

    def resolve_addr(self):
        res = socket.getaddrinfo(self.host_name, None)

        r = res[0]
        proto = r[0]
        self.addr = (r[4][0], self.port)

        if self.sock:
            self.sock.close()

        self.sock = socket.socket(proto, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

    def process(self):
        t = int(time.time())
        if t >= self.last_received_time + CONNECTION_EXPIRE_TIMEOUT:
            self.addr = None

        if self.addr is None and self.thr is not None:
            self.thread_alive = False
            self.thr.join()
            self.thr = None

        if self.addr is None:
            self.resolve_addr()
            if self.addr is None:
                return

            self.last_received_packet_number = 0
            self.last_received_time = t
            self.last_send_time = 0

        if len(self.packets) == 0 and t >= self.last_send_time + KEEP_ALIVE_PERIOD:
            self.packets.append(self.pack_json({}))

        sel = select.select([], [self.sock], [self.sock], 0)

        if len(sel[2]) != 0:
            print('UdpClient.do_send() socket error')
            return

        if len(sel[1]) == 0:
            return

        bts = self.pack()
        if bts is None:
            return

        self.sock.sendto(bts, self.addr)
        self.last_send_time = t

        if self.thr is None:
            self.thread_alive = True
            self.thr = threading.Thread(target=self._loop, daemon=True)
            self.thr.start()

    def is_alive(self):
        return self.addr is not None and self.last_received_packet_number > 0

    @staticmethod
    def is_same_address(a, b):
        if len(a) < 2 or len(b) < 2:
            return a == b
        return a[0] == b[0] and a[1] == b[1]

    def _loop(self):
        while self.thread_alive:
            sel = select.select([self.sock], [], [self.sock], 1.0)

            if len(sel[2]) != 0:
                print('UdpClient._loop() socket error')
                self.addr = None
                return

            if len(sel[0]) == 0:
                continue

            data, addr = self.sock.recvfrom(65536)
            if not self.is_same_address(addr, self.addr):
                continue

            pack_n = self.get_packet_number(data)
            if pack_n is None:
                continue

            if self.last_received_packet_number >= pack_n and \
                    not (pack_n < 64 and self.last_received_packet_number > 65536 - 64):
                continue

            self.last_received_time = int(time.time())
            self.last_received_packet_number = pack_n
            self.parse(data)

    def process_json(self, js):
        self.json_sig.emit(js)

    def process_jpeg(self, bts):
        self.jpeg_sig.emit(bts)
        self.packets.append(self.pack_ack(self.last_received_packet_number))

    def send_json(self, js):
        bts = self.pack_json(js)
        if bts is None:
            return

        self.packets.append(bts)

