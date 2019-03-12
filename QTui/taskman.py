from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import array
import time

import src.Cfuncs as cf
import src.Cyarr as cy
import src.Cyphys as cph
import src.Pfuncs as pf
import src.PHifuncs as phi

import logging
LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

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

        self.fpsRoll = np.zeros(9, float)
        self.st = st

        self.savecount = 0

    def initialize_buffers(self, st):
        self.imageDim = np.asarray(st.canvas.dim)
        self.imageScale = np.asarray(st.canvas.scale)

        if self.st.general.growth:
            dim = array.array('i', [20, 20])
            rand_center = 10
            self.resize_image(dim)
        else:
            dim = array.array('i', st.canvas.dim)
            rand_center = 0
            self.resize_image(dim)
        self.change_roll, self.head_position, self.tail_position,\
            self.buf_len, self.buf_stat,\
            self.dim_t, self.arr_t, self.buf_t,\
            self.dim_h, self.arr_h, self.buf_h = cf.init([dim[0], dim[1]], 10, rand_center)

        self.export_array(self.arr_h, 0)

#===============MAIN PROCESS OF THE THREAD===================#
    def process(self):
        self.error.emit('Proccess starting!')
        self.initialize_buffers(self.st)
        kwargs = self.prepare_frame()
        if self.st.general.growth: kwargs = self.growth_mode(kwargs)
        self.buffer_storage = {}

        while kwargs['running']:
            start = time.time()
            kwargs = self.update_frame(kwargs)
            if kwargs['update_settings']: kwargs = self.update_rules(kwargs)
            if self.st.general.growth: kwargs = self.growth_mode(kwargs)

            self.basic_update(kwargs)
            self.buffer_handler_head(kwargs)
            if kwargs['dim_h'][0] < 4:
                logging.info('Run breaking!')
                break
            self.image_processing(kwargs)
            self.buffer_handler_tail(kwargs)

            while time.time() - start < kwargs['frametime']: time.sleep(0.01)

        self.finished.emit()

    def basic_update(self, kwargs):
        logging.debug('Basic update')
        cf.ising_process(kwargs['updates'], kwargs['beta'], kwargs['dim_h'], kwargs['arr_h'])
        cf.add_stochastic_noise(kwargs['threshold'], kwargs['dim_h'], kwargs['arr_h'])
        cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
        cy.roll_columns_pointer(kwargs['roll'][0], kwargs['dim_h'], kwargs['arr_h'])
        cy.roll_rows_pointer(kwargs['roll'][1], kwargs['dim_h'], kwargs['arr_h'])
        cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
        cy.scroll_bars(kwargs['dim_h'], kwargs['arr_h'], kwargs['bars'])
        cf.scroll_noise(kwargs['dim_h'], kwargs['arr_h'], kwargs['fuzz'])
        cf.conway_process(cf.prepair_rule(kwargs['rules'], kwargs['head_position']),
                        kwargs['dim_h'], kwargs['arr_h'])
        cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
        if self.st.general.growth:
            _, _ = phi.recenter(
                cph.center_of_mass(kwargs['dim_h'], kwargs['arr_h']),
                kwargs['dim_h'], kwargs['arr_h'])

    def buffer_handler_head(self, kwargs):
        """
        Checks the array is the right size (if necc) and returns a new dim-buffer pair.
        Extends the buffer status to suit.
        Advances the array in the [new] buffer, and returns a new array while updating
        the head position.

        After this function, the array has been copied into the next position
        (possibly on a new array) and the head pointers have been updated.
        Head_position and buffer_status should be accurate.
        """
        if self.st.general.growth:
            logging.debug('Change zoom level')
            kwargs['dim_h'], kwargs['buf_h'], kwargs['change_roll'],\
                kwargs['buffer_status'] = cf.change_zoom_level(
                kwargs['head_position'], kwargs['buffer_length'],
                kwargs['buffer_status'], kwargs['change_roll'],
                kwargs['dim_h'], kwargs['buf_h']
            )
            if kwargs['change_roll'][0, 1]:
                self.buffer_storage.update(
                    {kwargs['change_roll'][0, 0]:(kwargs['dim_h'], kwargs['buf_h'])}
                )

        logging.debug('Update array positions')
        cf.advance_array(kwargs['head_position'], kwargs['buffer_length'], kwargs['buf_h'])
        kwargs['arr_h'] = cf.update_array_positions(
            kwargs['head_position'],
            kwargs['buffer_length'],
            kwargs['buffer_status'],
            kwargs['buf_h'],
            0
        )

    def image_processing(self, kwargs):
        cy.scroll_bars(kwargs['dim_t'], kwargs['arr_t'], kwargs['bars'])
        cf.scroll_noise(kwargs['dim_t'], kwargs['arr_t'], kwargs['fuzz'])
        cf.export_array(self.image, kwargs['colorlist'], kwargs['dim_t'], kwargs['arr_t'], 0)
        logging.debug('Sending image')
        self.send_image()

    def buffer_handler_tail(self, kwargs):
        if self.st.general.growth:
            logging.debug('Updating tail position')
            change_here = np.argwhere(kwargs['change_roll'][:, 0]==kwargs['tail_position'][0])
            if change_here.any():
                change_here = change_here[0][0]
                kwargs['tail_position'][1] += abs(kwargs['change_roll'][change_here, 1])

        logging.debug('Updating scroll instructions')
        cf.scroll_instruction_update(
            kwargs['bars'], kwargs['dim_t']
        )
        cf.scroll_instruction_update(
            kwargs['fuzz'], kwargs['dim_t']
        )
        logging.debug('Updating tail position')
        kwargs['arr_t'] = cf.update_array_positions(
            kwargs['tail_position'],
            kwargs['buffer_length'],
            kwargs['buffer_status'],
            kwargs['buf_t'],
            0
        )

        # if tail has changed, you need to prepair to delete the first buffer
        if self.st.general.growth and change_here.any():
            if kwargs['change_roll'][change_here, 1]:
                dim, buf = self.buffer_storage.pop(kwargs['change_roll'][change_here, 0])
                kwargs['buf_t'] = buf
                kwargs['dim_t'] = dim
                kwargs['arr_t'] = kwargs['buf_t'][kwargs['tail_position'][0] %\
                                                  kwargs['buffer_length']]
                kwargs['head_position'][1] -= 1
                kwargs['tail_position'][1] -= 1
                kwargs['buffer_status'] = cf.extend_buffer_status(kwargs['head_position'],
                                    kwargs['buffer_length'], kwargs['buffer_status'])
                self.image = QImage(kwargs['dim_t'][0], kwargs['dim_t'][1],
                                    QImage.Format_ARGB32)

    def update_frame(self, kwargs):
        kwargs.update({
            'running':self.st.general.running,
            'update_settings':self.st.general.update,
        })
        return kwargs

    def update_rules(self, kwargs):
        if self.st.general.resize:
            self.st.general.resize = False
            self.initialize_buffers(self.st)
            return self.prepare_frame()
        self.st.general.update = False
        kwargs.update({
            'running':self.st.general.running,
            'frametime':self.st.general.frametime,
            'update_settings':self.st.general.update,
            'colorlist':np.asarray(self.st.canvas.colorlist, np.intc),
            'threshold':self.st.noise.threshold,
            'updates':self.st.ising.updates,
            'beta':self.st.ising.beta,
            'rules':np.asarray(self.st.conway.rules, np.intc),
            'bounds':np.asarray(self.st.bounds, np.intc),
            'bars':np.asarray(self.st.scroll.bars, np.double),
            'fuzz':np.asarray(self.st.scroll.fuzz, np.double),
            'roll':np.asarray(self.st.transform.roll, np.intc),
        })
        return kwargs

    def growth_mode(self, kwargs):
        kwargs.update({
            'bounds':array.array('i', [-1, -1, -1, -1]),
            'roll':array.array('i', [0, 0]),
        })
        for i in range(len(kwargs['bars'])):
            kwargs['bars'][i, -1] = -1
        for i in range(len(kwargs['fuzz'])):
            kwargs['fuzz'][i, -1] = -2
        return kwargs

    def prepare_frame(self):
        kwargs={
            'running':self.st.general.running,
            'frametime':self.st.general.frametime, #NB: to get the to update in realtime, just use the original value
            'update_settings':self.st.general.update,
            'colorlist':np.asarray(self.st.canvas.colorlist, np.intc),
            'threshold':self.st.noise.threshold,
            'updates':self.st.ising.updates,
            'beta':self.st.ising.beta,
            'rules':np.asarray(self.st.conway.rules, np.intc),
            'bounds':np.asarray(self.st.bounds, np.intc),
            'bars':np.asarray(self.st.scroll.bars, np.double),
            'fuzz':np.asarray(self.st.scroll.fuzz, np.double),
            'roll':np.asarray(self.st.transform.roll, np.intc),
            'head_position':np.asarray(self.head_position, np.intc),
            'tail_position':np.asarray(self.tail_position, np.intc),
            'buffer_length':np.asarray(self.buf_len, np.intc),
            'buffer_status':np.asarray(self.buf_stat, np.intc),
            'change_roll':np.asarray(self.change_roll, np.intc),
            'dim_h':self.dim_h,
            'arr_h':self.arr_h,
            'buf_h':self.buf_h,
            'dim_t':self.dim_t,
            'arr_t':self.arr_t,
            'buf_t':self.buf_t,
        }
        return kwargs

    # Resize/reset
    # Image and array have the same size, should be resized in one function.
    def resize_image(self, dim):
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.send_image()

#===============Array processing and Image export=============#
    def send_image(self):
        ims = self.image.scaled(QSize(self.imageDim[0] * self.imageScale,
                                self.imageDim[1] * self.imageScale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.imageSig.emit(nupix)

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
                color = self.colorList[num + color_offset]
                self.image.setPixel(i, j, color)

    def replace_image_positions(self, L, color):
        """
        Updates the given positions with the specified color

        :param L:       List of positions to update
        :param color:   selection from colorlist
        :return:        None
        """
        [self.image.setPixel(el[0], el[1], self.colorList[color]) for el in L]
