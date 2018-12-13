from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


class IsingEngine():

    def initialize(self, canvas, frameLabel,  **kwargs):
        self.canvas = canvas
        self.n = kwargs['N']
        if kwargs['NEWARR']:
            self.canvas.Array = self.arrayInit(kwargs['N'], kwargs['ALLUP'])
        self.costUpdate(kwargs['BETA'])
        self.kwargs = kwargs
        self.frameLabel = frameLabel

    def updateKwargs(self, **kwargs):
        self.kwargs = kwargs

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
        return self.flattenArray(ARR)

    # Performs a monte carlo update. Could be exported to C, but this isn't
    # where the cycles go anyway
    def arrayUpdate(self):
        A = self.canvas.Array
        cost = self.cost
        A = self.fattenArray(A)
        N = self.kwargs['N']
        updateList=[]
        for _ in range(self.kwargs['MONTEUPDATES']):
            a = int(ra.random() * self.kwargs['N'])
            b = int(ra.random() * self.kwargs['N'])
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
                updateList.append([a,b,A[a][b]])
        time.sleep(0.001 * (100 - self.kwargs['SPEED']))
        return self.flattenArray(A), self.flattenForExport(updateList)

    def equilibrate(self):
        mont = self.kwargs['MONTEUPDATES']
        self.kwargs['MONTEUPDATES'] = self.kwargs['EQUILIBRATE']
        self.staticRun()
        self.kwargs['MONTEUPDATES'] = mont

    # Run in background (waay fast)
    def staticRun(self):
        self.canvas.Array, updateList  = self.arrayUpdate(**self.kwargs)
        self.canvas.exportList(updateList)

    # Run and update image continuously
    def dynamicRun(self):
        frameNum = 0
        for _ in range(self.kwargs['IMAGEUPDATES']):
            frameNum += 1
            self.canvas.Array, updateList = self.arrayUpdate(**self.kwargs)
            self.canvas.exportList(updateList)
            self.canvas.repaint()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')

    # Flattens the list so it works with the normal color scheme
    def flattenForExport(self, listIn):
        for idx,_ in enumerate(listIn):
            listIn[idx][2] = int((listIn[idx][2] + 1) / 2)
        return listIn

    def flattenArray(self, A):
        for i in range(self.n):
            for j in range(self.n):
                A[i][j] = int((A[i][j] + 1) / 2)
        return A

    def fattenArray(self, A):
        for i in range(self.n):
            for j in range(self.n):
                A[i][j] = int((2 * A[i][j]) - 1)
        return A
