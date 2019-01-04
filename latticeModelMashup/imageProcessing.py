from PyQt5.QtGui import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import time
from screeninfo import get_monitors


class ImageCreator(QObject):
    imageSig = pyqtSignal(QPixmap)
    nextarraySig = pyqtSignal()
    breakSig = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()
    canvasfpsSig = pyqtSignal(float)

    def __init__(self, st):
        QObject.__init__(self)

        self.error.emit('Image thread starting up!')
        self.colorList = st.canvas.colorlist
        self.wolfram_color_offset = 2

        self.scale = st.canvas.scale
        self.fpsRoll = np.zeros(9, float)
        self.st = st

        self.LIVING = np.zeros([0, 2], bool)
        self.CHANGE = np.zeros([0, 3], bool)
        self.resize_array(st.canvas.dim)

        line = np.random.randint(0, 2, (st.canvas.dim[1]))
        self.wolf = self.wolframgen(line)
        self.wavecounter = 0
        self.savecount = 0

        self.m = get_monitors()

    def reset_gifcount(self):
        self.savecount = 0

    # Resize/reset
    def resize_array(self, dim):
        self.ARRAY = np.zeros(dim, bool)
        self.ARRAYOLD = np.zeros(dim, bool)
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.export_array(self.ARRAY)

#==============Changes the internal settings================#
# Should make the event queue feeding this baby LIFO
    def change_settings(self, st):
        self.st = st
        self.colorList = st.canvas.colorlist
        self.scale = st.canvas.scale
        line = np.random.randint(0, 2, (st.canvas.dim[1]))
        self.wolf = self.wolframgen(line)

#==============Wolfram-style Cellular Automata==============#
    def wolfram_scroll(self):
        hi = int(self.st.canvas.dim[1] / self.st.wolfram.scale)
        line = next(self.wolf)
        [
            self.image.setPixel(
                (self.wavecounter + j) % self.st.canvas.dim[0],
                i,
                self.colorList[
                    line[int(i / self.st.wolfram.scale) % hi]\
                    + self.wolfram_color_offset
                ]
            )
            for i in range(self.st.canvas.dim[1])
            for j in range(self.st.wolfram.scale)
        ]

    def wolframgen(self, line):
        hi = int(self.st.canvas.dim[1] / self.st.wolfram.scale)
        rule = str(bin(self.st.wolfram.rule))[2:]   #gets binary repr. of update rule
        while len(rule) < 8:
            rule = '0' + rule
        while True:
            nb = [
                    int(
                        str(line[(i - 1) % hi])
                        + str(line[i])
                        + str(line[(i + 1) % hi]),
                        2)
                    for i in range(hi)
                ]
            line = [int(rule[-i - 1]) for i in nb]
            yield line

    def wolfram_paint(self):
        hi = int(self.st.canvas.dim[1] / self.st.wolfram.scale)
        wid = int(self.st.canvas.dim[0] / self.st.wolfram.scale)
        im = QImage(wid, hi, QImage.Format_ARGB32)
      # line = np.random.randint(0, 2, (shape))
        line = np.zeros(hi, int)
        line[int(hi / 2)] = 1
        linegen = self.wolframgen(line)
        for idx, lin in enumerate(range(wid)):
            line = next(linegen)
            for idy, pix in enumerate(line):
                im.setPixel(idx % wid, idy, self.colorList[pix + self.wolfram_color_offset])
            if idx == wid:
                break
        self.send_image(im)
        self.image = im.scaled(QSize(wid, hi))

#===============Array processing and Image export=============#
    def send_image(self, image):
        if self.st.canvas.fullscreen:
            ims = image.scaled(QSize(self.m[0].width, self.m[0].height))
        else:
            ims = image.scaled(QSize(self.st.canvas.dim[0] * self.st.canvas.scale,
                                     self.st.canvas.dim[1] * self.st.canvas.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)
        if self.st.canvas.record:
            ims.save('images/temp{:>04d}.png'.format(self.savecount), 'PNG')
            self.savecount += 1

    def process_single(self, array, pos):
        self.wavecounter = pos
        self.process_array(array)
        self.send_image(self.image)

    def processer_start(self, array, pos, dim):
        if not self.ARRAY.shape == dim:
            self.resize_array(dim)
        self.wavecounter = pos
        self.process_array(array)
        self.nextarraySig.emit()


    def process(self, array, pos):
        self.wavecounter = pos
        self.send_image(self.image)
        self.process_array(array)
        self.nextarraySig.emit()

    def process_array(self, array):
        now = time.time()
        self.ARRAY = array
        self.update_change()
        self.export_list(self.CHANGE)
        if self.st.general.wolfwave:
            self.wolfram_scroll()
        self.ARRAYOLD = np.copy(self.ARRAY)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.canvasfpsSig.emit(np.mean(self.fpsRoll))

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
#       if not self.CHANGE.size:
#           self.breakSig.emit()

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
        [self.image.setPixel(el[0], el[1], self.colorList[el[2]]) for el in L]

#====================The canvas=================#
# It isnt so exciting since I moved everything to the processor
class Canvas(QLabel):
    canvasfpsSig = pyqtSignal(float)

    def initialize(self, st):
        self.primaryColor = QColor(st.canvas.colorlist[0])
        self.colorList = []
        self.st = st
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.st.canvas.dim[0] * self.st.canvas.scale,
                                self.st.canvas.dim[1] * self.st.canvas.scale))
        self.pixmap().fill(self.primaryColor)

    def paint(self, image):
        self.setPixmap(image)
        self.repaint()
