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
LENGTH = 1000
RUNNING = True

screendim1 = [38, 149]
DIM = array.array('i', [20, 20])
ARR = cf.init_array(DIM)
ARR_OLD = np.copy(ARR)
DIM_OLD = np.copy(DIM)
cf.randomize_center(10, DIM, ARR)
FRAME = array.array('i', [0])

BETA = 1/8
UPDATES = 0
THRESHOLD = 0
RULES = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)

COM = cph.center_of_mass(DIM, ARR)
if not np.asarray(COM).any():
    import pdb; pdb.set_trace()  # XXX BREAKPOINT
    COM = np.array([DIM[0]/2, DIM[1]/2], np.float32)

TOT = np.zeros(LENGTH, np.intc)
RG = np.zeros_like(TOT)
E = np.zeros_like(TOT)
E2 = np.zeros_like(TOT)
M = np.zeros_like(TOT)
CHANGE = np.zeros((LENGTH, 2), np.intc)

def rezero():
    TOT = np.zeros(LENGTH, np.intc)
    RG = np.zeros_like(TOT)
    E = np.zeros_like(TOT)
    E2 = np.zeros_like(TOT)
    M = np.zeros_like(TOT)
    CHANGE = np.zeros((LENGTH, 2), np.intc)

def prepare_frame():
    kwargs={
        'running':RUNNING,
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
    global ARR_OLD, DIM_OLD, RUNNING
    _, _, = phi.recenter(COM, dim, arr)
    ARR_OLD = np.copy(arr)
    DIM_OLD = np.copy(dim)
    logging.debug('Basic update')
    cf.ising_process(updates, beta, dim, arr)
    cf.add_stochastic_noise(threshold, dim, arr)
    cf.conway_process(cf.prepair_rule(rules, frame), dim, arr)
    logging.debug('Change zoom level')
    if dim[0] <= 4:
        RUNNING = False

    dim, arr, change = cf.change_zoom_level_array(dim, arr)

    # cf.basic_print(dim, arr)
    return dim, arr

def analysis(frame=None, dim=None, arr=None, **_):

    global COM, TOT, RG, E, E2, M, CHANGE
    tot, _, COM, Rg, e, e2, m = cph.analysis_loop_energy(COM, dim, arr)
    if not tot:
        COM = np.array([dim[0]/2, dim[1]/2], np.float32)

    TOT[frame] = tot
    RG[frame] = Rg
    E[frame] = e
    E2[frame] = e2
    M[frame] = m
    CHANGE[frame, :] = cph.population_change(DIM_OLD, ARR_OLD, DIM, ARR)
    if not np.asarray(CHANGE).any():
        RUNNING = False

def truncate(frame=None, **_):
    global TOT, RG, E, E2, M, CHANGE
    fr = frame[0]
    TOT = TOT[: fr]
    RG = RG[: fr]
    E = E[: fr]
    E2 = E2[: fr]
    M = M[: fr]
    CHANGE = CHANGE[: fr, :]

def main():
    logging.info('Proccess starting!')
    kwargs = prepare_frame()

    rezero()
    start = time.time()
    while kwargs['frame'][0] < LENGTH and RUNNING:
        kwargs['dim'], kwargs['arr'] = basic_update(**kwargs)
        analysis(**kwargs)
        kwargs['frame'][0] += 1
#   truncate(**kwargs)
    print('Total time: {} Final length: {}'.format(time.time() - start, kwargs['frame'][0]))

if __name__ == "__main__": main()
