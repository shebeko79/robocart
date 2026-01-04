import os
import fcntl
import struct
import time

DEV_PATH = "/dev/watchdog"

WDIOC_SETTIMEOUT = 0xC0045706
WDIOC_KEEPALIVE = 0x80045705
WDIOC_SETOPTIONS = 0x80045704
WDIOS_DISABLECARD = 0x0001


def wdt_init(timeout_sec: int):
    fd = os.open(DEV_PATH, os.O_RDWR)

    try:
        buf = struct.pack("I", timeout_sec)
        fcntl.ioctl(fd, WDIOC_SETTIMEOUT, buf)
    finally:
        os.close(fd)


def wdt_feed():
    fd = os.open(DEV_PATH, os.O_RDWR)

    try:
        fcntl.ioctl(fd, WDIOC_KEEPALIVE, 0)
    finally:
        os.close(fd)


def stop():
    fd = os.open(DEV_PATH, os.O_RDWR)
    fcntl.ioctl(fd, WDIOC_SETOPTIONS, struct.pack("I", WDIOS_DISABLECARD))
    os.close(fd)


if __name__ == "__main__":
    wdt_init(5)
    for i in range(0, 60):
        wdt_feed()
        time.sleep(1)
    stop()
