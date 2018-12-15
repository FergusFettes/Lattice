from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

from isingEngine import IsingEngine

# TODO: build an awesome function that stochastically fluctuates the
# background, killing cells when the alive list is too long and bringing them
# to life when it is too small
class ConwayEngine():

    def initialize(self, canvas, frameLabel, nuArr=None, **kwargs):
        nuArr = nuArr if nuArr is not None else 0
        self.updateKwargs(**kwargs)
        self.canvas = canvas
        self.aliveList = []
        self.rules = []
        self.frameLabel = frameLabel
        self.Ising=IsingEngine()
        self.Ising.initialize(canvas, frameLabel, **kwargs)

    def reset(self):
        self.canvas.Array = self.arrayInit(self.kwargs['N'], 1)
        self.canvas.reset()
        self.aliveList = []
        self.findLiving(self.canvas.Array)
        self.canvas.exportList(self.addColorRow(self.aliveList))

    def findLiving(self, A):
        for i in range(self.n):
            for j in range(self.n):
                if A[i][j]:
                    self.aliveList.append([i, j])

    def updateKwargs(self, **kwargs):
        self.coverage = kwargs['COVERAGE']
        self.n = kwargs['N']
        self.stochastic = kwargs['STOCHASTIC']
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
    def arrayUpdate(self, rule):
      # rule = 4
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
        rule1 = np.bitwise_and(A, NB > self.rules[rule][0][0])
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB < self.rules[rule][1][0])
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB == self.rules[rule][2][0])
        #should just be the live cells
        C = rule2 + rule4
        #np.argwhere should be a list of all the cells that have chang
        time.sleep(0.001 * (100 - self.kwargs['SPEED']))
        return C, np.argwhere(C != A)

    # Is this obscene? All I am trying to do is unpack my regexes. No doubt
    # there is a better (more readable / faster?) way of doing this.
    # self.rules should be an array of all the values for the rules.
    def processRules(self, rulesMatch):
        rul = [i.group(1, 2, 3) for i in rulesMatch]
        self.rules = [[list(map(int, j.split(','))) for j in i] for i in rul]

    def addColorRow(self, L):
        A = self.canvas.Array
        return[[i[0], i[1], A[i[0], i[1]]] for i in L]

    def equilibrate(self):
        mont = self.kwargs['MONTEUPDATES']
        self.kwargs['MONTEUPDATES'] = self.kwargs['EQUILIBRATE']
        self.staticRun()
        self.kwargs['MONTEUPDATES'] = mont

    # Run in background (waay fast)
    def staticRun(self):
        self.canvas.Array, updateList  = self.arrayUpdate(0)
        if updateList:
            self.canvas.exportList(self.addColorRow(updateList))
        if self.stochastic:
            self.canvas.Array, updateList = self.Ising.arrayUpdate()
            self.canvas.exportList(updateList)

    # Run and update image continuously
    def dynamicRun(self):
        frameNum = 0
        for _ in range(self.kwargs['IMAGEUPDATES']):
            frameNum += 1
            self.canvas.Array, updateList = self.arrayUpdate(frameNum % len(self.rules))
            if updateList is None:
                print('No change')
                break
            self.canvas.exportList(self.addColorRow(updateList))
            if self.stochastic:
                self.canvas.Array, updateList = self.Ising.arrayUpdate()
                self.canvas.exportList(updateList)
            self.canvas.repaint()
            self.frameLabel.setText(str(frameNum) + ' / ')
        self.frameLabel.setText('0000/')
