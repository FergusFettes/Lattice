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
cf.randomize_center(10, DIM, ARR)
FRAME = array.array('i', [0])

BETA = 1/8
UPDATES = 0
THRESHOLD = 0
RULES = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)

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
    logging.debug('Basic update')
    cf.ising_process(updates, beta, dim, arr)
    cf.add_stochastic_noise(threshold, dim, arr)
    cf.conway_process(cf.prepair_rule(rules, frame), dim, arr)
    logging.debug('Change zoom level')
    dim, arr, change = cf.change_zoom_level_array(dim, arr)

    com = cph.center_of_mass(dim, arr)
    _, _, = phi.recenter(com, dim, arr)
    cf.basic_print(dim, arr)
    return dim, arr

if __name__ == "__main__":
    logging.info('Proccess starting!')
    kwargs = prepare_frame()

    while kwargs['running']:
        start = time.time()
        kwargs['dim'], kwargs['arr'] = basic_update(**kwargs)
        while time.time() - start < kwargs['frametime']:
            time.sleep(0.01)
