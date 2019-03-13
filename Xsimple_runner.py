import array

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

    def __init__(self, length=1000):
        self.RUNNING = True
        self.LENGTH = length
        self.DIM = array.array('i', [20, 20])
        self.ARR = cf.init_array(self.DIM)
        cy.clear_array(self.DIM, self.ARR)
        self.ARR_OLD = np.copy(self.ARR)
        self.DIM_OLD = np.copy(self.DIM)
        self.FRAME = array.array('i', [0])

        self.BETA = 1/8
        self.UPDATES = 0
        self.THRESHOLD = 0
        self.RULES = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)

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
        # _, _, = phi.recenter(self.COM, self.DIM, self.ARR) #turned off cause I think
        # this buggers the turnover rate
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
        if not np.asarray(change).any():
            self.RUNNING = False
            self.TOT[self.FRAME[0]: ] = tot

    def main(self):
        logging.info('Proccess starting!')

        start = time.time()
        cf.randomize_center(10, self.DIM, self.ARR)
        self.analysis()
        self.FRAME[0] += 1
        while self.FRAME[0] < self.LENGTH  and self.RUNNING:
            self.basic_update()
            self.analysis()
            self.FRAME[0] += 1
        print('Total time: {} Final length: {}'.format(time.time() - start, self.FRAME[0]))

if __name__ == "__main__":
    a = Run()
    a.main()
    print(a.TOT[0:5])
    print(a.CHANGE[0:5, :])
