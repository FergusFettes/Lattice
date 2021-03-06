#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from QTui.GUI import MainWindow
import random as ra
from munch import *
from yaml import safe_load

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
