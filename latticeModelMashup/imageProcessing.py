from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import time
from screeninfo import get_monitors
from src.pureUp import *


class ImageCreator(QObject, pureHandler):
    imageSig = pyqtSignal(QPixmap)
    analyseSig = pyqtSignal(np.ndarray)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()
    canvasfpsSig = pyqtSignal(float)

    def __init__(self, st):
        QObject.__init__(self)

        self.error.emit('Image thread starting up!')
        self.colorList = st.canvas.colorlist
        self.wolfram_color_offset = 2
        self.resize_image(st.canvas.dim)

        self.scale = st.canvas.scale
        self.fpsRoll = np.zeros(9, float)
        self.st = st

        self.savecount = 0

        self.m = get_monitors()
        super().make_wolf(True, self.st.canvas.dim, self.st.wolfram.scale,
                          self.st.wolfram.rule)

    def reset_gifcount(self):
        self.savecount = 0

    # Resize/reset
    def resize_image(self, dim):
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.imageDim = dim

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
        self.resize_image(dim)
        self.wavecounter = pos
        super().make_wolf(True, dim, self.st.wolfram.scale, self.st.wolfram.rule)
        super().save_array(array)
        self.process_array(array)
        self.analyseSig.emit(array)

    def process(self, array, pos, dim):
        if not self.imageDim == dim:
            self.resize_image(dim)
        self.send_image(self.image)
        self.analyseSig.emit(array)
        self.wavecounter = pos
        self.process_array(array)

    def process_array(self, array):
        now = time.time()
        change = super().change(array)
        self.export_list(change)
        if self.st.general.wolfwave:
            self.wolfram_scroll()
        super().save_array(array)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.canvasfpsSig.emit(np.mean(self.fpsRoll))

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

    def wolfram_paint(self):
        color_offset = 2 #background colors
        wolfarray = super().wolfram_screen()
        self.resize_image(wolfarray.shape)
        self.export_array(wolfarray, color_offset)
        self.send_image(self.image)
        self.image = self.image.scaled(QSize(self.st.canvas.dim[0],
                                             self.st.canvas.dim[1]))

    # Updates image with values from entire array. SLOW
    def export_array(self, A, color_offset):
        im = self.image
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                num = int(A[i][j])
                color = self.colorList[num + color_offset]
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
