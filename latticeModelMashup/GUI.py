from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from engineOperator import *
from imageProcessing import *

import random as ra
import math
import ffmpeg
import os
import re
import glob
from munch import *
from yaml import safe_load, safe_dump

# Draws the main window and contains the simulation code
class MainWindow(QWidget):

    # Initialises the window and variables. Very uncertain about which
    # variables should go where, but it's fine for now I guess.
    def __init__(self, st):
        super().__init__()

        # Internal Vars
        # This is the sigmoid for makeing the threshold.
        # To make it less steep (ie less flat at the top and bottom), reduce the #24.
        self.threshval = list(map((lambda x:1 - (1 / (1 + math.exp(-(x - 0.5) * 24)))), np.arange(100) / 100))
        self.conwayMangled = False

        # Save settings
        self.st = st

        # INITS
        # This means that you have to stop manipulating the controls for half a
        # second for the changes to be sent to the thread. This stops uneccesary
        # restarts, but needs to be tuned for comfort.
        self.initGUI(st)

#=====================Settings controllers================#
    def wolfram_rule(self, val):
        self.st.wolfram.rule = val()

    def wolfram_scale(self, val):
        self.st.wolfram.scale = val()

    def general_wolfwave(self, val):
        self.st.general.wolfwave = val()

    def wolfram_polarity(self, val):
        self.st.wolfram.polarity = val()

    def bounds_upper(self, val):
        self.st.bounds.upper = val()

    def bounds_lower(self, val):
        self.st.bounds.lower = val()

    def bounds_right(self, val):
        self.st.bounds.right = val()

    def bounds_left(self, val):
        self.st.bounds.left = val()

    def canvas_dim(self, val, dim):
        self.st.canvas.dim[dim] = val()

    def ising_updates(self, val):
        self.st.ising.updates = val()

    def ising_equilibrate(self, val):
        self.st.ising.equilibrate = val()

    def ising_degree(self, val):
        self.st.ising.degree = val()

    def canvas_scale(self, val):
        self.st.canvas.scale = val()

    def general_stochastic(self, val):
        self.st.general.stochastic = val()

    def frameChange(self):
        self.st.general.runtodo = self.frameCtrl.value()

    def speedChange(self):
        self.st.general.frametime = 1 / self.speedCtrl.value()
        self.speedLabel.setText('Max FPS = {:d}'.format(int(self.speedCtrl.value())))

    def coverageChange(self):
        coverage = self.thresholdCtrl.value()
        self.st.noise.threshold = self.threshval[coverage]
        self.thresholdLabel.setText('Threshold = {:2.2f}'.format(self.threshval[coverage]))

    def sliderChange(self):
        self.st.ising.beta = self.tempCtrl.value() / 100
        self.tempLabel.setText('Beta = {:01.2f}'.format(self.tempCtrl.value() / 100))

    def choose_color(self, callback, *args):
        dlg = QColorDialog()
        if dlg.exec():
            callback(dlg.selectedColor().name(), *args)

    def set_color(self, hexx, button, num):
        templist = self.st.canvas.colorlist
        templist[num] = QColor(hexx).rgba()
        self.st.canvas.colorlist = templist
        button.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

    #TODO: get rid of this, its dumb
    def conway_mangler(self):
        if self.conwayMangled:
            old = self.conwayRules.toPlainText()
            self.conwayRules.setText(old[2:-2])
            self.conwayMangled = False
        else:
            old = self.conwayRules.toPlainText()
            self.conwayRules.setText('!!{}!!'.format(old))
            self.conwayMangled = True

    def record_change(self):
        self.engine.taskthread.requestInterruption()
        value = not self.st.canvas.record
        self.st.canvas.record = value
        if value:
            self.record.setStyleSheet('QPushButton { background-color: %s; }' %  \
                                            QColor(Qt.red).name())
        else:
            self.record.setStyleSheet('QPushButton { background-color: %s; }' %  \
                                            QColor(Qt.white).name())
            self.gif_creator()
            self.engine.reset_gifcount()


    def rulesChange(self):
        regexTestString=r'^(?:([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:;\ ?)[\ \n]*)+$'
        regexMatchString=r'([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:,\ ?)([0-9])(?:;\ ?)'
        text = self.conwayRules.toPlainText()
        strTest = re.match(regexTestString, text)
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
        self.st.conway.rules = rules
        self.st.general.conway = not rules == []

    def make_fullscreen(self):
        self.st.general.fullscreen = not self.st.general.fullscreen

