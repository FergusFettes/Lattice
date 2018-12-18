from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time
import sys
import queue as queue

##==============Workers============##
# These fellas do little tasks ON A SINGLE SHARED ARRAY
# The array updaters all inherit the handler, so they can directly maniupalate the array
class arrayHandler(QObject):
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []   # A previous copy, updated periodically
    CHANGE = []     # The difference between the two ((Nx3), with state)
    LIVING = []     # Currently living cells, updated periodically(?)

    def __init__(self, array):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        ARRAY = array
        ARRAYOLD = np.zeros(ARRAY.shape, bool)
        LIVING = np.zeros([0, 2], bool)
        CHANGE = np.zeros([0, 3], bool)

    def process(self, mutex):
        mutex.lock()
        ARRAYOLD = ARRAY
        self.update_living()
        self.update_change()
        mutex.unlock()

    def update_living(self):
        LIVING = np.argwhere(ARRAY)

    def update_change(self):
        common = np.bitwise_and(ARRAY, ARRAYOLD)
        onlyOld = np.bitwise_xor(common, ARRAYOLD)
        onlyNew = np.bitwise_xor(common, ARRAY)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        CHANGE = np.concatenate((b, d))


# TODO add different noise distributions
class stochasticUpdater(arrayHandler):

    def __init__(self):
        """Adds white noise to an already existing array."""
        QObject.__init__(self)

    def process(self, threshold, mutex):
        A = np.random.random(ARRAY.shape) > threshold
        mutex.lock()
        B = np.bitwise_xor(ARRAY, A)
        ARRAY = B
        mutex.unlock()


class isingUpdater(arrayHandler):

    def __init__(self):
        """Ising-processes a given array."""
        QObject.__init__(self)

    def process(self, updates, beta, mutex):
        cost = np.zeros(3, float)
        cost[1] = np.exp(-4 * beta)
        cost[2] = cost[1] ** 2
        mutex.lock()
        A = ARRAY
        flip = np.zeros(A.shape, bool)
        N = A.shape[0]
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(N)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                  A[a][b] == A[(a - 1) % N][b],
                  A[a][b] == A[a][(b + 1) % N],
                  A[a][b] == A[a][(b - 1) % N],
                  -2])
            if nb <= 0 or np.random.random() < self.cost[nb]:
                A[a][b] = not A[a][b]
        mutex.unlock()


class conwayUpdater(arrayHandler):

    def __init__(self):
        """Conway-processes a given array with a given set up update rules"""
        QObject.__init__(self)

    def process(self, rule, mutex):
        mutex.lock()
        A = ARRAY
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
        rule1 = np.bitwise_and(A, NB > self.rule[0])
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB < self.rule[1])
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB == self.rule[2])
        #should just be the live cells
        ARRAY = rule2 + rule4
        mutex.unlock()


##===============TaskManager===============##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
# TODO update the taskman
class RunController(arrayHandler):
    arraySig = pyqtSignal(np.ndarray)
    changeSig = pyqtSignal(np.ndarray)
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    handlerSig = pyqtSignal(QMutex)
    isingSig = pyqtSignal(int, int, QMutex)
    noiseSig = pyqtSignal(int, QMutex)
    conwaySig = pyqtSignal(list, QMutex)
    error = pyqtSignal(str)

    def __init__(self, array):
        """Run controller makes sure the run doesnt get out of hand"""
        arrayHandler.__init__(self, array)
        QObject.__init__(self)
      # self.change_rules(rules)
        self.counter = 0

    def process(self):
        self.handlerSig.emit(mutex)
        self.changeSig.emit(CHANGE, 0)
        mutex = QMutex()
        self.error.emit('Controller Started!')
        for i in range(10):
            self.error.emit('Task Round 1')
            self.array_frame(1000, [1,4,1], mutex)
        self.error.emit('Shutting down!')
        self.finished.emit()

    def array_frame(self, updates, rule, mutex):
        if self.stochastic:
            self.isingSig.emit(updates, beta, mutex)
        if self.conway:
            self.conwaySig.emit(rule, mutex)
        self.handlerSig.emit(mutex)
        self.changeSig.emit(CHANGE, 0)

    def dynamic_run(self):
        now = time.time()
        for i in range(self.frames):
            if self.breaker:
                self.breaker = False
                break
            self.array_frame()
            self.frameSig.emit(i)
            while time.time() - now < 0.03:
                time.sleep(0.01)
            now = time.time()
        self.frameSig.emit(0)


##==============EngineOperator===============##
# This is the interface between the GUI and the threads.
# Controls the WorkHorse thread and the CanvasThread
class EngineOperator():

    def __init__(self, canvas, framelabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        self.rules = []
        self.array = np.zeros([kwargs['N'], kwargs['N']])
        self.kwargs = kwargs
        self.conway = True
        self.canvas = canvas
        self.framelabel = framelabel

        self.taskman_init()

    def reset(self):
    ##  self.handler.reset_array()
        self.framecounter = 0
    ##  self.canvas.Array = self.handler.array
        self.canvas.reset()
    ##  self.canvas.export_list(self.handler.living, 1)

    def noise_array(self):
        self.canvas.reset()
        self.handler.reset_array()
        self.handler.noiser.process()
        self.canvas.export_list(self.handler.change, 0)

    def update_kwargs(self, **kwargs):
        self.kwargs = kwargs
        self.handler.noiser.change_threshold(kwargs['COVERAGE'])
        self.handler.isingUp.change_cost(kwargs['BETA'])

    def frame_value_update(self, value):
        self.frameLabel.setText(str(value))

    def error_string(self, error='Unlabelled Error! Oh no!'):
        print(error)

    # Is this obscene? All I am trying to do is unpack my regexes. No doubt
    # there is a better (more readable / faster?) way of doing this.
    # self.rules should be an array of all the values for the rules.
    def process_rules(self, rulesMatch):
        rul = [i.group(1, 2, 3) for i in rulesMatch]
        self.rules = [[list(map(int, j.split(','))) for j in i] for i in rul]
        if self.rules == []:
            self.conway = False
        else:
         ## self.handler.conwayUp.change_rules(self.rules)
            self.conway = True

    def taskman_init(self):
        self.thread = QThread()
        self.taskman = RunController(self.array)
        self.taskman.moveToThread(self.thread)
        self.thread.started.connect(self.taskman.process)
        self.taskman.error.connect(self.error_string)
        self.taskman.finished.connect(self.thread.quit)
        self.taskman.frameSig.connect(self.frame_value_update)
        self.taskman.changeSig.connect(self.canvas.export_list)
        self.taskman.arraySig.connect(self.canvas.export_array)

        self.noiser = stochasticUpdater()
        self.noiser.moveToThread(self.thread)

        self.conwayUp = conwayUpdater()
        self.conwayUp.moveToThread(self.thread)

        self.isingUp = isingUpdater()
        self.isingUp.moveToThread(self.thread)

        self.handler.moveToThread(self.thread)


    def static_run(self):
        self.thread.start()
