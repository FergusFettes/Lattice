from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from isingEngine import IsingEngine
from pottsEngine import PottsEngine
from latticeCanvas import Canvas

import random as ra

# Draws the main window and contains the simulation code
# TODO: split the GUI and the simulations
class MainWindow(QWidget):

    # Initialises the window and variables. Very uncertain about which
    # variables should go where, but it's fine for now I guess.
    def __init__(self, **DEFAULTS):
        super().__init__()

        # VARS for display
        self.frameNum = 0       # Current Frame Number
        self.imageUpdates = DEFAULTS['IMAGEUPDATES']
        self.speed = DEFAULTS['SPEED']
        # Internal Vars
        self.beta = []
        self.colorList = []
        self.primaryColor = QColor(DEFAULTS['PRIMARYCOLOR'])
        self.secondaryColor = QColor(DEFAULTS['SECONDARYCOLOR'])
        # Degree of the Potts model
        self.deg = DEFAULTS['DEGREE']

        # Save kwargs
        self.kwargs = DEFAULTS

        # INITS
        self.initDummy(**DEFAULTS)

    # Initialise GUI
    def initDummy(self, **DEFAULTS):

        self.canvas = Canvas()
        self.canvas.initialize(**DEFAULTS)

        self.isingButt = QPushButton('Ising')
        self.isingButt.pressed.connect(partial(self.initIsingUI))
        self.pottsButt = QPushButton('Potts')
        self.pottsButt.pressed.connect(partial(self.initPottsUI))
        self.conwayButt = QPushButton('Conway')
      # self.conwayButt.pressed.connect(self.initConwayUI)

        hbTop = QHBoxLayout()
        hbTop.addWidget(self.isingButt)
        hbTop.addWidget(self.pottsButt)
        hbTop.addWidget(self.conwayButt)

        self.short = QPushButton()
        self.equilibrate = QPushButton()
        self.dynamic = QPushButton()

        self.primaryButton = QPushButton()
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' % self.primaryColor.name())
        self.primaryButton.pressed.connect(     \
            partial(self.choose_color, self.set_color, self.primaryButton, 0))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' % self.secondaryColor.name())
        self.secondaryButton.pressed.connect(   \
            partial(self.choose_color, self.set_color, self.secondaryButton, 1))

        self.gr = QGridLayout()
        self.gr.addWidget(self.primaryButton, 0, 0)
        self.gr.addWidget(self.secondaryButton, 0, 1)
        self.colorList = []
        self.colorList.append(self.primaryColor.rgba())
        self.colorList.append(self.secondaryColor.rgba())
        for i in range(2,4):
            temp = QPushButton('tst')
            self.gr.addWidget(temp, int(i / 2), i % 2)
        self.canvas.addColors(self.colorList, 2)

        self.tempCtrl = QSlider(Qt.Vertical)
        self.tempCtrl.setTickPosition(QSlider.TicksLeft)
        self.tempCtrl.setTickInterval(20)
        self.tempLabel = QLabel()

        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        vb = QVBoxLayout()
        vb.addWidget(self.short)
        vb.addWidget(self.equilibrate)
        vb.addWidget(self.dynamic)
        vb.addLayout(self.gr)
        vb.addWidget(self.tempCtrl)
        vb.addWidget(self.tempLabel)
        vb.addWidget(exit_button)

        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedLabel = QLabel('Speed = ???')
        self.frameLabel = QLabel('0000/ ')
        self.frameCtrl = QSpinBox()
        self.frameCtrl.setRange(10, 1000)
        self.frameCtrl.setSingleStep(10)
        self.frameCtrl.setValue(100)
        self.frameCtrl.setMaximumSize(100, 40)

        rbb = QHBoxLayout()
        rbb.addWidget(self.speedLabel)
        rbb.addStretch()
        rbb.addWidget(self.frameLabel)
        rbb.addWidget(self.frameCtrl)

        rb = QVBoxLayout()
        rb.addWidget(self.canvas)
        rb.addWidget(self.speedCtrl)
        rb.addLayout(rbb)

        hb = QHBoxLayout()
        hb.addLayout(vb)
        hb.addLayout(rb)

        vbM = QVBoxLayout()
        vbM.addLayout(hbTop)
        vbM.addLayout(hb)

        self.setLayout(vbM)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')

    def initIsingUI(self):
        kwargs = self.kwargs
        self.engine = IsingEngine()
        self.engine.initialize(self.canvas, self.frameLabel, **kwargs)

        self.short.setText('Short')
        self.short.clicked.connect(self.engine.staticRun)
        self.equilibrate.setText('Equilibrate')
        self.equilibrate.clicked.connect(self.engine.equilibrate)
        self.dynamic.setText('Dynamic')
        self.dynamic.clicked.connect(self.engine.dynamicRun)

        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(150)
        self.tempCtrl.setValue(kwargs['BETA'] * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = ' + str(kwargs['BETA']))

        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(kwargs['SPEED'])
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel.setText('Speed = ' + str(kwargs['SPEED']) + '%')
        self.frameCtrl.setValue(kwargs['IMAGEUPDATES'])
        self.frameCtrl.valueChanged.connect(self.frameChange)

    def initPottsUI(self):
        kwargs = self.kwargs
        self.engine = PottsEngine()
        self.engine.initialize(self.canvas, self.frameLabel, **kwargs)
        self.degree = kwargs['DEGREE']

        self.short.setText('Short')
        self.short.clicked.connect(self.engine.staticRun)
        self.equilibrate.setText('Equilibrate')
        self.equilibrate.clicked.connect(self.engine.equilibrate)
        self.dynamic.setText('Dynamic')
        self.dynamic.clicked.connect(self.engine.dynamicRun)

        for i in range(2, self.degree):
            temp = QPushButton()
            self.gr.addWidget(temp, int(i / 2), i % 2)
            colHex = int(ra.random() * int('0xffffffff', 16))
            temp.setStyleSheet('QPushButton { background-color: %s; }' % QColor.fromRgba(colHex).name())
            self.colorList.append(colHex)
        self.canvas.addColors(self.colorList, self.degree)

        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(350)
        self.tempCtrl.setValue(kwargs['BETA'] * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = ' + str(kwargs['BETA']))

        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(kwargs['SPEED'])
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel.setText('Speed = ' + str(kwargs['SPEED']) + '%')
        self.frameCtrl.setValue(kwargs['IMAGEUPDATES'])
        self.frameCtrl.valueChanged.connect(self.frameChange)

    def changeKwarg(self, kwarg, nuVal):
        self.kwargs[kwarg] = nuVal
        self.engine.updateKwargs(**self.kwargs)

    def choose_color(self, callback, *args):
        dlg = QColorDialog()
        if dlg.exec():
            callback(dlg.selectedColor().name(), *args)

    def set_color(self, hexx, button, Num):
        self.colorList[Num] = QColor(hexx).rgba()
        self.engine.setColor(button, QColor(hexx).rgba())
        button.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

    def frameChange(self):
        self.imageUpdates = self.frameCtrl.value()
        self.changeKwarg('IMAGEUPDATES', self.imageUpdates)
        # The following was necessary for the keyboard shortcuts to work again,
        # but it does mean that you have to type numbers longer than 2x twice
        a = self.frameCtrl.previousInFocusChain()
        a.setFocus()

    def speedChange(self):
        self.speed = self.speedCtrl.value()
        self.changeKwarg('SPEED', self.speed)
        self.speedLabel.setText('Speed = ' + str(self.speed) + '%')

    def sliderChange(self):
        self.beta = self.tempCtrl.value() / 100
        self.changeKwarg('BETA', self.beta)
        self.engine.costUpdate(self.beta)
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
        # Change Colors, RF
        elif e.key() == Qt.Key_R:
            self.primaryButton.click()
        elif e.key() == Qt.Key_F:
            self.secondaryButton.click()
        # Initialise chosen model, 123
        elif e.key() == Qt.Key_1:
            self.isingButt.click()
        elif e.key() == Qt.Key_2:
            self.pottsButt.click()
        elif e.key() == Qt.Key_3:
            self.conwayButt.click()
        elif e.key() == Qt.Key_E:
            self.dynamic.click()
        elif e.key() == Qt.Key_Q:
            self.equilibrate.click()
