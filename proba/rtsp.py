from maix import time, rtsp, camera, image, nn, display
import numpy as np
import cv2

#cam = camera.Camera(1920, 1080, image.Format.FMT_YVU420SP)
cam = camera.Camera(640, 640, image.Format.FMT_YVU420SP)
disp = display.Display()

server = rtsp.Rtsp(fps=10)
server.bind_camera(cam)
server.start()
print(server.get_url())

cam_yolo = cam.add_channel(320, 320)
yolo_model = nn.YOLO11(model="/root/models/yolo11n_320_room.mud")

rgn = server.add_region(0, 0, 640, 640)

canvas_count = 0


while True:
    img = cam_yolo.read()

    tm = time.time_ms()

    w = img.width()
    h = img.height()

    print(f'{w=} {h=}')
    img_rgb = img

    canvas_count += 1
    cnv = None
    if canvas_count > 4:
        cnv = rgn.get_canvas()

    objs = yolo_model.detect(img_rgb, conf_th=0.5, iou_th=0.45)
    for obj in objs:
        img_rgb.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
        msg = f'{yolo_model.labels[obj.class_id]}: {obj.score:.2f}'
        img_rgb.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

        if cnv:
            cnv.draw_rect(obj.x*2, obj.y*2, obj.w*2, obj.h*2, color=image.COLOR_RED, thickness=2)
            cnv.draw_string(obj.x*2, obj.y*2, msg, color=image.COLOR_RED)

    if cnv:
        rgn.update_canvas()

    disp.show(img_rgb)

