from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from engineOperator import *
from latticeCanvas import Canvas

import random as ra
import re
import math

# Draws the main window and contains the simulation code
class MainWindow(QWidget):

    # Initialises the window and variables. Very uncertain about which
    # variables should go where, but it's fine for now I guess.
    def __init__(self, **DEFAULTS):
        super().__init__()

        # Internal Vars
        # This is the sigmoid for converting the 'coverage percent' (lie) to a threshold.
        # To make it less steep (ie less flat at the top and bottom), reduce the #24.
        self.threshval = list(map((lambda x:1 - (1 / (1 + math.exp(-(x - 0.5) * 24)))), np.arange(100) / 100))
        self.conwayMangled = False
        # Degree of the Potts model
###     self.deg = DEFAULTS['DEGREE']   # Will the poor old Potts model ever make a comeback? Let's see.

        # Save kwargs
        self.kwargs = DEFAULTS

        # INITS
        self.initGUI(**DEFAULTS)

    # Initialise GUI
    def initGUI(self, **DEFAULTS):
        # Initialise the thread manager and painter and feed them the UI elements they
        # need to control. TODO: cleaner way of connecting signals to a parent? Using
        # Super perhaps? TODO: pass the guys with args anyway no?
        self.canvas = Canvas()
        self.canvas.initialize(**DEFAULTS)
        self.frameLabel = QLabel()
        self.arrayfpsLabel = QLabel()
        self.canvasfpsLabel = QLabel()
        self.engine = EngineOperator(self.canvas, self.frameLabel, self.arrayfpsLabel,
                                     self.canvasfpsLabel, **DEFAULTS)

##====================Controlls on the left====================##
        # Main pushbutton, this should be better highlighted.
        self.dynamic = QPushButton()
        self.dynamic.setText('Dynamic')
        self.dynamic.setStyleSheet('QPushButton { background-color: %s; }' %  \
                                         QColor(DEFAULTS['MOUSECOLOR1']).name())
        self.dynamic.clicked.connect(self.engine.dynamic_run)

        # Buttons and slier in the top left
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
        self.thresholdCtrl.setPageStep(4)
        self.thresholdCtrl.setValue(self.kwargs['THRESHOLD'])
        self.thresholdCtrl.valueChanged.connect(self.coverageChange)
        self.thresholdLabel= QLabel()
        self.thresholdLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.thresholdLabel.setText('Coverage = ' + str(self.kwargs['THRESHOLD']) + '%')
        # 'toplefthbox'
        tlhb = QHBoxLayout()
        tlhbvb = QVBoxLayout()
        tlhbvb.addWidget(self.short)
        tlhbvb.addWidget(self.equilibrate)
        tlhbvb.addWidget(self.clear)
        tlhbvb.addWidget(self.thresholdLabel)
        tlhb.addLayout(tlhbvb)
        tlhb.addWidget(self.thresholdCtrl)

        # Conway rule selector
        self.conwayLabel = QLabel()
        self.conwayRules = QTextEdit()
        self.textHolder = QVBoxLayout()
        self.textHolder.addWidget(self.conwayLabel)
        self.textHolder.addWidget(self.conwayRules)
        self.conwayLabel.setText('Enter the rules below. Multiple Rules seperated\nby semicolon. #1 <= NB <= #2, #3 <= P <= #4')
        self.conwayRules.setText('2 < NB < 7, P = 2;\n2 < NB < 7, P = 3;\n2 < NB < 5, P = 3;\n2 < NB < 5, P = 2;')
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)
        # Processes whatever is written above and sends it to the rules. TODO: this needs
        # to update the kwarg too, and anyway the box needs to be written by formatting
        # the default value instead of manually above.
        regexMatchString=r'([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)((?:[0-9],\ ?)*[0-9]);'
        ruleIter = re.finditer(regexMatchString, self.conwayRules.toPlainText())
        self.engine.process_rules(ruleIter)

        # Rules controller for cellular automata
        self.automataLabel = QLabel('Automata Rules: 0101010')
        self.automataString = QLineEdit()
        self.textHolder.addWidget(self.automataLabel)
        self.textHolder.addWidget(self.automataString)
        self.automataPalette = self.automataString.palette()
        self.automataPalette.setColor(QPalette.Base, Qt.red)
        self.automataString.setPalette(self.automataPalette)
       #self.automataString.textChanged.connect(self.automataStringChange)
        # TODO write the function for this baby

        # Default value changer
        NLab = QLabel('N= ')
        NLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.NCtrl = QSpinBox()
        self.NCtrl.setRange(10, 1000)
        self.NCtrl.setSingleStep(10)
        self.NCtrl.setValue(100)
        self.NCtrl.setMaximumSize(100, 40)
        MonteUpLab = QLabel('Up/Frame= ')
        MonteUpLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.MonteUpCtrl = QSpinBox()
        self.MonteUpCtrl.setRange(100, 5000)
        self.MonteUpCtrl.setSingleStep(100)
        self.MonteUpCtrl.setValue(1000)
        self.MonteUpCtrl.setMaximumSize(100, 40)
        LongLab = QLabel('Long#= ')
        LongLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.LongCtrl = QSpinBox()
        self.LongCtrl.setRange(10000, 1000000)
        self.LongCtrl.setSingleStep(10000)
        self.LongCtrl.setValue(100000)
        self.LongCtrl.setMaximumSize(100, 40)
        DegreeLab = QLabel('Degree= ')
        DegreeLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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

        # 'Fixed Defaults' concept superceded, delete XXX
        self.fixedBox = QCheckBox('Fixed')
        self.fixedBox.setChecked(True)
       #self.fixedBox.stateChanged.connect(self.fixedChange)
        # TODO make this work
        sathb = QHBoxLayout()
        self.satLab = QLabel('Saturation %')
        self.satLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.satCtrl = QSpinBox()
        self.satCtrl.setRange(20, 100)
        self.satCtrl.setSingleStep(10)
        self.satCtrl.setValue(100)
        self.satCtrl.setMaximumSize(100, 40)
        sathb.addWidget(self.fixedBox)
        sathb.addWidget(self.satLab)
        sathb.addWidget(self.satCtrl)

        # Color buttons, two for background, two for update and two for mouse.
        # TODO: rework the whole color organisation throughout.
        self.primaryButton = QPushButton()
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(DEFAULTS['BACKCOLOR1']).name())
        self.primaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.primaryButton, 0))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                           QColor(DEFAULTS['BACKCOLOR2']).name())
        self.secondaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.secondaryButton, 1))
        self.gr = QGridLayout()
        self.gr.addWidget(self.primaryButton, 0, 0)
        self.gr.addWidget(self.secondaryButton, 1, 0)
        self.colorList = []
        self.colorList.append(QColor(DEFAULTS['BACKCOLOR1']).rgba())
        self.colorList.append(QColor(DEFAULTS['BACKCOLOR2']).rgba())
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

        # Collects all of the above into a column.
        vb = QVBoxLayout()
        vb.addWidget(self.dynamic)
        vb.addLayout(tlhb)
        vb.addStretch()
        vb.addLayout(self.textHolder)
        vb.addLayout(defGr)
        vb.addStretch()
        vb.addLayout(sathb)
        vb.addWidget(self.primaryButton)
        vb.addWidget(self.secondaryButton)
        vb.addLayout(self.gr)

