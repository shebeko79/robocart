from maix import app, uart, time
import os
import subprocess

DEVICE_NAME = "/dev/ttyS0"
serial: uart.UART = None

CAR_NAME = "rccar"
DRIVE_CMD_STR = "cmd:"+CAR_NAME+":drive:{};{}\r"
STATE_CMD_STR = "cmd:"+CAR_NAME+":state\r"
SLEEP_CMD_STR = "cmd:"+CAR_NAME+":sleep:{}\r"

STATE_REQUEST_PERIOD = 5
last_state_request = 0
response_buffer = ''

commands_rejected = False
voltage = 0.0
left_speed = 0.0
right_speed = 0.0


def init():
    global serial

    serial = uart.UART(DEVICE_NAME, 115200)


def constrain(v):
    if v > 1:
        return 1
    elif v < -1:
        return -1
    return v


def move(y, x):
    y = constrain(y)
    x = constrain(x)

    cmd = DRIVE_CMD_STR.format(y, x)
    #print(cmd)
    serial.write_str(cmd)


def stop():
    cmd = DRIVE_CMD_STR.format(0, 0)
    serial.write_str(cmd)


def process():
    global response_buffer

    send_state_request()

    data = serial.read()
    if not data:
        return

    response_buffer += data.decode()
    parse_commands()


def send_state_request():
    global last_state_request

    cur_time = time.time_s()
    if cur_time <= last_state_request + STATE_REQUEST_PERIOD:
        return

    serial.write_str(STATE_CMD_STR)
    last_state_request = cur_time


def go_to_sleep(seconds):
    cmd = SLEEP_CMD_STR.format(seconds)
    os.sync()
    serial.write_str(cmd)
    subprocess.run(["/sbin/poweroff"])


def parse_commands():
    global response_buffer

    idx = response_buffer.rfind("\r")
    if idx == -1:
        return

    commands = response_buffer[:idx].split("\r")
    response_buffer = response_buffer[idx + 1:]

    for cmd in commands:
        process_command_response(cmd)


def process_command_response(cmd):
    global commands_rejected

    try:
        chunks = cmd.split(":", 4)
        if len(chunks) < 4:
            return

        params = None
        if len(chunks) == 5:
            params = chunks[4]

        if chunks[1] != 'cmd' or chunks[2] != CAR_NAME:
            return

        cmd_name = chunks[3]

        if chunks[0] == "reject":
            commands_rejected = True
            return

        if chunks[0] != "accept":
            return

        if cmd_name != "state":
            commands_rejected = False

        if cmd_name == "state":
            process_state_command_response(params)
    except Exception as e:
        print(e)


def process_state_command_response(params):
    global voltage
    global left_speed
    global right_speed

    if params is None:
        return

    chunks = params.split(";", 3)
    if len(chunks) < 4:
        return

    voltage = float(chunks[0])
    left_speed = float(chunks[1])
    right_speed = float(chunks[2])
