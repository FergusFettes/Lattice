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
                    format='%(asctime)s:[%(levelname)s]-(%(processName)s): %(message)s',
                    )

class Run():
    """
    Base class for Run objects.
    Run objects take a set of update rules and parameters, create an array and apply
    those rules to that array.
    """

    def __init__(self, length=1000, beta=1/8, updates=0,
                 threshold=0, rules=np.array([[2,3,3,3]], np.intc),
                 seed=None, show=False, grow=True):
        self.TOTTIME = time.time()
        self.RUNTIME = None
        self.RUNNING = True
        self.SHOW = show
        self.GROW = grow
        self.LENGTH = length
        self.FRAME = array.array('i', [0])
        self.DIM = None # for testing if array_setup needs to run automatically

        self.BETA = beta
        self.UPDATES = updates
        self.THRESHOLD = threshold
        self.RULES = np.asarray(rules, np.intc)

        self.TOT = np.zeros(self.LENGTH, np.intc)
        self.RG = np.zeros(self.LENGTH, np.float32)
        self.E = np.zeros_like(self.RG)
        self.E2 = np.zeros_like(self.RG)
        self.M = np.zeros_like(self.RG)
        self.CHANGE = np.zeros((self.LENGTH, 2), np.intc)
        self.AXES = np.zeros((self.LENGTH, 2), np.intc)

        self.SEED = seed if seed is not None else np.random.randint(0, 10**9)

    def permutater(self, n):
        for i in range(2**(n**2)):
            bin_rep = '{1:0{0}b}'.format(n**2, i)
            arr = np.asarray([int(i) for i in bin_rep], np.intc).reshape(n,n)
            yield arr

    def array_setup(self, grow=True, dim=None, init_noise=None):
        if grow:
            dim = dim if dim is not None else np.array([20, 20], np.intc)
        else:
            dim = dim if dim is not None else np.array([38, 149], np.intc)
            init_noise = init_noise if init_noise is not None else 0

        self.DIM = np.asarray(dim, np.intc)
        self.ARR = cf.init_array(self.DIM)

        cy.clear_array(self.DIM, self.ARR)
        if grow:
            cf.randomize_center(10, self.DIM, self.ARR, seed=self.SEED)
        else:
            cf.add_global_noise(init_noise, self.DIM, self.ARR)
        self.ARR_OLD = np.copy(self.ARR)
        self.DIM_OLD = np.copy(self.DIM)

        self.COM = cph.center_of_mass(self.DIM, self.ARR)
        self.analysis()
        self.FRAME[0] += 1

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

        if self.GROW:
            self.DIM, self.ARR, _ = cf.change_zoom_level_array(self.DIM, self.ARR)

    def analysis(self):
        tot, live, self.COM, Rg, e, e2, m = cph.analysis_loop_energy(self.COM, self.DIM, self.ARR)
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
            "Starting run: BETA:{}, THR:{}, UPD:{}, RUL1:{}, RUL#:{}".format(
                self.BETA, self.THRESHOLD, self.UPDATES,
                self.RULES[0], len(self.RULES))
        )
        start = time.time()
        if self.DIM is None:
            self.array_setup(grow=self.GROW)
        while self.FRAME[0] < self.LENGTH  and self.RUNNING:
            self.basic_update()
            self.analysis()
            if self.SHOW:
                cf.basic_print(self.DIM, self.ARR)
                time.sleep(0.05)
            self.FRAME[0] += 1

        #TODO: add some more analysis of the actual computation of the run, processor intensity or something
        self.RUNTIME = time.time() - start
        self.TOTTIME = time.time() - self.TOTTIME
        setup = self.TOTTIME - self.RUNTIME

        logging.info('Total time: {0:3.3f},{1:0.4f} Final length: {2}'.format(
            self.TOTTIME, setup, self.FRAME[0])
        )