#=====================Save defaults and GUI ket controls===============#
    def gif_creator(self):
        filenums = [re.findall('([0-9]{4}).png', i) for i in os.listdir('images')]
        fileints = [int(i[0]) for i in filter(None, filenums)]
        rules = ''.join([''.join([str(i) for i in j]) for j in self.st.conway.rules])

# Watermark, off for now
#       overlay_file = ffmpeg.input('images/watermark.png')
#       (
#           ffmpeg
#           .input('images/temp{:04d}.png'.format(max(fileints)))
#           .overlay(overlay_file)
#           .output('images/temp{:04d}.png'.format(max(fileints)))
#           .overwrite_output()
#           .run()
#       )
        (
            ffmpeg
            .input('images/temp%04d.png')
            .output('images/{3}x{4}-frames:{2}-wolf:{1}-rule:{0}.gif'.format(
                rules, self.st.general.wolfwave, max(fileints),
                self.st.canvas.dim[0], self.st.canvas.dim[1]), framerate=5, f='gif')
            .run()
        )
        #TODO: I dont think the framerate variable is doing anything

        filelist = glob.glob('images/temp*.png')
        for i in filelist:
            os.remove(i)


    #TODO: make it save the previous configuration before overwriting
    def save_defaults(self):
        original = safe_load(open('sav/defconf.yml'))
        sav = {'lastsave': unmunchify(self.st)}
        original.update(sav)
        safe_dump(original, open('sav/nowconf.yml', 'w'))

    def keyPressEvent(self, e):
        print(e.key())
        # TODO: make this a dictonary
        if e.key() == Qt.Key_Escape:
            if self.engine.updatethread.isRunning() or self.engine.imagethread.isRunning()\
                    or self.engine.taskthread.isRunning():
                self.st.general.equilibrate = False
                self.st.general.clear = False
                self.st.general.running = False
                self.engine.taskthread.requestInterruption()
                self.engine.updatethread.requestInterruption()
                self.engine.imagethread.quit()
                print('Attempting to interrupt!')
                # TODO: add a 'interrupted by user' popup (after a 'interrupting!'?)
            else:
                self.engine.taskthread.deleteLater()
                self.engine.updatethread.deleteLater()
                self.engine.imagethread.deleteLater()
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
        elif e.key() == Qt.Key_O:
            self.make_fullscreen()
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
        elif e.key() == Qt.Key_1:
            state = self.stochasticBox.isChecked()
            self.stochasticBox.setChecked(not state)
        elif e.key() == Qt.Key_2:
            self.conway_mangler()
        elif e.key() == Qt.Key_E:
            self.dynamic.click()
        elif e.key() == Qt.Key_Q:
            self.clear.click()

