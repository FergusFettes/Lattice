from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from engineOperator import *
from latticeCanvas import Canvas

import random as ra
import re

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
        self.beta = DEFAULTS['BETA']
        self.colorList = []
        self.primaryColor = QColor(DEFAULTS['PRIMARYCOLOR'])
        self.secondaryColor = QColor(DEFAULTS['SECONDARYCOLOR'])
        # Degree of the Potts model
        self.deg = DEFAULTS['DEGREE']

        # Save kwargs
        self.kwargs = DEFAULTS

        # INITS
        self.initGUI(**DEFAULTS)

    # Initialise GUI
    def initGUI(self, **DEFAULTS):
        self.canvas = Canvas()
        self.canvas.initialize(**DEFAULTS)
        self.frameLabel = QLabel()

        kwargs = self.kwargs
        self.engine = EngineOperator(self.canvas, self.frameLabel, **kwargs)

        self.dynamic = QPushButton()
        self.dynamic.setText('Dynamic')
        self.dynamic.setStyleSheet('QPushButton { background-color: %s; }' %  \
                                         self.primaryColor.name())
        self.dynamic.clicked.connect(self.engine.dynamic_run)

        self.short = QPushButton()
        self.equilibrate = QPushButton()
        self.short.setText('Step')
        self.short.clicked.connect(self.engine.static_run)
        self.equilibrate.setText('Long')
        self.equilibrate.clicked.connect(self.engine.long_run)
        self.clear = QPushButton()
        self.clear.setText('Clear')
        self.clear.clicked.connect(self.engine.noise_array)
        self.thresholdCtrl = QSlider(Qt.Vertical)
        self.thresholdCtrl.setTickPosition(QSlider.TicksRight)
        self.thresholdCtrl.setTickInterval(20)
        self.thresholdCtrl.setMinimum(1)
        self.thresholdCtrl.setMaximum(100)
        self.thresholdCtrl.setPageStep(2)
        self.thresholdCtrl.setValue(kwargs['COVERAGE'])
        self.thresholdCtrl.valueChanged.connect(self.coverageChange)
        self.thresholdLabel= QLabel()
        self.thresholdLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.thresholdLabel.setText('Coverage = ' + str(kwargs['COVERAGE']) + '%')
        tlhb = QHBoxLayout()
        tlhbvb = QVBoxLayout()
        tlhbvb.addWidget(self.short)
        tlhbvb.addWidget(self.equilibrate)
        tlhbvb.addWidget(self.clear)
        tlhbvb.addWidget(self.thresholdLabel)
        tlhb.addLayout(tlhbvb)
        tlhb.addWidget(self.thresholdCtrl)

        self.conwayLabel = QLabel()
        self.conwayRules = QTextEdit()
        self.textHolder = QVBoxLayout()
        self.textHolder.addWidget(self.conwayLabel)
        self.textHolder.addWidget(self.conwayRules)
        self.conwayLabel.setText('Enter the rules below. Multiple Rules seperated\nby semicolon. NB = neighbors, P = parents')
        self.conwayRules.setText('1 < NB < 4, P = 2;')
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)
        regexMatchString=r'([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)((?:[0-9],\ ?)*[0-9]);'
        ruleIter = re.finditer(regexMatchString, self.conwayRules.toPlainText())
        self.engine.process_rules(ruleIter)

        self.automataLabel = QLabel('Automata Rules: 0101010')
        self.automataString = QLineEdit()
        self.textHolder.addWidget(self.automataLabel)
        self.textHolder.addWidget(self.automataString)
        self.automataPalette = self.automataString.palette()
        self.automataPalette.setColor(QPalette.Base, Qt.red)
       #self.automataString.textChanged.connect(self.automataStringChange)
        # TODO write the function for this baby

        NLab = QLabel('N= ')
        self.NCtrl = QSpinBox()
        self.NCtrl.setRange(10, 1000)
        self.NCtrl.setSingleStep(10)
        self.NCtrl.setValue(100)
        self.NCtrl.setMaximumSize(100, 40)
        MonteUpLab = QLabel('Up/Frame= ')
        self.MonteUpCtrl = QSpinBox()
        self.MonteUpCtrl.setRange(100, 5000)
        self.MonteUpCtrl.setSingleStep(100)
        self.MonteUpCtrl.setValue(1000)
        self.MonteUpCtrl.setMaximumSize(100, 40)
        LongLab = QLabel('Long#= ')
        self.LongCtrl = QSpinBox()
        self.LongCtrl.setRange(10000, 1000000)
        self.LongCtrl.setSingleStep(10000)
        self.LongCtrl.setValue(100000)
        self.LongCtrl.setMaximumSize(100, 40)
        DegreeLab = QLabel('Degree= ')
        self.DegreeCtrl = QSpinBox()
        self.DegreeCtrl.setRange(2, 10)
        self.DegreeCtrl.setSingleStep(1)
        self.DegreeCtrl.setValue(2)
        self.DegreeCtrl.setMaximumSize(100, 40)
        SaveDefaults = QPushButton('Save Defaults')
        #TODO make this actualy save the defaults
        defGr = QGridLayout()
        defGr.addWidget(NLab, 0, 0)
        defGr.addWidget(self.NCtrl, 0, 1)
        defGr.addWidget(MonteUpLab, 1, 0)
        defGr.addWidget(self.MonteUpCtrl, 1, 1)
        defGr.addWidget(LongLab, 0, 2)
        defGr.addWidget(self.LongCtrl, 0, 3)
        defGr.addWidget(DegreeLab, 1, 2)
        defGr.addWidget(self.DegreeCtrl, 1, 3)
        defGr.addWidget(SaveDefaults, 2, 0, 1, 4)

        self.fixedBox = QCheckBox('Fixed Primaries')
        self.fixedBox.setChecked(True)
       #self.fixedBox.stateChanged.connect(self.fixedChange)
        # TODO make this work
        sathb = QHBoxLayout()
        self.satLab = QLabel('Saturation %')
        self.satCtrl = QSpinBox()
        self.satCtrl.setRange(20, 100)
        self.satCtrl.setSingleStep(10)
        self.satCtrl.setValue(100)
        self.satCtrl.setMaximumSize(100, 40)
        sathb.addWidget(self.satLab)
        sathb.addWidget(self.satCtrl)

        self.primaryButton = QPushButton()
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         self.primaryColor.name())
        self.primaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.primaryButton, 0))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                           self.secondaryColor.name())
        self.secondaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.secondaryButton, 1))

        self.gr = QGridLayout()
        self.gr.addWidget(self.primaryButton, 0, 0)
        self.gr.addWidget(self.secondaryButton, 1, 0)
        self.colorList = []
        self.colorList.append(self.primaryColor.rgba())
        self.colorList.append(self.secondaryColor.rgba())
        for i in range(2, 6):
            temp = QPushButton('tst')
            self.gr.addWidget(temp, i % 2, int(i / 2))
        self.canvas.addColors(self.colorList, 2)
