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
    handlerSig = pyqtSignal(dict)
    handlerinitSig = pyqtSignal(dict, dict)
#   isingSig = pyqtSignal(int, float)
#   noiseSig = pyqtSignal(float)
#   conwaySig = pyqtSignal(list)
#   clearSig = pyqtSignal(float, int, int)
#   boundSig = pyqtSignal(int)
#   waveSig = pyqtSignal(int, int, int)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, **kwargs):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = kwargs
        self.fpsTimer = QTimer(self)
        # Maximum fps = 1000 / the following
        self.fpsTimer.setInterval(1)
        self.mainTime = QTimer(self)
        self.wavecounter = 0
        # How often does a dynamic run break to look for new settings?
        self.mainTime.setInterval(99000)

#==============Changes the internal settings================#
# Should make the event queue feeding this baby LIFO
    def change_settings(self, kwargs):
        for i in kwargs:
            self.st[i] = kwargs[i]

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        self.error.emit('Process Starting!')
        self.mainTime.start()
#       frame1 = self.prepare_frame()
#       frame2 = self.prepare_frame()
#       self.handlerinitSig.emit(frame1, frame2)
        self.frame = self.prepare_frame()
        self.frametime = time.time()
        self.next_frame()

    def next_frame(self):
        QCoreApplication.processEvents()
        while time.time() - self.frametime < 0.05:
            QThread.msleep(5)
        if self.st['IMAGEUPDATES'] <= self.st['RUNFRAMES']:
            self.error.emit('Run finished')
            self.finished.emit()
            return
        if QThread.currentThread().isInterruptionRequested():
            self.error.emit('Interrupted')
            self.finished.emit()
            return
        if not self.st['RUN'] and not self.st['EQUILIBRATE'] and not self.st['CLEAR']:
            self.error.emit('Nothing happening!')
            self.finished.emit()
            return
        self.handlerSig.emit(self.frame)
        self.frame = self.prepare_frame()
        self.frametime = time.time()

    def prepare_frame(self):
        frame={
            'n':self.st['N'],
            'd':self.st['D'],
            'threshold':self.st['THRESHOLD'],
            'noisesteps':0,
            'isingupdates':0,
            'conwayrules':[],
            'beta':self.st['BETA'],
            'ub':self.st['UB'],
            'rb':self.st['RB'],
            'db':self.st['DB'],
            'lb':self.st['LB'],
            'wolfpole':self.st['WOLFPOLARITY'],
            'wolfpos':0,
            'wolfscale':self.st['WOLFSCALE'],
            }
        self.wavecounter += self.st['WOLFSCALE']
        self.wavecounter %= self.st['N']
        frame['wolfpos'] = self.wavecounter
        if self.st['WOLFWAVE'] == 0:
            frame['wolfpole'] = -1
        if self.st['EQUILIBRATE']:
            frame['conwayrules'] = []
            frame['isingupdates'] = self.st['LONGNUM']
        if self.st['CLEAR']:
            frame['conwayrules'] = []
            frame['isingupdates'] = 0
            frame['noisesteps'] = 1
            self.st['RUNFRAMES'] += 1
        if self.st['RUN']:
            rules = self.st['RULES']
            if len(rules) == 0:
                rule = []
            else:
                rule = rules[self.st['RUNFRAMES'] % len(rules)]
            if self.st['CONWAY'] and self.st['STOCHASTIC']:
                if self.st['RUNFRAMES'] % 2:
                    frame['isingupdates'] = self.st['MONTEUPDATES']
                else:
                    frame['conwayrules'] = rule
            else:
                frame['isingupdates'] = self.st['MONTEUPDATES'] * self.st['STOCHASTIC']
                frame['conwayrules'] = rule
            self.st['RUNFRAMES'] += 1
        return frame
