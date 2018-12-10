from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
import random as ra

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()
        cost = np.zeros(3)
        cost[1] = np.exp(-4 * beta)
        cost[2] = cost[1] * cost[1]
        allUp = 1
        self.isingInit(allUp)
        self.redoColors()

    def initUI(self):

        primary_color = QColor(Qt.black)

        self.canvas = QLabel()
        self.canvas.setPixmap(QPixmap(N * SCALE, N * SCALE))
        self.canvas.pixmap().fill(primary_color)

        button1 = QPushButton('These')
        button2 = QPushButton('buttons')
        button3 = QPushButton('do')
        button4 = QPushButton('nothing!')
        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        vb = QVBoxLayout()
        vb.addWidget(button1)
        vb.addWidget(button2)
        vb.addWidget(button3)
        vb.addWidget(button4)
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

    def isingInit(self, allUp):
        ARR = np.ones((N, N), int)
        if allUp:
            return ARR
        for i in range(0, N):
            for j in range(0, N):
                if ra.random() > 0.5:
                    ARR[i, j] = -1
        return ARR

    def MonteCarloUpdate(A, nSteps, cost):
        for _ in range(nSteps):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
        return A

    def exportArray(self, A):
        if SCALE > 1:
            A2 = np.ones((N * SCALE, N * SCALE), int)
            for i in range(N * SCALE):
                for j in range(N * SCALE):
                    A2[i][j] = A[int(i / SCALE)][int(j / SCALE)]
        else:
            A2 = A

        p = QPainter(self.canvas.pixmap())

        im = QImage()
        im.setColor(0, 0xffff00ff)
        im.setColor(1, 0xffffff00)
        im.fill(1)

    def redoColors(self):
        im = QImage((N * SCALE), (N * SCALE), QImage.Format_ARGB32)
        im.setColor(0, 0xffff00ff)
        im.fill(QColor(Qt.blue))

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)


if __name__ == '__main__':

    app = QApplication([])
    N = 100
    SCALE = 4
    beta = 0.3
    w = MainWindow()
    app.exec()
