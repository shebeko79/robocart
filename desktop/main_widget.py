from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGroupBox
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont
from PyQt5.QtCore import QRect, QPoint
import math


class MainWidget(QWidget):
    CAM_ANG = 5 / 180 * math.pi

    def __init__(self, application):
        super(MainWidget, self).__init__(application)
        self.app = application

        self.image = ImageWidget(self)

        self.camUpBtn = QPushButton('^', self)
        self.camDownBtn = QPushButton('v', self)
        self.camLeftBtn = QPushButton('<', self)
        self.camRightBtn = QPushButton('>', self)

        self.cartForwardBtn = QPushButton('^', self)
        self.cartBackwardBtn = QPushButton('v', self)
        self.cartLeftBtn = QPushButton('<', self)
        self.cartRightBtn = QPushButton('>', self)

        self.buttonsLayout = QVBoxLayout()

        self.init_ui()
        self.check_controls()

    def init_ui(self):
        self.image = ImageWidget(self)

        self.camUpBtn.clicked.connect(self.fire_cam_up)
        self.camDownBtn.clicked.connect(self.fire_cam_down)
        self.camLeftBtn.clicked.connect(self.fire_cam_left)
        self.camRightBtn.clicked.connect(self.fire_cam_right)

        self.cartForwardBtn.clicked.connect(self.fire_cart_forward)
        self.cartBackwardBtn.clicked.connect(self.fire_cart_backward)
        self.cartLeftBtn.clicked.connect(self.fire_cart_left)
        self.cartRightBtn.clicked.connect(self.fire_cart_right)

        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.camUpBtn)
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.camLeftBtn)
        hlayout.addWidget(self.camDownBtn)
        hlayout.addWidget(self.camRightBtn)
        vlayout.addLayout(hlayout)

        camera_group_box = QGroupBox("Camera")
        camera_group_box.setLayout(vlayout)


        vlayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.cartForwardBtn)
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.cartLeftBtn)
        hlayout.addWidget(self.cartBackwardBtn)
        hlayout.addWidget(self.cartRightBtn)
        vlayout.addLayout(hlayout)

        cart_group_box = QGroupBox("Cart")
        cart_group_box.setLayout(vlayout)

        ctl_layout = QVBoxLayout()
        ctl_layout.addWidget(camera_group_box)
        ctl_layout.addWidget(cart_group_box)
        ctl_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image)
        main_layout.addLayout(ctl_layout)

        self.setLayout(main_layout)

    def check_controls(self):
        #self.firstButton.setEnabled(not_first_img)
        pass

    def move_cam(self, pan, tilt):
        js = {'cmd': 'move_cam', 'pan': pan, 'tilt': tilt}
        self.app.udp.send_json(js)

    def moveto_cam(self, pan, tilt):
        js = {'cmd': 'moveto_cam', 'pan': pan, 'tilt': tilt}
        self.app.udp.send_json(js)

    def move_cart(self, speed, pan):
        js = {'cmd': 'move', 'speed': speed, 'pan': pan}
        self.app.udp.send_json(js)

    def fire_cam_up(self):
        self.move_cam(0, -self.CAM_ANG)

    def fire_cam_down(self):
        self.move_cam(0, self.CAM_ANG)

    def fire_cam_left(self):
        self.move_cam(-self.CAM_ANG, 0)

    def fire_cam_right(self):
        self.move_cam(self.CAM_ANG, 0)

    def fire_cart_forward(self):
        self.move_cart(1.0, 0.0)

    def fire_cart_backward(self):
        self.move_cart(-1.0, 0.0)

    def fire_cart_left(self):
        self.move_cart(0.0, -1.0)

    def fire_cart_right(self):
        self.move_cart(0.0, 1.0)

    def set_image(self, jpg):
        self.image.init(jpg)

    def keyPressEvent(self, e):
        k = e.key()

        if k == Qt.Key_W:
            self.fire_cam_up()
        elif k == Qt.Key_S:
            self.fire_cam_down()
        elif k == Qt.Key_A:
            self.fire_cam_left()
        elif k == Qt.Key_D:
            self.fire_cam_right()
        elif k == Qt.Key_Right:
            self.fire_cart_right()
        elif k == Qt.Key_Left:
            self.fire_cart_left()
        elif k == Qt.Key_Up:
            self.fire_cart_forward()
        elif k == Qt.Key_Down:
            self.fire_cart_backward()


