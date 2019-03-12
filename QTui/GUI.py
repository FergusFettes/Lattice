from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial

from QTui.engineOperator import *
from QTui.graphs import *

import random as ra
import math
import ffmpeg
import os
import re
import glob
from munch import *
from yaml import safe_load, safe_dump


import logging
LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

#====================The canvas=================#
class Canvas(QLabel):

    def __init__(self, st):
        super().__init__()
        self.primaryColor = QColor(st.canvas.colorlist[0])
        self.st = st
        self.reset()

    def reset(self):
        self.setPixmap(QPixmap(self.st.canvas.dim[0] * self.st.canvas.scale,
                               self.st.canvas.dim[1] * self.st.canvas.scale))
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

    def __init__(self, st):
        super().__init__()

        # Internal Vars
        # This is the sigmoid for makeing the threshold.
        # To make it less steep (ie less flat at the top and bottom), reduce the #24.
        self.threshval = list(map((lambda x:1 - (1 / (1 + math.exp(-(x - 0.5) * 24)))), np.arange(100) / 100))
        self.conwayMangled = False

        # Save settings
        self.st = st

        self.initGUI(st)

#=====================Settings controllers================#
    # I had to make all of these because of a disaster with adding partial functions
    # to the button callback thingies. This can presumably be done much better.
    def update_toggle(self):
        self.st.general.update = True

    def wolfram_rule(self, val):
        self.st.wolfram.rule = val()

    def wolfram_scale(self, val):
        self.st.wolfram.scale = val()

    def general_wolfwave(self, val):
        self.st.general.wolfwave = val()

    def wolfram_polarity(self, val):
        self.st.wolfram.polarity = val()

    def bounds_upper(self, val):
        self.st.bounds[3] = val()

    def bounds_right(self, val):
        self.st.bounds[2] = val()

    def bounds_lower(self, val):
        self.st.bounds[1] = val()

    def bounds_left(self, val):
        self.st.bounds[0] = val()

    def Vroll_update(self, val):
        self.st.transform.roll[0] = val()

    def Hroll_update(self, val):
        self.st.transform.roll[1] = val()

    def canvas_dim(self, val, dim):
        self.st.canvas.dim[dim] = val()
        self.st.general.resize = True

    def ising_updates(self, val):
        self.st.ising.updates = val() / 100

    def ising_equilibrate(self, val):
        self.st.ising.equilibrate = val()

    def ising_degree(self, val):
        self.st.ising.degree = val()

    def canvas_scale(self, val):
        self.st.canvas.scale = val()

    def general_growth(self, val):
        self.st.general.growth = val()

    def general_stochastic(self, val):
        self.st.noise.switch = val()

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

    def growth_switch(self):
        state = self.growthBox.isChecked()
        self.growthBox.setChecked(not state)

    def stochi_switch(self):
        state = self.stochasticBox.isChecked()
        self.stochasticBox.setChecked(not state)

    def choose_color(self, callback, *args):
        dlg = QColorDialog()
        if dlg.exec():
            callback(dlg.selectedColor().name(), *args)

    def set_color(self, hexx, button, num):
        templist = self.st.canvas.colorlist
        templist[num] = QColor(hexx).rgba()
        self.st.canvas.colorlist = templist
        button.setStyleSheet('QPushButton { background-color: %s; }' % hexx)

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
        logging.info(self.rul)
        self.send_rule()

    def send_rule(self):
        print('Rule sending!')
        rules = [[int(j) for j in i] for i in self.rul]
        if rules == []: rules = np.array([[-1,0,0,0]], np.intc)
        self.st.conway.rules = rules


    def barRulesChange(self):
        regexTestString=r'^(?:([0-9]*\.[0-9]*)(?:,\ ?)([0-9]*\.[0-9]*)(?:,\ ?)(-?[0-9]*\.[0-9]*)(?:,\ ?)([0-9]*\.[0-9]*)(?:,\ ?)([0-9]*\.[0-9]*)(?:,\ ?)(-?[0-9]*\.[0-9]*)(?:;\ ?)[\ \n]*)+$'
        regexMatchString=r'([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:;\ ?)'
        text = self.barRules.toPlainText()
        strTest = re.match(regexTestString, text)
        if strTest is None:
            self.barPalette.setColor(QPalette.Base, Qt.red)
            self.barRules.setPalette(self.barPalette)
            ruleIter = re.finditer(regexTestString, text)
            self.bar = [i.group(1,2,3,4,5,6) for i in ruleIter]
        else:
            self.barPalette.setColor(QPalette.Base, Qt.green)
            self.barRules.setPalette(self.barPalette)
            ruleIter = re.finditer(regexMatchString, text)
            self.bar = [i.group(1,2,3,4,5,6) for i in ruleIter]
        logging.info(self.bar)
        self.send_bar()

    def send_bar(self):
        print('Bar sending!')
        rules = [[float(j) for j in i] for i in self.bar]
        self.st.scroll.bars = rules

    def fuzzRulesChange(self):
        regexTestString=r'^(?:([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:;\ ?)[\ \n]*)+$'
        regexMatchString=r'([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)([0-9]+\.[0-9]+)(?:,\ ?)(-?[0-9]+\.[0-9]+)(?:;\ ?)'
        text = self.fuzzRules.toPlainText()
        strTest = re.match(regexTestString, text)
        if strTest is None:
            self.fuzzPalette.setColor(QPalette.Base, Qt.red)
            self.fuzzRules.setPalette(self.fuzzPalette)
            ruleIter = re.finditer(regexTestString, text)
            self.fuzz = [i.group(1,2,3,4,5,6,7) for i in ruleIter]
        else:
            self.fuzzPalette.setColor(QPalette.Base, Qt.green)
            self.fuzzRules.setPalette(self.fuzzPalette)
            ruleIter = re.finditer(regexMatchString, text)
            self.fuzz = [i.group(1,2,3,4,5,6,7) for i in ruleIter]
        logging.info(self.fuzz)
        self.send_fuzz()

    def send_fuzz(self):
        print('Fuzz sending!')
        rules = [[float(j) for j in i] for i in self.fuzz]
        self.st.scroll.fuzz = rules

    def make_fullscreen(self):
        self.st.canvas.fullscreen = not self.st.canvas.fullscreen

