from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


class IsingEngine():

    def initialize(beta, nuArr=1, allUp=0):
        if nuArr:
            self.Array = self.arrayInit(N, allUp)
        self.imageUpdates = 100
        self.monteUpdate = 1000

    # Initialises the data array (invisible to user)
    def arrayInit(self, N, allUp):
        ARR = np.ones((N, N), int)
        if allUp:
            return ARR
        for i in range(0, N):
            for j in range(0, N):
                if ra.random() > 0.5:
                    ARR[i, j] = -1
        return ARR

    # Performs a monte carlo update. Could be exported to C, but this isn't
    # where the cycles go anyway
    def arrayUpdate(self, A, nSteps, cost):
        updateList=[]
        for _ in range(nSteps):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
                updateList.append([a,b,A[a][b]])
        time.sleep(0.001 * (100 - self.speed))
        return A, updateList

    # Run in background (waay fast)
    def staticRun(self, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        self.spinArray, updateList  = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
        self.exportList(updateList, self.primaryColor.rgba(), self.secondaryColor.rgba())

    # Run and update image continuously
    def dynamicRun(self, imUp=None, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        imUp = imUp if imUp is not None else self.imageUpdates
        for _ in range(imUp):
            self.spinArray, updateList = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
            self.exportList(updateList, self.primaryColor.rgba(), self.secondaryColor.rgba())
            self.repaint()