##==========================THEGUI==============================##
##==============================================================##
    # Initialise GUI
    def initGUI(self, st):
        # Initialise the thread manager and painter and feed them the UI elements they
        # need to control. TODO: cleaner way of connecting signals to a parent? Using
        # Super perhaps? TODO: pass the guys with args anyway no?
        self.canvas = Canvas()
        self.canvas.initialize(st)
        self.frameLabel = QLabel()
        self.arrayfpsLabel = QLabel()
        self.canvasfpsLabel = QLabel()
        self.engine = EngineOperator(self.canvas, self.frameLabel, self.arrayfpsLabel,
                                     self.canvasfpsLabel, st)

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
        self.thresholdCtrl.setValue(26)
        self.thresholdCtrl.valueChanged.connect(self.coverageChange)
        self.thresholdLabel= QLabel()
        self.thresholdLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.thresholdLabel.setText('Threshold = {:2.2f}'.format(self.st.noise.threshold))
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
        self.conwayRules.setMaximumSize(200, 100)
        self.textHolder = QVBoxLayout()
        self.textHolder.addWidget(self.conwayLabel)
        self.textHolder.addWidget(self.conwayRules)
        self.conwayLabel.setText('Conway Rules')
        self.conwayRules.setText(''.join(['{0},{1},{2},{3};'.format(*i)\
                                          for i in self.st.conway.rules]))
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)

        # Rules controller for cellular automata
        self.automataTop = QLabel('Automata Rules')
        self.automataLabel = QLabel('Rule')
        self.wolfRule = QSpinBox()
        self.wolfRule.setRange(0, 255)
        self.wolfRule.setSingleStep(1)
        self.wolfRule.setValue(self.st.wolfram.rule)
        self.wolfRule.setMaximumSize(100, 40)
        self.wolfRule.valueChanged.connect(partial(self.wolfram_rule,
                                            self.wolfRule.value))
        self.wolfScaleLabel = QLabel('Scale')
        self.wolfScale = QSpinBox()
        self.wolfScale.setRange(1, 100)
        self.wolfScale.setSingleStep(1)
        self.wolfScale.setValue(self.st.wolfram.scale)
        self.wolfScale.setMaximumSize(100, 40)
        self.wolfScale.valueChanged.connect(partial(self.wolfram_scale,
                                                self.wolfScale.value))
        self.wolfCheck = QCheckBox('WolfWaveTM')
        self.wolfCheck.setChecked(self.st.general.wolfwave)
        self.wolfCheck.stateChanged.connect(partial(self.general_wolfwave,
                                            self.wolfCheck.isChecked))
        vbWolf = QVBoxLayout()
        hbt = QHBoxLayout()
        hbt.addWidget(self.automataLabel)
        hbt.addWidget(self.wolfRule)
        hbt1 = QHBoxLayout()
        hbt1.addWidget(self.wolfScaleLabel)
        hbt1.addWidget(self.wolfScale)
        vbWolf.addWidget(self.automataTop)
        vbWolf.addLayout(hbt)
        vbWolf.addLayout(hbt1)
        vbWolf.addWidget(self.wolfCheck)
        rulehb = QHBoxLayout()
        rulehb.addLayout(self.textHolder)
        vlineR = QFrame()
        vlineR.setFrameShape(QFrame.VLine)
        vlineR.setFrameShadow(QFrame.Sunken)
        rulehb.addWidget(vlineR)
        rulehb.addLayout(vbWolf)

        # Boundary conditions
        self.UBL = QLabel('UB')
        self.UB = QSpinBox()
        self.UB.setRange(-1, 1)
        self.UB.setValue(self.st.bounds.upper)
        self.UB.setMaximumSize(40, 40)
        self.UB.valueChanged.connect(partial(self.bounds_upper,
                                        self.UB.value))
        hlineUB = QFrame()
        hlineUB.setFrameShape(QFrame.HLine)
        hlineUB.setFrameShadow(QFrame.Sunken)
        self.LBL = QLabel('LB')
        self.LB = QSpinBox()
        self.LB.setRange(-1, 1)
        self.LB.setValue(self.st.bounds.lower)
        self.LB.setMaximumSize(40, 40)
        self.LB.valueChanged.connect(partial(self.bounds_lower,
                                        self.LB.value))
        vlineLB = QFrame()
        vlineLB.setFrameShape(QFrame.VLine)
        vlineLB.setFrameShadow(QFrame.Sunken)
