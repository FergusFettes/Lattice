from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import array
import time

import src.Cfuncs as cf
import src.Cyarr as cy
#import src.Cyphys as cph
import src.Pfuncs as pf
import src.PHifuncs as phi

##===============TaskManager===============##
##=========================================##
# This fancy chap goes into the thread with all the workers and controls what they do
# Also inherits the array handler so it can send and recieve arrays.
# All signals come in and out of this guy.
class RunController(QObject):
    popSig = pyqtSignal(np.ndarray, str)
    radSig = pyqtSignal(np.ndarray, str)
    imageSig = pyqtSignal(QPixmap)
    frameSig = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, st):
        """Run controller makes sure the run doesnt get out of hand"""
        QObject.__init__(self)
        self.st = st

        self.st.general.rundone = 0
        self.colorList = st.canvas.colorlist
        self.wolfram_color_offset = 2
        self.resize_image(st.canvas.dim)

        self.scale = st.canvas.scale
        self.fpsRoll = np.zeros(9, float)
        self.st = st

        self.savecount = 0

        self.dim = array.array('i', st.canvas.dim)
        self.buf_len = 10
        self.buf_stat = np.zeros(self.buf_len, np.intc)
        self.buf_stat[0] = 1
        self.head_position = array.array('i', [0, 0])
        self.tail_position = array.array('i', [0, 0])

        self.buf = cf.init_array_buffer(self.dim, self.buf_len)
        self.arr_h = self.buf[self.head_position[0] % self.buf_len]
        self.arr_t = self.buf[self.tail_position[0] % self.buf_len]

        # Process a few frames on startup
        for _ in range(3):
            cy.clear_array(self.dim, self.arr_h)
            cf.advance_array(self.head_position, self.buf_len, self.buf)
            self.arr_h = cf.update_array_positions(self.head_position, self.buf_len,
                                                self.buf_stat, self.buf, 0)
        self.buf_stat[1] = 2 #placing the tail
        self.fpsRoll = np.zeros(9, float)

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
#       QCoreApplication.processEvents()
        self.error.emit('Process starting!')
        while True:
            now = time.time()

            kwargs = self.prepare_frame()
            cy.roll_rows_pointer(-1, kwargs['dim'], kwargs['arr_h'])
            cf.basic_update_buffer(
                kwargs['updates'],
                kwargs['beta'],
                kwargs['threshold'],
                kwargs['rules'],
                kwargs['head_position'],
                kwargs['buffer_length'],
                kwargs['dim'],
                kwargs['arr_h'],
                kwargs['buf'],
                kwargs['bounds'],
                kwargs['bars'],
                kwargs['fuzz'],
            )
            kwargs['arr_h'] = cf.update_array_positions(
                kwargs['head_position'],
                kwargs['buffer_length'],
                kwargs['buffer_status'],
                kwargs['buf'],
                0
            )
            cy.set_bounds(kwargs['bounds'][0], kwargs['bounds'][1], kwargs['bounds'][2],
                          kwargs['bounds'][3], kwargs['dim'], kwargs['arr_t'])
            cy.scroll_bars(kwargs['dim'], kwargs['arr_t'], kwargs['bars'])
            cf.scroll_noise(kwargs['dim'], kwargs['arr_t'], kwargs['fuzz'])

            arr_t_old = self.buf[(self.tail_position[0] - 1) % self.buf_len]
            b, d = pf.get_births_deaths_P(arr_t_old, kwargs['arr_t'])
            self.replace_image_positions(self, b, 0)
            self.replace_image_positions(self, d, 0)
            self.send_image()

            cf.scroll_instruction_update(
                kwargs['bars'], kwargs['dim_t']
            )
            cf.scroll_instruction_update(
                kwargs['fuzz'], kwargs['dim_t']
            )
            kwargs['arr_t'] = cf.update_array_positions(
                kwargs['tail_position'],
                kwargs['buffer_length'],
                kwargs['buffer_status'],
                kwargs['buf_t'],
                0
            )

            self.fpsRoll[0] = time.time()-now
            self.fpsRoll = np.roll(self.fpsRoll, 1)
            self.arrayfpsSig.emit(np.mean(self.fpsRoll))

    def prepare_frame(self):
        kwargs={
            'dim':np.asarray(self.st.canvas.dim, np.intc),
            'threshold':self.st.noise.threshold,
            'updates':self.st.ising.updates,
            'beta':self.st.ising.beta,
            'rules':np.asarray(self.st.conway.rules, np.intc),
            'bounds':np.asarray(self.st.bounds, np.intc),
            'bars':np.asarray(self.st.scroll.bars, np.double),
            'fuzz':np.asarray(self.st.scroll.fuzz, np.double),
            'head_position':np.asarray(self.head_position, np.intc),
            'tail_position':np.asarray(self.tail_position, np.intc),
            'buffer_length':np.asarray(self.buf_len, np.intc),
            'buffer_status':np.asarray(self.buf_stat, np.intc),
            'dim':np.asarray(self.dim, np.intc),
            'arr_h':np.asarray(self.arr_h, np.intc),
            'buf':np.asarray(self.buf, np.intc),
            'arr_t':np.asarray(self.arr_t, np.intc),
        }
        return kwargs

    # Resize/reset
    # Image and array have the same size, should be resized in one function.
    def resize_image(self, dim):
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.imageDim = dim

#===============Array processing and Image export=============#
    def send_image(self):
        ims = self.image.scaled(QSize(self.st.canvas.dim[0] * self.st.canvas.scale,
                                 self.st.canvas.dim[1] * self.st.canvas.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)

    #TODO: surely I can just use the array as an image directly? This is rediculous.
    def export_array(self, A, color_offset):
        """
        Updates the image with the values from an entire array.

        :param self:
        :param A:               Array to use as new image
        :param color_offset:    Use primary colors (0) or secondary colors (2)?
        :return:                None
        """
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                num = int(A[i][j])
                color = self.canvas.colorList[num + color_offset]
                self.image.setPixel(i, j, color)

    def replace_image_positions(self, L, color):
        """
        Updates the given positions with the specified color

        :param L:       List of positions to update
        :param color:   selection from colorlist
        :return:        None
        """
        [self.image.setPixel(el[0], el[1], self.canvas.colorList[color]) for el in L]
