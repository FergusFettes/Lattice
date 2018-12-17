from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time
import sys
import queue as queue


# TODO add different noise distributions
class stochasticUpdater(QObject):
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, threshold=0.95):
        """Adds white noise to an already existing array."""
        QObject.__init__(self)
        self.change_threshold(threshold)
        self.change_array(array)

    def change_threshold(self, threshold):
        self.threshold = threshold
        print(threshold)

    def change_array(self, array):
        self.array = array

    def process(self):
        self.array = self.update_array()
        self.arraySig.emit(self.array)
        self.finished.emit()

    def update_array(self):
        array = self.array
        n = array.shape
        A = np.random.random(n) > self.threshold
        B = np.bitwise_xor(array, A)
        return B


class isingUpdater(QObject):
    arraySig = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, array, beta=1 / 8):
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
        A = np.copy(self.array)
        N = len(A)
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
        return A

    # Diarmuid's sneaky engine. NON-CANON, COMPUTATIONAL PHYSICISTS PLEASE LOOK AWAY
    # Scratch that, I doesn't work anyway (for now at least, but there are serious
    # problems with the concept I tihnk. We'll see.
    def update_array_NONFUNCIONING_LOL(self, iterations):
        a = np.copy(self.array)
        #i think things are easier if the costs are an array
        #of masks
        top = np.roll(a,-1,axis=0)
        bottom = np.roll(a,1,axis=0)
        left = np.roll(a,-1,axis=1)
        right = np.roll(a,1,axis=1)
        NB = np.zeros(a.shape)
        for matrix in [top, bottom, left, right]:
            NB += np.equal(a, matrix)
        #I'm not sure if this is the right way to
        #calc the threshold
        threshold = iterations / (a.shape[0] ** 2)
        #random msk used for selecting cells
        msk = np.random.random(a.shape) < threshold
        #new random used for the update rules below
        rndm_mask = np.random.random(a.shape)

        #changed by zero case
        flip_mask = np.bitwise_and(msk, NB <= 0)

        for i in range(1, 3):
            # these are the random cells with the right
            #number of neighbors
            b = np.bitwise_and(msk, NB == i)
            #these are the cells in b, for which ra.random()
            #is less than the cost function... I hope?
            #we add them to the flip mask, which should
            #still be boolean
            flip_mask += np.bitwise_and(b,rndm_mask < self.cost[i])

        return np.invert(a, where=flip_mask)


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
        self.error.emit('Array Started!')
        self.array = self.update_array()
        self.arraySig.emit(self.array)
        self.finished.emit()

    def update_array(self):
        rule = self.counter
        self.counter += 1
        self.counter %= self.ruleNum
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
    changeSig = pyqtSignal(np.ndarray)
    breakSig = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, N):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.n = N
        self.array = np.zeros([N, N], bool)
        self.arrayOld = np.zeros([N, N], bool)
        self.living = np.zeros([0, 2], bool)
        self.change = np.zeros([0, 3], bool)
        self.double = True

        self.reset_array()

    def process(self, array):
        self.error.emit('Array Started!')
        self.update_array(array)
        self.changeSig.emit(self.change)
        self.finished.emit()

    def reset_array(self):
        a = np.zeros([self.n, self.n], bool)
        self.update_array(a)

    def resize_array(self, N):
        self.n = N
        self.update_array(np.zeros([N, N], bool))

    def update_array(self, array):
        self.arrayOld = self.array
    #   print(self.double)
    #   if self.double:
    #       self.array = np.bitwise_or(self.arrayOld, array)
    #   else:
    #       self.array = array
        self.array = array
        self.update_living()
        self.update_change()

    def update_living(self):
        self.living = np.argwhere(self.array)
        if self.living.shape[0] == 0:
            self.breakSig.emit('None living!')

    def update_change(self):
        # Maybe my old method was better here? I guess not everything has to be
        # done in numpy..
  #Old  A = self.canvas.Array
  #Old  return[[i[0], i[1], A[i[0], i[1]]] for i in L]
        # I guess it really depends on how full the array is.
        common = np.bitwise_and(self.array, self.arrayOld)
        onlyOld = np.bitwise_xor(common, self.arrayOld)
        onlyNew = np.bitwise_xor(common, self.array)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        self.change = np.concatenate((b, d))

