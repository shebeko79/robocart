import struct
import json
from enum import Enum


class PacketType(Enum):
    JSON = 0,
    JPG = 1


class PacketProcessor:
    MAX_CHUNK_SIZE = 65500

    def __init__(self):
        self.send_packet_number = 0
        self.packets = []

    def pack(self) -> bytes:
        if len(self.packets) == 0:
            return

        self.send_packet_number += 1
        self.send_packet_number %= 65536

        fit_it = 0
        sz = 0
        for p in self.packets:
            sz += len(p)
            if sz > self.MAX_CHUNK_SIZE:
                break
            fit_it += 1

        ret = struct.pack("!H", len(self.send_packet_number))

        for i in range(0, fit_it):
            ret += self.packets[i]

        self.packets = self.packets[i:]
        return ret

    @staticmethod
    def pack_chunk(data, tp):
        return struct.pack("!H", len(data)) + struct.pack("!B", tp) + data

    def pack_json(self, js) -> bytes:
        return self.pack_chunk(json.dumps(js).encode('utf-8'), PacketType.JSON)

    @staticmethod
    def get_packet_number(packet: bytes):
        total_len = len(packet)
        if total_len < 2:
            return None

        packet_number = struct.unpack("!H", packet[0:2])
        i = 2

        while i < total_len:
            if i + 3 > total_len:
                return None

            chunk_len = struct.unpack("!H", packet[i:i+2])
            next_i = i+3+chunk_len
            if next_i > total_len:
                return None
            i = next_i

        return packet_number

    def parse(self, packet: bytes):
        total_len = len(packet)
        i = 2

        while i+4 <= total_len:
            chunk_len = struct.unpack("!H", packet[i:i+2])
            next_i = i+3+chunk_len
            if next_i > total_len:
                break

            chunk_type = packet[i+2]

            try:
                chunk = packet[i+3:i+3+chunk_len]
                if chunk_type == PacketType.JSON:
                    js = json.loads(chunk)
                    self.process_json(js)
                elif chunk_type == PacketType.JPG:
                    self.process_jpeg(chunk)
            except Exception as e:
                print(e)

            i = next_i

    def process_json(self, js):
        pass

    def process_jpeg(self, bts):
        pass
