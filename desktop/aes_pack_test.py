import os
from aes_pack import AesPack
import time

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
