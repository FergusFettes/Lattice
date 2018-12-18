from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import time
import sys
import queue as queue

# TODO: get a threadpool on the go so you dont need to artifically keep the thread alive
# TODO: use pythons 'queue' to move settings into the task managet in a timely fashion
# TODO: maybe use a mutex to share the array with the canvas? maybe not necc.
##==============Workers============##
# These fellas do little tasks ON A SINGLE SHARED ARRAY
# The array updaters all inherit the handler, so they can directly maniupalate the array
class Handler(QObject):
    changeSig = pyqtSignal(np.ndarray, int)
    arraySig = pyqtSignal(np.ndarray)
    ARRAY = []      # Array, shared among workers
    ARRAYOLD = []   # A previous copy, updated periodically
    CHANGE = []     # The difference between the two ((Nx3), with state)
    LIVING = []     # Currently living cells, updated periodically(?)

    def __init__(self, array):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        Handler.ARRAY = array
        Handler.ARRAYOLD = np.zeros(Handler.ARRAY.shape, bool)
        Handler.LIVING = np.zeros([0, 2], bool)
        Handler.CHANGE = np.zeros([0, 3], bool)

    def process(self):
#       self.update_living()
        self.update_change()
        self.changeSig.emit(Handler.CHANGE, 0)
        Handler.ARRAYOLD = Handler.ARRAY

    def update_living(self):
        Handler.LIVING = np.argwhere(Handler.ARRAY)

    def update_change(self):
        common = np.bitwise_and(Handler.ARRAY, Handler.ARRAYOLD)
        onlyOld = np.bitwise_xor(common, Handler.ARRAYOLD)
        onlyNew = np.bitwise_xor(common, Handler.ARRAY)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        Handler.CHANGE = np.concatenate((b, d))

    def noise_process(self, threshold):
        Handler.ARRAY = np.zeros(Handler.ARRAY.shape, bool)
        Handler.ARRAYOLD = Handler.ARRAY
        A = np.random.random(Handler.ARRAY.shape) > threshold
        B = np.bitwise_xor(Handler.ARRAY, A)
        Handler.ARRAY = B
        self.arraySig.emit(Handler.ARRAY)

    def ising_process(self, updates, beta):
        cost = np.zeros(3, float)
        cost[1] = np.exp(-4 * beta)
        cost[2] = cost[1] ** 2
        A = Handler.ARRAY
        N = A.shape[0]
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(N)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                            A[a][b] == A[(a - 1) % N][b],
                            A[a][b] == A[a][(b + 1) % N],
                            A[a][b] == A[a][(b - 1) % N],
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
        rule1 = np.bitwise_and(A, NB > rule[0][0])
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB < rule[1][0])
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB == rule[2][0])
        #should just be the live cells
        Handler.ARRAY = rule2 + rule4


##===============TaskManager===============##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
# TODO update the taskman
class RunController(QObject):
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    handlerSig = pyqtSignal()
    isingSig = pyqtSignal(int, float)
    noiseSig = pyqtSignal(int)
    conwaySig = pyqtSignal(list)
    arrayfpsSig = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, array):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = {
            'rules':      [[[1],[4],[1]]],
            'counter':    0,
            'stochastic': True,
            'conway':     True,
            'equilibrate':False,
            'clear':      False,
            'threshold':  0.01,
            'speed':      100,
            'frames':     0,
            'updates':    1000,
            'longnum':    100000,
            'beta':       1 / 8,
            'threshold':  0.99
        }

    def change_settings(self, kwargs):
     ## print(self.st)
        for i in kwargs:
            self.st[i] = kwargs[i]
     ## print(self.st)

    def process(self):
     ## self.error.emit('Process Starting!')
        self.handlerSig.emit()
        self.mainTime = QTimer(self)
        self.mainTime.setInterval(10000)
        self.mainTime.start()
        while self.mainTime.remainingTime() > 0:  #Can use this to check on the settings
            # every X seconds, then save the interrupt thing below for special things.
            while self.st['frames'] > 0:
                self.dynamic_run()
            if self.st['equilibrate']:
                self.st['equilibrate'] = False
                self.array_frame(self.st['longnum'], self.st['rules'],
                                    self.st['beta'])
            if self.st['clear']:
                self.st['clear'] = False
                self.noiseSig.emit(self.st['threshold'])
            QThread.msleep(10)
            interrupt = QThread.currentThread().isInterruptionRequested()
            if interrupt:
                break
     ## self.error.emit('Shutting down!')
        self.finished.emit()

    def breaker(self):
        self.mainTime.stop()

    def array_frame(self, updates, rule, beta):
        if self.st['stochastic']:
            self.isingSig.emit(updates, beta)
