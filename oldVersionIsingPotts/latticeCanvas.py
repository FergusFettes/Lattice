from PyQt5.QtGui import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time

class ImageCreator(QObject):
    imageSig = pyqtSignal(QPixmap)
    breakSig = pyqtSignal()

    def __init__(self, array):
        QObject.__init__(self)

        self.ARRAY = array
        self.ARRAYOLD = array
        self.LIVING = np.zeros([0, 2], bool)
        self.CHANGE = np.zeros([0, 3], bool)

    def resize_array(self, array):
        self.ARRAY = array
        self.ARRAYOLD = array
        self.imageSig.emit(array)

    def process(self, array):
        now = time.time()
        self.ARRAY = array
        self.update_change()
        self.export_list(self.CHANGE)
        self.ARRAYOLD = self.ARRAY
        self.canvasfpsSig.emit(time.time()-now)

    def update_living(self):
        self.LIVING = np.argwhere(self.ARRAY)

    def update_change(self):
        common = np.bitwise_and(self.ARRAY, self.ARRAYOLD)
        onlyOld = np.bitwise_xor(common, self.ARRAYOLD)
        onlyNew = np.bitwise_xor(common, self.ARRAY)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        self.CHANGE = np.concatenate((b, d))
        if not self.CHANGE.size:
            self.breakSig.emit()

    # Updates image with values from entire array. SLOW
    def export_array(self, A):
        im = QImage(self.n, self.n, QImage.Format_ARGB32)
        for i in range(self.n):
            for j in range(self.n):
                num = int(A[i][j])
                color = self.colorList[num]
                im.setPixel(i, j, color)

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)

    # Updates image only where the pixels have changed. FASTER
    def export_list(self, L, living):
        im = self.pixmap().toImage().scaled((QSize(self.n, self.n)))
        if living:
            [im.setPixel(el[0], el[1], self.colorList[1]) for el in L]
        else:
            [im.setPixel(el[0], el[1], self.colorList[el[2]]) for el in L]

        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)

#====================The canvas=================#
# It isnt so exciting since I moved everything to the processor
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

    def paint(self, image):
        self.setPixmap(image)
        self.update()
