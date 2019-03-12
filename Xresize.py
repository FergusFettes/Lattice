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

growth = True

screendim1 = [38, 149]
dim = array.array('i', [20, 20])
arr = cf.init_array(dim)
cf.randomize_center(10, dim, arr)
frame = array.array('i', [0])

beta = 1/8
updates = 0
threshold = 0
rules = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [0, -1, 0, -1])
bars = np.array([
                [0, 4, 1, 0, 1, -1],
                [0, 4, 1, 1, 1, -1],
                ], np.double)
fuzz = np.array([
                [70, 7, 0, 0, 1, 0.5, 1],
                [0, 4, 1, 1, 1, 0.5, -2],
                ], np.double)
roll = array.array('i', [0, 0])

def growth_mode(kwargs):
    kwargs.update({
        'bounds':array.array('i', [-1, -1, -1, -1]),
        'roll':array.array('i', [0, 0]),
    })
    for i in range(len(kwargs['bars'])):
        kwargs['bars'][i, -1] = -1
    for i in range(len(kwargs['fuzz'])):
        kwargs['fuzz'][i, -1] = -2

def prepare_frame():
    kwargs={
        'running':True,
        'frametime':0.2,
        'threshold':threshold,
        'updates':updates,
        'beta':beta,
        'rules':np.asarray(rules, np.intc),
        'bounds':np.asarray(bounds, np.intc),
        'bars':np.asarray(bars, np.double),
        'fuzz':np.asarray(fuzz, np.double),
        'roll':np.asarray(roll, np.intc),
        'frame':np.asarray(frame, np.intc),
        'dim':np.asarray(dim, np.intc),
        'arr':arr,
    }
    return kwargs

def basic_update(updates=None, beta=None, threshold=None, dim=None, arr=None, frame=None,
                 bounds=None, bars=None, fuzz=None, roll=None, **_):
    logging.debug('Basic update')
    cf.ising_process(updates, beta, dim, arr)
    cf.add_stochastic_noise(threshold, dim, arr)
    cy.set_bounds(bounds, dim, arr)
    cy.roll_columns_pointer(roll[0], dim, arr)
    cy.roll_rows_pointer(roll[1], dim, arr)
    cy.set_bounds(bounds, dim, arr)
    cy.scroll_bars(dim, arr, bars)
    cf.scroll_noise(dim, arr, fuzz)
    cf.conway_process(cf.prepair_rule(rules, frame),
                    dim, arr)
    cy.set_bounds(bounds, dim, arr)

def image_processing(dim=None, arr=None, bars=None, fuzz=None, **_):
    cy.scroll_bars(dim, arr, bars)
    cf.scroll_noise(dim, arr, fuzz)
    cf.basic_print(dim, arr)

def buffer_handler_tail(bars=None, dim=None, fuzz=None, **_):
    logging.debug('Updating scroll instructions')
    cf.scroll_instruction_update(bars, dim)
    cf.scroll_instruction_update(fuzz, dim)

if __name__ == "__main__":
    logging.info('Proccess starting!')
    kwargs = prepare_frame()
    if growth:
        growth_mode(kwargs)

    while kwargs['running']:
        start = time.time()

        basic_update(**kwargs)
        if growth:
            logging.debug('Change zoom level')
            kwargs['dim'], kwargs['arr'], kwargs['change'] = cf.change_zoom_level_array(
                kwargs['dim'], kwargs['arr']
            )
        image_processing(**kwargs)
        buffer_handler_tail(**kwargs)

        while time.time() - start < kwargs['frametime']:
            time.sleep(0.01)
