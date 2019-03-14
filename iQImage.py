import random as ra
import array
import numpy as np
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtWidgets import QLabel, QApplication, QMainWindow, QDockWidget
from PyQt5.QtCore import Qt, QCoreApplication, QSize, QByteArray, QByteArray

import src.Cfuncs as cf
import src.Cyarr as cy
import src.Cyphys as cph
import src.Pfuncs as pf
import src.PHifuncs as phi

siz = [100, 100]

dim = array.array('i', siz)
buf = cf.init_array_buffer(dim, 10)
buf_stat = np.zeros((1, 10), np.intc)
arr = buf[0]
cy.clear_array(dim, arr)
cf.add_global_noise(0.5, dim, arr)

pos = array.array('i', [0, 0])
rules = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [0, 1, 0, 1])
bars = np.array([
                [0, 4, 1, 0, 1, 1],
                [0, 4, 1, 1, 1, -1],
                ], np.double)
fuzz = np.array([
                [70, 7, 0, 0, 1, 1],
                [0, 4, 1, 1, 1, -2],
                ], np.double)
roll = array.array('i', [1, 1])


colHex1 = int(ra.random() * int('0xffffffff', 16))
colHex2 = int(ra.random() * int('0xffffffff', 16))
colHex3 = int(ra.random() * int('0xffffffff', 16))
colHex4 = int(ra.random() * int('0xffffffff', 16))
colorlist = np.asarray([colHex1, colHex2, colHex3, colHex4], np.intc)
L = np.random.randint(0, dim[0], (2 * dim[0] * dim[1]), np.intc).reshape((1 * dim[0] * dim[1]), 2)
image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
scale = np.asarray(4, np.intc)


#====================The canvas=================#
class Canvas(QLabel):

    def __init__(self):
        super().__init__()
        self.primaryColor = QColor(colorlist[0])
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(dim[0] * scale,
                               dim[1] * scale))
        self.pixmap().fill(self.primaryColor)

    def paint(self, image):
        self.setPixmap(image)
        self.repaint()

class MainWindow(QMainWindow):
    """
    The Main GUI window. This class contains all the QT code for the UI and all the
    functions that controll the simulation. It is pretty unwieldy. I wouldn't make
    half of these mistakes next time, but this is what it is. Lets let it be for now.
    """

    def __init__(self):
        super().__init__()

        self.canvas = Canvas()
        self.CanvasDock = QDockWidget()
        self.CanvasDock.setWidget(self.canvas)
        self.setCentralWidget(self.CanvasDock)
        self.show()
        self.setWindowRole('popup')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()

    def send_image(self):
        ims = image.scaled(QSize(dim[0] * scale,
                                 dim[1] * scale))
        nupix = QPixmap()
        nupix.convertFromImage(ims)
        self.canvas.paint(nupix)

app = QApplication([])
w = MainWindow()
app.exec()
