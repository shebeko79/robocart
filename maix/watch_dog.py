import os
import fcntl
import struct

DEV_PATH = "/dev/watchdog"

WDIOC_SETTIMEOUT = 0xC0045706
WDIOC_KEEPALIVE = 0x80045705
WDIOC_SETOPTIONS = 0x80045704
WDIOS_DISABLECARD = 0x0001


def init():
    fd = os.open(DEV_PATH, os.O_RDWR)
    try:
        buf = struct.pack("I", 60)
        fcntl.ioctl(fd, WDIOC_SETTIMEOUT, buf)
    finally:
        os.close(fd)


def feed():
    fd = os.open(DEV_PATH, os.O_RDWR)
    try:
        fcntl.ioctl(fd, WDIOC_KEEPALIVE, 0)
    finally:
        os.close(fd)


def stop():
    fd = os.open(DEV_PATH, os.O_RDWR)
    try:
        fcntl.ioctl(fd, WDIOC_SETOPTIONS, struct.pack("I", WDIOS_DISABLECARD))
    finally:
        os.close(fd)