#=====================Save defaults and GUI ket controls===============#
    def gif_creator(self):
        filenums = [re.findall('([0-9]{4}).png', i) for i in os.listdir('images')]
        fileints = [int(i[0]) for i in filter(None, filenums)]
        rules = ''.join([''.join([str(i) for i in j]) for j in self.st.conway.rules])

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
        sav = {'lastsave': unmunchify(self.st)}
        safe_dump(sav, open('sav/nowconf.yml', 'w'))

    def shutdown(self):
        if self.engine.taskthread.isRunning():
            self.st.general.equilibrate = False
            self.st.general.clear = False
            self.st.general.running = False
            self.engine.taskthread.requestInterruption()
            print('Attempting to interrupt!')
        else:
            self.engine.taskthread.deleteLater()
            QCoreApplication.instance().quit()
            print('Threads shutting down and powering off')

    def keyPressEvent(self, e):
        keys = {
            Qt.Key_Escape:self.shutdown,
            16777251:self.speedCtrl.setFocus, #left alt key
            Qt.Key_C:partial(self.speedCtrl.triggerAction, QSlider.SliderPageStepAdd),
            Qt.Key_X:partial(self.speedCtrl.triggerAction, QSlider.SliderPageStepSub),
            Qt.Key_O:self.make_fullscreen,
            Qt.Key_D:partial(self.tempCtrl.triggerAction, QSlider.SliderPageStepAdd),
            Qt.Key_A:partial(self.tempCtrl.triggerAction, QSlider.SliderPageStepSub),
            Qt.Key_W:partial(self.thresholdCtrl.triggerAction, QSlider.SliderPageStepAdd),
            Qt.Key_S:partial(self.thresholdCtrl.triggerAction, QSlider.SliderPageStepSub),
            Qt.Key_R:self.primaryButton.click,
            Qt.Key_F:self.secondaryButton.click,
            Qt.Key_E:self.dynamic.click,
            Qt.Key_1:self.stochi_switch,
            Qt.Key_2:self.growth_switch,
        }
        keys[e.key()]()

