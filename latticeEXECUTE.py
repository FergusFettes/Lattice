from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from latticeGUI import MainWindow

def initVars():
    DEF={
        'PRIMARYCOLOR':'#ffff557f',   # These are just random rn
        'SECONDARYCOLOR':'#ffffffa0',
        'ALLUP':0,      # Ising starts homogeneous?
        'N':150,        # Array dimensions
        'SCALE':3,      # Image dim = N*SCALE x N*SCALE
        'BETA':1 / 8,   # Critical temp for Ising
        'SPEED':60,     # Throttle %
        'DEGREE':4,     # Degree of the Potts model
        'IMAGEUPDATES':100 # Number of frames to run
    }
    return DEF


if __name__ == '__main__':

    app = QApplication([])
    DEFAULTS = initVars()
    w = MainWindow(**DEFAULTS)
    app.exec()
