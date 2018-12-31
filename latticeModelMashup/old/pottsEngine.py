from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


class PottsEngine():

    def initialize(self, canvas, frameLabel, nuArr=None, **kwargs):
        nuArr = nuArr if nuArr is not None else 1
        self.updateKwargs(**kwargs)
        if nuArr:
            self.Array = self.arrayInit(kwargs['N'], kwargs['ALLUP'])
            self.costUpdate(kwargs['BETA'])
        self.canvas = canvas
        self.frameLabel = frameLabel

    def updateKwargs(self, **kwargs):
        self.degree = kwargs['DEGREE']
        self.kwargs = kwargs

    def costUpdate(self, beta):
        self.cost = [0] * (self.degree + 1)
        self.cost[1] = np.exp(-1 * beta)
        for i in range(2, self.degree + 1):
            self.cost[i] = self.cost[1] ** i

    # Initialises the data array (invisible to user)
    def arrayInit(self, N, allUp):
        ARR = np.ones((N, N), int)
        if allUp:
            return ARR
        for i in range(0, N):
            for j in range(0, N):
                    ARR[i, j] = int(ra.random() * self.degree)
        return ARR

    # MonteCarlo Update
    def arrayUpdate(self, A=None, cost=None, **kwargs):
        A = A if A is not None else self.Array
        cost = cost if cost is not None else self.cost
        N = kwargs['N']
        updateList=[]
        for _ in range(kwargs['MONTEUPDATES']):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = int(A[a][b] == A[(a + 1) % N][b]) \
                + int(A[a][b] == A[(a - 1) % N][b]) \
                + int(A[a][b] == A[a][(b + 1) % N]) \
                + int(A[a][b] == A[a][(b - 1) % N])
            temp = int(ra.random() * self.degree)
            nb2 = int(temp == A[(a + 1) % N][b]) \
                + int(temp == A[(a - 1) % N][b]) \
                + int(temp == A[a][(b + 1) % N]) \
                + int(temp == A[a][(b - 1) % N])
            tempra = ra.random()
            if (nb - nb2) <= 0 or tempra < cost[(nb - nb2)]:
                A[a][b] = temp
                updateList.append([a,b,temp])
        time.sleep(0.001 * (100 - kwargs['SPEED']))
        return A, updateList


    def equilibrate(self):
        mont = self.kwargs['MONTEUPDATES']
        self.kwargs['MONTEUPDATES'] = self.kwargs['EQUILIBRATE']
        self.staticRun()
        self.kwargs['MONTEUPDATES'] = mont

    # Run in background (waay fast)
    def staticRun(self):
        self.Array, updateList  = self.arrayUpdate(**self.kwargs)
        self.canvas.exportList(updateList)

    # Run and update image continuously
    def dynamicRun(self):
        frameNum = 0
        for _ in range(self.kwargs['IMAGEUPDATES']):
            frameNum += 1
            self.Array, updateList = self.arrayUpdate(**self.kwargs)
            self.canvas.exportList(updateList)
            self.canvas.repaint()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')