##==========================THEGUI==============================##
##==============================================================##
    # Initialise GUI
    def initGUI(self, st):
        # Initialise the thread manager and painter and feed them the UI elements they
        # need to control.
        self.canvas = Canvas(st)
        self.frameLabel = QLabel()
        self.arrayfpsLabel = QLabel()
        self.canvasfpsLabel = QLabel()
        self.statusBar = super().statusBar()
        self.engine = EngineOperator(self.canvas, self.frameLabel, self.arrayfpsLabel,
                                     self.canvasfpsLabel, st)
        self.setDockNestingEnabled(True)

##====================Controlls on the left====================##
#MENUS/TOOLBARS==========================================
#================================================MainMenu
        self.MainMenu = QToolBar('Main Buttons')
        # Main pushbutton, this should be better highlighted.
        self.dynamic = QPushButton()
        self.dynamic.setText('Dynamic')
        self.dynamic.setStyleSheet('QPushButton { background-color: %s; }' %  \
                                         QColor('#ffff00ff').name())
        self.dynamic.clicked.connect(self.engine.dynamic_run)
        self.MainMenu.addWidget(self.dynamic)

        # Buttons and slider in the top left
        self.update = self.MainMenu.addAction('Update', self.update_toggle)
        self.update.setShortcuts(QKeySequence(Qt.Key_U))
#       self.equilibrate = self.MainMenu.addAction('Equilibrate', self.engine.long_run)
#       self.equilibrate.setShortcuts(QKeySequence(Qt.Key_L))
#       self.clear = self.MainMenu.addAction('Clear', self.engine.clear_array)
#       self.clear.setShortcuts(QKeySequence(Qt.Key_Q))
#       self.background = self.MainMenu.addAction('Background', self.engine.clear_background)
#       self.background.setShortcuts(QKeySequence(Qt.Key_B))

        self.tools = {'main': self.MainMenu}
        self.addToolBar(Qt.TopToolBarArea, self.MainMenu)
#..............................................................


#================================================WolframTool
#       self.WolframTool = QToolBar('Automata Rules')
#       self.automataLabel = QLabel('Rule')
#       self.WolframTool.addWidget(self.automataLabel)
#       self.wolfRule = QSpinBox()
#       self.wolfRule.setRange(0, 255)
#       self.wolfRule.setSingleStep(1)
#       self.wolfRule.setValue(self.st.wolfram.rule)
#       self.wolfRule.valueChanged.connect(partial(self.wolfram_rule,
#                                           self.wolfRule.value))
#       self.WolframTool.addWidget(self.wolfRule)
#       self.wolfScaleLabel = QLabel('Scale')
#       self.WolframTool.addWidget(self.wolfScaleLabel)
#       self.wolfScale = QSpinBox()
#       self.wolfScale.setRange(1, 100)
#       self.wolfScale.setSingleStep(1)
#       self.wolfScale.setValue(self.st.wolfram.scale)
#       self.wolfScale.valueChanged.connect(partial(self.wolfram_scale,
#                                               self.wolfScale.value))
#       self.WolframTool.addWidget(self.wolfScale)
#       self.wolfCheck = QCheckBox('WolfWaveTM')
#       self.wolfCheck.setChecked(self.st.general.wolfwave)
#       self.wolfCheck.stateChanged.connect(partial(self.general_wolfwave,
#                                           self.wolfCheck.isChecked))
#       self.WolframTool.addWidget(self.wolfCheck)

#       self.wolfLabel = QLabel('Polarity')
#       self.WolframTool.addWidget(self.wolfLabel)
#       self.wolfPole = QSpinBox()
#       self.wolfPole.setRange(-1, 1)
#       self.wolfPole.setValue(self.st.wolfram.polarity)
#       self.wolfPole.valueChanged.connect(partial(self.wolfram_polarity,
#                                        self.wolfPole.value))
#       self.WolframTool.addWidget(self.wolfPole)

