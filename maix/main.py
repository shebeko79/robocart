from maix import camera, image, display, app
import mover
import algos
import pan_tilt
import tracker
import states
from track_utils import CAM_SIZE
import http_server
import touch_process


cam: camera.Camera = None
disp: display.Display = None


def main_init():
    global cam
    global disp

    cam = camera.Camera(CAM_SIZE[0], CAM_SIZE[1], tracker.get_camera_format())
    disp = display.Display()
    touch_process.init(disp)

    image.load_font("sans", "/maixapp/share/font/sans.ttf", size=32)

    mover.init()
    pan_tilt.init()

    states.init()
    states.set_state(states.MainState.state_name)

    http_server.init()


def main_cycle():
    while not app.need_exit():
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

        http_server.last_img = img
        disp_img = st.draw_screen(img, [disp.width(), disp.height()])
        touch_process.draw(disp_img)

        disp.show(disp_img)

        touch_process.process(st, img)
        http_server.process()

    pan_tilt.shutdown()
    http_server.shutdown()


if __name__ == "__main__":
    main_init()
    main_cycle()
