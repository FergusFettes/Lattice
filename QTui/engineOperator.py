from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from imageProcessing import *
from taskman import *
from graphs import *

import munch

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
    interruptSig = pyqtSignal()
    backgroundSig = pyqtSignal()
    gifresetSig = pyqtSignal()
    plainSig = pyqtSignal(list)

    def __init__(self, canvas, graphs, frameLabel, arrayfpsLabel, canvasfpsLabel, st):
    # The kwargs consists of the following: speed, updates, frames, beta,
    # stochastic?, threshold/coverage.
        QObject.__init__(self)
        self.st = st
        self.canvas = canvas
        self.graphs = graphs
        self.frameLabel = frameLabel
        self.arrayfpsLabel = arrayfpsLabel
        self.canvasfpsLabel = canvasfpsLabel
        self.mainUpdates = 0

        self.taskman_init()

#=============Thread Communicators======#
    def reset_gifcount(self):
        self.gifresetSig.emit()

    def breaker(self):
        print('Breaker!')
        self.st.general.running = False
        self.st.general.equilibrate = False
        self.st.general.clear = False

    def thread_looper(self):
        print('Thread standing by.')

#===============Run Initiators=============#
    def static_run(self):
        self.taskthread.requestInterruption()
        self.st.general.running = True
        self.st.general.equilibrate = False
        self.st.general.clear = False
        self.st.general.rundone = -2
        self.taskthread.start()

    def dynamic_run(self):
        self.taskthread.requestInterruption()
        self.st.general.running = True
        self.st.general.equilibrate = False
        self.st.general.clear = False
        self.taskthread.start()

    def long_run(self):
        self.taskthread.requestInterruption()
        self.st.general.running = False
        self.st.general.equilibrate = True
        self.st.general.clear = False
        self.st.general.rundone = -3
        self.taskthread.start()

    def clear_background(self):
        self.backgroundSig.emit()
        self.imagethread.start()

    def clear_array(self):
        self.taskthread.requestInterruption()
        self.st.general.running = False
        self.st.general.equilibrate = False
        self.st.general.clear = True
        self.st.general.rundone = -3
        self.plainSig.emit(self.st.canvas.dim)
        self.imagethread.start()
        self.taskthread.start()

#===============GUI updaters=============#
    def array_fps_update(self, value):
        if value:
            self.arrayfpsLabel.setText('Array fps: {:03.3f}'.format(1 / value))

    def canvas_fps_update(self, value):
        if value:
            self.canvasfpsLabel.setText('Canvas fps: {:03.3f}'.format(1 / value))

    def frame_value_update(self, value):
        self.frameLabel.setText('Frames: {:04d}/'.format(value))
        if not value % 10:
            self.st.general.rundone = value

    def error_string(self, error='Unlabelled Error! Oh no!'):
        print(error)

#=================Thread Initiator============#
#==================HERE BE DRAGONS============#
    def taskman_init(self):
        # Initialise the threads and the workers, and put them in place
        self.taskthread = QThread()
        self.imagethread = QThread()
        self.updatethread = QThread()
        self.analysisthread = QThread()
        self.handler = Handler(self.st)
        self.taskman = RunController(self.st)
        self.image = ImageCreator(self.st)
        self.analyser = Analyser(self.st)
        self.taskman.moveToThread(self.taskthread)
        self.handler.moveToThread(self.updatethread)
        self.image.moveToThread(self.imagethread)
        self.analyser.moveToThread(self.analysisthread)

        self.taskthread.started.connect(self.taskman.process)
        self.taskthread.started.connect(self.imagethread.start)
        self.taskthread.started.connect(self.updatethread.start)
        self.taskthread.started.connect(self.analysisthread.start)

        # Connections from the engine to the workers
        self.interruptSig.connect(self.breaker)
        self.backgroundSig.connect(self.image.wolfram_paint)
        self.plainSig.connect(self.image.resize_array)
        self.gifresetSig.connect(self.image.reset_gifcount)

        # Connect up the signals between the workers
        self.taskman.handlerSig.connect(self.handler.next_array)
        self.taskman.handlerSingleSig.connect(self.handler.push_single_array)
        self.taskman.handlerinitSig.connect(self.handler.updater_start)
        self.handler.arraySig.connect(self.image.process)
        self.handler.arraySingleSig.connect(self.image.process_single)
        self.handler.arrayinitSig.connect(self.image.processer_start)
        self.image.analyseSig.connect(self.analyser.process)
        self.analyser.nextarraySig.connect(self.taskman.next_frame)

        # Connections for closing threads WORK NECC HERE
        # Need to figure out exactly ho long a thread will stay waiting, what activates
        # it, how it proecesses signals it has recieved while it has been shutdown etc.
        # TODO
        self.taskman.finished.connect(self.taskthread.quit)
        self.taskman.finished.connect(self.updatethread.quit)
        self.taskman.finished.connect(self.imagethread.quit)
        self.taskman.finished.connect(self.analysisthread.quit)
        self.taskthread.finished.connect(self.thread_looper)
        self.image.breakSig.connect(self.breaker)
        self.taskman.breakSig.connect(self.breaker)

        # Signals from the workers back to the GUI
        self.taskman.frameSig.connect(self.frame_value_update)
        self.handler.arrayfpsSig.connect(self.array_fps_update)
        self.image.canvasfpsSig.connect(self.canvas_fps_update)
        self.taskman.error.connect(self.error_string)
        self.image.error.connect(self.error_string)
        self.handler.error.connect(self.error_string)
        self.image.imageSig.connect(self.canvas.paint)
        self.analyser.popSig.connect(self.graphs.paint)
        self.analyser.radSig.connect(self.graphs.paint)