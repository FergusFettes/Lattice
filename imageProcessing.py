from PyQt5.QtGui import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time

class ImageCreator(QObject):
    imageSig = pyqtSignal(QPixmap)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()
    canvasfpsSig = pyqtSignal(float)

    def __init__(self, array, **kwargs):
        QObject.__init__(self)

        self.error.emit('Image thread starting up!')
        self.colorList = kwargs['COLORLIST']
        self.degree = 2

        self.scale = kwargs['SCALE']
        self.ARRAY = array
        self.N1 = array.shape[0]
        self.N2 = array.shape[1]
        self.ARRAYOLD = array
        self.LIVING = np.zeros([0, 2], bool)
        self.CHANGE = np.zeros([0, 3], bool)
        self.fpsRoll = np.zeros(5, float)

        self.image = QImage(self.N1, self.N2, QImage.Format_ARGB32)

    def addColors(self, colorList, degree):
        self.colorList = colorList
        self.degree = degree

    def resize_array(self, array):
        self.ARRAY = array
        self.ARRAYOLD = array
        self.imageSig.emit(array)

    def process(self):
        #this sure is living
        pass

    def process_array(self, array):
        now = time.time()
        self.ARRAY = array
        self.update_change()
        self.export_list(self.CHANGE)
        self.ARRAYOLD = self.ARRAY
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.canvasfpsSig.emit(np.mean(self.fpsRoll))
        self.finished.emit()

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
        im = self.image
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                num = int(A[i][j])
                color = self.colorList[num]
                im.setPixel(i, j, color)

        ims = im.scaled(QSize(A.shape[0] * self.scale, A.shape[1] * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)
        self.image = im

    # Updates image only where the pixels have changed. FASTER
    def export_list(self, L):
        im = self.image
        [im.setPixel(el[0], el[1], self.colorList[el[2]]) for el in L]

        ims = im.scaled(QSize(self.N1 * self.scale, self.N2 * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)
        self.image = im

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

    def paint(self, image):
        self.setPixmap(image)
        self.repaint()
