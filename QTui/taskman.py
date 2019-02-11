from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import time
import munch
from src.pureUp import *


##===============TaskManager===============##
##=========================================##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
# TODO update the taskman
class RunController(QObject):
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    handlerSig = pyqtSignal(dict)
    handlerSingleSig = pyqtSignal(dict)
    handlerinitSig = pyqtSignal(dict, dict, list)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, st):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = st

        self.wavecounter = 0
        self.st.general.rundone = 0

        # How often does a dynamic run break to look for new settings?
        self.mainTime = QTimer(self)
        self.mainTime.setInterval(99000)

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        QCoreApplication.processEvents()
        if self.st.general.rundone == -3:
            self.push_single_frame()
        elif self.st.general.rundone == -2:
            self.next_frame()
        else:
            if self.st.general.rundone == 0:
                self.init_new_process()
            else:
                self.next_frame()

    def init_new_process(self):
        self.mainTime.start()
        frame1 = self.prepare_frame()
        self.st.general.rundone += 1
        frame2 = self.prepare_frame()
        self.st.general.rundone += 1
        self.handlerinitSig.emit(frame1, frame2, self.st.canvas.dim)
        self.frame = self.prepare_frame()
        self.frametime = time.time()

    def push_single_frame(self):
        self.error.emit('Pushing single frame')
        self.frame = self.prepare_frame()
        self.handlerSingleSig.emit(self.frame)
        self.st.general.rundone += 1
        self.finished.emit()

    def next_frame(self):
        QCoreApplication.processEvents()
        while time.time() - self.frametime < self.st.general.frametime:
            QThread.msleep(1)
        if self.st.general.rundone == -1:
            self.error.emit('Step/Clear/Equilibrate done')
            self.st.general.rundone += 1
            self.finished.emit()
            return
        if self.st.general.runtodo > 0\
                and self.st.general.rundone >= self.st.general.runtodo:
            self.error.emit('Run finished')
            self.finished.emit()
            return
        if QThread.currentThread().isInterruptionRequested():
            self.error.emit('Interrupted')
            self.finished.emit()
            return
        self.handlerSig.emit(self.frame)
        self.frame = self.prepare_frame()
        self.st.general.rundone += 1
        self.frameSig.emit(self.st.general.rundone)
        self.frametime = time.time()

    def prepare_frame(self):
        frame={
            'dim':self.st.canvas.dim,
            'threshold':self.st.noise.threshold,
            'noisesteps':0,
            'clear':0,
            'isingupdates':0,
            'conwayrules':[],
            'beta':self.st.ising.beta,
            'ub':self.st.bounds.upper,
            'rb':self.st.bounds.right,
            'db':self.st.bounds.lower,
            'lb':self.st.bounds.left,
            'wolfpole':self.st.wolfram.polarity,
            'wolfpos':0,
            'wolfscale':self.st.wolfram.scale,
            }
        self.wavecounter += self.st.wolfram.scale
        self.wavecounter %= self.st.canvas.dim[0]
        frame['wolfpos'] = self.wavecounter
        if self.st.general.wolfwave == False:
            frame['wolfpole'] = -1
        if self.st.general.equilibrate:
            frame['conwayrules'] = []
            frame['isingupdates'] = self.st.ising.equilibrate
            self.error.emit('Equilibration Starting!')
        if self.st.general.clear:
            frame['conwayrules'] = []
            frame['isingupdates'] = 0
            frame['noisesteps'] = 1
            frame['clear'] = 1
        if self.st.general.running:
            rules = self.st.conway.rules
            if len(rules) == 0:
                rule = []
            else:
                rule = rules[self.st.general.rundone % len(rules)]
            if self.st.general.conway and self.st.general.stochastic:
#               if self.st.general.rundone % 2:
                frame['noisesteps'] = 1
#               else:
                frame['conwayrules'] = rule
            else:
                frame['isingupdates'] = self.st.ising.updates * self.st.general.stochastic
                frame['conwayrules'] = rule
        return frame


##==============Workers============##
##=================================##
class Handler(QObject, pureHandler):
    arraySig = pyqtSignal(np.ndarray, int, list)
    arraySingleSig = pyqtSignal(np.ndarray, int, list)
    arrayinitSig = pyqtSignal(np.ndarray, int, list)
    arrayfpsSig = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, st):
        """ Controls workers for the array updates,
            and processes the arrays returned. """
        QObject.__init__(self)
        self.array = super().resize_array(st.canvas.dim)
        self.fpsRoll = np.zeros(9, float)

    def updater_start(self, frame1, frame2, dim):
        if not self.array.shape == tuple(dim):
            self.array = super().resize_array(dim)
        self.array = super().process(frame1, self.array)
        self.arrayinitSig.emit(self.array, frame1['wolfpos'], dim)
        self.array = super().process(frame2, self.array)

    def push_single_array(self, frame):
        self.array = super().process(frame, self.array)
        self.arraySingleSig.emit(self.array, frame['wolfpos'], frame['dim'])

    def next_array(self, frame):
        if not self.array.shape == tuple(frame['dim']):
            self.array = super().resize_array(frame['dim'])
        now = time.time()
        self.arraySig.emit(self.array, frame['wolfpos'], frame['dim'])
        self.array = super().process(frame, self.array)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.arrayfpsSig.emit(np.mean(self.fpsRoll))