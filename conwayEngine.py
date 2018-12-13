from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time


# TODO: build an awesome function that stochastically fluctuates the
# background, killing cells when the alive list is too long and bringing them
# to life when it is too small
class ConwayEngine():

    def initialize(self, canvas, frameLabel, nuArr=None, **kwargs):
        nuArr = nuArr if nuArr is not None else 0
        self.updateKwargs(**kwargs)
        self.canvas = canvas
        self.aliveList = []
        self.n = kwargs['N']
        if nuArr:
            self.canvas.Array = self.arrayInit(kwargs['N'], 1)
            self.canvas.reset()
            self.canvas.exportList(self.addColorRow(self.aliveList))
        else:
            self.findLiving(self.canvas.Array)
        self.frameLabel = frameLabel

    def findLiving(self, A):
        for i in range(self.n):
            for j in range(self.n):
                if A[i][j]:
                    self.aliveList.append([i, j])

    def updateKwargs(self, **kwargs):
        self.coverage = kwargs['COVERAGE']
        self.kwargs = kwargs
        self.kwargs['MONTEUPDATES'] = 20

    # Initialises the data array (invisible to user)
    def arrayInit(self, N, allUp):
        ARR = np.zeros((N, N), int)
        for i in range(0, N):
            for j in range(0, N):
                alive = int(ra.random() < self.coverage / 100)
                if alive:
                    self.aliveList.append([i, j])
                    ARR[i, j] = alive
        return ARR

    # Diarmuid Engine
    def arrayUpdate(self):
        A = self.canvas.Array
        l = np.roll(A, -1, axis=0)
        r = np.roll(A, 1, axis=0)
        u = np.roll(A, 1 , axis=1)
        d = np.roll(A, -1, axis=1)
        ul = np.roll(l, 1, axis=1)
        dl = np.roll(l, -1, axis=1)
        ur = np.roll(r, 1, axis=1)
        dr = np.roll(r, -1, axis=1)
        NB = np.zeros(A.shape) + l + r + u + d + ul + dl + ur + dr
        #cells still alive after rule 1
        rule1 = np.bitwise_and(A, NB > 1)
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB < 4)
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB == 3)
        #should just be the live cells
        C = rule2 + rule4
        #np.argwhere should be a list of all the cells that have chang
        return C, np.argwhere(C != A)

    # MonteCarlo Update
    def arrayUpdateOld(self, A=None, **kwargs):
        A = A if A is not None else self.canvas.Array
        if not self.aliveList:
            print('No life!')
            return A, self.aliveList
        L = self.fattenAliveList(self.aliveList)
        N = self.n
        for _ in range(1):
            deaths = []
            births = []
            for el in L:
                alive = A[el[0],el[1]]
                nb = A[(el[0] + 1) % N, el[1]]          \
                   + A[(el[0] + 1) % N, (el[1] + 1) % N]\
                   + A[(el[0] + 1) % N, (el[1] - 1) % N]\
                   + A[(el[0] - 1) % N, el[1]]          \
                   + A[(el[0] - 1) % N, (el[1] + 1) % N]\
                   + A[(el[0] - 1) % N, (el[1] - 1) % N]\
                   + A[el[0], (el[1] + 1) % N]          \
                   + A[el[0], (el[1] - 1) % N]
                if nb < 2 and alive:
                    deaths.append(el)
                elif nb == 3 and not alive:
                    births.append(el)
                elif nb == 4 and alive:
                    deaths.append(el)
            for b in births:
                A[b[0],b[1]] = 1
                self.aliveList.append(b)
            for d in deaths:
                A[d[0],d[1]] = 0
                self.aliveList.pop(self.aliveList.index(d))
        bir = [el + [1] for el in births]
        det = [el + [0] for el in deaths]
        L = bir + det
        time.sleep(0.001 * (100 - kwargs['SPEED']))
        return A, L

    # Gets all the neighboring points, then removes repeates
    def fattenAliveList(self, L):
        N = self.n
        fatL = np.zeros((len(L * 5), 2), int)
        for idx,el in enumerate(L):
            fatL[5 * idx] = [el[0], el[1]]
            fatL[(5 * idx) + 1] = [(el[0] + 1) % N, el[1]]
            fatL[(5 * idx) + 2] = [(el[0] - 1) % N, el[1]]
            fatL[(5 * idx) + 3] = [el[0], (el[1] + 1) % N]
            fatL[(5 * idx) + 4] = [el[0], (el[1] - 1) % N]
        return np.unique(fatL, axis=0).tolist()

    # Have to add a row of ones. I guess there is a better way of doing this,
    # lets see how slow it runs.
    def addColorRowOld(self, L):
        if np.shape(L)[1] == 3:
              return L
        return [el + [1] for el in L]

    def addColorRow(self, L):
        A = self.canvas.Array
        return[[i[0], i[1], A[i[0], i[1]]] for i in L]

    # Run in background (waay fast)
    def staticRun(self):
        self.canvas.Array, updateList  = self.arrayUpdate()
        if updateList:
            self.canvas.exportList(self.addColorRow(updateList))

    # Run and update image continuously
    def dynamicRun(self):
        frameNum = 0
        for _ in range(self.kwargs['IMAGEUPDATES']):
            frameNum += 1
            self.canvas.Array, updateList = self.arrayUpdate()
            if updateList is None:
                print('No change')
                break
            self.canvas.exportList(self.addColorRow(updateList))
            self.canvas.repaint()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')
