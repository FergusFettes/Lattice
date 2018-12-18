#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from latticeGUI import MainWindow
import random as ra

def initVars():
    # TODO: add a load function here
    colHex1 = int(ra.random() * int('0xffffffff', 16))
    colHex2 = int(ra.random() * int('0xffffffff', 16))
    DEF = {
        'PRIMARYCOLOR':QColor.fromRgba(colHex1).name(),   # These are just random rn
        'SECONDARYCOLOR':QColor.fromRgba(colHex2).name(),
        'ALLUP':0,      # Ising starts homogeneous?
        'N':300,        # Array dimensions
        'SCALE':2,      # Image dim = N*SCALE x N*SCALE
        'BETA':1 / 8,   # Critical temp for Ising
        'SPEED':100,     # Throttle %
        'DEGREE':4,     # Degree of the Potts model
        'IMAGEUPDATES':60, # Number of frames to run
        'MONTEUPDATES':1000,# MonteCarlo updates per frame
        'EQUILIBRATE':100000,
        'COVERAGE':0.1,
        'NEWARR':1,
        'STOCHASTIC':True
    }
    TST = {
        'PRIMARYCOLOR':QColor.fromRgba(colHex1).name(),   # These are just random rn
        'SECONDARYCOLOR':QColor.fromRgba(colHex2).name(),
        'ALLUP':0,      # Ising starts homogeneous?
        'N':10,        # Array dimensions
        'SCALE':16,      # Image dim = N*SCALE x N*SCALE
        'BETA':1 / 8,   # Critical temp for Ising
        'SPEED':10,     # Throttle %
        'DEGREE':4,     # Degree of the Potts model
        'IMAGEUPDATES':60, # Number of frames to run
        'MONTEUPDATES':10,# MonteCarlo updates per frame
        'EQUILIBRATE':100000,
        'COVERAGE':5,
        'NEWARR':0.1,
        'STOCHASTIC':True
    }
    return DEF


#if __name__ == '__main__':

app = QApplication([])
DEFAULTS = initVars()
w = MainWindow(**DEFAULTS)
app.exec()
