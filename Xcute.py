#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import src.Cfuncs as cf
import src.Cyarr as cy
import src.Cyphys as cph
import src.Pfuncs as pf
import src.PHifuncs as phi

import array
import numpy as np
import time
import random as ra
from munch import *
from yaml import safe_load



# Draws the main window and contains the simulation code
class MainWindow(QMainWindow):

    def __init__(self, st):
        super().__init__()

        # Initialize the canvas and the image object that is freely manipulated.
        self.st = st
        self.canvas = QLabel()
        self.canvas.primaryColor = QColor(st.canvas.colorlist[0])
        self.canvas.colorList = st.canvas.colorlist
        self.canvas.setPixmap(QPixmap(self.st.canvas.dim[0] * self.st.canvas.scale,
                                self.st.canvas.dim[1] * self.st.canvas.scale))
        self.canvas.pixmap().fill(self.canvas.primaryColor)

        self.initialize_image(self.st.canvas.dim)

        # Create the canvas DockWidget and place it in the window, then show the window.
        self.CanvasDock = QDockWidget()
        self.buts = {'canvas': self.CanvasDock}
        self.CanvasDock.setWidget(self.canvas)
        self.setCentralWidget(self.CanvasDock)


        # Initialize the array
        self.dim = array.array('i', [st.canvas.dim[0], st.canvas.dim[1]])
        self.arr = cf.init_array(self.dim)

        self.show()
        self.setWindowRole('popup')

        # Run a little simulation
        self.bounds = array.array('i', [st.bounds.upper, st.bounds.right,
                                        st.bounds.lower, st.bounds.left])
        self.bars = np.array(st.scroll.bars, np.intc)
        self.fuzz = np.array(st.scroll.fuzz, np.intc)
        self.rules = np.array(st.conway.rules, np.intc)

    def smolrun(self):
        while True:
            cf.add_global_noise(0.5, self.dim, self.arr)
            self.export_array(self.arr, 0)
            self.send_image(self.image)
            time.sleep(0.1)



    def run(self):
        head_position, tail_position, buffer_length, buffer_status,\
            dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init([st.canvas.dim[0],
                                                                st.canvas.dim[1]])
        cf.add_global_noise(0.5, self.dim, self.arr)
        cf.basic_update_buffer(
                        self.st.ising.updates, self.st.ising.beta,
                        self.st.noise.threshold, self.st.scroll.coverage,
                        self.rules, head_position,
                        buffer_length,
                        dim_h, arr_h, buf_h,
                        self.bounds, self.bars, self.fuzz,
                    )
        arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status,
                                          buf_h, 0)

        changes = 0
        frame = memoryview(array.array('i', [0]))
        while True:
            # analysis here
            self.export_array(arr_t, 0)
            self.send_image(self.image)
            time.sleep(0.1)
            arr_t = cf.update_array_positions(tail_position, buffer_length, buffer_status,
                                            buf_t, 0)

            cf.basic_update_buffer(
                            self.st.ising.updates, self.st.ising.beta,
                            self.st.noise.threshold, self.st.scroll.coverage,
                            self.rules, head_position,
                            buffer_length,
                            dim_h, arr_h, buf_h,
                            self.bounds, self.bars, self.fuzz,
                        )
            arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status,
                                              buf_h, 1)
            cf.scroll_instruction_update(self.bars, dim_t)
            cf.scroll_instruction_update(self.fuzz, dim_t)
            cy.roll_rows_pointer(-1, dim_h, arr_h)
            frame[0] += 1

    def initialize_image(self, dim):
        """
        Creates the QImage object and saves the dimensions.

        :param dim:         Dimensions
        :return:            None
        """
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.imageDim = dim

    def send_image(self, image):
        """
        Resizes the image and converts to pixmap before export.

        :param image:       QImage QObject, bascially a direct copy of the current array.
        :return:            None
        """
        ims = image.scaled(QSize(self.st.canvas.dim[0] * self.st.canvas.scale,
                                    self.st.canvas.dim[1] * self.st.canvas.scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.canvas.setPixmap(nupix)
        self.canvas.repaint()

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

    #TODO: split this into a killer and a placer?
    def export_list(self, L):
        """
        Updates the image with values from a 2D array of [x, y, status].

        :param L:       List of changed positions and their new status
        :return:       None
        """
        [self.image.setPixel(el[0], el[1], self.canvas.colorList[el[2]]) for el in L]

    def keyPressEvent(self, e):
        """
        Replaces the default keypress controller, allows for custom keys.
        NB: avoid bloat, use a dict if necc.

        :param self:
        :param e:       keypress
        :return:       None
        """
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()
            print('Threads shutting down and powering off')


if __name__ == '__main__':
    colHex1 = int(ra.random() * int('0xffffffff', 16))
    colHex2 = int(ra.random() * int('0xffffffff', 16))
    colHex3 = int(ra.random() * int('0xffffffff', 16))
    colHex4 = int(ra.random() * int('0xffffffff', 16))

    try:
        yaml = safe_load(open('sav/nowconf.yml'))
        st = munchify(yaml['lastsave'])
    except:
        print('No saved file, using defaults')
        yaml = safe_load(open('sav/defconf.yml'))
        st = munchify(yaml['defaults'])


    st.canvas.colorlist[0:4] = [colHex1, colHex2, colHex3, colHex4]
    app = QApplication([])
    w = MainWindow(st)
    app.exec()
    w.run()
