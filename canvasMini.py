#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from latticeCanvas import Canvas

import random as ra
import re
import math
import numpy as np
import time

class Handler(QObject):
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []   # A previous copy, updated periodically
    CHANGE = []     # The difference between the two ((Nx3), with state)
    LIVING = []     # Currently living cells, updated periodically(?)

    def __init__(self, array):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        Handler.ARRAY = np.random.random([500,500]) > 0.3
        Handler.ARRAYOLD = np.zeros(Handler.ARRAY.shape, bool)
        Handler.LIVING = np.zeros([0, 2], bool)
        Handler.CHANGE = np.zeros([0, 3], bool)

    def process(self):
#       self.update_living()
        self.update_change()
        Handler.ARRAYOLD = np.copy(Handler.ARRAY)

    def update_living(self):
        Handler.LIVING = np.argwhere(Handler.ARRAY)

    def update_change(self):
        common = np.bitwise_and(Handler.ARRAY, Handler.ARRAYOLD)
        onlyOld = np.bitwise_xor(common, Handler.ARRAYOLD)
        onlyNew = np.bitwise_xor(common, Handler.ARRAY)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        Handler.CHANGE = np.concatenate((b, d))

    def noise_process(self, threshold):
        Handler.ARRAY = np.zeros(Handler.ARRAY.shape, bool)
        Handler.ARRAYOLD = np.copy(Handler.ARRAY)
        A = np.random.random(Handler.ARRAY.shape) > threshold
        B = np.bitwise_xor(Handler.ARRAY, A)
        Handler.ARRAY = B

class Canvas(QLabel, Handler):

    def __init__(self):
        Handler.__init__(self, [0,1])
        Handler.process(self)

    def initialize(self, **kwargs):
        self.primaryColor = QColor(kwargs['BACKCOLOR1'])
        self.secondaryColor = QColor(kwargs['BACKCOLOR2'])
        self.colorList = []
        self.colorList.append(self.primaryColor.rgba())
        self.colorList.append(self.secondaryColor.rgba())
        self.degree = 2
        self.n = kwargs['N']
        self.scale = kwargs['SCALE']
        self.reset()
       #self.export_array(Handler.ARRAY)
       #self.export_list(Handler.CHANGE, 0)
        self.wolfram()

    def wolfram(self):
        import pdb; pdb.set_trace()  # XXX BREAKPOINT
        line = np.random.randint(0, 2, (self.n,1))
        rule = str(bin(30))[2:]
        while len(rule) < 8:
            rule = '0' + rule
        nb = [sum(line[(i-1) % self.n], line[i], line[(i + 1) % self.n])\
              for i in range(self.n)]
        out = [int(rule[i]) for i in nb]

    def reset(self):
        self.setPixmap(QPixmap(self.n * self.scale, self.n * self.scale))

        self.pixmap().fill(self.primaryColor)

    def addColors(self, colorList, degree):
        self.colorList = colorList
        self.degree = degree

    # Updates image with values from entire array. SLOW
    def export_array(self, A):
        im = QImage(self.n, self.n, QImage.Format_ARGB32)
        now = time.time()
        for i in range(self.n):
            for j in range(self.n):
                num = int(A[i][j])
                color = self.colorList[num]
                im.setPixel(i, j, color)
        print(time.time() - now)
        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.setPixmap(nupix)
        self.repaint()

    # Updates image only where the pixels have changed. FASTER
    def export_list(self, L, living):
        now = time.time()
        im = self.pixmap().toImage().scaled((QSize(self.n, self.n)))
        if living:
            for el in L:
                im.setPixel(el[0], el[1], self.colorList[1])
        else:
            for el in L:
                im.setPixel(el[0], el[1], self.colorList[el[2]])

        print(time.time() - now)
        ims = im.scaled(QSize(self.n * self.scale, self.n * self.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.setPixmap(nupix)
        self.repaint()

class MainWindow(QWidget):

    def __init__(self, **DEFAULTS):
        super().__init__()
        self.initGUI(**DEFAULTS)

    def initGUI(self, **DEFAULTS):
        self.canvas = Canvas()
        self.canvas.initialize(**DEFAULTS)

        hb = QHBoxLayout()
        hb.addWidget(self.canvas)

        self.setLayout(hb)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')


    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()

def initVars():
    colHex1 = int(ra.random() * int('0xffffffff', 16))
    colHex2 = int(ra.random() * int('0xffffffff', 16))
    colHex3 = int(ra.random() * int('0xffffffff', 16))
    colHex4 = int(ra.random() * int('0xffffffff', 16))
    colHex5 = int('0xffffffff', 16)
    colHex6 = int('0xffffffff', 16)
    DEF = {
        'BACKCOLOR1':   QColor.fromRgba(colHex1).rgba(),    # These are just random rn
        'BACKCOLOR2':   QColor.fromRgba(colHex2).rgba(),
        'UPDATECOLOR1': QColor.fromRgba(colHex3).rgba(),    # To make fancy transitions,
        'UPDATECOLOR2': QColor.fromRgba(colHex4).rgba(),    # change these.
        'MOUSECOLOR1':  QColor.fromRgba(colHex5).rgba(),    # Not used rn. But soon?
        'MOUSECOLOR2':  QColor.fromRgba(colHex6).rgba(),
        'SATURATION':   80,     # This leaves changes on the image shortly
        'N':            500,    # Array dimensions
        'SCALE':        2,      # Image dim = N*SCALE x N*SCALE
        'BETA':         1 / 8,  # Critical temp for Ising
        'SPEED':        100,    # Throttle %
        'DEGREE':       4,      # Degree of the Potts model
        'IMAGEUPDATES': 600,    # Max number of frames to run
        'RUNFRAMES':    0,      # Frames in current run
        'MONTEUPDATES': 333,    # MonteCarlo updates per frame
        'LONGNUM':      100000, # MonteCarlo update to equilibrium
        'THRESHOLD':     0.1,   # Threshold for clear/noise (sigmoid function)
        'NEWARR':       1,      # New array upon engine creation?
        'STOCHASTIC':   True,   # Noise on?
        'CONWAY':       True,   # Conway on?
        'EQUILIBRATE':  False,  # Equilibrate array?
        'RUN':          False,   # Run the simulation
        'CLEAR':        False,  # Clear array?
                                # Update rules for conway
        'RULES':        [[3,6,2,2],\
                         [3,6,3,3],\
                         [3,4,3,3],\
                         [3,4,2,2]],
        'INTERRUPT':    False,  # Used to interrupt a run
    }
    return DEF

if __name__ == '__main__':

    app = QApplication([])
    DEFAULTS = initVars()
    w = MainWindow(**DEFAULTS)
    app.exec()
