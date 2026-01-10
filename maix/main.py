import os
from maix import camera, image, display, app, time
import mover
import algos
import pan_tilt
import tracker
import track_utils
import states
import watch_dog
from track_utils import CAM_SIZE
#import http_server
import touch_process
import telegram
import udp_server
import socket


cam: camera.Camera = None
disp: display.Display = None
udp_serv: udp_server.UdpServer = None


def main_init():
    global cam
    global disp
    global udp_serv

    track_utils.init()
    cam = camera.Camera(CAM_SIZE[0], CAM_SIZE[1], tracker.get_camera_format())
    disp = display.Display()
    touch_process.init(disp)

    image.load_font("sans", "/maixapp/share/font/sans.ttf", size=32)

    mover.init()
    pan_tilt.init()

    states.init()
    states.set_state(states.MainState.state_name)

    #http_server.init()
    telegram.init()

    udp_key = None
    if os.path.exists(track_utils.CFG_PATH + "/udp.key"):
        with open(track_utils.CFG_PATH + "/udp.key", 'rb') as file:
            udp_key = file.read()

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(('', udp_server.UDP_PORT))
    udp_serv = udp_server.UdpServer(sock)

    watch_dog.init()


def main_cycle():
    while not app.need_exit():
        watch_dog.feed()

        st = states.current_state
        if not st:
            break

        st.process()
        st = states.current_state
        if not st:
            break

        img = cam.read()

        tracker.track(img)
        algos.process()
        mover.process()
        touch_process.read()

        #http_server.last_img = img
        disp_img = st.draw_screen(img, [disp.width(), disp.height()])
        touch_process.draw(disp_img)

        disp.show(disp_img)

        touch_process.process(st, img)
        #http_server.process()
        udp_serv.process(img)
        telegram.process(img)

        if track_utils.SLEEP_IDLE_TIMEOUT > 0:
            cur_time = time.time_s()
            if track_utils.last_request_time < 1700000000:
                track_utils.last_request_time = cur_time

            if track_utils.last_request_time + track_utils.SLEEP_IDLE_TIMEOUT < cur_time:
                telegram.save_update_id()
                mover.go_to_sleep(track_utils.SLEEP_DURATION)

    pan_tilt.shutdown()
    #http_server.shutdown()
    watch_dog.stop()


if __name__ == "__main__":
    main_init()
    main_cycle()
