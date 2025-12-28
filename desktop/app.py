import sys
import os
import json
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QHBoxLayout,  QLabel
from main_widget import MainWidget
from udp_client import UdpReceiver


class MainWindow(QMainWindow):

    packet_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()

        self.host_name = "maixcam-962b.local"
        self.udp_port = 5005
        self.load_config()

        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.ConnectionLabel = None
        self.VoltageLabel = None
        self.StateLabel = None
        self.init_status_bar()

        self.setGeometry(50, 50, 1200, 800)
        self.setWindowTitle('Control application')

        self.packet_received.connect(self.on_packet_received)

        self.udp = UdpReceiver(self.host_name, self.udp_port, self.packet_received)
        self.udp.start()

    def init_status_bar(self):
        self.ConnectionLabel = QLabel('      ')
        self.VoltageLabel = QLabel('Ready')
        self.StateLabel = QLabel('      ')

        statusbar = self.statusBar()
        self.setStatusBar(statusbar)

        widget = QWidget(self)
        widget.setLayout(QHBoxLayout())
        widget.layout().addWidget(self.ConnectionLabel)
        widget.layout().addWidget(self.VoltageLabel)
        widget.layout().addWidget(self.StateLabel)
        widget.layout().addStretch(1)
        statusbar.addWidget(widget, 1)

    def fit_size(self):
        self.setFixedSize(self.layout().sizeHint())

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

    def on_packet_received(self, data):
        print(f"on_packet_received(): {len(data)=}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
