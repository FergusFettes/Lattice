from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

# TODO: write and interrupt handler, so you don't need to have those stupid
# 'frames' anymore, and you can just quit a run. This is probably the best
# place to do it?
class Canvas(QLabel):
    canvasfpsSig = pyqtSignal(float)

    def initialize(self, **kwargs):
        self.primaryColor = QColor(kwargs['BACKCOLOR1'])
        self.secondaryColor = QColor(kwargs['BACKCOLOR2'])
        self.colorList = []
        self.degree = 2
        self.n = kwargs['N']
        self.scale = kwargs['SCALE']
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))

        self.pixmap().fill(self.primaryColor)

    def addColors(self, colorList, degree):
        self.colorList = colorList
        self.degree = degree

    # Updates image with values from entire array. SLOW
    def export_array(self, A):
        now = time.time()
        im = QImage(self.n, self.n, QImage.Format_ARGB32)
        for i in range(self.n):
            for j in range(self.n):
                num = A[i][j]
                color = self.colorList[num]
                im.setPixel(i, j, color)

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.setPixmap(nupix)
        self.repaint()
        self.canvasfpsSig.emit(time.time()-now)


    # Updates image only where the pixels have changed. FASTER
    def export_list(self, L, living):
        now = time.time()
        im = self.pixmap().toImage().scaled((QSize(self.n, self.n)))
        if living:
            for el in L:
                im.setPixel(el[0], el[1], self.colorList[1])
           #map((lambda x: im.setPixel(x[0], x[1], self.colorList[1])), L)
        else:
            for el in L:
                im.setPixel(el[0], el[1], self.colorList[el[2]])
           #map((lambda x: im.setPixel(x[0], x[1], self.colorList[x[2]])), L)

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.setPixmap(nupix)
        self.repaint()
        self.canvasfpsSig.emit(time.time()-now)
