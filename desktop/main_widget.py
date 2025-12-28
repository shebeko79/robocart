import sys
import os
import cv2
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QComboBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QLabel
from PyQt5.QtWidgets import QDesktopWidget, QMessageBox, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPen, QFont
from PyQt5.QtCore import QRect, QPoint
import packet_processor


class MainWidget(QWidget):
    def __init__(self, application):
        super(MainWidget, self).__init__(application)
        self.app = application

        self.image = ImageWidget(self)

        self.camUpBtn = QPushButton('^', self)
        self.camDownBtn = QPushButton('v', self)
        self.camLeftBtn = QPushButton('<', self)
        self.camRightBtn = QPushButton('>', self)

        self.cartUpBtn = QPushButton('^', self)
        self.cartDownBtn = QPushButton('v', self)
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
        self.camRightBtn.clicked.connect(self.fire_cam_down)

        self.cartUpBtn.clicked.connect(self.fire_cam_up)
        self.cartDownBtn.clicked.connect(self.fire_cam_down)
        self.cartLeftBtn.clicked.connect(self.fire_cam_left)
        self.cartRightBtn.clicked.connect(self.fire_cam_down)

        cam_vlayout = QVBoxLayout()
        cam_vlayout.addWidget(self.camUpBtn)

        cam_hlayout = QHBoxLayout()
        cam_hlayout.addWidget(self.camLeftBtn)
        cam_hlayout.addWidget(self.camDownBtn)
        cam_hlayout.addWidget(self.camRightBtn)

        cam_vlayout.addLayout(cam_hlayout)

        cart_vlayout = QVBoxLayout()
        cart_vlayout.addWidget(self.cartUpBtn)

        cart_hlayout = QHBoxLayout()
        cart_hlayout.addWidget(self.cartLeftBtn)
        cart_hlayout.addWidget(self.cartDownBtn)
        cart_hlayout.addWidget(self.cartRightBtn)

        cart_vlayout.addLayout(cart_hlayout)

        ctl_layout = QVBoxLayout()
        ctl_layout.addLayout(cam_vlayout)
        ctl_layout.addLayout(cart_vlayout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image)
        main_layout.addLayout(ctl_layout)

        self.setLayout(main_layout)

    def check_controls(self):
        #self.firstButton.setEnabled(not_first_img)
        pass

    def fire_cam_up(self):
        pass

    def fire_cam_down(self):
        pass

    def fire_cam_left(self):
        pass

    def fire_cam_right(self):
        pass

    def fire_cart_up(self):
        pass

    def fire_cart_down(self):
        pass

    def fire_cart_left(self):
        pass

    def fire_cart_right(self):
        pass

    def setCurrentImage(self):
        '''
        img_file = self.images[self.cur_image]
        filename, ext = os.path.splitext(img_file)

        img_file = os.path.join(self.directory, "images/"+img_file)

        self.app.fileName.setText(filename)
        self.app.progress.setText(str(self.cur_image)+'/'+str(len(self.images)))

        self.image.init(img_file)
        '''
        self.app.fitSize()

    def keyPressEvent(self, e):
        k = e.key()
        '''
        if self.image.drawing:
            if e.key() == Qt.Key_Escape:
                self.image.resetDrawing()
            return

        if 0x30 <= e.key() <= 0x39:
            idx = e.key()-0x30
            if idx < self.classesCombo.count():
                self.classesCombo.setCurrentIndex(idx)
            self.image.markBox(idx)
        if e.key() == Qt.Key_Escape:
            self.image.removeLast()
        elif e.key() == Qt.Key_Right:
            self.nextImage()
        elif e.key() == Qt.Key_Left:
            self.prevImage()
        elif e.key() == Qt.Key_Up:
            sel_idx = self.classesCombo.currentIndex()
            sel_idx -= 1
            if sel_idx >= 0:
                self.classesCombo.setCurrentIndex(sel_idx)
                self.image.markBox(sel_idx)
        elif e.key() == Qt.Key_Down:
            sel_idx = self.classesCombo.currentIndex()
            sel_idx += 1
            if sel_idx < len(self.classes):
                self.classesCombo.setCurrentIndex(sel_idx)
                self.image.markBox(sel_idx)
        '''


class ImageWidget(QWidget):
    def __init__(self, main_widget: MainWidget):
        super(ImageWidget, self).__init__(main_widget.app)
        self.main_widget = main_widget
        self.app = main_widget.app
        self.results = []
        self.setMouseTracking(True)
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.modified = False

        self.init_ui()

    def init_ui(self):
        self.pixmap = QPixmap()
        self.image = QLabel()
        self.image.setObjectName("image")
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

        self.drawing = False
        self.lastPoint = QPoint()
        hbox = QHBoxLayout(self.image)
        self.setLayout(hbox)

    def init(self, img_file, txt_file):
        self.setPixmap(img_file)
        self.txt_file = txt_file
        self.pixmap = self.drawResultBox()
        self.update()

    def setPixmap(self, image_fn):
        self.pixmap = QPixmap(image_fn)
        self.W, self.H = self.pixmap.width(), self.pixmap.height()

        if self.H > self.screen_height * 0.8:
            resize_ratio = (self.screen_height * 0.8) / self.H
            self.W = round(self.W * resize_ratio)
            self.H = round(self.H * resize_ratio)
            self.pixmap = QPixmap.scaled(self.pixmap, self.W, self.H,
                                         transformMode=Qt.SmoothTransformation)

        self.setFixedSize(self.W, self.H)
        self.pixmapOriginal = QPixmap.copy(self.pixmap)

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
