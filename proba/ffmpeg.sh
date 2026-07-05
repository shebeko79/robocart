#!/bin/bash
ffmpeg -i polet_navigatora.mp4 -f rtsp -c copy rtsp://0.0.0.0:8554/live

ffmpeg -i polet_navigatora.mp4 -map 0:1 -f rtp -c copy rtp://192.168.33.7:8554/live

#ffmpeg -rtsp_transport tcp -i rtsp://127.0.0.1:8554/live -c copy -bsf:v setts=pts=N/TB:dts=N/TB -f rtsp -rtsp_transport tcp rtsp://93.127.143.124:8554/camera