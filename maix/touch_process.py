from maix import touchscreen, time
import states
import track_utils

touch: touchscreen.TouchScreen = None
prev_touched = False
start_point = None
touched = False
touch_pt = None
disp_width = 0
disp_height = 0

last_request_time = time.time_s()


def init(disp):
    global touch
    global disp_width
    global disp_height

    touch = touchscreen.TouchScreen()

    disp_width = disp.width()
    disp_height = disp.height()


def read():
    global touched
    global touch_pt

    touch_status = touch.read()
    touched = touch_status[2]
    touch_pt = [touch_status[0], touch_status[1]]


def draw(disp_img):
    global start_point

    if start_point:
        rc = track_utils.make_rect(start_point, touch_pt)
        disp_img.draw_rect(rc[0], rc[1], rc[2] - rc[0], rc[3] - rc[1],
                           states.BaseState.rectangle_color, 3)


def process(st: states.BaseState, img):
    global prev_touched
    global start_point
    global touched
    global touch_pt
    global disp_width
    global disp_height
    global last_request_time

    if touched:
        last_request_time = time.time_s()

    if touched and not prev_touched:
        btn = st.hit_test(touch_pt)
        if btn:
            st.on_click_button(btn)
        else:
            if st.accept_click:
                x = touch_pt[0] / disp_width
                y = touch_pt[1] / disp_height
                st.on_click([x, y])

            if st.accept_rectangle:
                start_point = touch_pt

    if not touched and prev_touched:
        if st.accept_rectangle and start_point:
            x1 = start_point[0] / disp_width
            y1 = start_point[1] / disp_height
            x2 = touch_pt[0] / disp_width
            y2 = touch_pt[1] / disp_height
            rc = track_utils.make_rect([x1, y1], [x2, y2])

            st.on_rectangle(img, rc)
            start_point = None

    prev_touched = touched
