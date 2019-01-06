from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

class isingUpdateThread(QThread):
# This guy takes an array, performs an specific number of updates with a
# specified cost function and then returns the array.
    isingArray = pyqtSignal()
    def __init__(self, beta):
        QThread.__init__(self)
        self.cost = []
        self._update_cost(beta)
        self.array = []

    def __del__(self):
        self.wait()

    def _update_cost(self, beta):
        self.cost = [0] * 3
        self.cost[1] = np.exp(-4 * beta)
        self.cost[2] = self.cost[1] ** 2

    def _update_array(self, updates, array):
        A = array
        cost = self.cost
        N = len(A)
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(N)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b], \
                  A[a][b] == A[(a - 1) % N][b], \
                  A[a][b] == A[a][(b + 1) % N], \
                  A[a][b] == A[a][(b - 1) % N], \
                  -2])
            if nb <= 0 or np.random.random() < cost[nb]:
                A[a][b] = not A[a][b]
        self.array = A
        return A

    def run(self, updates, array=None, beta=None):
        array = array if array is not None else self.array
        if beta:
            self._update_cost(beta)
        A = self._update_array(array, updates)
        self.isingArray.emit(A)
        self.array = array

# self.connect(self.IsingUpdateThreadInstance,
# SIGNAL("isingArray(PyQt_PyObject)"), self.array_handler


class IsingEngine():

    def initialize(self, canvas, frameLabel,  **kwargs):
        self.updateKwargs(**kwargs)
        self.canvas = canvas
        if kwargs['NEWARR']:
            self.canvas.Array = self.arrayInit(kwargs['N'], kwargs['ALLUP'])
        self.frameLabel = frameLabel

    def updateKwargs(self, **kwargs):
        self.kwargs = kwargs
        self.beta = kwargs['BETA']
        self.n = kwargs['N']
        self.speed = kwargs['SPEED']
        self.imageUpdates = kwargs['IMAGEUPDATES']
        self.monteUpdates = kwargs['MONTEUPDATES']

    # Initialises the data array (invisible to user)
    def arrayInit(self, N, THRESHOLD):
        return np.random.random([N,N]) > THRESHOLD

    def equilibrate(self):
        mont = self.kwargs['MONTEUPDATES']
        self.kwargs['MONTEUPDATES'] = self.kwargs['EQUILIBRATE']
        self.staticRun()
        self.kwargs['MONTEUPDATES'] = mont

    # Run in background (waay fast)
    def staticRun(self):
        self.canvas.Array, updateList  = self.arrayUpdate()
        self.canvas.exportList(updateList)

    @pyqtSlot()
    def array_handler(self, array):
        type(self.canvas.Array)
        type(array)
        posList = np.argwhere(array != self.canvas.Array)
        updateList = [[el[0], el[1], A[el[0], el[1]]] for el in posList]
        self.canvas.exportList(updateList)
        self.canvas.repaint()

    # Run and update image continuously
    def dynamicRun(self):
        updateThread = isingUpdateThread(self.beta)
        updateThread.isingArray.connect(self.array_handler)
        self.updateThread.start(self.imageUpdates, self.canvas.Array)
        frameNum = 0
        for _ in range(self.imageUpdates - 1):
            frameNum += 1
            updateThread.start()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')