#       self.boundPole.setMaximumSize(100, 40)
        self.wolfLabel = QLabel('WB')
        self.wolfPole = QSpinBox()
        self.wolfPole.setRange(-1, 1)
        self.wolfPole.setValue(self.st.wolfram.polarity)
        self.wolfPole.setMaximumSize(40, 40)
        self.wolfPole.valueChanged.connect(partial(self.wolfram_polarity,
                                         self.wolfPole.value))
        vlineWB = QFrame()
        vlineWB.setFrameShape(QFrame.VLine)
        vlineWB.setFrameShadow(QFrame.Sunken)
        self.RBL = QLabel('RB')
        self.RB = QSpinBox()
        self.RB.setRange(-1, 1)
        self.RB.setMaximumSize(40, 40)
        self.RB.setValue(self.st.bounds.right)
        self.RB.valueChanged.connect(partial(self.bounds_right,
                                        self.RB.value))
        vlineRB = QFrame()
        vlineRB.setFrameShape(QFrame.VLine)
        vlineRB.setFrameShadow(QFrame.Sunken)
        self.DBL = QLabel('LoB')
        self.DB = QSpinBox()
        self.DB.setRange(-1, 1)
        self.DB.setValue(self.st.bounds.lower)
        self.DB.setMaximumSize(40, 40)
        self.DB.valueChanged.connect(partial(self.bounds_lower,
                                        self.DB.value))
        hlineDB = QFrame()
        hlineDB.setFrameShape(QFrame.HLine)
        hlineDB.setFrameShadow(QFrame.Sunken)
        grPole = QGridLayout()
        grPole.addWidget(self.UBL, 0, 2)
        grPole.addWidget(self.UB, 0, 3)
        grPole.addWidget(hlineUB, 1, 1, 1, 5)
        grPole.addWidget(self.LBL, 2, 0)
        grPole.addWidget(self.LB, 3, 0)
        grPole.addWidget(vlineLB, 2, 1, 3, 1)
        grPole.addWidget(self.wolfLabel, 2, 2)
        grPole.addWidget(self.wolfPole, 3, 2)
        grPole.addWidget(vlineWB, 2, 3, 3, 1)
        grPole.addWidget(self.RBL, 2, 6)
        grPole.addWidget(self.RB, 3, 6)
        grPole.addWidget(vlineRB, 2, 5, 3, 1)
        grPole.addWidget(self.DBL, 6, 2)
        grPole.addWidget(self.DB, 6, 3)
        grPole.addWidget(hlineDB, 5, 1, 1, 5)



        # Default value changer
        NLab = QLabel('WxH')
        NLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.NCtrl = QSpinBox()
        self.NCtrl.setRange(10, 1000)
        self.NCtrl.setSingleStep(10)
        self.NCtrl.setValue(self.st.canvas.dim[0])
        self.NCtrl.setMaximumSize(100, 40)
        self.NCtrl.valueChanged.connect(partial(self.canvas_dim,
                                        self.NCtrl.value, 0))
        self.DCtrl = QSpinBox()
        self.DCtrl.setRange(10, 1000)
        self.DCtrl.setSingleStep(10)
        self.DCtrl.setValue(self.st.canvas.dim[1])
        self.DCtrl.setMaximumSize(100, 40)
        self.DCtrl.valueChanged.connect(partial(self.canvas_dim,
                                        self.DCtrl.value, 1))
        MonteUpLab = QLabel('Monte= ')
        MonteUpLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.MonteUpCtrl = QSpinBox()
        self.MonteUpCtrl.setRange(100, 5000)
        self.MonteUpCtrl.setSingleStep(100)
        self.MonteUpCtrl.setValue(self.st.ising.updates)
        self.MonteUpCtrl.setMaximumSize(100, 40)
        self.MonteUpCtrl.valueChanged.connect(partial(self.ising_updates,
                                        self.MonteUpCtrl.value))
        LongLab = QLabel('Long#= ')
        LongLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.LongCtrl = QSpinBox()
        self.LongCtrl.setRange(10000, 1000000)
        self.LongCtrl.setSingleStep(10000)
        self.LongCtrl.setValue(self.st.ising.equilibrate)
        self.LongCtrl.setMaximumSize(100, 40)
        self.LongCtrl.valueChanged.connect(partial(self.ising_equilibrate,
                                        self.LongCtrl.value))
        DegreeLab = QLabel('Degree= ')
        DegreeLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.DegreeCtrl = QSpinBox()
        self.DegreeCtrl.setRange(2, 10)
        self.DegreeCtrl.setSingleStep(1)
        self.DegreeCtrl.setValue(self.st.ising.degree)
        self.DegreeCtrl.setMaximumSize(100, 40)
        self.DegreeCtrl.valueChanged.connect(partial(self.ising_degree,
                                        self.DegreeCtrl.value))
        ScaleLab = QLabel('Scale= ')
        ScaleLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ScaleCtrl = QSpinBox()
        self.ScaleCtrl.setRange(1, 20)
        self.ScaleCtrl.setSingleStep(1)
        self.ScaleCtrl.setValue(self.st.canvas.scale)
        self.ScaleCtrl.setMaximumSize(100, 40)
        self.ScaleCtrl.valueChanged.connect(partial(self.canvas_scale,
                                        self.ScaleCtrl.value))
        SaveDefaults = QPushButton('Save Defaults')
        SaveDefaults.clicked.connect(self.save_defaults)
        defGr = QGridLayout()
        defGr.addWidget(NLab, 0, 0)
        defGr.addWidget(self.NCtrl, 0, 1)
        defGr.addWidget(self.DCtrl, 0, 2)
        defGr.addWidget(MonteUpLab, 1, 0)
        defGr.addWidget(self.MonteUpCtrl, 1, 1, 1, 2)
        defGr.addWidget(LongLab, 0, 3)
        defGr.addWidget(self.LongCtrl, 0, 4)
        defGr.addWidget(DegreeLab, 1, 3)
        defGr.addWidget(self.DegreeCtrl, 1, 4)
        defGr.addWidget(ScaleLab, 2, 0)
        defGr.addWidget(self.ScaleCtrl, 2, 1, 1, 2)
        defGr.addWidget(SaveDefaults, 2, 3, 1, 2)

