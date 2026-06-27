from maix import time, rtsp, camera, image, nn, display
import numpy as np
import cv2

#cam = camera.Camera(1920, 1080, image.Format.FMT_YVU420SP)
#cam = camera.Camera(640, 640, image.Format.FMT_YVU420SP)
cam = camera.Camera(320, 320, image.Format.FMT_YVU420SP)
disp = display.Display()

server = rtsp.Rtsp()
server.bind_camera(cam)
server.start()

print(server.get_url())

yolo_model = nn.YOLO11(model="/root/models/yolo11n_320_room.mud")

while True:
    img = cam.read()

    tm = time.time_ms()

    w = img.width()
    h = img.height()

    yuv = np.frombuffer(img.to_bytes(), dtype=np.uint8)
    #print(f'frombuffer()={time.time_ms() - tm}')
    yuv = yuv.reshape((h * 3 // 2, w))
    #print(f'reshape()={time.time_ms() - tm}')
    rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB_NV21)
    #print(f'cvtColor()={time.time_ms() - tm}')
    img_rgb = image.cv2image(rgb, bgr=False, copy=False)
    #print(f'cv2image()={time.time_ms() - tm}')

    objs = yolo_model.detect(img_rgb, conf_th=0.5, iou_th=0.45)
    for obj in objs:
        img_rgb.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
        msg = f'{yolo_model.labels[obj.class_id]}: {obj.score:.2f}'
        img_rgb.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

    disp.show(img_rgb)