#       while len(self.colorList) > 2:
#           self.colorList.pop()
#       for i in range(2, self.degree):
#           temp = QPushButton()
#           self.gr.addWidget(temp, int(i / 2), i % 2)
#           colHex = int(ra.random() * int('0xffffffff', 16))
#           temp.setStyleSheet('QPushButton { background-color: %s; }' %  \
#                              QColor.fromRgba(colHex).name())
#           self.colorList.append(colHex)
#       self.canvas.addColors(self.colorList, self.degree)

        vb = QVBoxLayout()
        vb.addWidget(self.dynamic)
        vb.addLayout(tlhb)
        vb.addStretch()
        vb.addLayout(self.textHolder)
        vb.addLayout(defGr)
        vb.addStretch()
        vb.addWidget(self.fixedBox)
        vb.addLayout(sathb)
        vb.addWidget(self.primaryButton)
        vb.addWidget(self.secondaryButton)
        vb.addLayout(self.gr)

        self.tempCtrl = QSlider(Qt.Horizontal)
        self.tempCtrl.setTickPosition(QSlider.TicksAbove)
        self.tempCtrl.setTickInterval(20)
        self.tempLabel = QLabel()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(200)
        self.tempCtrl.setPageStep(20)
        self.tempCtrl.setValue(kwargs['BETA'] * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = ' + str(kwargs['BETA']))

        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(kwargs['SPEED'])
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel = QLabel()
        self.speedLabel.setText('Speed = ' + str(kwargs['SPEED']) + '%')
        self.frameLabel.setText('0000/ ')
        self.frameCtrl = QSpinBox()
        self.frameCtrl.setValue(kwargs['IMAGEUPDATES'])
        self.frameCtrl.valueChanged.connect(self.frameChange)
        self.frameCtrl.setRange(10, 1000)
        self.frameCtrl.setSingleStep(10)
        self.frameCtrl.setMaximumSize(100, 40)

        rbb = QHBoxLayout()
        rbb.addWidget(self.speedLabel)
        rbb.addWidget(self.speedCtrl)
        rbb.addWidget(self.frameLabel)
        rbb.addWidget(self.frameCtrl)
        self.stochasticBox = QCheckBox('Stochi')
        self.stochasticBox.setChecked(kwargs['STOCHASTIC'])
        self.stochasticBox.stateChanged.connect(self.stochasticChange)
        rbb2 = QHBoxLayout()
        rbb2.addWidget(self.tempLabel)
        rbb2.addWidget(self.tempCtrl)
        rbb2.addWidget(self.stochasticBox)

        rb = QVBoxLayout()
        rb.addWidget(self.canvas)
        rb.addLayout(rbb)
        rb.addLayout(rbb2)

        hb = QHBoxLayout()
        hb.addLayout(vb)
        hb.addLayout(rb)

        vbM = QVBoxLayout()
        vbM.addLayout(vb)
        vbM.addLayout(hb)

        self.setLayout(vbM)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')

<<<<<<< HEAD
=======
    def initIsingUI(self):
        kwargs = self.kwargs
        self.engine = IsingEngine()
        self.engine.initialize(self.canvas, self.frameLabel, **kwargs)
        self.changeKwarg('NEWARR', 0)

        self.short.setText('Short')
        self.short.clicked.connect(self.engine.staticRun)
        self.equilibrate.setText('Equilibrate')
        self.equilibrate.clicked.connect(self.engine.equilibrate)
        self.dynamic.setText('Dynamic')
        self.dynamic.clicked.connect(self.engine.dynamicRun)

        # Clears the color buttons
        for i in range(2, self.kwargs['DEGREE']):
            temp = QPushButton()
            self.gr.addWidget(temp, int(i / 2), i % 2)

        self.tempCtrl.disconnect()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(150)
        self.tempCtrl.setPageStep(20)
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

        while len(self.colorList) > 2:
            self.colorList.pop()
        for i in range(2, self.degree):
            temp = QPushButton()
            self.gr.addWidget(temp, int(i / 2), i % 2)
            colHex = int(ra.random() * int('0xffffffff', 16))
            temp.setStyleSheet('QPushButton { background-color: %s; }' %  \
                               QColor.fromRgba(colHex).name())
            self.colorList.append(colHex)
        self.canvas.addColors(self.colorList, self.degree)

        self.tempCtrl.disconnect()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(350)
        self.tempCtrl.setPageStep(20)
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

    def initConwayUI(self):
        kwargs = self.kwargs
        self.engine = ConwayEngine()
        self.engine.initialize(self.canvas, self.frameLabel,  **kwargs)
        self.degree = 2
        self.coverage = kwargs['COVERAGE']

        self.short.setText('Short')
      # self.short.clicked.connect(self.engine.staticRun)
        self.equilibrate.setText('Clean Canvas')
        self.equilibrate.clicked.connect(self.engine.reset)
        self.dynamic.setText('Dynamic')
        self.dynamic.clicked.connect(self.engine.dynamicRun)

        while len(self.colorList) > 2:
            self.colorList.pop()
        # Clears the buttons
        for i in range(2, self.kwargs['DEGREE']):
            temp = QPushButton()
            self.gr.addWidget(temp, int(i / 2), i % 2)
        self.canvas.addColors(self.colorList, self.degree)
        self.spareButton = QPushButton('Huh?')
        self.stochasticBox = QCheckBox('Stochi')
        self.stochasticBox.setChecked(True)
        self.stochasticBox.stateChanged.connect(self.stochasticChange)
        self.gr.addWidget(self.spareButton, 1, 0)
        self.gr.addWidget(self.stochasticBox, 1, 1)

        self.conwayLabel.setText('Enter the rules below. Multiple Rules seperated\nby semicolon. NB = neighbors, P = parents')
        self.conwayRules.setText('1 < NB < 4, P = 2;')
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)
        regexMatchString=r'([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)((?:[0-9],\ ?)*[0-9]);'
        ruleIter = re.finditer(regexMatchString, self.conwayRules.toPlainText())
        self.engine.thread.processRules(ruleIter)

        self.tempCtrl.disconnect()
        self.tempCtrl.setMinimum(1)
        self.tempCtrl.setPageStep(2)
        self.tempCtrl.setMaximum(40)
        self.tempCtrl.setValue(kwargs['COVERAGE'])
        self.tempCtrl.valueChanged.connect(self.coverageChange)
        self.tempLabel.setText('Coverage')

        exit_button = QPushButton('EXIT!')
        exit_button.clicked.connect(self.exit_button_clicked)

        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(kwargs['SPEED'])
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel.setText('Speed = ' + str(kwargs['SPEED']) + '%')
        self.frameCtrl.setValue(kwargs['IMAGEUPDATES'])
        self.frameCtrl.valueChanged.connect(self.frameChange)

