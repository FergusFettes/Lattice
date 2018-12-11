from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()
        self.cost = np.zeros(3)
        self.cost[1] = np.exp(-4 * beta)
        self.cost[2] = self.cost[1] * self.cost[1]
        self.imageUpdates = 500
        self.monteUpdates = 1000
        self.spinArray = self.isingInit()
        self.exportArray(self.spinArray, primaryColor, secondaryColor)
        # self.redoColors(0xff00ff00, 0xff00ffff, 1)

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')

    def staticRun(self, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        self.spinArray, updateList  = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
        self.exportList(updateList, primaryColor, secondaryColor)

    def dynamicRun(self, imUp=None, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        imUp = imUp if imUp is not None else self.imageUpdates
        for _ in range(imUp):
            self.spinArray, updateList = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
            self.exportList(updateList, primaryColor, secondaryColor)
            self.repaint()

    def initUI(self):

        primary_color = QColor(Qt.black)

        self.canvas = QLabel()
        self.canvas.setPixmap(QPixmap(N * SCALE, N * SCALE))
        self.canvas.pixmap().fill(primary_color)

        short = QPushButton('Short')
        short.clicked.connect(partial(self.staticRun, None))
        dynamic = QPushButton('Dynamic')
        dynamic.clicked.connect(partial(self.dynamicRun, None, None))
        button3 = QPushButton('NIX')
        equilibrate = QPushButton('Equilibrate')
        equilibrate.clicked.connect(partial(self.staticRun, 50000))
        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        vb = QVBoxLayout()
        vb.addWidget(short)
        vb.addWidget(dynamic)
        vb.addWidget(button3)
        vb.addWidget(equilibrate)
        vb.addStretch()
        vb.addWidget(exit_button)

        hb = QHBoxLayout()
        # vb.setStretch(1, 1)
        hb.addLayout(vb)
        # canvas.setSizePolicy(QSizePolicy.setHorizontalStretch(QSizePolicy, 3))
        hb.addWidget(self.canvas)

        self.setLayout(hb)
        self.show()

    def exit_button_clicked(self):
        QCoreApplication.instance().quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()

    def isingInit(self):
        ARR = np.ones((N, N), int)
        if allUp:
            return ARR
        for i in range(0, N):
            for j in range(0, N):
                if ra.random() > 0.5:
                    ARR[i, j] = -1
        return ARR

    def MonteCarloUpdate(self, A, nSteps, cost):
        updateList=[]
        for _ in range(nSteps):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
                updateList.append([a,b,A[a][b]])
        return A, updateList

    def exportArray(self, A, color, color2):
        im = QImage((N * SCALE), (N * SCALE), QImage.Format_ARGB32)
        for i in range(N * SCALE):
            for j in range(N * SCALE):
                if A[int(i / SCALE)][int(j / SCALE)]==1:
                    im.setPixel(i, j, color)
                else:
                    im.setPixel(i, j, color2)

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)

    def exportList(self, L, color, color2):
        im = self.canvas.pixmap().toImage()
        for el in L:
            for i in range(SCALE):
                for j in range(SCALE):
                    if el[2] == 1:
                        im.setPixel((SCALE * el[0]) + i, (SCALE * el[1]) + j, color)
                    else:
                        im.setPixel((SCALE * el[0]) + i, (SCALE * el[1]) + j, color2)

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)


    def redoColors(self, color, color2, stripes):
        im = QImage((N * SCALE), (N * SCALE), QImage.Format_ARGB32)
        if stripes:
            for i in range(N * SCALE):
                for j in range(N * SCALE):
                    if int(i / 2) % 2 == 0:
                        im.setPixel(i, j, color)
                    else:
                        im.setPixel(i, j, color2)
        else:
            im.fill(color)

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)


if __name__ == '__main__':

    app = QApplication([])
    primaryColor = 0xffff0000
    secondaryColor = 0xff00ff00
    allUp = 0
    N = 100
    SCALE = 4
    beta = 0.7
    w = MainWindow()
    app.exec()

    # w.basicRun(3)
