import socket
import threading
from packet_processor import PacketProcessor


class UdpReceiver(PacketProcessor):
    def __init__(self, host_name, port, sig):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = (socket.gethostbyname(host_name), port)
        self.sig = sig
        self.packets.append(self.pack_json({}))
        self.do_send()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def do_send(self):
        bts = self.pack()
        if bts is None:
            return

        print(bts)
        self.sock.sendto(bts, self.addr)

    def _loop(self):

        while True:
            print("loop1")
            data, addr = self.sock.recvfrom(65536)
            print("loop2")
            if addr != self.addr:
                continue

            print(f"_loop(): {len(data)=}")

            self.sig.emit(data)