class ImageWidget(QWidget):
    def __init__(self, main_widget: MainWidget):
        super(ImageWidget, self).__init__(main_widget.app)
        self.main_widget = main_widget
        self.app = main_widget.app
        self.results = []
        self.setMouseTracking(True)
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.modified = False

        self.pixmap = QPixmap()
        self.image = QLabel()
        self.image.setObjectName("image")
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

        self.drawing = False
        self.lastPoint = QPoint()
        hbox = QHBoxLayout(self.image)
        self.setLayout(hbox)

    def init(self, jpeg_data):
        self.pixmap.loadFromData(jpeg_data,"JPEG")
        self.W, self.H = self.pixmap.width(), self.pixmap.height()
        #print(f'{self.W=} {self.H=}')

        if self.H > self.screen_height * 0.8:
            resize_ratio = (self.screen_height * 0.8) / self.H
            self.W = round(self.W * resize_ratio)
            self.H = round(self.H * resize_ratio)
            self.pixmap = QPixmap.scaled(self.pixmap, self.W, self.H,
                                         transformMode=Qt.SmoothTransformation)

        self.setFixedSize(self.W, self.H)
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

        #self.pixmap = self.drawResultBox()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.pixmap)

    def mousePressEvent(self, event):
        pass
        '''
        if event.button() == Qt.LeftButton:
            self.prev_pixmap = self.pixmap
            self.drawing = True
            self.lastPoint = event.pos()
        elif event.button() == Qt.RightButton:
            x, y = event.pos().x(), event.pos().y()
            for i, box in enumerate(self.results):
                lx, ly, rx, ry = box[:4]
                if lx <= x <= rx and ly <= y <= ry:
                    self.results.pop(i)
                    self.modified = True
                    self.pixmap = self.drawResultBox()
                    self.update()
                    break
        '''

    def constrains(self, x, y):
        if x < 0:
            x = 0
        elif x >= self.pixmap.width():
            x = self.pixmap.width() - 1

        if y < 0:
            y = 0
        elif y >= self.pixmap.height():
            y = self.pixmap.height() - 1

        return [x, y]

    def mouseMoveEvent(self, event):
        pass
        '''
        self.app.cursorPos.setText(f'({event.pos().x()}, {event.pos().y()})')
        if event.buttons() and Qt.LeftButton and self.drawing:
            self.pixmap = QPixmap.copy(self.prev_pixmap)
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            p1_x, p1_y = self.lastPoint.x(), self.lastPoint.y()
            p2_x, p2_y = event.pos().x(), event.pos().y()
            p2_x, p2_y = self.constrains(p2_x, p2_y)
            painter.drawRect(min(p1_x, p2_x), min(p1_y, p2_y),
                             abs(p1_x - p2_x), abs(p1_y - p2_y))
            self.update()
        '''

    def mouseReleaseEvent(self, event):
        pass
        '''
        if event.button() != Qt.LeftButton:
            return

        if not self.drawing:
            return

        self.drawing = False

        p1_x, p1_y = self.lastPoint.x(), self.lastPoint.y()
        p2_x, p2_y = event.pos().x(), event.pos().y()
        p2_x, p2_y = self.constrains(p2_x, p2_y)

        if (p1_x, p1_y) == (p2_x, p2_y):
            return

        l1x, l1y = min(p1_x, p2_x), min(p1_y, p2_y)
        l2x, l2y = max(p1_x, p2_x), max(p1_y, p2_y)

        self.results.append([l1x, l1y, l2x, l2y, 0])

        sel_idx = self.main_widget.classesCombo.currentIndex()
        if sel_idx < 0:
            sel_idx = 0
        self.markBox(sel_idx)
        '''

    def resetDrawing(self):
        self.drawing = False
        self.pixmap = self.drawResultBox()
        self.update()

    def drawResultBox(self):
        res = QPixmap.copy(self.pixmapOriginal)
        painter = QPainter(res)
        font = QFont('mono', 15, 1)
        painter.setFont(font)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        for box in self.results:
            lx, ly, rx, ry = box[:4]
            painter.drawRect(lx, ly, rx - lx, ry - ly)
            idx = box[4]
            if 0 <= idx < len(self.main_widget.classes):
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawText(lx, ly + 15, self.main_widget.classes[idx])
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        return res
