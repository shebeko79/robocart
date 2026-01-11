import time

l = 1 << 18

t = time.time_ns() / 1000000
data = bytearray(l)
for i in range(0, int(l/2)):
    data[i:i+2] = [i%256, (i+1)%256]
data = bytes(data)
t = time.time_ns() / 1000000 - t
print(f'{t=} {data[:10]=} {l=}')

'''
t = time.time_ns() / 1000000
data = b''
for i in range(0, int(l/2)):
    data += bytes([i%256, (i+1)%256])
t = time.time_ns() / 1000000 - t
print(f'{t=} {data[:10]=} {l=}')
'''


def foo(arr):
    return arr

def call_foo(crypted):
    global data

    t = time.time_ns() / 1000000
    for i in range(0, 10000):
        if crypted:
            data = foo(data)
        else:
            data = data
    t = time.time_ns() / 1000000 - t
    print(f'{t=} {data[:10]=} {l=} {crypted=}')


call_foo(False)
call_foo(True)
