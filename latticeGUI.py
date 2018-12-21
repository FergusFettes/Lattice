from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from engineOperator import *
from imageProcessing import *

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
        self.kwarg_send_timer = QTimer()
        self.kwarg_send_timer.timeout.connect(self.kwarg_send)
        # This means that you have to stop manipulating the controls for a full three
        # seconds for the changes to be sent to the thread. This stops uneccesary
        # restarts, but needs to be tuned for comfort.
        self.kwarg_send_timer.setInterval(500)
        self.initGUI(**DEFAULTS)

#=====================Settings controllers================#
    def Kwarger(self, kwarg, callback):
        self.changeKwarg(kwarg, callback())

    def changeKwarg(self, kwarg, nuVal):
        print('Changing ' + kwarg)
        self.kwargs[kwarg] = nuVal
        print(self.kwargs[kwarg])
        self.kwarg_send_timer.start()

    def kwarg_send(self):
        print('Sending new kwargs')
        self.engine.update_kwargs(**self.kwargs)
        self.kwarg_send_timer.stop()

    def frameChange(self):
        self.changeKwarg('IMAGEUPDATES', self.frameCtrl.value())
        # The following was necessary for the keyboard shortcuts to work again,
        # but it does mean that you have to type numbers longer than 2x twice
        a = self.frameCtrl.previousInFocusChain()
        a.setFocus()

    def speedChange(self):
        self.changeKwarg('SPEED', self.speedCtrl.value())
        self.speedLabel.setText('Speed = ' + str(self.speedCtrl.value()) + '%')

    def coverageChange(self):
        coverage = self.thresholdCtrl.value()
        self.changeKwarg('THRESHOLD', self.threshval[coverage])
        self.thresholdLabel.setText('Coverage = ' + str(coverage + 1) + '%')

    def sliderChange(self):
        self.changeKwarg('BETA', self.tempCtrl.value() / 100)
        self.tempLabel.setText('Beta = ' + str(self.tempCtrl.value() / 100))

    def choose_color(self, callback, *args):
        dlg = QColorDialog()
        if dlg.exec():
            callback(dlg.selectedColor().name(), *args)

    def set_color(self, hexx, button, num):
        templist = self.kwargs['COLORLIST']
        templist[num] = QColor(hexx).rgba()
        self.changeKwarg('COLORLIST', templist)
        self.engine.image.addColors(templist, self.kwargs['DEGREE'])
        button.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

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
        regexTestString=r'^(?:([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:;\ ?)[\ \n]*)+$'
        regexMatchString=r'([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:;\ ?)'
        text = self.conwayRules.toPlainText()
        strTest = re.match(regexTestString, text)
        # This timer waits for ten seconds for you to dick about with the rules before
        # sending them to the engine. If you get caught with your pants down, conway will
        # turn off for some seconds.
        if strTest is None:
            self.conwayPalette.setColor(QPalette.Base, Qt.red)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexTestString, text)
            self.rul = [i.group(1,2,3,4) for i in ruleIter]
        else:
            self.conwayPalette.setColor(QPalette.Base, Qt.green)
            self.conwayRules.setPalette(self.conwayPalette)
            ruleIter = re.finditer(regexMatchString, text)
            self.rul = [i.group(1,2,3,4) for i in ruleIter]
        self.send_rule()

    def send_rule(self):
        print('Rule sending!')
        rules = [[int(j) for j in i] for i in self.rul]
        self.changeKwarg('RULES', rules)
        self.changeKwarg('CONWAY', not rules == [])

#=====================Save defaults and GUI ket controls===============#
    #TODO: make it save the previous configuration before overwriting
    def save_defaults(self):
        with open('save.txt', 'w') as file:
            savestr = ''.join(['{0}:{1};'.format(i, self.kwargs[i]) for i in self.kwargs])
            file.write(savestr)

    def keyPressEvent(self, e):
        # TODO: make this a dictonary
        if e.key() == Qt.Key_Escape:
            if self.engine.thread.isRunning() or self.engine.thread2.isRunning():
                self.changeKwarg('EQUILIBRATE', False)
                self.changeKwarg('CLEAR', False)
                self.changeKwarg('RUN', False)
                self.engine.thread.requestInterruption()
                self.engine.thread2.requestInterruption()
                print('Attempting to interrupt!')
                # TODO: add a 'interrupted by user' popup (after a 'interrupting!'?)
            else:
                self.engine.thread.deleteLater()
                self.engine.thread2.deleteLater()
                QCoreApplication.instance().quit()
                print('Threads shutting down and powering off')
                # TODO: add a 'are you sure?' popup
        # left alt key. guess i could just look this up?
        elif e.key() == 16777251:
            self.speedCtrl.setFocus()
        elif e.key() == Qt.Key_C:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepAdd)
        elif e.key() == Qt.Key_X:
            self.speedCtrl.triggerAction(QSlider.SliderPageStepSub)
        elif e.key() == Qt.Key_B:
            self.background.click()
        elif e.key() == Qt.Key_L:
            self.equilibrate.click()
        elif e.key() == Qt.Key_Z:
            self.short.click()
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

