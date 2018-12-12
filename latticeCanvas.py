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
        self.reset(**kwargs)
        self.N = kwargs['N']
        self.SCALE = kwargs['SCALE']

    def reset(self, **kwargs):
        self.setPixmap(QPixmap(kwargs['N'] * kwargs['SCALE'], kwargs['N'] * kwargs['SCALE']))

        self.pixmap().fill(self.primaryColor)

    # Updates image with values from entire array. SLOW
    def exportArray(self, A):
        im = QImage((self.N * self.SCALE), (self.N * self.SCALE), QImage.Format_ARGB32)
        for i in range(self.N * self.SCALE):
            for j in range(self.N * self.SCALE):
                if A[int(i / self.SCALE)][int(j / self.SCALE)]==1:
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
            for i in range(self.SCALE):
                for j in range(self.SCALE):
                    if el[2] == 1:
                        im.setPixel((self.SCALE * el[0]) + i, (self.SCALE * el[1]) + j, self.primaryColor.rgba())
                    else:
                        im.setPixel((self.SCALE * el[0]) + i, (self.SCALE * el[1]) + j, self.secondaryColor.rgba())

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.setPixmap(nupix)