#       self.fixedBox = QCheckBox('Fixed')
#       self.fixedBox.setChecked(True)
#      #self.fixedBox.stateChanged.connect(self.fixedChange)
        # TODO make this work
#       sathb = QHBoxLayout()
#       self.satLab = QLabel('Saturation %')
#       self.satLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#       self.satCtrl = QSpinBox()
#       self.satCtrl.setRange(20, 100)
#       self.satCtrl.setSingleStep(10)
#       self.satCtrl.setValue(100)
#       self.satCtrl.setMaximumSize(100, 40)
#       sathb.addWidget(self.fixedBox)
#       sathb.addWidget(self.satLab)
#       sathb.addWidget(self.satCtrl)

        # Color buttons, two for background, two for update and two for mouse.
        self.primaryButton = QPushButton()
        self.primaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.st.canvas.colorlist[0]).name())
        self.primaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.primaryButton, 0))
        self.secondaryButton = QPushButton()
        self.secondaryButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                           QColor(self.st.canvas.colorlist[1]).name())
        self.secondaryButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.secondaryButton, 1))
        self.updateButton = QPushButton()
        self.updateButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.st.canvas.colorlist[2]).name())
        self.updateButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.updateButton, 2))
        self.update2Button = QPushButton()
        self.update2Button.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.st.canvas.colorlist[3]).name())
        self.update2Button.pressed.connect(
            partial(self.choose_color, self.set_color, self.update2Button, 3))
        self.mouseButton = QPushButton()
        self.mouseButton.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.st.canvas.colorlist[4]).name())
        self.mouseButton.pressed.connect(
            partial(self.choose_color, self.set_color, self.mouseButton, 4))
        self.mouse2Button = QPushButton()
        self.mouse2Button.setStyleSheet('QPushButton { background-color: %s; }' %
                                         QColor(self.st.canvas.colorlist[5]).name())
        self.mouse2Button.pressed.connect(
            partial(self.choose_color, self.set_color, self.mouse2Button, 5))
        self.gr = QGridLayout()
        self.gr.addWidget(self.primaryButton, 0, 0)
        self.gr.addWidget(self.secondaryButton, 1, 0)
        self.gr.addWidget(self.updateButton, 0, 1)
        self.gr.addWidget(self.update2Button, 1, 1)
        self.gr.addWidget(self.mouseButton, 0, 2)
        self.gr.addWidget(self.mouse2Button, 1, 2)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)
        hline2 = QFrame()
        hline2.setFrameShape(QFrame.HLine)
        hline2.setFrameShadow(QFrame.Sunken)
        hline3 = QFrame()
        hline3.setFrameShape(QFrame.HLine)
        hline3.setFrameShadow(QFrame.Sunken)
        hline4 = QFrame()
        hline4.setFrameShape(QFrame.HLine)
        hline4.setFrameShadow(QFrame.Sunken)
        hline5 = QFrame()
        hline5.setFrameShape(QFrame.HLine)
        hline5.setFrameShadow(QFrame.Sunken)
        hline6 = QFrame()
        hline6.setFrameShape(QFrame.HLine)
        hline6.setFrameShadow(QFrame.Sunken)
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Sunken)
        vline2 = QFrame()
        vline2.setFrameShape(QFrame.VLine)
        vline2.setFrameShadow(QFrame.Sunken)

        # Collects all of the above into a column.
        vb = QVBoxLayout()
        vb.addWidget(self.dynamic)
        vb.addLayout(tlhb)
        vb.addWidget(hline)
        vb.addWidget(hline2)
        vb.addLayout(rulehb)
        vb.addLayout(grPole)
        vb.addStretch()
        vb.addWidget(hline3)
        vb.addWidget(hline4)
        vb.addLayout(defGr)
