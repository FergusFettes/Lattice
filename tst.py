from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time
import sys
import queue as queue

class stochasticUpdater(QObject):
# Simple worker just creates noise
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, threshold = 0.95):
        QObject.__init__(self)
        self.change_threshold(threshold)
        self.change_array(array)

    def change_threshold(self, threshold):
        self.threshold = threshold

    def change_array(self, array):
        self.array = array

    def process(self):
        self.array = self.update_array()
        self.arraySig.emit(self.array)
        self.finished.emit()

    def update_array(self):
        array = self.array
        n = np.shape(array)
        A = np.random.random(n) > self.threshold
        B = np.bitwise_xor(array, A)
        return B

class isingUpdater(QObject):
# Simple worker just creates noise
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, beta):
        QObject.__init__(self)
        self.change_array(array)
        self.change_cost(beta)

    def change_cost(self, beta):
        self.cost = np.zeros(3, float)
        self.cost[1] = np.exp(-4 * beta)
        self.cost[2] = self.cost[1] ** 2

    def change_array(self, array):
        self.array = array

    def process(self, updates):
        self.array = self.update_array(updates)
        self.arraySig.emit(self.array)
        self.finished.emit()

    def update_array(self, updates):
        A = self.array
        N = len(A)
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(N)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b], \
                  A[a][b] == A[(a - 1) % N][b], \
                  A[a][b] == A[a][(b + 1) % N], \
                  A[a][b] == A[a][(b - 1) % N], \
                  -2])
            if nb <= 0 or np.random.random() < self.cost[nb]:
                A[a][b] = not A[a][b]
        self.array = A # This does nothing right? Because it a shallow copy..
        return A

class conwayUpdater(QObject):
# Simple worker just creates noise
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, rules):
        QObject.__init__(self)
        self.change_array(array)
        self.change_rules(rules)
        self.counter = 0

    def change_rules(self, rules):
        self.rules = rules
        self.ruleNum = len(rules)

    def change_array(self, array):
        self.array = array

    def process(self):
        self.array = self.update_array()
        self.arraySig.emit(self.array)
        self.finished.emit()

    def update_array(self):
        rule = self.counter
        self.counter+=1
        self.counter%=self.ruleNum
        A = self.array
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
        return rule2 + rule4

class arrayHandler():
# Controlls all the jobs for the array updaters

    def __init__(self, N):
        self.array = []
        self.reset_array(N)

    def reset_array(self, N):
        self.update_array(np.zeros([N, N], bool))

    def randomize_array(self, N, DEGREE=2):
        self.array = np.random.ranint([N, N], DEGREE)

    def update_array(self, array):
        self.array = array

    def error_string(self, error='Unlabelled Error! Oh no!'):
        print(error)

    def noise_init(self, threshold=0.95):
        self.noiseThread = QThread()
        self.noiser = stochasticUpdater(self.array)
        self.noiser.moveToThread(self.noiseThread)
        self.noiseThread.started.connect(self.noiser.process)
        self.noiser.error.connect(self.error_string)
        self.noiser.finished.connect(self.noiseThread.quit)
        self.noiseThread.finished.connect(self.noiseThread.deleteLater)
        self.noiser.arraySig.connect(self.update_array)
        self.noiseThread.start()

    def ising_init(self, beta):
        self.isingThread = QThread()
        self.isingUp = isingUpdater(self.array, beta)
        self.isingUp.moveToThread(self.isingThread)
        self.isingThread.started.connect(self.isingUp.process)
        self.isingUp.error.connect(self.error_string)
        self.isingUp.finished.connect(self.isingThread.quit)
        self.isingThread.finished.connect(self.isingThread.deleteLater)
        self.isingUp.arraySig.connect(self.update_array)
        self.isingThread.start()

    def conway_init(self, rules):
        self.conwayThread = QThread()
        self.conwayUp = conwayUpdater(self.array, rules)
        self.conwayUp.moveToThread(self.conwayThread)
        self.conwayThread.started.connect(self.conwayUp.process)
        self.conwayUp.error.connect(self.error_string)
        self.conwayUp.finished.connect(self.conwayThread.quit)
        self.conwayThread.finished.connect(self.conwayThread.deleteLater)
        self.conwayUp.arraySig.connect(self.update_array)
        self.conwayThread.start()

if __name__=='__main__':
    arrH = arrayHandler(20)
    arrH.noise_init()
    arrH.ising_init(0.3)
    arrH.conway_init([[[1],[4],[3]]])
    arrH.noiser.change_threshold(0.80)
    arrH.noiser.process()
    arrH.conwayUp.change_array(arrH.array)
    arrH.conwayUp.process()
    print(arrH.array*1)
    arrH.isingUp.change_array(arrH.array)
    arrH.isingUp.process(1000)
