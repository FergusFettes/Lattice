from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

import numpy as np
import random as ra
import time

# Draws the main window and contains the simulation code
# TODO: split the GUI and the simulations
class MainWindow(QWidget):

    # Initialises the window and variables. Very uncertain about which
    # variables should go where, but it's fine for now I guess.
    def __init__(self):
        super().__init__()

        #VARS
        self.colorList=[]
        self.beta = beta
        self.cost = np.zeros(3)
        self.cost[1] = np.exp(-4 * self.beta)
        self.cost[2] = self.cost[1] * self.cost[1]
        self.costP = np.zeros(4)
        self.costP[0] = np.exp(-1 * self.beta)
        self.costP[1] = self.costP[0] ** 2
        self.costP[2] = self.costP[0] ** 3
        self.costP[3] = self.costP[0] ** 3
        # Number of frames to generate
        # TODO: make '-1' result in infinite run
        self.imageUpdates = 100
        # Number of updates between frames
        self.monteUpdates = 1000
        self.speed = speed
        self.primaryColor = QColor(primaryColor)
        self.secondaryColor = QColor(secondaryColor)
        # Degree of the Potts model
        self.deg = degree

        #INITS
        self.initUI()
        # self.spinArray = self.isingInit()
        self.spinArray = self.pottsInit(self.deg)
        # self.exportArray(self.spinArray, self.primaryColor.rgba(), self.secondaryColor.rgba())
        self.exportPottsArray(self.spinArray, None, self.deg)

    # Initialise GUI
    def initUI(self):

        self.canvas = QLabel()
        self.canvas.setPixmap(QPixmap(N * SCALE, N * SCALE))

        short = QPushButton('Short')
      # short.clicked.connect(partial(self.staticRun, None))
        short.clicked.connect(partial(self.staticRunPotts, None))
        self.equilibrate = QPushButton('Equilibrate')
      # self.equilibrate.clicked.connect(partial(self.staticRun, 50000))
        self.equilibrate.clicked.connect(partial(self.staticRunPotts, 50000))
        self.dynamic = QPushButton('Dynamic')
      # self.dynamic.clicked.connect(partial(self.dynamicRun, None, None))
        self.dynamic.clicked.connect(partial(self.dynamicRunPotts, None, None))

        self.primaryButton = QPushButton()
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' % self.primaryColor.name())
        self.primaryButton.pressed.connect(lambda: self.choose_color(self.set_primary_color))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' % self.secondaryColor.name())
        self.secondaryButton.pressed.connect(lambda: self.choose_color(self.set_secondary_color))

        gr = QGridLayout()
        gr.addWidget(self.primaryButton, 0, 0)
        gr.addWidget(self.secondaryButton, 0, 1)
        self.colorList = []
        self.colorList.append(self.primaryColor.rgba())
        self.colorList.append(self.secondaryColor.rgba())
        for i in range(self.deg-2):
            temp = QPushButton()
            colHex = int(ra.random() * int('0xffffffff', 16))
            temp.setStyleSheet('QPushButton { background-color: %s; }' % QColor.fromRgb(colHex).name())
            self.colorList.append(colHex)
            gr.addWidget(temp)

        self.tempCtrl = QSlider(Qt.Vertical)
        self.tempCtrl.setMinimum(1)
        self.tempCtrl.setMaximum(150)
        self.tempCtrl.setValue(self.beta * 100)
        self.tempCtrl.setTickPosition(QSlider.TicksLeft)
        self.tempCtrl.setTickInterval(20)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel = QLabel('Beta = ' + str(self.beta))

        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        vb = QVBoxLayout()
        vb.addWidget(short)
        vb.addWidget(self.equilibrate)
        vb.addWidget(self.dynamic)
        vb.addLayout(gr)
        vb.addWidget(self.tempCtrl)
        vb.addWidget(self.tempLabel)
        vb.addWidget(exit_button)

        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(self.speed)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel = QLabel('Speed = ' + str(self.speed) + '%')

        rb = QVBoxLayout()
        rb.addWidget(self.canvas)
        rb.addWidget(self.speedCtrl)
        rb.addWidget(self.speedLabel)

        hb = QHBoxLayout()
        hb.addLayout(vb)
        hb.addLayout(rb)

        self.setLayout(hb)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')

    def choose_color(self, callback):
        dlg = QColorDialog()
        if dlg.exec():
            callback( dlg.selectedColor().name() )

    def set_primary_color(self, hexx):
        self.primaryColor = QColor(hexx)
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

    def set_secondary_color(self, hexx):
        self.secondaryColor = QColor(hexx)
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

    def speedChange(self):
        self.speed = self.speedCtrl.value()
        self.speedLabel.setText('Speed = ' + str(self.speed) + '%')

    def sliderChange(self):
        self.beta = self.tempCtrl.value() / 100
        self.cost[1] = np.exp(-4 * self.beta)
        self.cost[2] = self.cost[1] * self.cost[1]
        self.costP[0] = np.exp(-1 * self.beta)
        self.costP[1] = self.costP[0] ** 2
        self.costP[2] = self.costP[0] ** 3
        self.costP[3] = self.costP[0] ** 3
        self.tempLabel.setText('Beta = ' + str(self.beta))

    def exit_button_clicked(self):
        QCoreApplication.instance().quit()

    def keyPressEvent(self, e):
        # print(e.key())
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()
        elif e.key() == Qt.Key_D:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_A:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepSub)
        elif e.key() == Qt.Key_W:
            self.tempCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_S:
            self.tempCtrl.triggerAction(QSlider.SliderPageStepSub)
        elif e.key() == Qt.Key_1:
            self.primaryButton.click()
        elif e.key() == Qt.Key_2:
            self.secondaryButton.click()
        elif e.key() == Qt.Key_E:
            self.dynamic.click()
        elif e.key() == Qt.Key_Q:
            self.equilibrate.click()

