import array

import pandas as pd
import numpy as np
import time

import src.Cfuncs as cf
import src.Pfuncs as pf
import src.Cyphys as cph
import src.Cyarr as cy
import src.PHifuncs as phi

import logging
LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

class Run():

    def __init__(self, length=1000, dim=np.array([20, 20], np.intc), beta=1/8, updates=0,
                 threshold=0, rules=np.array([[2,3,3,3]], np.intc)):
        self.TOTTIME = time.time()
        self.RUNTIME = 0
        self.RUNNING = True
        self.LENGTH = length
        self.DIM = np.asarray(dim, np.intc)
        self.ARR = cf.init_array(self.DIM)
        cy.clear_array(self.DIM, self.ARR)
        self.ARR_OLD = np.copy(self.ARR)
        self.DIM_OLD = np.copy(self.DIM)
        self.FRAME = array.array('i', [0])

        self.BETA = beta
        self.UPDATES = updates
        self.THRESHOLD = threshold
        self.RULES = np.asarray(rules, np.intc)

        self.COM = cph.center_of_mass(self.DIM, self.ARR)

        self.TOT = np.zeros(self.LENGTH, np.intc)
        self.RG = np.zeros(self.LENGTH, np.float32)
        self.E = np.zeros_like(self.RG)
        self.E2 = np.zeros_like(self.RG)
        self.M = np.zeros_like(self.RG)
        self.CHANGE = np.zeros((self.LENGTH, 2), np.intc)
        self.AXES = np.zeros((self.LENGTH, 2), np.intc)

        if not np.asarray(self.COM).any():
            self.COM = np.array([self.DIM[0]/2, self.DIM[1]/2], np.float32)

    def basic_update(self):
        self.ARR_OLD = np.copy(self.ARR)
        self.DIM_OLD = np.copy(self.DIM)
        logging.debug('Basic update')
        cf.ising_process(self.UPDATES, self.BETA, self.DIM, self.ARR)
        cf.add_stochastic_noise(self.THRESHOLD, self.DIM, self.ARR)
        cf.conway_process(cf.prepair_rule(self.RULES, self.FRAME), self.DIM, self.ARR)
        logging.debug('Change zoom level')
        if self.DIM[0] <= 4:
            self.RUNNING = False

        self.DIM, self.ARR, _ = cf.change_zoom_level_array(self.DIM, self.ARR)

    def analysis(self):

        tot, live, self.COM, Rg, e, e2, m = cph.analysis_loop_energy(self.COM, self.DIM, self.ARR)
        if not tot:
            self.COM = np.array([self.DIM[0]/2, self.DIM[1]/2], np.float32)

        self.TOT[self.FRAME[0]] = tot
        self.RG[self.FRAME[0]] = Rg
        self.E[self.FRAME[0]] = e
        self.E2[self.FRAME[0]] = e2
        self.M[self.FRAME[0]] = m
        change = cph.population_change(self.DIM_OLD, self.ARR_OLD, self.DIM, self.ARR)
        self.CHANGE[self.FRAME[0], :] = change
        axes = pf.axial_diameter_P(live)
        self.AXES[self.FRAME[0], :] = axes

    def main(self):
        logging.info(
                    r"""Starting run: BETA:{}, THR:{}, UPD:{}, RUL1:{}, RUL#:{}""".format(
                     self.BETA, self.THRESHOLD, self.UPDATES,
                     self.RULES[0], len(self.RULES))
        )
        start = time.time()
        cf.randomize_center(10, self.DIM, self.ARR)
        self.analysis()
        self.FRAME[0] += 1
        while self.FRAME[0] < self.LENGTH  and self.RUNNING:
            self.basic_update()
            self.analysis()
            self.FRAME[0] += 1
        #TODO: add some more analysis of the actual computation of the run, processor intensity or something
        self.RUNTIME = time.time() - start
        self.TOTTIME = time.time() - self.TOTTIME

        setup = self.TOTTIME - self.RUNTIME

        logging.info('Total time: {0:3.3f},{1:0.4f} Final length: {2}'.format(
            self.TOTTIME, setup, self.FRAME[0])
        )

class Repeater():

    def __init__(self, repeat=50, length=1000):
        self.REPEAT = repeat
        self.LENGTH = length

    def go(self):
        frames = {}
        for i in range(self.REPEAT):
            R = Run(self.LENGTH)
            R.main()
            temp = pd.DataFrame({
                'time':R.TOTTIME,
                'frame':list(range(self.LENGTH)),
                'populus':R.TOT,
                'growth':R.CHANGE[:, 0] - R.CHANGE[:, 1],
                'turnover':R.CHANGE.sum(axis=1),
                'comnorm':cph.norm(R.COM[0], R.COM[1]),
                'rad':R.RG,
                'diameter':R.AXES.max(axis=1),
            })
            temp['density'] = temp['populus'].div(temp['rad'], fill_value=0)
            temp['Dgrowth'] = temp['growth'].sub(temp['growth'].shift())
            temp['Drad'] = temp['rad'].sub(temp['rad'].shift())
            assert(temp['growth'].sum()==R.TOT[-1])
            frames[i] = temp
        return frames

if __name__=='__main__':
    a = Repeater(1, 60)
    out = a.go()
    print(out[0])
