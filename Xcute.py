#!/usr/bin/python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import random as ra
from munch import *
from yaml import safe_load



# Draws the main window and contains the simulation code
class MainWindow(QMainWindow):

    def __init__(self, st):
        super().__init__()

        self.st = st
        self.canvas = QLabel()
        self.canvas.primaryColor = QColor(st.canvas.colorlist[0])
        self.canvas.colorList = []
        self.canvas.setPixmap(QPixmap(self.st.canvas.dim[0] * self.st.canvas.scale,
                                self.st.canvas.dim[1] * self.st.canvas.scale))
        self.canvas.pixmap().fill(self.canvas.primaryColor)

#========================================================CanvasDock
        #Wrap that all up in a DockWidget
        self.CanvasDock = QDockWidget()
        self.buts = {'canvas': self.CanvasDock}
        self.CanvasDock.setWidget(self.canvas)
        self.setCentralWidget(self.CanvasDock)
#............................................................

        self.show()
        self.setWindowRole('popup')

    def paint(self, image):
        self.canvas.setPixmap(image)
        self.canvas.repaint()

    def keyPressEvent(self, e):
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
