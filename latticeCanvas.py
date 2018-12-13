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
        self.colorList = []
        self.degree = 2
        self.n = kwargs['N']
        self.scale = kwargs['SCALE']
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))

        self.pixmap().fill(self.primaryColor)

    def setColor(self, color, newValue):
        self.color = QColor(newValue)

    def addColors(self, colorList, degree):
        self.colorList = colorList
        self.degree = degree

    # Updates image with values from entire array. SLOW
    def exportArray(self, A):
        im = QImage((self.n * self.scale), (self.n * self.scale), QImage.Format_ARGB32)
        for i in range(self.n * self.scale):
            for j in range(self.n * self.scale):
                num = A[int(i / self.scale)][int(j / self.scale)]
                color = self.colorList[num]
                im.setPixel(i, j, color)

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
                    im.setPixel((self.scale * el[0]) + i, (self.scale * el[1])\
                                + j, self.colorList[el[2]])

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.setPixmap(nupix)
