import array

import numpy as np
import time

import src.Cfuncs as cf
import src.Cyarr as cy
import src.Cyphys as cph
import src.PHifuncs as phi

import logging
LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s:[%(levelname)s]-(%(processName)-15s): %(message)s',
                    )

screendim1 = [38, 149]
DIM = array.array('i', [20, 20])
ARR = cf.init_array(DIM)
ARR_OLD = np.copy(ARR)
cf.randomize_center(10, DIM, ARR)
FRAME = array.array('i', [0])

BETA = 1/8
UPDATES = 0
THRESHOLD = 0
RULES = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)

TOT = np.zeros(1000, np.intc)
Rg = np.zeros_like(TOT)
E = np.zeros_like(TOT)
E2 = np.zeros_like(TOT)
M = np.zeros_like(TOT)
CHANGE = np.zeros((1000, 2), np.intc)
COM = cph.center_of_mass(DIM, ARR)

def prepare_frame():
    kwargs={
        'running':True,
        'frametime':0.2,
        'threshold':THRESHOLD,
        'updates':UPDATES,
        'beta':BETA,
        'rules':np.asarray(RULES, np.intc),
        'frame':np.asarray(FRAME, np.intc),
        'dim':np.asarray(DIM, np.intc),
        'arr':ARR,
    }
    return kwargs

def basic_update(updates=None, beta=None, threshold=None, dim=None, arr=None, frame=None,
                 rules=None, **_):
    _, _, = phi.recenter(COM, dim, arr)
    ARR_OLD = np.copy(ARR)
    logging.debug('Basic update')
    cf.ising_process(updates, beta, dim, arr)
    cf.add_stochastic_noise(threshold, dim, arr)
    cf.conway_process(cf.prepair_rule(rules, frame), dim, arr)
    logging.debug('Change zoom level')
    dim, arr, change = cf.change_zoom_level_array(dim, arr)

    # cf.basic_print(dim, arr)
    return dim, arr

def analysis(frame=None, dim=None, arr=None):

    tot, _, COM, Rg, e, e2, m = cph.analysis_loop_energy(com, dim, arr)
    TOT[frame] = tot
    Rg[frame] = Rg
    E[frame] = e
    E2[frame] = e2
    M[frame] = m
    CHANGE[frame, :] = cph.population_change(ARR_OLD, arr)

if __name__ == "__main__":
    logging.info('Proccess starting!')
    kwargs = prepare_frame()

    start = time.time()
    while kwargs['frame'][0] < 1000:
        kwargs['dim'], kwargs['arr'] = basic_update(**kwargs)
        kwargs['frame'][0] += 1
    print('Total time: {}'.format(time.time() - start))
