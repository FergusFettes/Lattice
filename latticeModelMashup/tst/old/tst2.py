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

class isingFastUpdater(QObject):
# Simple cheaty version of the Ising model. Reasonable for small numbers of
# updates. Slows with larger arrays.
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, beta):
        print('Ising Fast Updater Initialized!')
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
        A = np.bitwise_xor(A, flip)
        self.array = A
        return A

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

    def ising_fast_init(self, beta):
        self.isingFThread = QThread()
        self.isingFUp = isingFastUpdater(self.array, beta)
        self.isingFUp.moveToThread(self.isingFThread)
        self.isingFThread.started.connect(self.isingFUp.process)
        self.isingFUp.error.connect(self.error_string)
        self.isingFUp.finished.connect(self.isingFThread.quit)
        self.isingFThread.finished.connect(self.isingFThread.deleteLater)
        self.isingFUp.arraySig.connect(self.update_array)
        self.isingFThread.start()

class SimpleThread(QThread):
    arrayOut = pyqtSignal(np.ndarray)

    def __init__(self, que, callback, parent=None):
        QThread.__init__(self, parent)
        self.que = que
        self.arrayOut.connect(callback)

    def run(self):
        print('thread running')
        while True:
            workerIdent = self.que.get()
            print(workerIdent)
            if kwargs is None:
                print("Shutting Down a Simple Thread")
                return
            self.worker_init(workerIdent)
            self.worker.process()

    def worker_init(self, workerLamb):
        print('workers initlaised!')
        self.worker = workerLamb()
        self.started.connect(self.worker.process)
        self.worker.error.connect(self.error_string)
        self.worker.finished.connect(self.quit)
        self.worker.finished.connect(self.deleteLater)
        self.worker.arraySig.connect(self.arrayOut)
        self.worker.start()


class arrayTaskManager():
# This guy outputs all the tasks to the threadibois

    def __init__(self, N):
        self.array = []
        self.arrayMulti = []
        self.reset_array(N)

    def reset_array(self, N):
        self.update_array(np.zeros([N, N], bool))

    def randomize_array(self, N):
        self.array = np.random.random([N, N]) > 0.5

    def randomize_array_multi(self, N, DEGREE=2):
        self.array = np.random.ranint([N, N], DEGREE)

    def update_array(self, array):
        self.array = array

    def error_string(self, error='Unlabelled Error! Oh no!'):
        print(error)

    def process(self):
        MAX_CORES = 2
        self.que = queue.Queue()
        self.threads = []
        for _ in range(MAX_CORES):
            thread = SimpleThread(self.que, self.update_array)
            self.threads.append(thread)
            thread.start()
           #print(thread.isRunning())

        for _ in range(3):
            self.que.put(stochasticUpdater)#, False, timeout=2)
           #print(self.que.get())

        for _ in range(MAX_CORES):
            self.que.put(None)
            print(self.que.qsize())

if __name__=='__main__':
    arrTM = arrayTaskManager(10)
    print(arrTM.array)
    arrTM.process()
    print(arrTM.array)

  # arrH = arrayHandler(100)
  # arrH.noise_init()
  # arrH.ising_init(0.3)
  # arrH.ising_fast_init(0.3)
  # arrH.noiser.change_threshold(0.6)
  # arrH.noiser.process()
  # arrH.isingUp.change_array(arrH.array)
  # arrH.isingUp.process(1000)
  # arrH.isingFUp.change_array(arrH.array)
  # arrH.isingFUp.process(1000)
