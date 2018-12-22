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
    backgroundSig = pyqtSignal()
    plainSig = pyqtSignal(int)

    def __init__(self, canvas, frameLabel, arrayfpsLabel, canvasfpsLabel, **kwargs):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        QObject.__init__(self)
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

    def clear_background(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=False)
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.backgroundSig.emit()
        self.thread2.start()

    def clear_array(self):
        self.thread.requestInterruption()
        self.update_kwargs(RUN=False, CLEAR=True)
        self.settingsSig.emit({i:self.kwargs[i] for i in self.kwargs})
        self.plainSig.emit(self.kwargs['N'])
        self.thread2.start()
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
#==================HERE BE DRAGONS============#
    def taskman_init(self):
        # Initialise the threads and the workers, and put them in place
        self.thread = QThread()
        self.thread2 = QThread()
        self.handler = Handler(**self.kwargs)
        self.taskman = RunController(**self.kwargs)
        self.image = ImageCreator(**self.kwargs)
        self.taskman.moveToThread(self.thread)
        self.handler.moveToThread(self.thread)
        self.image.moveToThread(self.thread2)

        self.thread.started.connect(self.taskman.process)
        self.thread2.started.connect(self.image.process)
        self.handler.startSig.connect(self.thread2.start)

        # Connections from the engine to the workers
        self.settingsSig.connect(self.taskman.change_settings)
        self.settingsSig.connect(self.image.change_settings)
        self.interruptSig.connect(self.breaker)
        self.backgroundSig.connect(self.image.wolfram_paint)
        self.plainSig.connect(self.image.resize_array)

        # Connect up the signals between the workers
        self.taskman.isingSig.connect(self.handler.ising_process)
        self.taskman.noiseSig.connect(self.handler.noise_process)
        self.taskman.conwaySig.connect(self.handler.conway_process)
        self.taskman.handlerSig.connect(self.handler.process)
        self.taskman.clearSig.connect(self.handler.resize_array)
        self.handler.arraySig.connect(self.image.process_array)

        # Connections for closing threads WORK NECC HERE
        # Need to figure out exactly ho long a thread will stay waiting, what activates
        # it, how it proecesses signals it has recieved while it has been shutdown etc.
        # TODO
        self.taskman.finished.connect(self.thread.quit)
      # self.taskman.finished.connect(self.clear_temp_kwargs)
        self.thread.finished.connect(self.thread_looper)
#       self.image.finished.connect(self.thread2.quit)       # what happens if you remove this?
        self.image.breakSig.connect(self.breaker)

        # Signals from the workers back to the GUI
        self.taskman.frameSig.connect(self.frame_value_update)
        self.taskman.arrayfpsSig.connect(self.array_fps_update)
        self.image.canvasfpsSig.connect(self.canvas_fps_update)
        self.taskman.error.connect(self.error_string)
        self.image.error.connect(self.error_string)
        self.image.imageSig.connect(self.canvas.paint)

        self.thread.start()
