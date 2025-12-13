
CAM_SIZE = [640, 640]
FOCAL_DIST = CAM_SIZE[1]*2.8
BASE_PATH = "/root/robot"

SLEEP_IDLE_TIMEOUT = 5*60  # timeout before module got to sleep mode. If zero module will not go to sleep
SLEEP_DELAY = 30*60  # how long module sleeping


def make_rect(pt1, pt2):
    x1 = min(pt1[0], pt2[0])
    y1 = min(pt1[1], pt2[1])
    x2 = max(pt1[0], pt2[0])
    y2 = max(pt1[1], pt2[1])
    return [x1, y1, x2, y2]
