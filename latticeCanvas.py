from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

class Canvas(QLabel):

    def initialize(self, PRIMARYCOLOR=None, SECONDARYCOLOR=None, **DEFAULTS):
        self.primaryColor = QColor(PRIMARYCOLOR)
        self.secondaryColor = QColor(SECONDARYCOLOR)
        self.reset(**DEFAULTS)

    def reset(self, N=None, SCALE=None, **DEFAULTS):
        self.setPixmap(QPixmap(N * SCALE, N * SCALE))

        self.pixmap().fill(self.primaryColor)