##===================Canvas and controls, right======================##
        # Stats at the top of the canvas
        statBox = QHBoxLayout()
        self.canvasfpsLabel.setText('Canvas fps: ')
        self.arrayfpsLabel.setText('Array fps: ')
        statBox.addWidget(self.canvasfpsLabel)
        statBox.addWidget(self.arrayfpsLabel)

        # Temperature slider and label
        self.tempCtrl = QSlider(Qt.Horizontal)
        self.tempCtrl.setTickPosition(QSlider.TicksAbove)
        self.tempCtrl.setTickInterval(20)
        self.tempLabel = QLabel()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(200)
        self.tempCtrl.setPageStep(20)
        self.tempCtrl.setValue(self.kwargs['BETA'] * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = ' + str(self.kwargs['BETA']))

        # Speed slider and label
        # TODO: get this working again
        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(self.kwargs['SPEED'])
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel = QLabel()
        self.speedLabel.setText('Speed = ' + str(self.kwargs['SPEED']) + '%')
        self.frameLabel.setText('0000/ ')
        self.frameCtrl = QSpinBox()
        self.frameCtrl.setValue(self.kwargs['IMAGEUPDATES'])
        self.frameCtrl.valueChanged.connect(self.frameChange)
        self.frameCtrl.setRange(10, 1000)
        self.frameCtrl.setSingleStep(10)
        self.frameCtrl.setMaximumSize(100, 20)

        # 'right bottom box [LEFT/MID/RIGHT]' -- sorts out the sliders
        rbbL = QVBoxLayout()
        rbbL.addWidget(self.speedLabel)
        rbbL.addWidget(self.tempLabel)
        rbbM = QVBoxLayout()
        rbbM.addWidget(self.speedCtrl)
        rbbM.addWidget(self.tempCtrl)
        rbbR = QVBoxLayout()
        rbbRt = QHBoxLayout()
        rbbRt.addWidget(self.frameLabel)
        rbbRt.addWidget(self.frameCtrl)
        self.stochasticBox = QCheckBox('Stochi')
        self.stochasticBox.setChecked(self.kwargs['STOCHASTIC'])
        self.stochasticBox.stateChanged.connect(self.stochasticChange)
        rbbR.addLayout(rbbRt)
        rbbR.addWidget(self.stochasticBox)
        rbb = QHBoxLayout()
        rbb.addLayout(rbbL)
        rbb.addLayout(rbbM)
        rbb.addLayout(rbbR)

        # Layout canvas and sliders
        rb = QVBoxLayout()
        rb.addLayout(statBox)
        rb.addWidget(self.canvas)
        rb.addLayout(rbb)

        # Layout control column and canvasbox
        hb = QHBoxLayout()
        hb.addLayout(vb)
        hb.addLayout(rb)

        self.setLayout(hb)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')

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
        self.changeKwarg('IMAGEUPDATES', self.frameCtrl.value())
        # The following was necessary for the keyboard shortcuts to work again,
        # but it does mean that you have to type numbers longer than 2x twice
        a = self.frameCtrl.previousInFocusChain()
        a.setFocus()

    def conway_mangler(self):
        if self.conwayMangled:
            old = self.conwayRules.toPlainText()
            self.conwayRules.setText(old[2:-2])
            self.conwayMangled = False
        else:
            old = self.conwayRules.toPlainText()
            self.conwayRules.setText('!!' + old + '!!')
            self.conwayMangled = True

    def rulesChange(self):
        regexTestString=r'^(?:([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)([0-9],\ ?)*([0-9]);[\ \n]*)+$'
        regexMatchString=r'([0-9])(?:\ ?<\ ?[Nn][Bb]\ ?<\ ?)([0-9])(?:,\ ?[Pp]\ ?=\ ?)((?:[0-9],\ ?)*[0-9]);'
        text = self.conwayRules.toPlainText()
        strTest = re.match(regexTestString, text)
        # TODO: use a timer to emit this information after a pause (with a LIFO?) so it
        # only sends once when you are editing it
        if strTest is None:
            self.conwayPalette.setColor(QPalette.Base, Qt.red)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexTestString, text)
            self.engine.process_rules(ruleIter)
        else:
            self.conwayPalette.setColor(QPalette.Base, Qt.green)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexMatchString, text)
            self.engine.process_rules(ruleIter)

    def stochasticChange(self):
        self.changeKwarg('STOCHASTIC', self.stochasticBox.isChecked())

    def speedChange(self):
        self.changeKwarg('SPEED', self.speedCtrl.value())
        self.speedLabel.setText('Speed = ' + str(self.speedCtrl.value()) + '%')

    def coverageChange(self):
        coverage = self.thresholdCtrl.value()
        self.changeKwarg('THRESHOLD', self.threshval[coverage])
        self.thresholdLabel.setText('Coverage = ' + str(coverage) + '%')

    def sliderChange(self):
        self.changeKwarg('BETA', self.tempCtrl.value() / 100)
        self.tempLabel.setText('Beta = ' + str(self.tempCtrl.value() / 100))

    def keyPressEvent(self, e):
        # TODO: make this a dictonary
        if e.key() == Qt.Key_Escape:
            if self.engine.thread.isRunning():
                self.changeKwarg('INTERRUPT', True)
                # TODO: add a 'interrupted by user' popup (after a 'interrupting!'?)
            else:
                QCoreApplication.instance().quit()
                # TODO: add a 'are you sure?' popup
        # left alt key. guess i could just look this up?
        elif e.key() == 16777251:
            self.speedCtrl.setFocus()
        elif e.key() == Qt.Key_C:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_X:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepSub)
        elif e.key() == Qt.Key_D:
            self.tempCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_A:
            self.tempCtrl.triggerAction(QSlider.SliderPageStepSub)
        elif e.key() == Qt.Key_W:
            self.thresholdCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_S:
            self.thresholdCtrl.triggerAction(QSlider.SliderPageStepSub)
        # Change Colors, RF
        elif e.key() == Qt.Key_R:
            self.primaryButton.click()
        elif e.key() == Qt.Key_F:
            self.secondaryButton.click()
        # Initialise chosen model, 123
        elif e.key() == Qt.Key_1:
            state = self.stochasticBox.isChecked()
            self.stochasticBox.setChecked(not state)
        elif e.key() == Qt.Key_2:
            self.conway_mangler()
#       elif e.key() == Qt.Key_3:
#           self.conwayButt.click()
        elif e.key() == Qt.Key_E:
            self.dynamic.click()
        elif e.key() == Qt.Key_Q:
            self.clear.click()
