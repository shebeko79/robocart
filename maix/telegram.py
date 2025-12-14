from maix import time
import telegram_bot
import requests
import tracker
import track_utils
import json
import mover
import os

telegramUpdateId = 0
lastUpdateTime = 0

coolDownCount = 10

DEVICE_NAME = 'robocart'
MAX_COMMAND_UPDATE_DELAY = 300
MIN_COMMAND_UPDATE_DELAY = 10
commandUpdateDelay = MAX_COMMAND_UPDATE_DELAY


def init():
    global telegramUpdateId

    file_path = track_utils.CFG_PATH+"/telegram_update_id.txt"

    if not os.path.isfile(file_path):
        return

    with open(file_path, 'r') as file:
        telegramUpdateId = int(file.read())


def save_update_id():
    global telegramUpdateId

    file_path = track_utils.CFG_PATH + "/telegram_update_id.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(telegramUpdateId))


def send_message(message):
    req = f'https://api.telegram.org/{telegram_bot.ID}/sendMessage?chat_id={telegram_bot.CHAT_ID}&text={message}'
    res = requests.get(req)
    # print(res.text)


def get_updates():
    global telegramUpdateId

    req = f'https://api.telegram.org/{telegram_bot.ID}/getUpdates?allowed_updates=message&limit=10&offset={telegramUpdateId+1}'
    res = requests.get(req)
    res = json.loads(res.text)
    if 'ok' not in res or not res['ok']:
        return None

    if 'result' not in res:
        return None

    res = res['result']

    for r in res:
        if 'update_id' in r:
            telegramUpdateId = r['update_id']

    return res


def get_commands():
    cmds = []

    res = get_updates()
    if res is None:
        return cmds

    for r in res:
        if 'message' not in r:
            continue

        msg = r['message']

        if 'text' not in msg:
            continue

        txt = msg['text']

        chunks = txt.split(":", 4)
        if len(chunks) < 3:
            continue

        if chunks[0] != 'cmd' or chunks[1] != DEVICE_NAME:
            continue

        c = {'name': chunks[2], 'params': []}

        if len(chunks) == 4:
            c['params'] = chunks[3].split(";")

        cmds.append(c)

    return cmds


def answer_command(cmd, status, params = None):
    cmd_name = cmd['name']
    msg = f'{status}:{cmd_name}:{DEVICE_NAME}'

    if params is not None:
        msg += ':' + ";".join(params)

    send_message(msg)


def process_sleep(cmd):
    params = cmd['params']
    if len(params) < 1:
        return

    idle = int(params[0])

    if len(params) >= 2:
        track_utils.SLEEP_DURATION = int(params[1])

    track_utils.SLEEP_IDLE_TIMEOUT = idle
    track_utils.save_cfg()


def process_state(cmd):
    params = [f"{mover.voltage:.1f}"]
    return params


def process_image(cmd, img):
    send_img = img.copy()
    tracker.draw_trackers(send_img)

    if not send_img:
        return

    jpg = send_img.to_jpeg()
    if not jpg:
        return

    bts = jpg.to_bytes()
    file_path = track_utils.CFG_PATH+"/screenshot.jpg"
    with open(file_path, "wb") as f:
        f.write(bts)

    bts = None

    with open(file_path, "rb") as f:
        url = f'https://api.telegram.org/{telegram_bot.ID}/sendPhoto'
        params = {'chat_id': telegram_bot.CHAT_ID}
        files = {'photo': f}
        response = requests.post(url, params, files=files)


def process(img):
    global lastUpdateTime
    global coolDownCount
    global commandUpdateDelay
    global MAX_COMMAND_UPDATE_DELAY
    global MIN_COMMAND_UPDATE_DELAY

    if coolDownCount > 0:
        coolDownCount -= 1
        return

    cur_time = time.time_s()
    if cur_time < lastUpdateTime + commandUpdateDelay:
        return

    lastUpdateTime = cur_time

    try:
        cmds = get_commands()
    except Exception as e:
        print(e)
        return

    if len(cmds) == 0:
        commandUpdateDelay *= 2
        if commandUpdateDelay > MAX_COMMAND_UPDATE_DELAY:
            commandUpdateDelay = MAX_COMMAND_UPDATE_DELAY
        return

    response_params = None

    for cmd in cmds:
        cmd_name = cmd['name']
        try:
            if cmd_name == 'set_sleep':
                process_sleep(cmd)
            elif cmd_name == 'state':
                response_params = process_state(cmd)
            elif cmd_name == 'image':
                process_image(cmd, img)
            else:
                answer_command(cmd, "unknown")
                continue

            answer_command(cmd, "accept", response_params)
            commandUpdateDelay = MIN_COMMAND_UPDATE_DELAY
        except Exception as e:
            print(e)