#=================Simulation Station===============#
    # Initialises the data array (invisible to user)
    def pottsInit(self, DEGREE):
        ARR = np.zeros((N, N), int)
        if allUp:
            return ARR
        for i in range(N):
            for j in range(N):
                tempra = ra.random()
                for k in range(DEGREE):
                    if (k / DEGREE) <= tempra <= ((k + 1) / DEGREE):
                        ARR[i, j] = k
        return ARR

    # Initialises the data array (invisible to user)
    def isingInit(self):
        ARR = np.ones((N, N), int)
        if allUp:
            return ARR
        for i in range(0, N):
            for j in range(0, N):
                if ra.random() > 0.5:
                    ARR[i, j] = -1
        return ARR

    # MonteCarlo algorithm for Potts
    def PottsUpdate(self, A, nSteps, costP, DEGREE):
        updateList=[]
        for _ in range(nSteps):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = int(A[a][b] == A[(a + 1) % N][b]) \
                + int(A[a][b] == A[(a - 1) % N][b]) \
                + int(A[a][b] == A[a][(b + 1) % N]) \
                + int(A[a][b] == A[a][(b - 1) % N])
            print(nb)
            tempra=ra.random()
            for k in range(DEGREE):
                if (k / DEGREE) <=  tempra <= ((k + 1) / DEGREE):
                    temp = k
            print(temp)
            nb2 = int(k == A[(a + 1) % N][b]) \
                + int(k == A[(a - 1) % N][b]) \
                + int(k == A[a][(b + 1) % N]) \
                + int(k == A[a][(b - 1) % N])
            print(nb2)
            if (nb2 - nb) <= 0 or ra.random() < costP[(nb2 - nb) - 1]:
                A[a][b] = k
                updateList.append([a,b,A[a][b]])
        time.sleep(0.001 * (100 - self.speed))
        return A, updateList

    # Performs a monte carlo update. Could be exported to C, but this isn't
    # where the cycles go anyway
    def MonteCarloUpdate(self, A, nSteps, cost):
        updateList=[]
        for _ in range(nSteps):
            a = int(ra.random() * N)
            b = int(ra.random() * N)
            nb = A[a][b] * (A[(a + 1) % N][b] + A[(a - 1) % N][b] + A[a][(b + 1) % N] + A[a][(b - 1) % N])
            if nb <= 0 or ra.random() < cost[int(nb / 4)]:
                A[a][b] = -A[a][b]
                updateList.append([a,b,A[a][b]])
        time.sleep(0.001 * (100 - self.speed))
        return A, updateList

    # Potts Array Update (VERY SLOW)
    def exportPottsArray(self, A, colorList=None, DEGREE=None):
        colorList = colorList if colorList is not None else self.colorList
        DEGREE = DEGREE if DEGREE is not None else self.deg
        im = QImage((N * SCALE), (N * SCALE), QImage.Format_ARGB32)
        for i in range(N * SCALE):
            for j in range(N * SCALE):
                num = A[int(i / SCALE)][int(j / SCALE)]
                color = colorList[num]
                im.setPixel(i, j, color)

        nupix = QPixmap()
        nupix.convertFromImage(im)
        self.canvas.setPixmap(nupix)

    # Updates image with values from entire array. SLOW
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

    # Updates image only where the pixels have changed. FASTER
    # TODO: Make more performant, use bitdata, also QGLWidget
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

    # Potts Static
    def staticRunPotts(self, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        self.spinArray, updateList  = self.PottsUpdate(self.spinArray, montUp, self.costP, self.deg)
        self.exportPottsArray(self.spinArray, self.colorList, self.deg)

    # Potts Dynamic
    def dynamicRunPotts(self, imUp=None, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        imUp = imUp if imUp is not None else self.imageUpdates
        for _ in range(imUp):
            self.spinArray, updateList = self.PottsUpdate(self.spinArray, montUp, self.costP, self.deg)
            self.exportPottsArray(self.spinArray, self.colorList, self.deg)

    # Run in background (waay fast)
    def staticRun(self, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        self.spinArray, updateList  = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
        self.exportList(updateList, self.primaryColor.rgba(), self.secondaryColor.rgba())

    # Run and update image continuously
    def dynamicRun(self, imUp=None, montUp=None):
        montUp = montUp if montUp is not None else self.monteUpdates
        imUp = imUp if imUp is not None else self.imageUpdates
        for _ in range(imUp):
            self.spinArray, updateList = self.MonteCarloUpdate(self.spinArray, montUp, self.cost)
            self.exportList(updateList, self.primaryColor.rgba(), self.secondaryColor.rgba())
            self.repaint()

    # Repaint the whole field. Doesnt reset data array. Should probably just
    # replace this with an isinInit + exportArray. Good for testing though.
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

    # w.basicRun(3)