#       self.tools = {'wolf': self.WolframTool}
#       self.addToolBar(Qt.TopToolBarArea, self.WolframTool)
#............................................................

#====================================================SettingsTool
        self.SettingsTool = QToolBar('Settings')
        # Default value changer
        NLab = QLabel('WxH')
        NLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.SettingsTool.addWidget(NLab)
        self.NCtrl = QSpinBox()
        self.NCtrl.setRange(10, 1000)
        self.NCtrl.setSingleStep(10)
        self.NCtrl.setValue(self.st.canvas.dim[0])
        self.NCtrl.valueChanged.connect(partial(self.canvas_dim,
                                        self.NCtrl.value, 0))
        self.SettingsTool.addWidget(self.NCtrl)
        self.DCtrl = QSpinBox()
        self.DCtrl.setRange(10, 1000)
        self.DCtrl.setSingleStep(10)
        self.DCtrl.setValue(self.st.canvas.dim[1])
        self.DCtrl.valueChanged.connect(partial(self.canvas_dim,
                                        self.DCtrl.value, 1))
        self.SettingsTool.addWidget(self.DCtrl)
        MonteUpLab = QLabel('Updates= ')
        MonteUpLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.SettingsTool.addWidget(MonteUpLab)
        self.MonteUpCtrl = QSpinBox()
        self.MonteUpCtrl.setRange(0, 500)
        self.MonteUpCtrl.setSingleStep(1)
        self.MonteUpCtrl.setValue(self.st.ising.updates * 100)
        self.MonteUpCtrl.valueChanged.connect(partial(self.ising_updates,
                                        self.MonteUpCtrl.value))
        self.SettingsTool.addWidget(self.MonteUpCtrl)
        ScaleLab = QLabel('Scale= ')
        ScaleLab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.SettingsTool.addWidget(ScaleLab)
        self.ScaleCtrl = QSpinBox()
        self.ScaleCtrl.setRange(1, 20)
        self.ScaleCtrl.setSingleStep(1)
        self.ScaleCtrl.setValue(self.st.canvas.scale)
        self.ScaleCtrl.valueChanged.connect(partial(self.canvas_scale,
                                        self.ScaleCtrl.value))
        self.SettingsTool.addWidget(self.ScaleCtrl)
        SaveDefaults = QPushButton('Save Defaults')
        SaveDefaults.clicked.connect(self.save_defaults)
        self.SettingsTool.addWidget(SaveDefaults)

        self.tools = {'settings': self.SettingsTool}
        self.addToolBar(Qt.TopToolBarArea, self.SettingsTool)
#............................................................

#====================================================ColorTool
        self.ColorTool = QToolBar('ColorChooser')

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
        self.ColorTool.addWidget(QLabel('Primary'))
        temp = QHBoxLayout()
        temp.addWidget(self.primaryButton)
        temp.addWidget(self.secondaryButton)
        tempwidget = QWidget()
        tempwidget.setLayout(temp)
        self.ColorTool.addWidget(tempwidget)
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
        self.ColorTool.addWidget(QLabel('Secondary'))
        temp = QHBoxLayout()
        temp.addWidget(self.updateButton)
        temp.addWidget(self.update2Button)
        tempwidget = QWidget()
        tempwidget.setLayout(temp)
        self.ColorTool.addWidget(tempwidget)
#       self.mouseButton = QPushButton()
#       self.mouseButton.setStyleSheet('QPushButton { background-color: %s; }' %
#                                        QColor(self.st.canvas.colorlist[4]).name())
#       self.mouseButton.pressed.connect(
#           partial(self.choose_color, self.set_color, self.mouseButton, 4))
#       self.mouse2Button = QPushButton()
#       self.mouse2Button.setStyleSheet('QPushButton { background-color: %s; }' %
#                                        QColor(self.st.canvas.colorlist[5]).name())
#       self.mouse2Button.pressed.connect(
#           partial(self.choose_color, self.set_color, self.mouse2Button, 5))
#       self.ColorTool.addWidget(QLabel('Tertiary'))
#       temp = QHBoxLayout()
#       temp.addWidget(self.mouseButton)
#       temp.addWidget(self.mouse2Button)
#       tempwidget = QWidget()
#       tempwidget.setLayout(temp)
#       self.ColorTool.addWidget(tempwidget)

        self.tools = {'color': self.ColorTool}
        self.addToolBar(Qt.TopToolBarArea, self.ColorTool)