class EngineOperator():
# This badboy assigns the tasks to the array manager and the canvas

    def __init__(self, canvas, framelabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        self.array = np.zeros([kwargs['N'], kwargs['N']])
        self.kwargs = kwargs
        self.thread = []
        self.worker_init()
        self.noise_init()
        self.ising_init()
        self.conway_init()
        self.array_init(self.kwargs['N'])
        self.framecounter = 0
        self.rules = []
        self.breaker = False
        self.conway = True

        self.canvas = canvas
        self.framelabel = framelabel

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

    def breaker(self):
        self.breaker = True
        print('No change!')

    def dynamic_run(self):
        if self.conway and self.kwargs['STOCHASTIC']:
            self.handler.double = True
        now = time.time()
        for i in range(self.kwargs['IMAGEUPDATES']):
            if self.breaker:
                self.breaker = False
                break
            if self.conway:
                self.handler.conwayUp.process()
                #self.canvas.export_array(self.handler.array)
                self.canvas.export_list(self.handler.change, 0)
                self.canvas.repaint()
            if self.kwargs['STOCHASTIC']:
                self.handler.isingUp.process(self.kwargs['MONTEUPDATES'])
                #self.canvas.export_array(self.handler.array)
                self.canvas.export_list(self.handler.change, 0)
                self.canvas.repaint()
            self.framelabel.setText(str(i + 1) + ' / ')
            while time.time() - now < 0.03:
                time.sleep(0.01)
            now = time.time()
        self.framelabel.setText('0000/ ')
        self.canvas.repaint()
        self.handler.double = False

    def static_run(self):
        self.thread.worker_setter(self.isingUp, self.handler)
        self.thread.start()

    def static_run_OLD(self):
        if self.conway and self.kwargs['STOCHASTIC']:
            self.handler.double = True
        if self.kwargs['STOCHASTIC']:
            self.handler.isingUp.process(self.kwargs['MONTEUPDATES'])
        if self.conway:
            self.handler.conwayUp.process()
        self.canvas.export_array(self.handler.array)
        self.handler.double = False

    def long_run(self):
        if self.kwargs['STOCHASTIC']:
            self.handler.isingUp.process(self.kwargs['EQUILIBRATE'])
        self.canvas.export_array(self.handler.array)
       #self.canvas.export_list(self.handler.change, 0)

    def worker_init(self):
        self.synchro = QWaitCondition()
        self.thread = WorkHorse(self.kwargs['N'], self.synchro)
        self.thread.error.connect(self.error_string)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.changeSig.connect(self.temp_change_handler)
        self.thread.start()

    def temp_change_handler(self, array):
        print('array')
        self.canvas.export_list(array, 0)
        self.canvas.repaint()

    def noise_init(self, threshold=0.95):
        self.noiser = stochasticUpdater(self.array)
        self.noiser.moveToThread(self.thread)
      # self.thread.started.connect(self.noiser.process)
        self.noiser.error.connect(self.error_string)
      # self.noiser.finished.connect(self.thread.quit)
        self.noiser.arraySig.connect(self.thread.array_handler)

    def conway_init(self, rules=[[[1], [4], [1]]]):
        self.conwayUp = conwayUpdater(self.array, rules)
        self.conwayUp.moveToThread(self.thread)
      # self.thread.started.connect(self.conwayUp.process)
        self.conwayUp.error.connect(self.error_string)
      # self.conwayUp.finished.connect(self.thread.quit)
        self.conwayUp.arraySig.connect(self.thread.array_handler)

    def ising_init(self, beta=1 / 8):
        self.isingUp = isingUpdater(self.array, beta)
        self.isingUp.moveToThread(self.thread)
      # self.thread.started.connect(self.isingUp.process)
        self.isingUp.error.connect(self.error_string)
      # self.isingUp.finished.connect(self.thread.quit)
        self.isingUp.arraySig.connect(self.thread.array_handler)

    def array_init(self, N):
        self.handler = arrayHandler(N)
        self.handler.moveToThread(self.thread)
      # self.thread.started.connect(self.handler.process)
        self.handler.error.connect(self.error_string)
      # self.handler.finished.connect(self.thread.quit)
        self.handler.changeSig.connect(self.thread.change_handler)

#class RunController(QObject):
#    finished = pyqtSignal()
#    error = pyqtSignal(str)
#
#    def __init__(self, array, rules):
#        """Run controller makes sure the run doesnt get out of hand"""
#        QObject.__init__(self)
#        self.change_array(array)
#        self.change_rules(rules)
#        self.counter = 0


class WorkHorse(QThread):
# All the work
    changeSig = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, N, synchro, parent=None):
        QThread.__init__(self, parent)

        self.worker = QObject()
        self.handler = QObject()
        self.array = np.zeros([N, N], bool)
        self.change = np.zeros([0, 3], bool)
        self.synchro = synchro
        self.mutex = QMutex

    def worker_setter(self, worker, handler):
        self.worker = worker
        self.handler = handler

    def run(self):
        self.mutex.lock()
        while self.synchro.wait(self.mutex, 5000):
            self.error.emit('Workhorse Started!')
            self.update_array()
            self.worker.process(2000)
            self.update_array()
            self.handler.process(self.array)
            self.changeSig.emit(self.change)
        self.mutex.unlock()
        self.error.emit('Timeout! Shutting down.')
        self.emit.finish()

    def update_array(self):
        self.worker.change_array(self.array)

    def array_handler(self, array):
        self.array = array

    def change_handler(self, array):
        self.change = array
