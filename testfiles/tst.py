from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time
import sys
import queue as queue

# TODO add different noise distributions
class stochasticUpdater(QObject):
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, threshold = 0.95):
        """Adds white noise to an already existing array."""
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

# TODO add diarmuids cheaty engine
class isingUpdater(QObject):
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, beta):
        """Ising-processes a given array."""
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
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, rules):
        """Conway-processes a given array with a given set up update rules"""
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

class arrayHandler(QObject):
#   breakSig = pyqtSignal()

    def __init__(self, N):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.n = N
        self.array = np.zeros([N, N], bool)
        self.arrayOld = np.zeros([N, N], bool)
        self.living = np.zeros([0, 2], bool)
        self.change = np.zeros([0, 3], bool)

        self.noise_init()
        self.ising_init()
        self.conway_init()

        self.reset_array(N)

    def reset_array(self, N):
        self.update_array(np.zeros([N, N], bool))
        self.noiser.update_array(self.array)
        self.isingUp.update_array(self.array)
        self.conwayUp.update_array(self.array)

    def update_array(self, array):
        self.arrayOld = self.array
        self.array = array
        self.update_living()

    def update_living(self):
        self.living = np.argwhere(self.array)
#       if self.living.shape[0] == 0:
#           self.breakSig.emit()

    def update_change(self):
        # Maybe my old method was better here? I guess not everything has to be
        # done in numpy..
  #Old  A = self.canvas.Array
  #Old  return[[i[0], i[1], A[i[0], i[1]]] for i in L]
        # I guess it really depends on how full the array is.
        common = np.bitwise_and(self.array, self.arrayOld)
        onlyOld = np.bitwise_xor(common, self.arrayOld)
        onlyNew = np.bitwise_xor(common, self.array)
        b = np.concatenate((np.argwhere(onlyNew), np.ones([births.shape[0], 1])), axis=1)
        d = np.concatenate((np.argwhere(onlyOld), np.zeros([deaths.shape[0], 0])), axis=1)
        self.change = np.concatenate((b, d))

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

    def conway_init(self, rules=[[[1],[4],[1]]]):
        self.conwayThread = QThread()
        self.conwayUp = conwayUpdater(self.array, rules)
        self.conwayUp.moveToThread(self.conwayThread)
        self.conwayThread.started.connect(self.conwayUp.process)
        self.conwayUp.error.connect(self.error_string)
        self.conwayUp.finished.connect(self.conwayThread.quit)
        self.conwayThread.finished.connect(self.conwayThread.deleteLater)
        self.conwayUp.arraySig.connect(self.update_array)
        self.conwayThread.start()

class EngineOperator():
# This badboy assigns the tasks to the array manager and the canvas

    def __init__(self, **kwargs):#, canvas, framelabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        self.kwargs = kwargs
        self.framecounter = 0
        self.rules = []
        self.breaker = False

      #  self.canvas = canvas
        self.handler = arrayHandler(self.kwargs['N'])
      # self.handler.breakSig.connect(self.breaker)
      # self.framelabel = framelabel

    def reset(self):
        self.handler.reset_array()
        self.framecounter = 0
      #  self.canvas.reset()

    def noise_array(self):
        self.handler.reset_array()
        self.handler.noiser.process()

    def update_kwargs(self, **kwargs):
        self.kwargs = kwargs
        self.handler.noiser.change_threshold(1-kwargs['COVERAGE'])
        self.handler.isingUp.change_cost(kwargs['BETA'])

    # Is this obscene? All I am trying to do is unpack my regexes. No doubt
    # there is a better (more readable / faster?) way of doing this.
    # self.rules should be an array of all the values for the rules.
    def process_rules(self, rulesMatch):
        rul = [i.group(1, 2, 3) for i in rulesMatch]
        self.rules = [[list(map(int, j.split(','))) for j in i] for i in rul]
        self.handler.conwayUp.change_rules(self.rules)

    def breaker(self):
        self.breaker = True

    def dynamic_run(self):
        now = time.time()
        for i in range(self.kwargs['IMAGEUPDATES']):
            if self.breaker:
                self.breaker = False
                break
            self.handler.conwayUp.process()
            if self.kwargs['STOCHASTIC']:
                self.handler.isingUp.process(self.kwargs['MONTEUPDATES'])
          # self.canvas.repaint()
            print(self.handler.array*1)
          # self.framelabel.setText(str(i) + ' / ')
            while time.time() - now < 0.02:
                time.sleep(0.01)
                print('waiting, round ' + str(i))
            now = time.time()

    def static_run(self):
        if self.kwargs['STOCHASTIC']:
            self.handler.isingUp.process(self.kwargs['MONTEUPDATES'])
        self.handler.conwayUp.process()

    def long_run(self):
        if self.kwargs['STOCHASTIC']:
            self.handler.isingUp.process(self.kwargs['EQUILIBRATE'])
