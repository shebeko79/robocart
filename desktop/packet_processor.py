import struct
import json
from enum import IntEnum


class PacketType(IntEnum):
    JSON = 0,
    JPG = 1,
    ACK = 2


class PacketProcessor:
    MAX_CHUNK_SIZE = 65500

    def __init__(self):
        self.send_packet_number = 0
        self.packets = []
        self.is_crypted = False

    def pack(self) -> bytes:
        if len(self.packets) == 0:
            return

        self.send_packet_number = self.get_next_packet_number()

        fit_it = 0
        sz = 0
        for p in self.packets:
            chunk_len = len(p)
            if sz + chunk_len > self.MAX_CHUNK_SIZE:
                break
            fit_it += 1
            sz += chunk_len

        payload = bytearray(sz)
        off = 0
        for i in range(0, fit_it):
            chunk_len = len(self.packets[i])
            payload[off:off+chunk_len] = self.packets[i]
            off += chunk_len

        if self.is_crypted:
            payload = self.crypt(payload)

        sz = len(payload)
        ret = bytearray(sz + 2)
        ret[:2] = struct.pack("!H", self.send_packet_number)
        ret[2:] = payload

        self.packets = self.packets[fit_it:]
        return ret

    def get_next_packet_number(self):
        ret = self.send_packet_number + 1
        ret %= 65536
        return ret

    @staticmethod
    def pack_chunk(data, tp: PacketType):
        ret = struct.pack("!H", len(data))
        ret += struct.pack("!B", tp)
        ret += data
        return ret

    def pack_json(self, js) -> bytes:
        return self.pack_chunk(json.dumps(js).encode('utf-8'), PacketType.JSON)

    def pack_ack(self, received_packet_number) -> bytes:
        bts = struct.pack("!H", received_packet_number)
        return self.pack_chunk(bts, PacketType.ACK)

    @staticmethod
    def get_packet_number(packet: bytes):
        total_len = len(packet)
        if total_len < 2:
            return None

        packet_number, = struct.unpack("!H", packet[0:2])
        return packet_number

    def parse(self, packet: bytes):
        packet_number, = struct.unpack("!H", packet[0:2])
        i = 2

        if self.is_crypted:
            payload = self.decrypt(packet[i:], packet_number)
            if payload is None:
                return False
            return self.iparse(payload, 0)
        else:
            return self.iparse(packet, i)

    def iparse(self, packet, offset):
        total_len = len(packet)

        i = offset
        while i < total_len:
            if i + 3 > total_len:
                return False

            chunk_len, = struct.unpack("!H", packet[i:i+2])
            next_i = i+3+chunk_len
            if next_i > total_len:
                return False
            i = next_i

        i = offset
        while i+4 <= total_len:
            chunk_len, = struct.unpack("!H", packet[i:i+2])
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
                elif chunk_type == PacketType.ACK:
                    ack_packet_number, = struct.unpack("!H", chunk)
                    self.process_ack(ack_packet_number)

            except Exception as e:
                print(e)

            i = next_i

        return True

    def crypt(self, bts):
        return bts

    def decrypt(self, bts, packet_number):
        return bts

    def process_json(self, js):
        pass

    def process_jpeg(self, bts):
        pass

    def process_ack(self, ack_packet_number):
        pass
