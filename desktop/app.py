import sys
import os
import json
import time
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QHBoxLayout,  QLabel
from main_widget import MainWidget
from udp_client import UdpClient

CONFIG_FILE = 'config.cfg'
UDP_KEY_FILE = 'udp.key'


class MainWindow(QMainWindow):

    json_received = pyqtSignal(object)
    jpeg_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()

        self.local_name = "robocart"
        self.udp_port = 5005
        self.relay_host = ""
        self.relay_port = self.udp_port
        self.load_config()

        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.ConnectionLabel = QLabel('Not connected')
        self.VoltageLabel = QLabel('Unknown')
        self.StateLabel = QLabel('Unknown')
        self.MessageLabel = QLabel('')
        self.init_status_bar()

        self.setGeometry(50, 50, 950, 750)
        self.setWindowTitle('Robocart control')

        self.json_received.connect(self.on_json_received)
        self.jpeg_received.connect(self.on_jpeg_received)

        udp_key = None
        if os.path.exists(UDP_KEY_FILE):
            with open(UDP_KEY_FILE, 'rb') as file:
                udp_key = file.read()

        if self.local_name != "":
            self.udp = UdpClient(self.local_name, self.udp_port, self.json_received, self.jpeg_received, udp_key)
            try:
                self.udp.resolve_addr()
            except Exception as e:
                print(e)

        if self.local_name == "" or self.udp.addr is None:
            self.udp = UdpClient(self.relay_host, self.relay_port, self.json_received, self.jpeg_received, udp_key)

        self.udp_timer = QTimer()
        self.udp_timer.timeout.connect(self.process_udp)
        self.udp_timer.start(250)
        self.udp_alive = False
        self.udp_time_delta = 0

        self.size_fixed = False

    def init_status_bar(self):
        statusbar = self.statusBar()

        widget = QWidget(self)
        widget.setLayout(QHBoxLayout())
        widget.layout().addWidget(self.VoltageLabel)
        widget.layout().addWidget(self.StateLabel)
        widget.layout().addWidget(self.MessageLabel)
        widget.layout().addWidget(self.ConnectionLabel)
        widget.layout().addStretch()
        statusbar.addWidget(widget)

    def closeEvent(self, ev):
        ev.accept()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        with open(CONFIG_FILE, 'r') as config_file:
            try:
                config_dict = json.load(config_file)
            except ValueError:
                config_dict = {}

        self.local_name = config_dict["local_name"]
        self.udp_port = config_dict["udp_port"]
        self.relay_host = config_dict["relay_host"]
        self.relay_port = config_dict["relay_port"]

    @staticmethod
    def remove_action(buttons, action_name):
        for b in buttons:
            if b['caption'] == action_name:
                buttons.remove(b)
        return buttons

    def on_json_received(self, js):
        voltage = js['voltage']
        if voltage is not None:
            voltage = f"{voltage:.1f}V"
        self.VoltageLabel.setText(voltage)

        state_name = js['state_name']

        if state_name != self.mainWidget.cur_state:
            self.StateLabel.setText(state_name)
            buttons = js.get('buttons')
            if buttons is None:
                buttons = []

            accept_click = js['accept_click']
            accept_rectangle = js['accept_rectangle']

            if state_name == 'main':
                buttons = self.remove_action(buttons, 'Pan')
                buttons = self.remove_action(buttons, 'Move')

            self.mainWidget.set_buttons(buttons)
            self.mainWidget.cur_state = js['state_name']
            self.mainWidget.set_mouse_policy(accept_click, accept_rectangle)

            status = ''
            if accept_click:
                status = js['click_cap']
            elif accept_rectangle:
                status = js['rectangle_cap']

            self.MessageLabel.setText(status)

    def on_jpeg_received(self, data):
        self.mainWidget.set_image(data)
        if not self.size_fixed:
            self.setFixedSize(self.layout().sizeHint())
            self.size_fixed = True

    def process_udp(self):
        self.udp.process()
        alive = self.udp.is_alive()
        time_delta = int(time.time())-self.udp.last_received_time

        if alive != self.udp_alive or (alive and self.udp_time_delta != time_delta):
            self.udp_alive = alive
            if alive:
                label = f'{self.udp.addr[0]} delay {time_delta}s'
                self.udp_time_delta = time_delta
            else:
                label = 'Not connected'
            self.ConnectionLabel.setText(label)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
