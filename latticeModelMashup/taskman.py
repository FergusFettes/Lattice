from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import time


##===============TaskManager===============##
##=========================================##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
# TODO update the taskman
class RunController(QObject):
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    handlerSig = pyqtSignal(munch.Munch)
    handlerSingleSig = pyqtSignal(munch.Munch)
    handlerinitSig = pyqtSignal(munch.Munch, munch.Munch, list)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, st):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = st
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

        self.wavecounter = 0

        # How often does a dynamic run break to look for new settings?
        self.mainTime = QTimer(self)
        self.mainTime.setInterval(99000)

#==============Changes the internal settings================#
# Should make the event queue feeding this baby LIFO
    def change_settings(self, st):
        self.st = st

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        QCoreApplication.processEvents()
        if self.st.general.runframes == -3:
            self.push_single_frame()
            self.st.general.runframes += 1
        if self.st.general.runframes == -2:
            self.error.emit('setup single step!')
        else:
            self.init_new_process()

    def init_new_process(self):
        self.mainTime.start()
        frame1 = self.prepare_frame()
        frame2 = self.prepare_frame()
        self.handlerinitSig.emit(frame1, frame2, self.st.canvas.dim)
        self.frame = self.prepare_frame()
        self.frametime = time.time()

    def push_single_frame(self):
        self.error.emit('Pushing single frame')
        self.frame = self.prepare_frame()
        self.handlerSingleSig.emit(self.frame)
        self.finished.emit()

    def next_frame(self):
        QCoreApplication.processEvents()
        while time.time() - self.frametime < self.st.general.frametime:
            QThread.msleep(1)
        if self.st.general.rundone == -1:
            self.error.emit('Step/Clear/Equilibrate done')
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
        self.wavecounter += self.st.wolfram.scale
        self.wavecounter %= self.st.canvas.dim[0]
        frame['wolfpos'] = self.wavecounter
        if self.st.general.wolfwave == 0:
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
                rule = rules[self.st.general.runframes % len(rules)]
            if self.st.general.conway and self.st.general.stochastic:
                if self.st.general.rundone % 2:
                    frame['noisesteps'] = 1
                else:
                    frame['conwayrules'] = rule
            else:
                frame['isingupdates'] = self.st.ising.updates * self.st.general.stochastic
                frame['conwayrules'] = rule
        return frame
