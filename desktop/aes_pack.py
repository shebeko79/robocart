import os
import pyaes
from crc import Calculator, Crc8
import struct


class AesPack:
    def __init__(self, key):
        self.key = key
        self.crc = Calculator(Crc8.CCITT, optimized=True)

    def crypt(self, bts, packet_number):
        bts = os.urandom(2) + bts
        check_sum = self.crc.checksum(bts)
        bts += struct.pack("!B", check_sum)

        counter = pyaes.Counter(initial_value=packet_number)
        aes = pyaes.AESModeOfOperationCTR(self.key, counter=counter)
        return aes.encrypt(bts)

    def decrypt(self, bts, packet_number):
        if len(bts) < 4:
            return None

        counter = pyaes.Counter(initial_value=packet_number)
        aes = pyaes.AESModeOfOperationCTR(self.key, counter=counter)
        decrypted = aes.decrypt(bts)

        stored_check_sum = decrypted[-1]
        check_sum = self.crc.checksum(decrypted[:-1])
        if check_sum != stored_check_sum:
            return None

        return decrypted[2:-1]
