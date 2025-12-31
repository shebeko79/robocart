import socket
import threading
from packet_processor import PacketProcessor


class UdpReceiver(PacketProcessor):
    def __init__(self, host_name, port, json_sig, jpeg_sig):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (socket.gethostbyname(host_name), port)
        self.json_sig = json_sig
        self.jpeg_sig = jpeg_sig
        self.last_received_packet_number = 0

        self.packets.append(self.pack_json({}))
        self.do_send()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def do_send(self):
        bts = self.pack()
        if bts is None:
            return

        self.sock.sendto(bts, self.addr)

    def _loop(self):

        while True:
            data, addr = self.sock.recvfrom(65536)
            if addr != self.addr:
                continue

            pack_n = self.get_packet_number(data)
            if pack_n is None:
                continue

            if self.last_received_packet_number >= pack_n and \
                    not (pack_n < 64 and self.last_received_packet_number > 65536 - 64):
                continue

            self.last_received_packet_number = pack_n
            self.parse(data)

    def process_json(self, js):
        self.json_sig.emit(js)

    def process_jpeg(self, bts):
        self.jpeg_sig.emit(bts)
        self.packets.append(self.pack_ack(self.last_received_packet_number))
        self.do_send()
