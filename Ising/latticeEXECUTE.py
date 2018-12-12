from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

from latticeGUI import MainWindow

if __name__ == '__main__':

    app = QApplication([])
    primaryColor = '#ffff557f'
    secondaryColor = '#ffffffa0'
    # Ising array starts out homogeneous?
    allUp = 0
    # Array dimensions
    N = 150
    # Image dimensions = N*SCALE x N*SCALE
    # You'll see this used in a few places to convert between the data arrray
    # and the image data. This took a while to figure out but was TOTALLY WORTH
    # IT.
    SCALE = 3
    # 0.1 is HOT (noisy), 0.9 is COLD (homogeneous). Play with this.
    beta = 1 / 8
    # Speed is a sort of throttle, 100 is no throttle, 1 is lots of throttle
    speed = 60
    # Degree of the Potts model
    degree = 4
    w = MainWindow()
    app.exec()
