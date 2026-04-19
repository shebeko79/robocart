from maix import time, rtsp, camera, image, nn

cam = camera.Camera(1920, 1080, image.Format.FMT_YVU420SP)
server = rtsp.Rtsp()
server.bind_camera(cam)
server.start()

print(server.get_url())

yolo_model = nn.YOLO11(model="/root/models/yolo11n_320_room.mud")

while True:
    img = cam.read()
    if img is not None:
        print(f'Image ({img.width()},{img.height()})')
    else:
        print(f'Image is None')

    img_rgb = img.to_format(image.Format.FMT_RGB888)

    yolo_objects = yolo_model.detect(img_rgb, conf_th=0.5, iou_th=0.45)
    print(f'{yolo_objects=}')

