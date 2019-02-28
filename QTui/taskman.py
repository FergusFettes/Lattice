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
class RunController(QObject):
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, st):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = st

        self.st.general.rundone = 0

        self.array = super().resize_array(st.canvas.dim)
        self.fpsRoll = np.zeros(9, float)

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        QCoreApplication.processEvents()
        if self.st.general.rundone == 0:
            self.init_new_process()
        else:
            self.next_frame()

    def init_new_process(self):
        frame1 = self.prepare_frame()
        self.st.general.rundone += 1
        frame2 = self.prepare_frame()
        self.st.general.rundone += 1
        self.handlerinitSig.emit(frame1, frame2, self.st.canvas.dim)
        self.frame = self.prepare_frame()
        self.frametime = time.time()

    def next_frame(self):
        QCoreApplication.processEvents()
        while time.time() - self.frametime < self.st.general.frametime:
            QThread.msleep(1)
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
            'isingupdates':0,
            'beta':self.st.ising.beta,
            'conwayrules':[],
            'bounds':[], #TODO:
            'bars':[], #TODO:
            'fuzz':[], #TODO:
            }
        frame['isingupdates'] = self.st.ising.updates * self.st.general.stochastic
        frame['conwayrules'] = rules
        return frame

    def updater_start(self, frame1, frame2, dim):
        if not self.array.shape == tuple(dim):
            self.array = super().resize_array(dim)
        self.array = super().process(frame1, self.array)
        self.arrayinitSig.emit(self.array, frame1['wolfpos'], dim)
        self.array = super().process(frame2, self.array)

    #TODO: This is what the basic head neads to have in it
    def next_array(self, frame):
        now = time.time()
        self.arraySig.emit(self.array, frame['wolfpos'], frame['dim'])
        self.array = super().process(frame, self.array)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.arrayfpsSig.emit(np.mean(self.fpsRoll))


class Analyser(QObject, pureHandler):
    popSig = pyqtSignal(np.ndarray, str)
    radSig = pyqtSignal(np.ndarray, str)
    nextarraySig = pyqtSignal()


    def __init__(self, st):
        QObject.__init__(self)

        self.st = st
        super().clear()

    def process(self, array):
        super().analyse(array)
        center,population,radius = super().export()
        self.popSig.emit(population, 'p1')
        self.radSig.emit(radius, 'p2')
        self.nextarraySig.emit()

class ImageCreator(QObject, pureHandler):
    imageSig = pyqtSignal(QPixmap)
    analyseSig = pyqtSignal(np.ndarray)
    breakSig = pyqtSignal()
    error = pyqtSignal(str)
    finished = pyqtSignal()
    canvasfpsSig = pyqtSignal(float)

    def __init__(self, st):
        QObject.__init__(self)

        self.error.emit('Image thread starting up!')
        self.colorList = st.canvas.colorlist
        self.wolfram_color_offset = 2
        self.resize_image(st.canvas.dim)

        self.scale = st.canvas.scale
        self.fpsRoll = np.zeros(9, float)
        self.st = st

        self.savecount = 0

    def reset_gifcount(self):
        self.savecount = 0

    # Resize/reset
    # Image and array have the same size, should be resized in one function.
    def resize_image(self, dim):
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.imageDim = dim

#===============Array processing and Image export=============#
    def send_image(self, image):
        ims = image.scaled(QSize(self.st.canvas.dim[0] * self.st.canvas.scale,
                                 self.st.canvas.dim[1] * self.st.canvas.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)
        if self.st.canvas.record:
            ims.save('images/temp{:>04d}.png'.format(self.savecount), 'PNG')
            self.savecount += 1

    def processer_start(self, array, pos, dim):
        self.resize_image(dim)
        self.wavecounter = pos
        super().make_wolf(True, dim, self.st.wolfram.scale, self.st.wolfram.rule)
        super().save_array(array)
        self.process_array(array)
        self.analyseSig.emit(array)

    def process(self, array, pos, dim):
        if not self.imageDim == dim:
            self.resize_image(dim)
        self.send_image(self.image)
        self.analyseSig.emit(array)
        self.wavecounter = pos
        self.process_array(array)

    def process_array(self, array):
        now = time.time()
        change = super().change(array)
        self.export_list(change)
        if self.st.general.wolfwave:
            self.wolfram_scroll()
        super().save_array(array)
        self.fpsRoll[0] = time.time()-now
        self.fpsRoll = np.roll(self.fpsRoll, 1)
        self.canvasfpsSig.emit(np.mean(self.fpsRoll))
