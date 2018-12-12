from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


class IsingEngine():

    def initialize(self, nuArr=None, **kwargs):
        nuArr = nuArr if nuArr is not None else 1
        if nuArr:
            self.Array = self.arrayInit(kwargs['N'], kwargs['ALLUP'])
            self.costUpdate(kwargs['BETA'])

    def costUpdate(self, beta):
        self.cost = [0] * 3
        self.cost[1] = np.exp(-4 * beta)
        self.cost[2] = self.cost[1] ** 2

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
    def arrayUpdate(self, A=None, cost=None, **kwargs):
        A = A if A is not None else self.Array
        cost = cost if cost is not None else self.cost
        N = kwargs['N']
        updateList=[]
        for _ in range(kwargs['MONTEUPDATES']):
            a = int(ra.random() * kwargs['N'])
            b = int(ra.random() * kwargs['N'])
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
                updateList.append([a,b,A[a][b]])
        time.sleep(0.001 * (100 - kwargs['SPEED']))
        return A, updateList

    # Run in background (waay fast)
    def staticRun(self, canvas, **kwargs):
        self.Array, updateList  = self.arrayUpdate(**kwargs)
        canvas.exportList(updateList)

    # Run and update image continuously
    def dynamicRun(self, canvas, **kwargs):
        for _ in range(kwargs['IMAGEUPDATES']):
            self.Array, updateList = self.arrayUpdate(**kwargs)
            canvas.exportList(updateList)
            canvas.repaint()