#............................................................

#DOCKWIDGETS=====================================================
#====================================================AutomataDock
        # Conway rule selector
        self.conwayRules = QTextEdit()
        self.conwayRules.setMaximumSize(200, 30)
        self.conwayRules.setText(''.join(['{0},{1},{2},{3};'.format(*i)\
                                          for i in self.st.conway.rules]))
        self.conwayPalette = self.conwayRules.palette()
        self.conwayPalette.setColor(QPalette.Base, Qt.green)
        self.conwayRules.setPalette(self.conwayPalette)
        self.conwayRules.setAcceptRichText(False)
        self.conwayRules.textChanged.connect(self.rulesChange)

        #Wrap that all up in a DockWidget
        self.AutomataButtons = QDockWidget('Conway Rules')
        self.buts = {'auto': self.AutomataButtons}
        self.AutomataButtons.setWidget(self.conwayRules)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.AutomataButtons)
#............................................................

#DOCKWIDGETS=====================================================
#========================================================BarsDock
        # Conway rule selector
        self.barRules = QTextEdit()
        self.barRules.setMaximumSize(200, 80)
        self.barRules.setText(''.join(['{0},{1},{2},{3},{4},{5};'.format(*i)\
                                          for i in self.st.scroll.bars]))
        self.barPalette = self.barRules.palette()
        self.barPalette.setColor(QPalette.Base, Qt.green)
        self.barRules.setPalette(self.barPalette)
        self.barRules.setAcceptRichText(False)
        self.barRules.textChanged.connect(self.barRulesChange)

        #Wrap that all up in a DockWidget
        self.BarButtons = QDockWidget('Bar Rules')
        self.buts.update({'bar': self.BarButtons})
        self.BarButtons.setWidget(self.barRules)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.BarButtons)
#............................................................

#DOCKWIDGETS=====================================================
#========================================================FuzzDock
        # Conway rule selector
        self.fuzzRules = QTextEdit()
        self.fuzzRules.setMaximumSize(200, 80)
        self.fuzzRules.setText(''.join(['{0},{1},{2},{3},{4},{5},{6};'.format(*i)\
                                          for i in self.st.scroll.fuzz]))
        self.fuzzPalette = self.fuzzRules.palette()
        self.fuzzPalette.setColor(QPalette.Base, Qt.green)
        self.fuzzRules.setPalette(self.fuzzPalette)
        self.fuzzRules.setAcceptRichText(False)
        self.fuzzRules.textChanged.connect(self.fuzzRulesChange)

        #Wrap that all up in a DockWidget
        self.FuzzButtons = QDockWidget('Fuzz Rules')
        self.buts.update({'fuzz': self.FuzzButtons})
        self.FuzzButtons.setWidget(self.fuzzRules)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.FuzzButtons)
#............................................................

#=======================================================RollDock
        # Roll settings
        self.HrollL = QLabel('HRoll')
        self.Hroll = QSpinBox()
        self.Hroll.setRange(-1, 1)
        self.Hroll.setValue(self.st.transform.roll[1])
        self.Hroll.setMaximumSize(40, 40)
        self.Hroll.valueChanged.connect(partial(self.Hroll_update,
                                        self.Hroll.value))
        hlineHroll = QFrame()
        hlineHroll.setFrameShape(QFrame.HLine)
        hlineHroll.setFrameShadow(QFrame.Sunken)
        self.VrollL = QLabel('VRoll')
        self.Vroll = QSpinBox()
        self.Vroll.setRange(-1, 1)
        self.Vroll.setMaximumSize(40, 40)
        self.Vroll.setValue(self.st.transform.roll[0])
        self.Vroll.valueChanged.connect(partial(self.Vroll_update,
                                        self.Vroll.value))
        vlineVroll = QFrame()
        vlineVroll.setFrameShape(QFrame.VLine)
        vlineVroll.setFrameShadow(QFrame.Sunken)
        grRoll = QGridLayout()
        grRoll.addWidget(self.HrollL, 0, 1)
        grRoll.addWidget(self.Hroll, 0, 2)
        grRoll.addWidget(hlineHroll, 1, 0, 1, 4)
        grRoll.addWidget(self.VrollL, 2, 5)
        grRoll.addWidget(self.Vroll, 3, 5)
        grRoll.addWidget(vlineVroll, 2, 4, 3, 1)


        #Wrap that all up in a DockWidget
        self.RollButtons = QDockWidget('Roll Controls')
        self.buts.update({'roll': self.RollButtons})
        temp = QWidget()
        temp.setLayout(grRoll)
        self.RollButtons.setWidget(temp)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.RollButtons)