#       vb.addLayout(sathb)
        vb.addStretch()
        vb.addWidget(hline5)
        vb.addWidget(hline6)
        vb.addLayout(self.gr)

##===================Canvas and controls, right======================##
        # Stats at the top of the canvas
        statBox = QHBoxLayout()
        self.canvasfpsLabel.setText('Canvas fps: ')
        self.arrayfpsLabel.setText('Array fps: ')
        self.record = QPushButton()
        self.record.setText('Record')
        self.record.clicked.connect(self.record_change)
        statBox.addWidget(self.canvasfpsLabel)
        statBox.addWidget(self.arrayfpsLabel)
        statBox.addWidget(self.record)

        # Temperature slider and label
        self.tempCtrl = QSlider(Qt.Horizontal)
        self.tempCtrl.setTickPosition(QSlider.TicksAbove)
        self.tempCtrl.setTickInterval(20)
        self.tempLabel = QLabel()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(200)
        self.tempCtrl.setPageStep(20)
        self.tempCtrl.setValue(self.st.ising.beta * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = {:01.2f}'.format(self.st.ising.beta))

        # Speed slider and label
        # TODO: get this working again
        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(int(1 / self.st.general.frametime))
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel = QLabel()
        self.speedLabel.setText('Max FPS = {:03d}'.format(int(1 / self.st.general.frametime)))
        self.frameLabel.setText('0000/ ')
        self.frameCtrl = QSpinBox()
        self.frameCtrl.setRange(-1, 2000)
        self.frameCtrl.setSingleStep(10)
        self.frameCtrl.setMaximumSize(100, 20)
        self.frameCtrl.setValue(self.st.general.runtodo)
        self.frameCtrl.valueChanged.connect(self.frameChange)

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
        self.stochasticBox.setChecked(self.st.general.stochastic)
        self.stochasticBox.stateChanged.connect(partial(self.general_stochastic,
                                                    self.stochasticBox.isChecked))

        rbbR.addLayout(rbbRt)
        rbbR.addWidget(self.stochasticBox)
        rbb = QHBoxLayout()
        rbb.addLayout(rbbL)
        rbb.addLayout(rbbM)
        rbb.addLayout(rbbR)

        # Layout canvas and sliders
        hliner1 = QFrame()
        hliner1.setFrameShape(QFrame.HLine)
        hliner1.setFrameShadow(QFrame.Sunken)
        hliner2 = QFrame()
        hliner2.setFrameShape(QFrame.HLine)
        hliner2.setFrameShadow(QFrame.Sunken)
        hliner3 = QFrame()
        hliner3.setFrameShape(QFrame.HLine)
        hliner3.setFrameShadow(QFrame.Sunken)
        hliner4 = QFrame()
        hliner4.setFrameShape(QFrame.HLine)
        hliner4.setFrameShadow(QFrame.Sunken)
        rb = QVBoxLayout()
        rb.addLayout(statBox)
        rb.addWidget(hliner1)
        rb.addWidget(hliner2)
        rb.addWidget(self.canvas)
        rb.addWidget(hliner3)
        rb.addWidget(hliner4)
        rb.addLayout(rbb)

        # Layout control column and canvasbox
        hb = QHBoxLayout()
        hb.addLayout(vb)
        hb.addWidget(vline)
        hb.addWidget(vline2)
        hb.addLayout(rb)

        self.setLayout(hb)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')
