from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import time


##==============Workers============##
##=================================##
# These fellas do little tasks ON A SINGLE SHARED ARRAY
# The array updaters all inherit the handler, so they can directly maniupalate the array
class Handler(QObject):
    arraySig = pyqtSignal(np.ndarray)
    startSig = pyqtSignal()
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []      # Array, shared among workers
    BOUNDARY = []

    def __init__(self, **kwargs):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.resize_array(kwargs['THRESHOLD'], kwargs['N'], kwargs['D'])

    def set_boundary(self, polarity):
        Handler.ARRAY[1, ...] = polarity
        Handler.ARRAY[-1, ...] = polarity
        Handler.ARRAY[..., 1] = polarity
        Handler.ARRAY[..., -1] = polarity

    def clear_wavefront(self, start, end, polarity):
    #   print(Handler.ARRAY*1)
    #   print(start)
    #   print(end)
    #   print(polarity)
        Handler.ARRAY[start:end, ...] = polarity
    #   print(Handler.ARRAY*1)

    def resize_array(self, threshold, height, width):
        Handler.ARRAY = np.zeros([height, width], bool)
        Handler.ARRAYOLD = np.zeros([height, width], bool)
        self.noise_process(threshold)

    def process(self):
      # self.dumpObjectInfo()
        self.arraySig.emit(Handler.ARRAY)
        self.startSig.emit()
        Handler.ARRAYOLD = np.copy(Handler.ARRAY)

    def noise_process(self, threshold):
        A = np.random.random(Handler.ARRAY.shape) > threshold
        B = np.bitwise_xor(Handler.ARRAY, A)
        Handler.ARRAY = B
        self.arraySig.emit(Handler.ARRAY)
        self.startSig.emit()

    def ising_process(self, updates, beta):
        cost = np.zeros(3, float)
        cost[1] = np.exp(-4 * beta)
        cost[2] = cost[1] ** 2
        # Really want to undestand object permanence better, here is a case-study--
        # this breaks without np.copy. Maybe werite all the array engines in Cython so
        # its all a little more clear.
       #A = Handler.ARRAY
        A = np.copy(Handler.ARRAY)
        N = A.shape[0]
        D = A.shape[1]
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(D)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                            A[a][b] == A[(a - 1) % N][b],
                            A[a][b] == A[a][(b + 1) % D],
                            A[a][b] == A[a][(b - 1) % D],
                            -2])
            if nb <= 0 or np.random.random() < cost[nb]:
                A[a][b] = not A[a][b]
        Handler.ARRAY = A

    def conway_process(self, rule):
        A = Handler.ARRAY
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
        rule1 = np.bitwise_and(A, NB >= rule[0])
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB <= rule[1])
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB >= rule[2])
        rule5 = np.bitwise_and(rule4, NB <= rule[3])
        #should just be the live cells
        Handler.ARRAY = rule2 + rule5
        # Rule 4 was being added in here for ages! Produces mad shapes!
        # This  is equivalent to makeing #4=8
