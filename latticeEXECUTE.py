#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from latticeGUI import MainWindow
import random as ra


def initVars():
    # TODO: add a load function here
    colHex1 = int(ra.random() * int('0xffffffff', 16))
    colHex2 = int(ra.random() * int('0xffffffff', 16))
    DEF = {
        'BACKCOLOR1':   QColor.fromRgba(colHex1).name(),    # These are just random rn
        'BACKCOLOR2':   QColor.fromRgba(colHex2).name(),
        'UPDATECOLOR1': QColor.fromRgba(colHex1).name(),    # To make fancy transitions,
        'UPDATECOLOR2': QColor.fromRgba(colHex2).name(),    # change these.
        'MOUSECOLOR1':  QColor.fromRgba(colHex1).name(),    # Not used rn. But soon?
        'MOUSECOLOR2':  QColor.fromRgba(colHex2).name(),
        'SATURATION':   80,     # This leaves changes on the image shortly
        'N':            350,    # Array dimensions
        'SCALE':        2,      # Image dim = N*SCALE x N*SCALE
        'BETA':         1 / 8,  # Critical temp for Ising
        'SPEED':        100,    # Throttle %
        'DEGREE':       4,      # Degree of the Potts model
        'IMAGEUPDATES': 60,    # Number of frames to run
        'RUNFRAMES':    0,      # Frames in current run
        'MONTEUPDATES': 333,    # MonteCarlo updates per frame
        'LONGNUM':      100000, # MonteCarlo update to equilibrium
        'THRESHOLD':     0.1,   # Threshold for clear/noise (sigmoid function)
        'NEWARR':       1,      # New array upon engine creation?
        'STOCHASTIC':   True,   # Noise on?
        'CONWAY':       True,   # Conway on?
        'EQUILIBRATE':  False,  # Equilibrate array?
        'CLEAR':        False,  # Clear array?
                                # Update rules for conway
        'RULES':        [[3,6,2,2]\
                         [3,6,3,3]\
                         [3,4,3,3]\
                         [3,4,2,2]]
    }
    return DEF


if __name__ == '__main__':

    app = QApplication([])
    DEFAULTS = initVars()
    w = MainWindow(**DEFAULTS)
    app.exec()
