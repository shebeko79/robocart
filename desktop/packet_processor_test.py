import os
import aes_pack
import time
from packet_processor import PacketProcessor, PacketType

received_jpeg = b''
received_jsons = []


class TestProcessor(PacketProcessor):
    def __init__(self, name, key=None):
        super().__init__()
        self.name = name

        if key is not None:
            self.aes = aes_pack.AesPack(key)
            self.is_crypted = True

    def receive(self, data):
        pack_n = self.get_packet_number(data)
        if pack_n is None:
            return

        if self.is_packet_too_old(pack_n):
            return

        #print(f'receive({self.name})1: {pack_n=}')
        if self.parse(data):
            self.last_received_packet_number = pack_n

    def crypt(self, bts):
        return self.aes.crypt(bts)

    def decrypt(self, bts, packet_number):
        return self.aes.decrypt(bts)

    def process_json(self, js):
        global received_jsons
        #print(f'process_json({self.name}): {js=}')
        received_jsons.append(js)

    def process_jpeg(self, bts):
        global received_jpeg
        #print(f'process_jpeg({self.name}): {len(bts)=}')
        received_jpeg = bts

    def process_ack(self, ack_packet_number):
        print(f'process_ack({self.name}): {ack_packet_number=}')
        pass


peer1: TestProcessor = None
peer2: TestProcessor = None


def send(sender: TestProcessor, receiver: TestProcessor):
    i = 0
    while True:
        packet = sender.pack()
        #print(f'test send({i}): {packet=} {sender.packets=}')
        if not packet:
            break

        receiver.receive(packet)
        i += 1


def test_it(sender, receiver, jpeg_data_len, is_before_packet, is_after_packet):
    global received_jpeg
    global received_jsons

    received_jpeg = b''
    received_jsons = []

    jpeg_data = bytearray(i % 256 for i in range(jpeg_data_len))

    before_packet = {'before': 1}
    after_packet = {'after': 1}

    if is_before_packet:
        peer1.packets.append(peer1.pack_json(before_packet))

    peer1.packets.append(peer1.pack_chunk(jpeg_data, PacketType.JPG))

    if is_after_packet:
        peer1.packets.append(peer1.pack_json(after_packet))

    send(peer1, peer2)

    if jpeg_data != received_jpeg:
        print(f'{sender.name}->{receiver.name}: fails {len(jpeg_data)=} {len(received_jpeg)=}')
        return

    expected_json = []
    if is_before_packet:
        expected_json.append(before_packet)

    if is_after_packet:
        expected_json.append(after_packet)

    if received_jsons != expected_json:
        print(f'{sender.name}->{receiver.name}: json fails {received_jsons=} {expected_json=}')


def test(jpeg_data_len):
    #print(f'test: {jpeg_data_len=}')

    test_it(peer1, peer2, jpeg_data_len, False, False)
    test_it(peer2, peer1, jpeg_data_len, False, False)

    test_it(peer1, peer2, jpeg_data_len, True, False)
    test_it(peer2, peer1, jpeg_data_len, True, False)

    test_it(peer1, peer2, jpeg_data_len, False, True)
    test_it(peer2, peer1, jpeg_data_len, False, True)

    test_it(peer1, peer2, jpeg_data_len, True, True)
    test_it(peer2, peer1, jpeg_data_len, True, True)


def run_length_tests():
    test(1)
    test(2)
    test(256)
    test(1024)
    for i in range(-6, 6):
        test(PacketProcessor.MAX_PACKET_SIZE+i)
    for i in range(-6, 6):
        test(PacketProcessor.MAX_PACKET_SIZE*2+i)

    test(65000)
    test(100000)


peer1 = TestProcessor("peer1")
peer2 = TestProcessor("peer2")
run_length_tests()

rand_key = os.urandom(16)
peer1 = TestProcessor("peer1", rand_key)
peer2 = TestProcessor("peer2", rand_key)
run_length_tests()
