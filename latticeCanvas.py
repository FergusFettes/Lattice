from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

class Canvas(QLabel):

    def initialize(self, **kwargs):
        self.primaryColor = QColor(kwargs['PRIMARYCOLOR'])
        self.secondaryColor = QColor(kwargs['SECONDARYCOLOR'])
        self.n = kwargs['N']
        self.scale = kwargs['SCALE']
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))

        self.pixmap().fill(self.primaryColor)

    def setColor(self, color, newValue):
        self.color = QColor(newValue)

    # Updates image with values from entire array. SLOW
    def exportArray(self, A):
        im = QImage((self.n * self.scale), (self.n * self.scale), QImage.Format_ARGB32)
        for i in range(self.n * self.scale):
            for j in range(self.n * self.scale):
                if A[int(i / self.scale)][int(j / self.scale)]==1:
                    im.setPixel(i, j, self.primaryColor.rgba())
                else:
                    im.setPixel(i, j, self.secondaryColor.rgba())

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.setPixmap(nupix)

    # Updates image only where the pixels have changed. FASTER
    # TODO: Make more performant, use bitdata, also QGLWidget
    def exportList(self, L):
        im = self.pixmap().toImage()
        for el in L:
            for i in range(self.scale):
                for j in range(self.scale):
                    if el[2] == 1:
                        im.setPixel((self.scale * el[0]) + i,\
                                    (self.scale * el[1]) + j,\
                                     self.primaryColor.rgba())
                    else:
                        im.setPixel((self.scale * el[0]) + i,\
                                    (self.scale * el[1]) + j,\
                                     self.secondaryColor.rgba())

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.setPixmap(nupix)
