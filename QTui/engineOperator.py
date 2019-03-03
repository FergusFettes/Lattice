from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from QTui.imageProcessing import *
from QTui.taskman import *
from QTui.graphs import *

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
        QObject.__init__(self)
        self.st = st
        self.canvas = canvas
        self.frameLabel = frameLabel
        self.arrayfpsLabel = arrayfpsLabel
        self.canvasfpsLabel = canvasfpsLabel
        self.mainUpdates = 0

        self.taskman_init()

#=============Thread Communicators======#
    def reset_gifcount(self):
        self.gifresetSig.emit()

#===============Run Initiators=============#
    def dynamic_run(self):
        self.taskthread.requestInterruption()
        self.st.general.running = True
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
        self.taskman = RunController(self.st)
        self.taskman.moveToThread(self.taskthread)

        self.taskthread.started.connect(self.taskman.process)
        self.taskman.finished.connect(self.taskthread.quit)

        # Signals from the workers back to the GUI
        self.taskman.frameSig.connect(self.frame_value_update)
        self.handler.arrayfpsSig.connect(self.array_fps_update)
        self.image.canvasfpsSig.connect(self.canvas_fps_update)
        self.taskman.error.connect(self.error_string)
        self.image.imageSig.connect(self.canvas.paint)