class Repeater():

    def __init__(self, show=False, grow=True, repeat=50, length=1000, beta=1/8, updates=0,
                 threshold=0, rules=np.array([[2,3,3,3]], np.intc), dim=None,
                 thermo=None, init_noise=None, squeeze=False):
        self.SQUEEZE = squeeze
        self.THERMO = thermo
        self.INIT_NOISE = init_noise
        self.DIM = dim
        self.SHOW = show
        self.GROW = grow
        self.LENGTH = length
        self.REPEAT = repeat

        self.BETA = beta
        self.UPDATES = updates
        self.THRESHOLD = threshold
        self.RULES = np.asarray(rules, np.intc)

    def gro(self):
        TOTTIME = time.time()
        frames = {}
        for i in range(self.REPEAT):
            R = Run(grow=self.GROW, length=self.LENGTH, beta=self.BETA, updates=self.UPDATES,
                    threshold=self.THRESHOLD, rules=self.RULES, show=self.SHOW)
            if self.DIM is not None or self.INIT_NOISE is not None:
                R.array_setup(grow=self.GROW, dim=self.DIM, init_noise=self.INIT_NOISE)
            R.main()
            temp = pd.DataFrame({
                'time':R.TOTTIME,
                'seed':R.SEED,
                'fr':pd.Series(range(self.LENGTH)),
                'populus':R.TOT,

                'growth':R.CHANGE[:, 0] - R.CHANGE[:, 1],
                'turnover':R.CHANGE.sum(axis=1),
                'comnorm':cph.norm(R.COM[0], R.COM[1]),
                'radius':R.RG,
                'diameter':R.AXES.max(axis=1),
            })
            temp['density'] = temp['populus'].div(temp['radius'], fill_value=0)
            temp['Dgrowth'] = temp['growth'].sub(temp['growth'].shift())
            temp['Drad'] = temp['radius'].sub(temp['radius'].shift())
            frames[i] = temp
        TOTTIME = time.time() - TOTTIME
        logging.info('Completed {0} runs of length {1} in {2:4.3f}s'.format(
            self.REPEAT, self.LENGTH, TOTTIME))
        return frames

    def glo(self):
        TOTTIME = time.time()
        frames = pd.DataFrame()
        for i in range(self.REPEAT):
            be = self.thermostat(i)
            R = Run(grow=self.GROW, length=self.LENGTH, beta=be,
                    updates=self.UPDATES,
                    threshold=self.THRESHOLD, rules=self.RULES, show=self.SHOW)
            if self.DIM is not None or self.INIT_NOISE is not None:
                R.array_setup(grow=self.GROW, dim=self.DIM, init_noise=self.INIT_NOISE)
            R.main()
            temp = pd.DataFrame({
                'run':i,
                'fr':pd.Series(range(self.LENGTH)),
                'time':R.TOTTIME,
                'populus':R.TOT,
                'turnover':R.CHANGE.sum(axis=1),
                'e':R.E,
                'e2':R.E2,
                'm':R.M,
                'beta':be,
            }, columns=['run', 'fr', 'time', 'populus', 'turnover', 'e', 'e2', 'm', 'beta'])
            #temp.set_index(['run', 'frame'], inplace=True)
            temp['density'] = temp['populus'].div(self.DIM[0] * self.DIM[1], fill_value=0)
            ee = R.E[self.LENGTH//5:].mean()
            ee22 = R.E2[self.LENGTH//5:].mean()
            nn = self.DIM[0] * self.DIM[1]
            temp['C'] = ((be**2)*(ee22 - ee**2))/nn
            frames = frames.append(temp)
        # This makes it into a MultiArray
        frames.set_index(['run', 'fr'], inplace=True)
        TOTTIME = time.time() - TOTTIME
        logging.info('Completed {0} runs of length {1} in {2:4.3f}s'.format(
            self.REPEAT, self.LENGTH, TOTTIME))
        return frames

    def gloperm(self):
        TOTTIME = time.time()
        frames = pd.DataFrame()
        for i in range(self.REPEAT):
            be = self.thermostat(i)
            R = Run(grow=self.GROW, length=self.LENGTH, beta=be,
                    updates=self.UPDATES,
                    threshold=self.THRESHOLD, rules=self.RULES, show=self.SHOW)
            if self.DIM is not None or self.INIT_NOISE is not None:
                R.array_setup(grow=self.GROW, dim=self.DIM, init_noise=self.INIT_NOISE)
            R.main()
            cut=5
            temp = pd.DataFrame({
                'run':[i],
                'time':[R.TOTTIME],
                'populus':[R.TOT[cut:].mean()],
                'populusstd':[R.TOT[cut:].std()],
                'turnover':[R.CHANGE[cut:].sum(axis=1).mean()],
                'turnoverstd':[R.CHANGE[cut:].sum(axis=1).std()],
                'e':[R.E[cut:].mean()],
                'estd':[R.E[cut:].std()],
                'e2':[R.E2[cut:].mean()],
                'e2std':[R.E2[cut:].std()],
                'm':[R.M[cut:].mean()],
                'mstd':[R.M[cut:].std()],
                'beta':[be],
            })
            temp['density'] = temp['populus'].div(self.DIM[0] * self.DIM[1], fill_value=0)
            ee = R.E[self.LENGTH//5:].mean()
            ee22 = R.E2[self.LENGTH//5:].mean()
            nn = self.DIM[0] * self.DIM[1]
            temp['C'] = ((be**2)*(ee22 - ee**2))/nn
            frames = frames.append(temp)
        # This makes it into a MultiArray
        frames.set_index('run', inplace=True)
        TOTTIME = time.time() - TOTTIME
        logging.info('Completed {0} runs of length {1} in {2:4.3f}s'.format(
            self.REPEAT, self.LENGTH, TOTTIME))
        return frames

    def glosqueeze(self):
        TOTTIME = time.time()
        frames = pd.DataFrame()
        for i in range(self.REPEAT):
            be = self.thermostat(i)
            R = Run(grow=self.GROW, length=self.LENGTH, beta=be,
                    updates=self.UPDATES,
                    threshold=self.THRESHOLD, rules=self.RULES, show=self.SHOW)
            if self.DIM is not None or self.INIT_NOISE is not None:
                R.array_setup(grow=self.GROW, dim=self.DIM, init_noise=self.INIT_NOISE)
            R.main()
            cut=5
            temp = pd.DataFrame({
                'run':[i],
                'time':[R.TOTTIME],
                'populus':[R.TOT[cut:].mean()],
                'populusstd':[R.TOT[cut:].std()],
                'turnover':[R.CHANGE[cut:].sum(axis=1).mean()],
                'turnoverstd':[R.CHANGE[cut:].sum(axis=1).std()],
                'e':[R.E[cut:].mean()],
                'estd':[R.E[cut:].std()],
                'e2':[R.E2[cut:].mean()],
                'e2std':[R.E2[cut:].std()],
                'm':[R.M[cut:].mean()],
                'mstd':[R.M[cut:].std()],
                'beta':[be],
            })
            temp['density'] = temp['populus'].div(self.DIM[0] * self.DIM[1], fill_value=0)
            ee = R.E[self.LENGTH//5:].mean()
            ee22 = R.E2[self.LENGTH//5:].mean()
            nn = self.DIM[0] * self.DIM[1]
            temp['C'] = ((be**2)*(ee22 - ee**2))/nn
            frames = frames.append(temp)
        # This makes it into a MultiArray
        frames.set_index('run', inplace=True)
        TOTTIME = time.time() - TOTTIME
        logging.info('Completed {0} runs of length {1} in {2:4.3f}s'.format(
            self.REPEAT, self.LENGTH, TOTTIME))
        return frames

    def thermostat(self, repeat):
        if self.THERMO is None:
            return self.BETA
        return self.BETA - (self.THERMO/2) + ((self.THERMO/self.REPEAT) * repeat)

    def go(self):
        if self.GROW:
            return self.gro()
        if self.SQUEEZE:
            return self.glosqueeze()
        return self.glo()

if __name__=='__main__':
    a = Repeater(1, 60)
    out = a.go()
    print(out[0])
