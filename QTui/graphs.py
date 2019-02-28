from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
import numpy as np
from src.pureUp import *


class Graphs(pg.GraphicsView):
    def __init__(self):
        super().__init__()

        """
        Demonstrate the use of layouts to control placement of multiple plots / selfs /
        labels
        """
        l = pg.GraphicsLayout(border=(100,100,100))
        super().setCentralItem(l)
        super().setWindowTitle('THE SCIENCE GOES HERE')

        self.plots = {'description':'a list of plots'}

        ## Title at top
        text = """
        Array in, science out.
        """
        l.addLabel(text, col=1, colspan=2)
        l.nextRow()

        ## Put vertical label on left side
        l.addLabel('Serious Biznis', angle=-90, rowspan=3)

        ## Add 3 plots into the first row (automatic position)
        self.p1 = l.addPlot(title="Population")
        self.plots.update({'p1': self.p1})
        vb = l.addViewBox(lockAspect=True)
        img = pg.ImageItem(np.random.normal(size=(100,100)))
        vb.addItem(img)
        vb.autoRange()

        ## Add a sub-layout into the second row (automatic position)
        ## The added item should avoid the first column, which is already filled
        l.nextRow()
        self.p2 = l.addPlot(title="Radius", col=1, colspan=2)
        self.plots.update({'p2': self.p2})

        ## Add 2 more plots into the third row (manual position)
        self.p3 = l.addPlot(row=3, col=1, colspan=2)
        self.plots.update({'p3': self.p3})

    def paint(self, data, plot):
        self.plots[plot].plot(data)
