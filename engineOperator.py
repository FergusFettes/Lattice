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
##=================================##
# These fellas do little tasks ON A SINGLE SHARED ARRAY
# The array updaters all inherit the handler, so they can directly maniupalate the array
class Handler(QObject):
    changeSig = pyqtSignal(np.ndarray, int)
    arraySig = pyqtSignal(np.ndarray)
    breakSig = pyqtSignal()
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
#       self.arraySig.emit(Handler.ARRAY)
        Handler.ARRAYOLD = np.copy(Handler.ARRAY)

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
        if not Handler.CHANGE.size:
            self.breakSig.emit()

    def noise_process(self, threshold):
        Handler.ARRAY = np.zeros(Handler.ARRAY.shape, bool)
        Handler.ARRAYOLD = np.copy(Handler.ARRAY)
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
        rule1 = np.bitwise_and(A, NB >= rule[0])
        #alive cells that will live
        rule2 = np.bitwise_and(rule1, NB <= rule[1])
        #dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB >= rule[2])
        rule5 = np.bitwise_and(rule4, NB <= rule[3])
        #should just be the live cells
        Handler.ARRAY = rule2 + rule4 + rule5


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
    arrayfpsSig = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, array, **kwargs):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = kwargs
        self.fpsTimer = QTimer(self)
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
        if self.st['CLEAR']:
            self.noiseSig.emit(self.st['THRESHOLD'])
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
            self.arrayfpsSig.emit(time.time() - now)
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


##==============EngineOperator===============##
##===========================================##
# This is the interface between the GUI and the threads.
# Controls the Updater thread and the CanvasThread
class EngineOperator(QObject):
    settingsSig = pyqtSignal(dict)
    interruptSig = pyqtSignal()

    def __init__(self, canvas, frameLabel, arrayfpsLabel, canvasfpsLabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        QObject.__init__(self)
        self.array = np.zeros([kwargs['N'], kwargs['N']], bool)
        self.kwargs = kwargs
        self.canvas = canvas
        self.frameLabel = frameLabel
        self.arrayfpsLabel = arrayfpsLabel
        self.canvasfpsLabel = canvasfpsLabel
        self.mainUpdates = 0

        self.taskman_init()

#=============Thread Communicators======#
#   def update_kwargs(self, **kwargs):
#       print('Updating Threads')
#       for i in kwargs:
#           self.kwargs[i] = kwargs[i]
#       if self.thread.isRunning():
#           print('Requesting Interrution')
#           self.thread.requestInterruption()
#       else:
#           self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})

    def update_kwargs(self, **kwargs):
        for i in kwargs:
            self.kwargs[i] = kwargs[i]

    def breaker(self):
        self.update_kwargs(RUN=False)

    def thread_looper(self):
#       if self.kwargs['RUN'] is True and self.kwargs['RUNFRAMES'] < self.kwargs['IMAGEUPDATES']:
#           self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
#           self.thread.start()
#       elif self.kwargs['CLEAR'] is True or self.kwargs['EQUILIBRATE'] is True:
#           self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
#           self.thread.start()
#           self.simple_update(CLEAR=False, EQUILIBRATE=False)
#       else:
#           self.simple_update(RUN=False)
        print('Thread standing by.')

#===============Run Initiators=============#
    def static_run(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=True, RUNFRAMES=(self.kwargs['IMAGEUPDATES']-1))
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.thread.start()

    def dynamic_run(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=True, RUNFRAMES=0)
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.thread.start()

    def long_run(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=False, EQUILIBRATE=True)
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.thread.start()
        self.update_kwargs(EQUILIBRATE=False)

    def clear_array(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=False, CLEAR=True)
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.thread.start()
        self.update_kwargs(CLEAR=False)

    def noise_array(self):
        pass
        self.thread.start()

#===============GUI updaters=============#
    def array_fps_update(self, value):
        print(value)
        self.arrayfpsLabel.setText('Array fps: ' + str(1 / value))

    def canvas_fps_update(self, value):
        self.canvasfpsLabel.setText('Canvas fps: ' + str(1 / value))

    def frame_value_update(self, value):
        self.frameLabel.setText(str(value))
        if not value % 10:
            self.kwargs['RUNFRAMES'] = value

    def error_string(self, error='Unlabelled Error! Oh no!'):
        print(error)

#=================Thread Initiator============#
    def taskman_init(self):
        self.thread = QThread()
        self.handler = Handler(self.array)
        self.taskman = RunController(self.array, **self.kwargs)
        self.taskman.moveToThread(self.thread)
        self.thread.started.connect(self.taskman.process)
        self.taskman.error.connect(self.error_string)
        self.taskman.finished.connect(self.thread.quit)
      # self.taskman.finished.connect(self.clear_temp_kwargs)
        self.thread.finished.connect(self.thread_looper)
        self.taskman.frameSig.connect(self.frame_value_update)
        self.taskman.arrayfpsSig.connect(self.array_fps_update)
        self.canvas.canvasfpsSig.connect(self.canvas_fps_update)
        self.taskman.isingSig.connect(self.handler.ising_process)
        self.taskman.noiseSig.connect(self.handler.noise_process)
        self.taskman.conwaySig.connect(self.handler.conway_process)
        self.taskman.handlerSig.connect(self.handler.process)

        self.handler.changeSig.connect(self.canvas.export_list)
        self.handler.arraySig.connect(self.canvas.export_array)
        self.handler.breakSig.connect(self.breaker)

        self.settingsSig.connect(self.taskman.change_settings)
        self.interruptSig.connect(self.breaker)

        self.thread.start()
