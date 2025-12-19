import cv2
import socket
import select
import numpy as np

UDP_IP = "192.168.33.6"
UDP_PORT = 5005


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)

    try:
        while True:

            while True:
                print(f'send({UDP_IP}:{UDP_PORT})')
                sock.sendto(b'1', (UDP_IP, UDP_PORT))

                ready = select.select([sock], [], [], 5.0)
                if ready[0]:
                    break

            jpg, addr = sock.recvfrom(65536)
            np_arr = np.frombuffer(jpg, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("JPG Stream", frame)
                if cv2.waitKey(1) == 27:
                    break
    finally:
        cv2.destroyAllWindows()