#............................................................

#====================================================BoundaryDock
        # Boundary conditions
        self.UBL = QLabel('UB')
        self.UB = QSpinBox()
        self.UB.setRange(-1, 1)
        self.UB.setValue(self.st.bounds[3])
        self.UB.setMaximumSize(40, 40)
        self.UB.valueChanged.connect(partial(self.bounds_upper,
                                        self.UB.value))
        vlineLB = QFrame()
        vlineLB.setFrameShape(QFrame.VLine)
        vlineLB.setFrameShadow(QFrame.Sunken)
        self.RBL = QLabel('RB')
        self.RB = QSpinBox()
        self.RB.setRange(-1, 1)
        self.RB.setMaximumSize(40, 40)
        self.RB.setValue(self.st.bounds[2])
        self.RB.valueChanged.connect(partial(self.bounds_right,
                                        self.RB.value))
        vlineRB = QFrame()
        vlineRB.setFrameShape(QFrame.VLine)
        vlineRB.setFrameShadow(QFrame.Sunken)
        self.DBL = QLabel('LoB')
        self.DB = QSpinBox()
        self.DB.setRange(-1, 1)
        self.DB.setValue(self.st.bounds[1])
        self.DB.setMaximumSize(40, 40)
        self.DB.valueChanged.connect(partial(self.bounds_lower,
                                        self.DB.value))
        hlineUB = QFrame()
        hlineUB.setFrameShape(QFrame.HLine)
        hlineUB.setFrameShadow(QFrame.Sunken)
        self.LBL = QLabel('LB')
        self.LB = QSpinBox()
        self.LB.setRange(-1, 1)
        self.LB.setValue(self.st.bounds[0])
        self.LB.setMaximumSize(40, 40)
        self.LB.valueChanged.connect(partial(self.bounds_left,
                                        self.LB.value))
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
        grPole.addWidget(self.RBL, 2, 6)
        grPole.addWidget(self.RB, 3, 6)
        grPole.addWidget(vlineRB, 2, 5, 3, 1)
        grPole.addWidget(self.DBL, 6, 2)
        grPole.addWidget(self.DB, 6, 3)
        grPole.addWidget(hlineDB, 5, 1, 1, 5)


        #Wrap that all up in a DockWidget
        self.BoundaryButtons = QDockWidget('Boundary Controls')
        self.buts.update({'bound': self.BoundaryButtons})
        temp = QWidget()
        temp.setLayout(grPole)
        self.BoundaryButtons.setWidget(temp)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.BoundaryButtons)
#............................................................
##===================Canvas and controls, right======================##
#====================================================StatusBar
        # Stats at the top of the canvas
        self.canvasfpsLabel.setText('Canvas fps: ')
        self.arrayfpsLabel.setText('Array fps: ')
#       self.record = QPushButton()
#       self.record.setText('Record')
#       self.record.clicked.connect(self.record_change)
        self.stochasticBox = QCheckBox('Stochi')
        self.stochasticBox.setChecked(self.st.noise.switch)
        self.stochasticBox.stateChanged.connect(partial(self.general_stochastic,
                                                    self.stochasticBox.isChecked))
        self.growthBox = QCheckBox('Growth')
        self.growthBox.setChecked(self.st.general.growth)
        self.growthBox.stateChanged.connect(partial(self.general_growth,
                                                    self.growthBox.isChecked))
        self.statusBar.addWidget(self.canvasfpsLabel)
        self.statusBar.addWidget(self.arrayfpsLabel)
