from maix import image, time
from packet_processor import PacketProcessor, PacketType
import socket
import select

import mover
import pan_tilt
import states
import track_utils
import tracker

UDP_PORT = 5005
IMG_NO_ACK_TIMEOUT = 500


class UdpServer(PacketProcessor):
    def __init__(self, sock: socket):
        super().__init__()
        self.img: image.Image = None
        self.require_state_answer = False
        self.jpeg_quality = 50

        self.sock = sock
        self.sock.setblocking(False)
        self.last_received_addr = None
        self.last_received_packet_number = 0

        self.last_ack_packet_number = 0

        self.last_image_packet = 0
        self.last_image_send_time = time.time_ms()

    def process(self, img):
        self.do_receive()
        self.do_send(img)

    def do_receive(self):
        sel = select.select([self.sock], [], [self.sock], 0)

        if len(sel[2]) != 0:
            print('UdpServer.do_receive() socket error')
            return

        if len(sel[0]) == 0:
            return

        data, addr = self.sock.recvfrom(65535)
        pack_n = self.get_packet_number(data)
        if pack_n is None:
            return

        if self.last_received_addr is None or self.last_received_addr != addr:
            self.last_received_addr = addr
            self.last_received_packet_number = pack_n
        elif self.last_received_packet_number >= pack_n and \
                not (pack_n < 64 and self.last_received_packet_number > 65536-64):
            return

        self.last_received_packet_number = pack_n
        self.parse(data)

    def do_send(self, img):
        if self.last_received_addr is None:
            return

        sel = select.select([], [self.sock], [self.sock], 0)

        if len(sel[2]) != 0:
            print('UdpServer.do_send() socket error')
            return

        if len(sel[1]) == 0:
            return

        is_ready_to_send = True

        if len(self.packets) > 0:
            bts = self.pack()
            self.sock.sendto(bts, self.last_received_addr)

            sel = select.select([], [self.sock], [self.sock], 0)

            if len(sel[2]) != 0:
                print('UdpServer.do_send() socket error after sending')
                return

            is_ready_to_send = len(sel[1]) > 0

        tm = time.time_ms()
        self.img = img
        is_send_image = self.img is not None and is_ready_to_send and len(self.packets) == 0 and\
                        (self.last_ack_packet_number == self.last_image_packet or
                         tm >= self.last_image_send_time + IMG_NO_ACK_TIMEOUT)

        print(f'{is_send_image}: {is_ready_to_send=} {len(self.packets)=} {tm=} {self.last_image_send_time=} {self.last_ack_packet_number=} {self.last_image_packet=}')
        if is_send_image:
            bts = self.pack_img()
            if bts is not None:
                self.last_image_packet = self.get_next_packet_number()
                self.last_image_send_time = tm
                self.packets.append(bts)

        if self.require_state_answer:
            self.require_state_answer = False

            bts = self.pack_state()
            if bts is not None:
                self.packets.append(bts)

        if is_ready_to_send and len(self.packets) > 0:
            bts = self.pack()
            self.sock.sendto(bts, self.last_received_addr)

    def pack_img(self) -> bytes:
        if not self.img:
            return None

        img = self.img.copy()
        if not img:
            return None

        tracker.draw_trackers(img)

        jpg = img.to_jpeg(self.jpeg_quality)
        if not jpg:
            return

        bts = jpg.to_bytes()
        if len(bts) > self.MAX_CHUNK_SIZE:
            self.jpeg_quality -= 5
            if self.jpeg_quality < 5:
                self.jpeg_quality = 5
            return
        elif len(bts) < self.MAX_CHUNK_SIZE*0.8:
            self.jpeg_quality += 5
            if self.jpeg_quality > 95:
                self.jpeg_quality = 95

        return self.pack_chunk(jpg.to_bytes(), PacketType.JPG)

    def pack_state(self) -> bytes:
        st = states.current_state
        cur_state = {}

        if st is not None:
            cur_state['state_name'] = st.state_name
            cur_state['accept_click'] = st.accept_click
            cur_state['accept_rectangle'] = st.accept_rectangle
            cur_state['rectangle_cap'] = st.rectangle_cap
            cur_state['click_cap'] = st.click_cap
            cur_state['voltage'] = mover.voltage

            buttons = []
            for b in st.buttons:
                buttons.append({'caption': b.caption, 'enabled': b.enabled})
            cur_state['buttons'] = buttons

        return self.pack_json(cur_state)

    def process_ack(self, ack_packet_number):
        self.last_ack_packet_number = ack_packet_number
        pass

    def process_json(self, js):
        if 'cmd' not in js:
            return

        cmd = js['cmd']

        if cmd == "click":
            self.click(js)
        elif cmd == "click_point":
            self.click_point(js)
        elif cmd == "sel_rect":
            self.sel_rect(js)
        elif cmd == "move_cam":
            self.move_cam(js)
        elif cmd == "moveto_cam":
            self.moveto_cam(js)
        elif cmd == "move":
            self.move(js)

    def click(self, js):
        state_name = js['state_name']
        caption = js['caption']
        self.require_state_answer = True

        st = states.current_state
        if st is None or state_name != st.state_name:
            return

        btn = st.button_by_name(caption)
        if btn is not None and btn.enabled:
            st.on_click_button(btn)

    def click_point(self, js):
        state_name = js['state_name']
        x = js['x']
        y = js['y']
        self.require_state_answer = True

        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise Exception("Coordinates out of range")

        st = states.current_state
        if st is None or state_name != st.state_name:
            return

        if st.accept_click:
            st.on_click([x, y])

    def sel_rect(self, js):
        state_name = js['state_name']
        x1 = js['x1']
        y1 = js['y1']
        x2 = js['x2']
        y2 = js['y2']
        self.require_state_answer = True

        if not (0.0 <= x1 <= 1.0 and 0.0 <= y1 <= 1.0 and 0.0 <= x2 <= 1.0 and 0.0 <= y2 <= 1.0):
            raise Exception("Coordinates out of range")

        st = states.current_state
        if st is None or state_name != st.state_name:
            return

        if st.accept_rectangle and self.img:
            rc = track_utils.make_rect([x1, y1], [x2, y2])
            st.on_rectangle(self.img, rc)

    def move_cam(self, js):
        pan = js['pan']
        tilt = js['tilt']
        self.require_state_answer = True

        st = states.current_state
        if st is None or not st.accept_user_move_cam:
            return

        p = pan_tilt.get_pan_angle()
        t = pan_tilt.get_tilt_angle()

        p = p + pan
        t = t + tilt

        pan_tilt.set_pan_angle(p)
        pan_tilt.set_tilt_angle(t)

    def moveto_cam(self, js):
        pan = js['pan']
        tilt = js['tilt']
        self.require_state_answer = True

        st = states.current_state
        if st is None or not st.accept_user_move_cam:
            return

        if not isinstance(pan, str):
            pan = pan_tilt.angle2pan(pan)
        elif pan.upper() == "LEFT":
            pan = pan_tilt.Pan.LEFT
        elif pan.upper() == "RIGHT":
            pan = pan_tilt.Pan.RIGHT
        elif pan.upper() == "CENTER":
            pan = pan_tilt.Pan.CENTER
        elif pan.upper() == "MIN":
            pan = pan_tilt.Pan.MIN
        elif pan.upper() == "MAX":
            pan = pan_tilt.Pan.MAX
        else:
            pan = pan_tilt.get_pan()

        if not isinstance(tilt, str):
            tilt = pan_tilt.angle2tilt(tilt)
        elif tilt.upper() == "BACKWARD":
            tilt = pan_tilt.Tilt.BACKWARD
        elif tilt.upper() == "UP":
            tilt = pan_tilt.Tilt.UP
        elif tilt.upper() == "FRONT":
            tilt = pan_tilt.Tilt.FRONT
        elif tilt.upper() == "MIN":
            tilt = pan_tilt.Tilt.MIN
        elif tilt.upper() == "MAX":
            tilt = pan_tilt.Tilt.MAX
        else:
            tilt = pan_tilt.get_tilt()

        pan_tilt.set_pan(pan)
        pan_tilt.set_tilt(tilt)

    def move(self, js):
        speed = js['speed']
        pan = js['pan']
        self.require_state_answer = True

        st = states.current_state
        if st is None or not st.accept_user_move_cam:
            return

        mover.move(speed, pan)
