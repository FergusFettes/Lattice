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
    handlerSig = pyqtSignal()
    isingSig = pyqtSignal(int, float)
    # Note to self, remember how much time you wasted on signals that were converting
    # float to int.
    noiseSig = pyqtSignal(float)
    conwaySig = pyqtSignal(list)
    clearSig = pyqtSignal(float, int, int)
    arrayfpsSig = pyqtSignal(float)
    boundSig = pyqtSignal(int)
    waveSig = pyqtSignal(int, int, int)
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
        self.wavecounter = 0
        # How often does a dynamic run break to look for new settings?
#       self.mainTime.setInterval(99000)

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
            self.dynamic_run()
            if self.st['IMAGEUPDATES'] <= self.st['RUNFRAMES']:
                self.error.emit('Run finished')
                self.finished.emit()
                return
        self.finished.emit()

#===============This handles the standard run method===================#
    def dynamic_run(self):
        rule = []
        now = time.time()
        while self.st['RUNFRAMES'] < self.st['IMAGEUPDATES']:
            if QThread.currentThread().isInterruptionRequested():
                self.error.emit('Interrupted')
                return
            if self.st['CONWAY']:
                rules = self.st['RULES']
                rule = rules[self.st['RUNFRAMES'] % len(rules)]
            self.array_frame(self.st['MONTEUPDATES'], rule, self.st['BETA'])
            self.st['RUNFRAMES'] += 1
            self.frameSig.emit(self.st['RUNFRAMES'])
#           self.fpsRoll[0] = time.time()-now
#           self.fpsRoll = np.roll(self.fpsRoll, 1)
#           self.arrayfpsSig.emit(np.mean(self.fpsRoll))
            while time.time() - now < 0.05:
                QThread.msleep(1)
            now = time.time()

#==============='One' frame (actually two image updates occur)=========#
    def array_frame(self, updates, rule, beta):
        if self.st['STOCHASTIC']:
            if self.st['WOLFWAVE']:
                start = self.wavecounter
                self.wavecounter += self.st['WOLFSCALE']
                self.wavecounter %= self.st['N']
                self.waveSig.emit(start, start + self.st['WOLFSCALE'], self.st['WOLFPOLARITY'])
            if self.st['BOUNDARY']:
                self.boundSig.emit(self.st['POLARITY'])
            self.isingSig.emit(updates, beta)
            self.handlerSig.emit()
        if self.st['CONWAY']:
            if self.st['WOLFWAVE']:
                start = self.wavecounter
                self.wavecounter += self.st['WOLFSCALE']
                self.wavecounter %= self.st['N']
                self.waveSig.emit(start, start + self.st['WOLFSCALE'], self.st['WOLFPOLARITY'])
            if self.st['BOUNDARY']:
                self.boundSig.emit(self.st['POLARITY'])
            self.conwaySig.emit(rule)
            self.handlerSig.emit()
