import os
import json

CAM_SIZE = [640, 640]
FOCAL_DIST = CAM_SIZE[1]*2.8
BASE_PATH = "/root/robot"
CFG_PATH = "/root"

SLEEP_IDLE_TIMEOUT = 5*60  # timeout before module go to sleep mode. If zero module will remain active
SLEEP_DURATION = 30*60  # how long module sleeping

last_request_time = 0


def make_rect(pt1, pt2):
    x1 = min(pt1[0], pt2[0])
    y1 = min(pt1[1], pt2[1])
    x2 = max(pt1[0], pt2[0])
    y2 = max(pt1[1], pt2[1])
    return [x1, y1, x2, y2]


def init():
    global SLEEP_IDLE_TIMEOUT
    global SLEEP_DURATION

    file_path = CFG_PATH+"/robot.cfg"

    if not os.path.isfile(file_path):
        return

    with open(file_path, 'r') as file:
        data = json.load(file)
        SLEEP_IDLE_TIMEOUT = data['sleep_idle_timeout']
        SLEEP_DURATION = data['sleep_duration']


def save_cfg():
    global SLEEP_IDLE_TIMEOUT
    global SLEEP_DURATION

    data = {'sleep_idle_timeout': SLEEP_IDLE_TIMEOUT, 'sleep_duration': SLEEP_DURATION}

    file_path = CFG_PATH+"/robot.cfg"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
