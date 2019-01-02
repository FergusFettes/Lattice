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
    arraySig = pyqtSignal(np.ndarray, int)
    arrayinitSig = pyqtSignal(np.ndarray, int, int, int)
    arrayfpsSig = pyqtSignal(float)
    startSig = pyqtSignal()
    nextSig = pyqtSignal()
    error = pyqtSignal(str)
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []      # Array, shared among workers
    BOUNDARY = []

    def __init__(self, **kwargs):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.resize_array(kwargs['N'], kwargs['D'])
        self.fpsRoll = np.zeros(9, float)

    def updater_start(self, frame1, frame2, N, D):
        if not Handler.ARRAY.shape[0] == N or not Handler.ARRAY.shape[1] == D:
            self.resize_array(N, D)
        self.process(frame1)
        self.arrayinitSig.emit(Handler.ARRAY, frame1['wolfpos'], N, D)
        self.process(frame2)

    def next_array(self, frame):
        now = time.time()
        self.arraySig.emit(Handler.ARRAY, frame['wolfpos'])
        self.process(frame)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.arrayfpsSig.emit(np.mean(self.fpsRoll))

    def process(self, job):
        if job['clear']:
            self.resize_array(Handler.ARRAY.shape[0], Handler.ARRAY.shape[1])
        if job['wolfpole'] >= 0:
            self.clear_wavefront(job['wolfpos'], job['wolfscale'], job['wolfpole'])
        for i in range(job['noisesteps']):
            self.noise_process(job['threshold'])
        self.set_boundary(job['ub'], job['rb'], job['db'], job['lb'])
        if job['isingupdates'] > 0:
            self.ising_process(job['isingupdates'], job['beta'])
        if not job['conwayrules'] == []:
            self.conway_process(job['conwayrules'])

    def set_boundary(self, ub, rb, db, lb):
        if ub >= 0:
            Handler.ARRAY[0, ...] = ub
        if db >= 0:
            Handler.ARRAY[-1, ...] = db
        if lb >= 0:
            Handler.ARRAY[..., 0] = lb
        if rb >= 0:
            Handler.ARRAY[..., -1] = rb

    def clear_wavefront(self, start, scale, polarity):
        n = Handler.ARRAY.shape[0]
        for i in range(scale):
            Handler.ARRAY[(start + i) % n, ...] = polarity

    def resize_array(self, height, width):
        Handler.ARRAY = np.zeros([height, width], bool)
        Handler.ARRAYOLD = np.zeros([height, width], bool)

    def noise_process(self, threshold):
        A = np.random.random(Handler.ARRAY.shape) > threshold
        B = np.bitwise_xor(Handler.ARRAY, A)
        Handler.ARRAY = B

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
