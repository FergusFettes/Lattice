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
        self.primaryColor = QColor(kwargs['PRIMARYCOLOR'])
        self.secondaryColor = QColor(kwargs['SECONDARYCOLOR'])
        self.interrupt = False
        self.colorList = []
        self.degree = 2
        self.n = kwargs['N']
        self.scale = kwargs['SCALE']
        self.reset()
        self.Array = np.zeros((self.n * self.scale, self.n * self.scale), int)

    def reset(self):
        self.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))

        self.pixmap().fill(self.primaryColor)

    def setColor(self, color, newValue):
        self.color = QColor(newValue)

    def addColors(self, colorList, degree):
        self.colorList = colorList
        self.degree = degree

    def INTERRUPT(self, state):
        self.interrupt

    # Updates image with values from entire array. SLOW
    def export_array(self, A):
        now = time.time()
        im = QImage(self.n, self.n, QImage.Format_ARGB32)
        for i in range(self.n):
            for j in range(self.n):
                num = A[int(i)][int(j)]
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

    # Updates image only where the pixels have changed. FASTER
    # TODO: Make more performant, use bitdata, also QGLWidget
    def export_list2(self, L, living):
        im = self.pixmap().toImage()
        if living:
            for el in L:
                for i in range(self.scale):
                    for j in range(self.scale):
                        im.setPixel((self.scale * el[0]) + i, (self.scale * el[1])
                                    + j, self.colorList[1])
        else:
            for el in L:
                for i in range(self.scale):
                    for j in range(self.scale):
                        im.setPixel((self.scale * el[0]) + i, (self.scale * el[1])\
                                    + j, self.colorList[el[2]])

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.setPixmap(nupix)
        self.repaint()
