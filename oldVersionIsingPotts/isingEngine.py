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

    # This version is not legitimate, but it certainly is fast
    def arrayUpdateNOTWORKING(self):
        A = self.canvas.Array
        N = len(A)
        updates = self.kwargs['MONTEUPDATES']
        l = np.roll(A, -1, axis=0)
        r = np.roll(A, 1, axis=0)
        u = np.roll(A, 1 , axis=1)
        d = np.roll(A, -1, axis=1)
        NB = np.zeros(A.shape) + l + r + u + d
        # Select a bunch of positions
        msk = np.random.random(A.shape) > (updates / (N * N))
        # Split them into spin dead and alive
        mskUp = np.bitwise_and(A, msk)
        mskDown = np.bitwise_and(~A, msk)
        # Flip them quick if they gain energy
        flip0U = np.bitwise_and(mskUp, NB <= 2)
        flip0D = np.bitwise_and(mskDown, NB >= 2)
        # Find all the ones that weren't flipped quick
        remainU = np.bitwise_xor(mskUp, flip0U)
        remainD = np.bitwise_xor(mskDown, flip0D)
        # Create a random number for each remaining position
        oddsU = np.random.random(A.shape) * remainU
        oddsD = np.random.random(A.shape) * remainD
        # Further split the odds into a set for NB = 3,4
        odds3U = np.bitwise_and(remainU, NB == 3) * oddsU
        odds3D = np.bitwise_and(remainD, NB == 1) * oddsD
        odds4U = np.bitwise_and(remainU, NB == 4) * oddsU
        odds4D = np.bitwise_and(remainD, NB == 0) * oddsD
        # Finally, flip them if they satisfy the condition
        flip3U = np.bitwise_and(A, odds3U < self.cost[1])
        flip3U = np.bitwise_and(flip3U, odds3U > 0)
        flip3D = np.bitwise_and(A, odds3D < self.cost[1])
        flip3D = np.bitwise_and(flip3D, odds3D > 0)
        flip4U = np.bitwise_and(A, odds4U < self.cost[2])
        flip4U = np.bitwise_and(flip4U, odds4U > 0)
        flip4D = np.bitwise_and(A, odds4D < self.cost[2])
        flip4D = np.bitwise_and(flip4D, odds4D > 0)
        flip = np.zeros(A.shape, bool) + flip0U + flip0D + flip3U + flip3D + flip4U + flip4D
        B = np.bitwise_xor(A, flip)
        self.array = B
        time.sleep(0.001 * (100 - self.speed))
        posList = np.argwhere(B != A)
        updateList = [[el[0], el[1], A[el[0], el[1]]] for el in posList]
        return B, updateList

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