>>>>>>> thread
    def changeKwarg(self, kwarg, nuVal):
        self.kwargs[kwarg] = nuVal
        self.engine.update_kwargs(**self.kwargs)

    def choose_color(self, callback, *args):
        dlg = QColorDialog()
        if dlg.exec():
            callback(dlg.selectedColor().name(), *args)

    def set_color(self, hexx, button, Num):
        self.colorList[Num] = QColor(hexx).rgba()
        button.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

    def frameChange(self):
        self.imageUpdates = self.frameCtrl.value()
        self.changeKwarg('IMAGEUPDATES', self.imageUpdates)
        # The following was necessary for the keyboard shortcuts to work again,
        # but it does mean that you have to type numbers longer than 2x twice
        a = self.frameCtrl.previousInFocusChain()
        a.setFocus()

    def rulesChange(self):
        regexTestString=r'^(?:([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)([0-9],\ ?)*([0-9]);[\ \n]*)+$'
        regexMatchString=r'([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)((?:[0-9],\ ?)*[0-9]);'
        text = self.conwayRules.toPlainText()
        strTest = re.match(regexTestString, text)
        if strTest is None:
            self.conwayPalette.setColor(QPalette.Base, Qt.red)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexTestString, text)
            self.engine.process_rules(ruleIter)
            time.sleep(0.1)
        else:
            self.conwayPalette.setColor(QPalette.Base, Qt.green)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexMatchString, text)
