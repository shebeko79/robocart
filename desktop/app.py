import sys
import os
import json
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QHBoxLayout,  QLabel
from main_widget import MainWidget
from udp_client import UdpClient


class MainWindow(QMainWindow):

    json_received = pyqtSignal(object)
    jpeg_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()

        self.host_name = "robocart"
        self.udp_port = 5005
        self.load_config()

        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.ConnectionLabel = QLabel('Not connected')
        self.VoltageLabel = QLabel('Unknown')
        self.StateLabel = QLabel('Unknown')
        self.init_status_bar()

        self.setGeometry(50, 50, 1200, 800)
        self.setWindowTitle('Robocart control')

        self.json_received.connect(self.on_json_received)
        self.jpeg_received.connect(self.on_jpeg_received)

        self.udp = UdpClient(self.host_name, self.udp_port, self.json_received, self.jpeg_received)
        self.udp_timer = QTimer()
        self.udp_timer.timeout.connect(self.process_udp)
        self.udp_timer.start(250)
        self.udp_alive = False

        self.size_fixed = False

    def init_status_bar(self):
        statusbar = self.statusBar()
        #self.setStatusBar(statusbar)

        widget = QWidget(self)
        widget.setLayout(QHBoxLayout())
        widget.layout().addWidget(self.ConnectionLabel)
        widget.layout().addWidget(self.VoltageLabel)
        widget.layout().addWidget(self.StateLabel)
        widget.layout().addStretch()
        statusbar.addWidget(widget)

    def closeEvent(self, ev):
        ev.accept()

    def load_config(self):
        if not os.path.exists('config.json'):
            return

        with open('config.json', 'r') as config_file:
            try:
                config_dict = json.load(config_file)
            except ValueError:
                config_dict = {}

        self.host_name = config_dict["host_name"]
        self.udp_port = config_dict["udp_port"]

    def on_json_received(self, js):
        voltage = js['voltage']
        if voltage is not None:
            voltage = f"{voltage:.1f}V"
        self.VoltageLabel.setText(voltage)

        self.StateLabel.setText(js['state_name'])

        #js['accept_click']
        #js['accept_rectangle']
        #js['rectangle_cap']
        #js['click_cap']

    def on_jpeg_received(self, data):
        self.mainWidget.set_image(data)
        if not self.size_fixed:
            self.setFixedSize(self.layout().sizeHint())
            self.size_fixed = True

    def process_udp(self):
        self.udp.process()
        alive = self.udp.is_alive()
        if alive != self.udp_alive:
            self.udp_alive = alive
            self.ConnectionLabel.setText('Connected' if alive else 'Not connected')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
