from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time
import sys
import queue as queue


##==============Workers============##
##=================================##
# These fellas do little tasks ON A SINGLE SHARED ARRAY
# The array updaters all inherit the handler, so they can directly maniupalate the array
class Handler(QObject):
    arraySig = pyqtSignal(np.ndarray)
    startSig = pyqtSignal()
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []      # Array, shared among workers

    def __init__(self, **kwargs):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.resize_array(kwargs['THRESHOLD'], kwargs['N'], kwargs['D'])

    def resize_array(self, threshold, height, width):
        Handler.ARRAY = np.zeros([height, width], bool)
        Handler.ARRAYOLD = np.zeros([height, width], bool)
        self.noise_process(threshold)

    def process(self):
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
        A = np.copy(Handler.ARRAY)
        # Really want to underant object permanence better, here is a case-study--
        # this breaks without np.copy. Maybe werite all the array engines in Cython so
        # its all a little more clear.
       #A = Handler.ARRAY
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


##===============TaskManager===============##
##=========================================##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
# TODO update the taskman
class RunController(QObject):
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    handlerSig = pyqtSignal()
    isingSig = pyqtSignal(int, float)
    # Note to self, remember how much time you wasted on signals that were converting
    # float to int.
    noiseSig = pyqtSignal(float)
    conwaySig = pyqtSignal(list)
    clearSig = pyqtSignal(float, int)   ### change this for N*D XXX
    arrayfpsSig = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, **kwargs):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = kwargs
        self.fpsTimer = QTimer(self)
        self.fpsRoll = np.zeros(5, float)
        # Maximum fps = 1000 / the following
        self.fpsTimer.setInterval(1)
        self.mainTime = QTimer(self)
        # How often does a dynamic run break to look for new settings?
        self.mainTime.setInterval(99000)

#==============Changes the internal settings================#
# Should make the event queue feeding this baby LIFO
    def change_settings(self, kwargs):
        for i in kwargs:
            self.st[i] = kwargs[i]

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        ## THE FOLLOWING LINE WAS ALL I NEEDED two days of reading lol
        QCoreApplication.processEvents()
        self.error.emit('Process Starting!')
        self.mainTime.start()
        if self.st['CLEAR']:        # This is the clear/reset/resize function
            self.clearSig.emit(self.st['THRESHOLD'], self.st['N'], self.st['D'])
            self.error.emit('Cleared')
            self.finished.emit()
            return
        if self.st['EQUILIBRATE']:
            self.st['CONWAY'] = False
            self.array_frame(self.st['LONGNUM'], self.st['RULES'], self.st['BETA'])
            self.error.emit('Equilibrated')
            self.finished.emit()
            return
        if self.st['RUN']:
            while not QThread.currentThread().isInterruptionRequested():
                self.dynamic_run()
                if self.st['IMAGEUPDATES'] <= self.st['RUNFRAMES']:
                    self.error.emit('Run finished')
                    self.finished.emit()
                    return
            self.error.emit('Interrupted')
        self.finished.emit()

#===============This handles the standard run method===================#
    def dynamic_run(self):
        rule = []
        now = time.time()
        while self.st['RUNFRAMES'] < self.st['IMAGEUPDATES']:
            if self.st['CONWAY']:
                rules = self.st['RULES']
                rule = rules[self.st['RUNFRAMES'] % len(rules)]
            self.array_frame(self.st['MONTEUPDATES'], rule, self.st['BETA'])
            self.st['RUNFRAMES'] += 1
            self.frameSig.emit(self.st['RUNFRAMES'])
            self.fpsRoll[0] = time.time()-now
            self.fpsRoll = np.roll(self.fpsRoll, 1)
            self.arrayfpsSig.emit(np.mean(self.fpsRoll))
            while time.time() - now < 0.05:
                QThread.msleep(1)
                if not self.mainTime.remainingTime():
                    return
            now = time.time()
            if not self.mainTime.remainingTime():
                return
            # I tried replacing the calsl to time() with a QTimer and obvious did
            # everything wrong, but this is fine anyway.

#==============='One' frame (actually two image updates occur)=========#
    def array_frame(self, updates, rule, beta):
        if self.st['STOCHASTIC']:
            self.isingSig.emit(updates, beta)
            self.handlerSig.emit()
        if self.st['CONWAY']:
            self.conwaySig.emit(rule)
            self.handlerSig.emit()