<<<<<<< HEAD
            self.engine.process_rules(ruleIter)
            time.sleep(0.1)
=======
            self.engine.thread.processRules(ruleIter)
>>>>>>> thread

    def stochasticChange(self):
        self.stochastic = self.stochasticBox.isChecked()
        self.changeKwarg('STOCHASTIC', self.stochastic)

    def speedChange(self):
        self.speed = self.speedCtrl.value()
        self.changeKwarg('SPEED', self.speed)
        self.speedLabel.setText('Speed = ' + str(self.speed) + '%')

    def coverageChange(self):
        self.coverage = self.thresholdCtrl.value()
        self.changeKwarg('COVERAGE', self.coverage)
        self.thresholdLabel.setText('Coverage = ' + str(self.coverage) + '%')

    def sliderChange(self):
        self.beta = self.tempCtrl.value() / 100
        self.changeKwarg('BETA', self.beta)
        self.tempLabel.setText('Beta = ' + str(self.beta))

    def exit_button_clicked(self):
        QCoreApplication.instance().quit()

    def keyPressEvent(self, e):
#       print(e.key())
<<<<<<< HEAD
        if e.key() == Qt.Key_Escape:
            QCoreApplication.instance().quit()
        elif e.key() == 16777400:
            self.speedCtrl.setFocus()
=======
        if e.key() == Qt.Key_F1:
            QCoreApplication.instance().quit()
        elif e.key() == Qt.Key_Control:
            self.speedCtrl.setFocus()
        elif e.key() == Qt.Key_Escape:
            self.engine.thread.quit()
>>>>>>> thread
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