#       self.statusBar.addWidget(self.record)
        self.statusBar.addWidget(self.stochasticBox)
        self.statusBar.addWidget(self.growthBox)
#............................................................

#====================================================SubControlDock
        # Temperature slider and label
        self.tempCtrl = QSlider(Qt.Horizontal)
        self.tempCtrl.setTickPosition(QSlider.TicksBelow)
        self.tempCtrl.setTickInterval(20)
        self.tempLabel = QLabel()
        self.tempCtrl.setMinimum(10)
        self.tempCtrl.setMaximum(200)
        self.tempCtrl.setPageStep(20)
        self.tempCtrl.setValue(self.st.ising.beta * 100)
        self.tempCtrl.valueChanged.connect(self.sliderChange)
        self.tempLabel.setText('Beta = {:01.2f}'.format(self.st.ising.beta))

        # Speed slider and label
        self.speedCtrl = QSlider(Qt.Horizontal)
        self.speedCtrl.setTickPosition(QSlider.TicksBelow)
        self.speedCtrl.setTickInterval(20)
        self.speedCtrl.setMinimum(1)
        self.speedCtrl.setMaximum(100)
        self.speedCtrl.setValue(int(1 / self.st.general.frametime))
        self.speedCtrl.valueChanged.connect(self.speedChange)
        self.speedLabel = QLabel()
        self.speedLabel.setText('Max FPS = {:03d}'.format(int(1 / self.st.general.frametime)))
        self.frameLabel.setText('Frames: {:04d}/'.format(0))
        self.frameCtrl = QSpinBox()
        self.frameCtrl.setRange(-1, 2000)
        self.frameCtrl.setSingleStep(10)
        self.frameCtrl.setMaximumSize(100, 20)
        self.frameCtrl.setValue(self.st.general.runtodo)
        self.frameCtrl.valueChanged.connect(self.frameChange)

        self.thresholdCtrl = QSlider(Qt.Horizontal)
        self.thresholdCtrl.setTickPosition(QSlider.TicksBelow)
        self.thresholdCtrl.setTickInterval(20)
        self.thresholdCtrl.setMinimum(0)
        self.thresholdCtrl.setMaximum(99)
        self.thresholdCtrl.setPageStep(4)
        self.thresholdCtrl.setValue(26)
        self.thresholdCtrl.valueChanged.connect(self.coverageChange)
        self.thresholdLabel= QLabel()
        self.thresholdLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.thresholdLabel.setText('Threshold = {:2.2f}'.format(self.st.noise.threshold))

        # 'right bottom box' -- sorts out the sliders
        rbb = QHBoxLayout()
        rbb.addWidget(self.tempLabel)
        rbb.addWidget(self.tempCtrl)
        rbb.addWidget(self.thresholdLabel)
        rbb.addWidget(self.thresholdCtrl)
        rbb.addWidget(self.speedLabel)
        rbb.addWidget(self.speedCtrl)
        rbb.addWidget(self.frameLabel)
        rbb.addWidget(self.frameCtrl)

        #Wrap that all up in a DockWidget
        self.Sliders = QDockWidget('Settings Sliders')
        self.buts.update({'sliders': self.Sliders})
        temp = QWidget()
        temp.setLayout(rbb)
        self.Sliders.setWidget(temp)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.Sliders)
#............................................................

#========================================================CanvasDock
        #Wrap that all up in a DockWidget
        self.CanvasDock = QDockWidget()
        self.buts.update({'canvas': self.CanvasDock})
        self.CanvasDock.setWidget(self.canvas)
        self.setCentralWidget(self.CanvasDock)
#............................................................

        self.buts['auto'].setMaximumSize(300,200)
        self.buts['bound'].setMaximumSize(200,150)
        self.buts['sliders'].setMaximumSize(1500,100)
        self.show()

        # The allows i3 to popup the window (add to i3/config)
        # 'for_window [window_role='popup'] floating enable'
        self.setWindowRole('popup')
