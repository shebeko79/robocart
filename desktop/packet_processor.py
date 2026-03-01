import struct
import json
from enum import IntEnum


class PacketType(IntEnum):
    JSON = 0,
    JPG = 1,
    ACK = 2


class PacketProcessor:
    MAX_PACKET_SIZE = 1400
    MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - 3

    def __init__(self):
        self.send_packet_number = 0
        self.packets = []
        self.is_crypted = False
        self.send_partial_offset = 0
        self.receive_partial_chunk = b''
        self.last_received_packet_number = 0
        self.last_received_time = 0

    def pack(self) -> bytes:
        if len(self.packets) == 0:
            return

        self.send_packet_number = self.get_next_packet_number()

        fit_it = 0
        sz = 0
        for p in self.packets:
            chunk_len = len(p[1]) + 5
            if fit_it == 0:
                chunk_len -= self.send_partial_offset

            if fit_it != 0 and sz + chunk_len > self.MAX_PAYLOAD_SIZE:
                break
            fit_it += 1
            sz += chunk_len

        first_chunk_over_size = sz > self.MAX_PAYLOAD_SIZE
        if first_chunk_over_size:
            sz = self.MAX_PAYLOAD_SIZE

        next_partial_offset = self.send_partial_offset

        payload = bytearray(sz)
        off = 0
        for i in range(0, fit_it):
            p = self.packets[i]
            chunk_len = len(p[1])

            payload[off:off+4] = struct.pack("!I", chunk_len)
            payload[off+4] = p[0]

            chunk_offset = 0

            if i == 0:
                chunk_offset = self.send_partial_offset
                chunk_len -= self.send_partial_offset

            data_off = off + 5
            if data_off + chunk_len > sz:
                chunk_len = sz - data_off
                next_partial_offset += chunk_len
            else:
                next_partial_offset = 0

            payload[data_off:data_off+chunk_len] = p[1][chunk_offset:chunk_offset+chunk_len]
            off += chunk_len + 5

        if self.is_crypted:
            payload = self.crypt(payload)

        sz = len(payload)
        ret = bytearray(sz + 3)
        ret[:2] = struct.pack("!H", self.send_packet_number)
        ret[2] = 1 if self.send_partial_offset != 0 else 0
        ret[3:] = payload

        self.send_partial_offset = next_partial_offset

        if not first_chunk_over_size:
            self.packets = self.packets[fit_it:]

        return ret

    def get_next_packet_number(self):
        ret = self.send_packet_number + 1
        ret %= 65536
        return ret

    def get_next_packet_number(self):
        ret = self.send_packet_number + 1
        ret %= 65536
        return ret

    @staticmethod
    def pack_chunk(data, tp: PacketType):
        return tp, data

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

    def is_packet_too_old(self, pack_n):
        return self.last_received_packet_number >= pack_n and \
                not (pack_n < 64 and self.last_received_packet_number > 65536 - 64)

    def parse(self, packet: bytes):
        if len(packet) < 3:
            return False

        packet_number, = struct.unpack("!H", packet[0:2])
        is_next_partial = packet[2] != 0
        i = 3

        if is_next_partial and packet_number != self.last_received_packet_number + 1:
            return False

        if self.is_crypted:
            payload = self.decrypt(packet[i:], packet_number)
            if payload is None:
                return False
            return self.iparse(payload, 0, is_next_partial)
        else:
            return self.iparse(packet, i, is_next_partial)

    def iparse(self, packet, offset, is_next_partial):
        if not is_next_partial:
            self.receive_partial_chunk = b''
        received_partial_len = len(self.receive_partial_chunk)

        total_len = len(packet)
        i = offset
        item = 0
        while i < total_len:
            if i + 5 > total_len:
                return False
            chunk_len, = struct.unpack("!I", packet[i:i+4])

            if item == 0:
                if chunk_len <= received_partial_len:
                    return False
                chunk_len -= received_partial_len

            next_i = i+5+chunk_len
            if next_i > total_len and item != 0:
                return False

            i = next_i
            item += 1

        i = offset
        item = 0
        #print(f'iparse()2: {is_next_partial=} {received_partial_len=} {total_len=} {i=}')
        while i+5 <= total_len:
            chunk_len, = struct.unpack("!I", packet[i:i+4])

            if item == 0:
                chunk_len -= received_partial_len

            #print(f'iparse()3: {chunk_len=}')

            next_i = i+5+chunk_len
            if next_i > total_len and item != 0:
                break

            chunk = packet[i + 5:i + 5 + chunk_len]
            chunk_type = packet[i+4]

            if item == 0:
                if next_i > total_len:
                    self.receive_partial_chunk += chunk
                    #print(f'iparse()5: {len(self.receive_partial_chunk)=}')
                    return True
                chunk = self.receive_partial_chunk + chunk
                self.receive_partial_chunk = b''
                received_partial_len = 0

            try:
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
