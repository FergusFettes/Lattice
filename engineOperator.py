from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from updaters import *
from imageProcessing import *

import numpy as np
import time
import sys
import queue as queue

# TODO: get a threadpool on the go so you dont need to artifically keep the thread alive
# TODO: use pythons 'queue' to move settings into the task managet in a timely fashion
# TODO: maybe use a mutex to share the array with the canvas? maybe not necc.
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
        self.taskman.isingSig.connect(self.handler.ising_process)
        self.taskman.noiseSig.connect(self.handler.noise_process)
        self.taskman.conwaySig.connect(self.handler.conway_process)
        self.taskman.handlerSig.connect(self.handler.process)

        self.image = ImageCreator(self.array, **self.kwargs)
        self.thread2 = QThread()
        self.image.moveToThread(self.thread2)
        self.thread2.started.connect(self.image.process)
        self.image.error.connect(self.error_string)
        self.image.finished.connect(self.thread2.quit)       # what happens if you remove this?
        self.handler.startSig.connect(self.thread2.start)
        self.image.imageSig.connect(self.canvas.paint)
        self.image.breakSig.connect(self.breaker)
        self.image.canvasfpsSig.connect(self.canvas_fps_update)
        self.handler.arraySig.connect(self.image.process_array)

        self.settingsSig.connect(self.taskman.change_settings)
        self.interruptSig.connect(self.breaker)

        self.thread.start()
