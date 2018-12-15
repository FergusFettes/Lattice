from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


class IsingEngine():

    def initialize(self, canvas, frameLabel,  **kwargs):
        self.updateKwargs(**kwargs)
        self.canvas = canvas
        if kwargs['NEWARR']:
            self.canvas.Array = self.arrayInit(kwargs['N'], kwargs['ALLUP'])
        self.costUpdate(kwargs['BETA'])
        self.frameLabel = frameLabel

    def updateKwargs(self, **kwargs):
        self.kwargs = kwargs
        self.n = kwargs['N']
        self.speed = kwargs['SPEED']

    def costUpdate(self, beta):
        self.cost = [0] * 3
        self.cost[1] = np.exp(-4 * beta)
        self.cost[2] = self.cost[1] ** 2

    # Initialises the data array (invisible to user)
    def arrayInit(self, N, THRESHOLD):
        return np.random.random([N,N]) > THRESHOLD

    # Performs a monte carlo update. Could be exported to C, but this isn't
    # where the cycles go anyway
    def arrayUpdate(self):
        A = self.canvas.Array
        C = np.copy(A)
        cost = self.cost
        N = self.n
        for _ in range(self.kwargs['MONTEUPDATES']):
            a = np.random.randint(self.n)
            b = np.random.randint(self.n)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b], \
                  A[a][b] == A[(a - 1) % N][b], \
                  A[a][b] == A[a][(b + 1) % N], \
                  A[a][b] == A[a][(b - 1) % N], \
                  -2])
            if nb <= 0 or np.random.random() < cost[nb]:
                A[a][b] = not A[a][b]
        time.sleep(0.001 * (100 - self.speed))
        posList = np.argwhere(C != A)
        updateList = [[el[0], el[1], A[el[0], el[1]]] for el in posList]
        return A, updateList

    def equilibrate(self):
        mont = self.kwargs['MONTEUPDATES']
        self.kwargs['MONTEUPDATES'] = self.kwargs['EQUILIBRATE']
        self.staticRun()
        self.kwargs['MONTEUPDATES'] = mont

    # Run in background (waay fast)
    def staticRun(self):
        self.canvas.Array, updateList  = self.arrayUpdate()
        self.canvas.exportList(updateList)

    # Run and update image continuously
    def dynamicRun(self):
        frameNum = 0
        for _ in range(self.kwargs['IMAGEUPDATES']):
            frameNum += 1
            self.canvas.Array, updateList = self.arrayUpdate()
            self.canvas.exportList(updateList)
            self.canvas.repaint()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')
