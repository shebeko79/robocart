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

        self.cur_state = ''

        self.image = ImageWidget(self)

        self.camUpBtn = QPushButton('^ (W)', self)
        self.camDownBtn = QPushButton('v (S)', self)
        self.camLeftBtn = QPushButton('< (A)', self)
        self.camRightBtn = QPushButton('> (D)', self)

        self.camLeftPosBtn = QPushButton('Left (L)', self)
        self.camRightPosBtn = QPushButton('Right (R)', self)
        self.camFrontBtn = QPushButton('Front (F)', self)
        self.camTopBtn = QPushButton('Top (T)', self)
        self.camBackBtn = QPushButton('Back (B)', self)

        self.camLeftMostBtn = QPushButton('< (Q)', self)
        self.camRightMostBtn = QPushButton('> (E)', self)
        self.camBackMostBtn = QPushButton('^ (Z)', self)
        self.camFrontMostBtn = QPushButton('v (C)', self)

        self.cartForwardBtn = QPushButton('^', self)
        self.cartBackwardBtn = QPushButton('v', self)
        self.cartLeftBtn = QPushButton('<', self)
        self.cartRightBtn = QPushButton('>', self)

        self.dynamic_buttons_group_box = QGroupBox("Actions")
        self.dynamic_buttons = []

        self.buttonsLayout = QVBoxLayout()

        self.init_ui()
        self.check_controls()

    def init_ui(self):
        self.image = ImageWidget(self)

        self.camUpBtn.clicked.connect(self.fire_cam_up)
        self.camDownBtn.clicked.connect(self.fire_cam_down)
        self.camLeftBtn.clicked.connect(self.fire_cam_left)
        self.camRightBtn.clicked.connect(self.fire_cam_right)

        self.camLeftPosBtn.clicked.connect(self.fire_cam_left_pos)
        self.camRightPosBtn.clicked.connect(self.fire_cam_right_pos)
        self.camFrontBtn.clicked.connect(self.fire_cam_front)
        self.camTopBtn.clicked.connect(self.fire_cam_top)
        self.camBackBtn.clicked.connect(self.fire_cam_back)

        self.camLeftMostBtn.clicked.connect(self.fire_cam_left_most)
        self.camRightMostBtn.clicked.connect(self.fire_cam_right_most)
        self.camBackMostBtn.clicked.connect(self.fire_cam_back_most)
        self.camFrontMostBtn.clicked.connect(self.fire_cam_front_most)

        self.cartForwardBtn.clicked.connect(self.fire_cart_forward)
        self.cartBackwardBtn.clicked.connect(self.fire_cart_backward)
        self.cartLeftBtn.clicked.connect(self.fire_cart_left)
        self.cartRightBtn.clicked.connect(self.fire_cart_right)

        self.image.setFixedSize(640, 640)

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
        hlayout.addWidget(self.camBackMostBtn)
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.camBackBtn)
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.camLeftMostBtn)
        hlayout.addWidget(self.camTopBtn)
        hlayout.addWidget(self.camRightMostBtn)
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.camLeftPosBtn)
        hlayout.addWidget(self.camFrontBtn)
        hlayout.addWidget(self.camRightPosBtn)
        vlayout.addLayout(hlayout)

        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.camFrontMostBtn)
        hlayout.addStretch()
        vlayout.addLayout(hlayout)

        cam_views_group_box = QGroupBox("Camera views")
        cam_views_group_box.setLayout(vlayout)

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

        vlayout = QVBoxLayout()
        self.dynamic_buttons_group_box.setLayout(vlayout)

        ctl_layout = QVBoxLayout()
        ctl_layout.addWidget(camera_group_box)
        ctl_layout.addWidget(cam_views_group_box)
        ctl_layout.addWidget(cart_group_box)
        ctl_layout.addWidget(self.dynamic_buttons_group_box)
        ctl_layout.addStretch()

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image)
        image_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(image_layout)
        main_layout.addLayout(ctl_layout)

        self.setLayout(main_layout)

        self.setFocusPolicy(Qt.TabFocus)
        self.image.setFocusPolicy(Qt.NoFocus)
        self.camUpBtn.setFocusPolicy(Qt.TabFocus)
        self.camDownBtn.setFocusPolicy(Qt.TabFocus)
        self.camLeftBtn.setFocusPolicy(Qt.TabFocus)
        self.camRightBtn .setFocusPolicy(Qt.TabFocus)
        self.camLeftPosBtn.setFocusPolicy(Qt.TabFocus)
        self.camRightPosBtn.setFocusPolicy(Qt.TabFocus)
        self.camFrontBtn.setFocusPolicy(Qt.TabFocus)
        self.camTopBtn.setFocusPolicy(Qt.TabFocus)
        self.camBackBtn.setFocusPolicy(Qt.TabFocus)
        self.camLeftMostBtn.setFocusPolicy(Qt.TabFocus)
        self.camRightMostBtn.setFocusPolicy(Qt.TabFocus)
        self.camBackMostBtn.setFocusPolicy(Qt.TabFocus)
        self.camFrontMostBtn.setFocusPolicy(Qt.TabFocus)
        self.cartForwardBtn.setFocusPolicy(Qt.TabFocus)
        self.cartBackwardBtn.setFocusPolicy(Qt.TabFocus)
        self.cartLeftBtn.setFocusPolicy(Qt.TabFocus)
        self.cartRightBtn.setFocusPolicy(Qt.TabFocus)

    def check_controls(self):
        #self.firstButton.setEnabled(not_first_img)
        pass

    def set_buttons(self, buttons):
        layout = self.dynamic_buttons_group_box.layout()
        print(buttons)

        for w in self.dynamic_buttons:
            layout.removeWidget(w)
            w.deleteLater()

        self.dynamic_buttons = []

        for b in buttons:
            button_name = b['caption']
            w = QPushButton('', self)
            w.setText(button_name)
            w.setEnabled(b['enabled'])
            w.clicked.connect(lambda state, bn=button_name: self.fire_dynamic_button(bn))

            self.dynamic_buttons.append(w)
            layout.addWidget(w)

    def move_cam(self, pan, tilt):
        js = {'cmd': 'move_cam', 'pan': pan, 'tilt': tilt}
        self.app.udp.send_json(js)

    def moveto_cam(self, pan, tilt):
        js = {'cmd': 'moveto_cam', 'pan': pan, 'tilt': tilt}
        self.app.udp.send_json(js)

    def moveto_cam(self, pan, tilt):
        js = {'cmd': 'moveto_cam', 'pan': pan, 'tilt': tilt}
        self.app.udp.send_json(js)

    def move_cart(self, speed, pan):
        js = {'cmd': 'move', 'speed': speed, 'pan': pan}
        self.app.udp.send_json(js)

    def fire_dynamic_button(self, button_name):
        js = {'cmd': 'click', 'state_name': self.cur_state, 'caption': button_name}
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

    def fire_cam_left_pos(self):
        self.moveto_cam('LEFT', 'FRONT')

    def fire_cam_right_pos(self):
        self.moveto_cam('RIGHT', 'FRONT')

    def fire_cam_front(self):
        self.moveto_cam('CENTER', 'FRONT')

    def fire_cam_top(self):
        self.moveto_cam('CENTER', 'UP')

    def fire_cam_back(self):
        self.moveto_cam('CENTER', 'BACKWARD')

    def fire_cam_left_most(self):
        self.moveto_cam('MIN', 'CURRENT')

    def fire_cam_right_most(self):
        self.moveto_cam('MAX', 'CURRENT')

    def fire_cam_back_most(self):
        self.moveto_cam('CURRENT', 'MIN')

    def fire_cam_front_most(self):
        self.moveto_cam('CURRENT', 'MAX')

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
        elif k == Qt.Key_L:
            self.fire_cam_left_pos()
        elif k == Qt.Key_R:
            self.fire_cam_right_pos()
        elif k == Qt.Key_F:
            self.fire_cam_front()
        elif k == Qt.Key_T:
            self.fire_cam_top()
        elif k == Qt.Key_B:
            self.fire_cam_back()
        elif k == Qt.Key_Q:
            self.fire_cam_left_most()
        elif k == Qt.Key_E:
            self.fire_cam_right_most()
        elif k == Qt.Key_Z:
            self.fire_cam_back_most()
        elif k == Qt.Key_C:
            self.fire_cam_front_most()
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
