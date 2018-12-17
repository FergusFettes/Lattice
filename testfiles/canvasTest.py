from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time
import sys
import queue as queue

class StandardWindow(QWidget):

    def __init__(self, N, SCALE):
        super().__init__()

        self.n = N
        self.scale = SCALE
        self.canvas = QLabel()

        self.primaryColor = QColor(Qt.red)
        self.secondaryColor = QColor(Qt.green)
        self.colorList = []
        self.colorList.append(self.primaryColor)
        self.colorList.append(self.secondaryColor)
        self.reset()

        MainBox = QVBoxLayout()
        MainBox.addWidget(self.canvas)
        self.setLayout(MainBox)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
#       self.setWindowRole('popup')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()

    def reset(self):
        self.canvas.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))
        self.canvas.pixmap().fill(self.colorList[0])

    # Updates image with values from entire array. SLOW
    def export_array_scale(self, A):
        im = QImage(self.n, self.n, QImage.Format_ARGB32)
        for i in range(self.n):
            for j in range(self.n):
                if A[i][j]:
                    im.setPixel(i, j, self.colorList[1].rgba())
                else:
                    im.setPixel(i, j, self.colorList[0].rgba())

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.canvas.setPixmap(nupix)

    # Updates image with values from entire array. SLOW
    def export_array(self, A):
        im = QImage((self.n * self.scale), (self.n * self.scale), QImage.Format_ARGB32)
        for i in range(self.n * self.scale):
            for j in range(self.n * self.scale):
                if A[int(i / self.scale)][int(j / self.scale)]:
                    im.setPixel(i, j, self.colorList[1].rgba())
                else:
                    im.setPixel(i, j, self.colorList[0].rgba())

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)

    def export_list_refactor2(self, L, living):
        im = self.canvas.pixmap().toImage().scaled((QSize(self.n, self.n)))
        map((lambda x: im.setPixel(x[0], x[1], self.colorList[x[2]].rgba())), L)

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.canvas.setPixmap(nupix)

    # Updates image only where the pixels have changed. FASTER
    # TODO: Make more performant, use bitdata, also QGLWidget
    def export_list_refactor(self, L, living):
        im = self.canvas.pixmap().toImage().scaled((QSize(self.n, self.n)))
        for el in L:
            im.setPixel(el[0], el[1], self.colorList[el[2]].rgba())

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.canvas.setPixmap(nupix)

    # Updates image only where the pixels have changed. FASTER
    # TODO: Make more performant, use bitdata, also QGLWidget
    def export_list(self, L, living):
        im = self.canvas.pixmap().toImage()
        for el in L:
            for i in range(self.scale):
                for j in range(self.scale):
                    im.setPixel((self.scale * el[0]) + i, (self.scale * el[1])\
                                + j, self.colorList[el[2]].rgba())

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)

#if __name__ == '__main__':

app = QApplication([])
N = 100
SCALE = 5
THRESH = 0.1
array = np.random.random([N, N]) > THRESH
living = np.argwhere(array)
A = array
change = [[i[0], i[1], A[i[0], i[1]]] for i in living]

w = StandardWindow(N, SCALE)
#w.export_list(change, 0)
w.export_list_refactor(change, 0)
#w.export_array(array)
#w.export_list(living, 1)
#w.canvas.repaint()

app.exec()
