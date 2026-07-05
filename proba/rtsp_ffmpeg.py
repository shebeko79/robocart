from maix import camera, image, video, app
import time
import subprocess

cam = camera.Camera(640, 480, image.Format.FMT_YVU420SP)
e = video.Encoder()

# This line really work. I've checked, but quit slow.
#ffmpeg -rtsp_transport tcp -i rtsp://127.0.0.1:8554/live -c copy -bsf:v setts=pts=N/TB:dts=N/TB -f rtsp -rtsp_transport tcp rtsp://93.127.143.124:8554/camera

ffmpeg = subprocess.Popen([
    'ffmpeg',
    '-re',
    '-f', 'hevc',
    '-i', '-',  # stdin
    '-c', 'copy',
    '-f', 'rtp',
    'rtp://192.168.33.7:1234'
], stdin=subprocess.PIPE)

while not app.need_exit():
    img = cam.read()
    frame = e.encode(img)
    ffmpeg.stdin.write(frame.to_bytes())
