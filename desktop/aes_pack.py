import os
import pyaes
import struct
import numpy as np
# import time


class AesPack:
    def __init__(self, key):
        self.bin_nonce = os.urandom(8)
        self.nonce, = struct.unpack("!Q", self.bin_nonce)
        self.crypt_seq = bytearray(0)
        self.aes = pyaes.AES(key)

        self.decrypt_nonce = None
        self.decrypt_seq = bytearray(0)

    def crypt(self, bts):
        check_sum = self.checksum(bts)
        bts += struct.pack("!L", check_sum)

        self.crypt_seq = self.expand_crypt_seq(self.crypt_seq, len(bts), self.nonce)
        return self.bin_nonce + self.do_xor(bts, self.crypt_seq)

    def decrypt(self, bts):
        if len(bts) < 9:
            return None

        nonce, = struct.unpack("!Q", bts[:8])
        if self.decrypt_nonce != nonce:
            self.decrypt_nonce = nonce
            self.decrypt_seq = bytearray(0)

        self.decrypt_seq = self.expand_crypt_seq(self.decrypt_seq, len(bts)-8, nonce)
        decrypted = self.do_xor(bts[8:], self.decrypt_seq)

        stored_check_sum, = struct.unpack("!L", decrypted[-4:])
        res = decrypted[:-4]
        check_sum = self.checksum(res)
        if check_sum != stored_check_sum:
            return None

        return res

    def expand_crypt_seq(self, crypt_seq, seq_len, nonce):
        if seq_len <= len(crypt_seq):
            return crypt_seq

        chunks_count = int((seq_len+15)/16)
        existent_chunks_count = int(len(crypt_seq)/16)

        crypt_seq += bytearray((chunks_count - existent_chunks_count)*16)

        for chunk in range(existent_chunks_count, chunks_count):
            c = struct.pack("!Q", nonce + chunk) + struct.pack("!Q", nonce + chunk + 1)
            crypt_seq[chunk*16:(chunk+1)*16] = self.aes.encrypt(c)

        #print(f'expand {chunks_count=} {existent_chunks_count=} {nonce=}')

        return crypt_seq

    @staticmethod
    def do_xor(bts, crypt_seq):
        np_bts = np.frombuffer(bts, dtype=np.uint8)
        crypt_bts = np.frombuffer(crypt_seq[:len(bts)], dtype=np.uint8)
        res = np_bts ^ crypt_bts
        #print(f'{np_bts=} {crypt_bts=} {res=}')
        return res.tobytes()

    @staticmethod
    def checksum(bts):
        np_bts = np.frombuffer(bts, dtype=np.uint8)
        return int(np.sum(np_bts) % 0x100000000)


'''
if __name__ == "__main__":
    rand_key = os.urandom(16)
    aes1 = AesPack(rand_key)
    aes2 = AesPack(rand_key)

    def test(data):
        crypt_seq1 = aes1.crypt(data)
        decrypt_seq1 = aes2.decrypt(crypt_seq1)

        if data != decrypt_seq1:
            print(f'1->2: fails {data=} {len(data)=} {crypt_seq1=} {len(crypt_seq1)=} {decrypt_seq1=}')
            return

        crypt_seq2 = aes2.crypt(decrypt_seq1)
        decrypt_seq2 = aes1.decrypt(crypt_seq2)

        if data != decrypt_seq2:
            print(f'2->1: fails {data=} {len(data)=} {crypt_seq2=} {len(crypt_seq2)=} {decrypt_seq2=}')
            return


    test(b'Hello world')
    test(b'Hello world1234')
    test(b'Hello world12345')

    d = os.urandom(32000)
    test(d)

    t = int(time.time_ns()/1000000)
    for i in range(0, 10):
        test(d)
    t = int(time.time_ns()/1000000)-t
    print(f'{t=}')
'''