##==========================THEGUI==============================##
##==============================================================##
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
                                         QColor('#ffff00ff').name())
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
        self.clear.clicked.connect(self.engine.clear_array)
        self.background = QPushButton()
        self.background.setText('Background')
        self.background.clicked.connect(self.engine.clear_background)
        self.thresholdCtrl = QSlider(Qt.Vertical)
        self.thresholdCtrl.setTickPosition(QSlider.TicksRight)
        self.thresholdCtrl.setTickInterval(20)
        self.thresholdCtrl.setMinimum(0)
        self.thresholdCtrl.setMaximum(99)
        self.thresholdCtrl.setPageStep(4)
        self.thresholdCtrl.setValue(self.kwargs['THRESHOLD'] + 1)
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
        tlhbvb.addWidget(self.background)
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
        self.conwayRules.setText(''.join(['{0},{1},{2},{3};'.format(*i) for i in self.kwargs['RULES']]))
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)

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
        self.NCtrl.setValue(self.kwargs['N'])
        self.NCtrl.setMaximumSize(100, 40)
        self.NCtrl.valueChanged.connect(partial(self.Kwarger, 'N', self.NCtrl.value))
        MonteUpLab = QLabel('Up/Frame= ')
        MonteUpLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.MonteUpCtrl = QSpinBox()
        self.MonteUpCtrl.setRange(100, 5000)
        self.MonteUpCtrl.setSingleStep(100)
        self.MonteUpCtrl.setValue(self.kwargs['MONTEUPDATES'])
        self.MonteUpCtrl.setMaximumSize(100, 40)
        self.MonteUpCtrl.valueChanged.connect(partial(self.Kwarger, 'MONTEUPDATES',
                                                      self.MonteUpCtrl.value))
        LongLab = QLabel('Long#= ')
        LongLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.LongCtrl = QSpinBox()
        self.LongCtrl.setRange(10000, 1000000)
        self.LongCtrl.setSingleStep(10000)
        self.LongCtrl.setValue(self.kwargs['EQUILIBRATE'])
        self.LongCtrl.setMaximumSize(100, 40)
        self.LongCtrl.valueChanged.connect(partial(self.Kwarger, 'EQUILIBRATE',
                                                   self.LongCtrl.value))
        DegreeLab = QLabel('Degree= ')
        DegreeLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.DegreeCtrl = QSpinBox()
        self.DegreeCtrl.setRange(2, 10)
        self.DegreeCtrl.setSingleStep(1)
        self.DegreeCtrl.setValue(self.kwargs['DEGREE'])
        self.DegreeCtrl.setMaximumSize(100, 40)
        self.DegreeCtrl.valueChanged.connect(partial(self.Kwarger, 'DEGREE',
                                                     self.DegreeCtrl.value))
        ScaleLab = QLabel('Scale= ')
        ScaleLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ScaleCtrl = QSpinBox()
        self.ScaleCtrl.setRange(1, 20)
        self.ScaleCtrl.setSingleStep(1)
        self.ScaleCtrl.setValue(self.kwargs['SCALE'])
        self.ScaleCtrl.setMaximumSize(100, 40)
        self.ScaleCtrl.valueChanged.connect(partial(self.Kwarger, 'SCALE',
                                                    self.ScaleCtrl.value))
        SaveDefaults = QPushButton('Save Defaults')
        SaveDefaults.clicked.connect(self.save_defaults)
        defGr = QGridLayout()
        defGr.addWidget(NLab, 0, 0)
        defGr.addWidget(self.NCtrl, 0, 1)
        defGr.addWidget(MonteUpLab, 1, 0)
        defGr.addWidget(self.MonteUpCtrl, 1, 1)
        defGr.addWidget(LongLab, 0, 2)
        defGr.addWidget(self.LongCtrl, 0, 3)
        defGr.addWidget(DegreeLab, 1, 2)
        defGr.addWidget(self.DegreeCtrl, 1, 3)
        defGr.addWidget(ScaleLab, 2, 0)
        defGr.addWidget(self.ScaleCtrl, 2, 1)
        defGr.addWidget(SaveDefaults, 2, 2, 1, 2)

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
                                         QColor(self.kwargs['COLORLIST'][0]).name())
        self.primaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.primaryButton, 0))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                           QColor(self.kwargs['COLORLIST'][1]).name())
        self.secondaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.secondaryButton, 1))
        self.updateButton = QPushButton()
        self.updateButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.kwargs['COLORLIST'][2]).name())
        self.updateButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.updateButton, 0))
        self.update2Button = QPushButton()
        self.update2Button.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.kwargs['COLORLIST'][3]).name())
        self.update2Button.pressed.connect(
            partial(self.choose_color, self.set_color, self.update2Button, 0))
        self.mouseButton = QPushButton()
        self.mouseButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.kwargs['COLORLIST'][4]).name())
        self.mouseButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.mouseButton, 0))
        self.mouse2Button = QPushButton()
        self.mouse2Button.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.kwargs['COLORLIST'][5]).name())
        self.mouse2Button.pressed.connect(
            partial(self.choose_color, self.set_color, self.mouse2Button, 0))
        self.gr = QGridLayout()
        self.gr.addWidget(self.primaryButton, 0, 0)
        self.gr.addWidget(self.secondaryButton, 1, 0)
        self.gr.addWidget(self.updateButton, 0, 1)
        self.gr.addWidget(self.update2Button, 1, 1)
        self.gr.addWidget(self.mouseButton, 0, 2)
        self.gr.addWidget(self.mouse2Button, 1, 2)

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
        self.frameCtrl.setRange(10, 2000)
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
        self.stochasticBox.stateChanged.connect(partial(self.Kwarger, 'STOCHASTIC',
                                                self.stochasticBox.isChecked))
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