# can add an extra frame in here, should add minimal time to the loop. lets see
        if self.st['conway']:
            self.conwaySig.emit(rule)
        self.handlerSig.emit()

    def dynamic_run(self):
        now = time.time()
        rule = []
        for i in range(self.st['frames']):
            if self.st['conway']:
                rules = self.st['rules']
                rule = rules[i % len(rules)]
            if self.breaker:
                self.breaker = False
                break
            self.array_frame(self.st['updates'], rule, self.st['beta'])
            self.frameSig.emit(i)
            self.arrayfpsSig.emit(time.time() - now)
            while time.time() - now < 0.03:
                time.sleep(0.01)
            now = time.time()
            self.st['frames'] -= 1
        self.frameSig.emit(0)


##==============EngineOperator===============##
# This is the interface between the GUI and the threads.
# Controls the WorkHorse thread and the CanvasThread
class EngineOperator(QObject):
    settingsSig = pyqtSignal(dict)
    breakSig = pyqtSignal()

    def __init__(self, canvas, frameLabel, arrayfpsLabel, canvasfpsLabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        QObject.__init__(self)
        self.rules = []
        self.array = np.zeros([kwargs['N'], kwargs['N']], bool)
        self.kwargs = kwargs
        self.conway = True
        self.canvas = canvas
        self.frameLabel = frameLabel
        self.arrayfpsLabel = arrayfpsLabel
        self.canvasfpsLabel = canvasfpsLabel

        self.taskman_init()

    def noise_array(self):
        sett = {'clear': True, 'threshold': self.kwargs['COVERAGE']}
        self.settingsSig.emit(sett)
        self.thread.requestInterruption()

    def update_kwargs(self, **kwargs):
        for i in kwargs:
            self.kwargs[i] = kwargs[i]

    def array_fps_update(self, value):
        self.arrayfpsLabel.setText('Array fps: ' + str(1 / value))

    def canvas_fps_update(self, value):
        self.canvasfpsLabel.setText('Canvas fps: ' + str(1 / value))

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

        sett = {'rules': self.rules, 'conway': not self.rules==[]}
        self.settingsSig.emit(sett)
        self.thread.requestInterruption()

    def taskman_init(self):
        self.thread = QThread()
        self.handler = Handler(self.array)
        self.handler.moveToThread(self.thread)
        self.taskman = RunController(self.array)
        self.taskman.moveToThread(self.thread)
        self.thread.started.connect(self.taskman.process)
        self.taskman.error.connect(self.error_string)
        self.taskman.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.start)
        self.taskman.frameSig.connect(self.frame_value_update)
        self.taskman.arrayfpsSig.connect(self.array_fps_update)
        self.canvas.canvasfpsSig.connect(self.canvas_fps_update)
        self.taskman.isingSig.connect(self.handler.ising_process)
        self.taskman.noiseSig.connect(self.handler.noise_process)
        self.taskman.conwaySig.connect(self.handler.conway_process)
        self.taskman.handlerSig.connect(self.handler.process)

        self.handler.changeSig.connect(self.canvas.export_list)
        self.handler.arraySig.connect(self.canvas.export_array)

        self.settingsSig.connect(self.taskman.change_settings)

        self.thread.start()

    def static_run(self):
        sett = {'frames': 1}
        self.settingsSig.emit(sett)
        self.thread.requestInterruption()

    def dynamic_run(self):
        sett = {'frames': self.kwargs['IMAGEUPDATES']}
        self.settingsSig.emit(sett)
        self.thread.requestInterruption()

    def long_run(self):
        sett = {'frames': 0, 'long': self.kwargs['EQUILIBRATE'], 'equilibrate': True}
        self.settingsSig.emit(sett)
        self.thread.requestInterruption()

    def clear_array(self):
        pass
        self.thread.start()
