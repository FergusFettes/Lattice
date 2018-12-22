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

    def __init__(self, **kwargs):
        QObject.__init__(self)

        self.error.emit('Image thread starting up!')
        self.colorList = kwargs['COLORLIST']
        self.degree = 2

        self.scale = kwargs['SCALE']
        self.fpsRoll = np.zeros(5, float)
        self.kwargs = kwargs

        self.N = kwargs['N']
        self.D = kwargs['D']
        self.resize_array(self.N, self.D)

        line = np.random.randint(0, 2, (self.N))
        self.wolf = self.wolframgen(line)
        self.current = 0

    # Resize/reset
    def resize_array(self, N, D):
        self.ARRAY = np.zeros([N, D], bool)
        self.ARRAYOLD = np.zeros([N, D], bool)
        self.LIVING = np.zeros([0, 2], bool)
        self.CHANGE = np.zeros([0, 3], bool)
        self.image = QImage(N, D, QImage.Format_ARGB32)
        self.export_array(self.ARRAY)
      # nupix = QPixmap()
      # nupix.convertFromImage(self.image)
      # self.imageSig.emit(nupix)

#==============Changes the internal settings================#
# Should make the event queue feeding this baby LIFO
    def change_settings(self, kwargs):
        if not self.kwargs['WOLFRULE'] == kwargs['WOLFRULE']:
            line = np.random.randint(0, 2, (self.N))
            self.wolf = self.wolframgen(line)
        for i in kwargs:
            self.kwargs[i] = kwargs[i]
        self.addColors()

    def addColors(self):
        self.colorList = self.kwargs['COLORLIST']
        self.degree = self.kwargs['DEGREE']

#==============Wolfram-style Cellular Automata==============#
    def wolfram_scroll(self):
        n = int(self.N / self.kwargs['WOLFSCALE'])
        line = next(self.wolf)
        [self.image.setPixel((self.current + j) % self.N, i,\
            self.colorList[line[int(i / self.kwargs['WOLFSCALE']) % n] + 2])
                for i in range(self.D) for j in range(self.kwargs['WOLFSCALE'])]
        self.current += self.kwargs['WOLFSCALE']
        self.current %= self.N

    def wolframgen(self, line):
        n = int(self.D / self.kwargs['WOLFSCALE'])
      # n = self.shape
        rule = str(bin(self.kwargs['WOLFRULE']))[2:]
        while len(rule) < 8:
            rule = '0' + rule
        while True:
            nb = [int(str(line[(i - 1) % n]) + str(line[i]) + str(line[(i + 1) % n]),\
                    2) for i in range(n)]
            line = [int(rule[-i - 1]) for i in nb]
            yield line

    def wolfram_paint(self):
        N = int(self.D / self.kwargs['WOLFSCALE'])
        D = int(self.N / self.kwargs['WOLFSCALE'])
        im = QImage(D, N, QImage.Format_ARGB32)
      # line = np.random.randint(0, 2, (shape))
        line = np.zeros(D, int)
        line[int(D / 2)] = 1
        linegen = self.wolframgen(line)
        for idx, lin in enumerate(range(N)):
            line = next(linegen)
            for idy, pix in enumerate(line):
                im.setPixel(idx % N, idy, self.colorList[pix + 2])      #pix+2 means background colors
            if idx == N:
                break
        self.send_image(im)

#===============Array processing and Image export=============#
    def send_image(self, image):
        ims = image.scaled(QSize(self.N * self.scale, self.D * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)
        self.image = image.scaled(QSize(self.N, self.D))

    def process(self):
        #this sure is living
        pass

    def process_array(self, array):
        now = time.time()
        self.ARRAY = array
        self.update_change()
        self.export_list(self.CHANGE)
        if self.kwargs['WOLFWAVE']:
            self.wolfram_scroll()
        self.ARRAYOLD = self.ARRAY
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.canvasfpsSig.emit(np.mean(self.fpsRoll))
        self.finished.emit()
        self.send_image(self.image)

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

    # Updates image only where the pixels have changed. FASTER
    def export_list(self, L):
        im = self.image
        [im.setPixel(el[0], el[1], self.colorList[el[2]]) for el in L]

#====================The canvas=================#
# It isnt so exciting since I moved everything to the processor
class Canvas(QLabel):
    canvasfpsSig = pyqtSignal(float)

    def initialize(self, **kwargs):
        self.primaryColor = QColor(kwargs['COLORLIST'][0])
        self.colorList = []
        self.degree = 2
        self.N = kwargs['N']
        self.D = kwargs['D']
        self.scale = kwargs['SCALE']
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.N * self.scale, self.D * self.scale))
        self.pixmap().fill(self.primaryColor)

    def paint(self, image):
        self.setPixmap(image)
        self.repaint()
