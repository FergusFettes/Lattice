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
buffer_storage = {}

growth = True

screendim1 = [38, 149]
dim = [20, 20]

change_roll, head_position, tail_position, buf_len, buf_stat,\
    dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(dim, 10, 14)

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
        'head_position':np.asarray(head_position, np.intc),
        'tail_position':np.asarray(tail_position, np.intc),
        'buffer_length':np.asarray(buf_len, np.intc),
        'buffer_status':np.asarray(buf_stat, np.intc),
        'change_roll':np.asarray(change_roll, np.intc),
        'dim_h':np.asarray(dim, np.intc),
        'dim_t':np.asarray(dim, np.intc),
        'arr_h':arr_h,
        'buf_h':buf_h,
        'buf_t':buf_t,
        'arr_t':arr_t,
    }
    return kwargs

def basic_update(kwargs):
    logging.debug('Basic update')
    cf.ising_process(kwargs['updates'], kwargs['beta'], kwargs['dim_h'], kwargs['arr_h'])
    cf.add_stochastic_noise(kwargs['threshold'], kwargs['dim_h'], kwargs['arr_h'])
    cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
    cy.roll_columns_pointer(kwargs['roll'][0], kwargs['dim_h'], kwargs['arr_h'])
    cy.roll_rows_pointer(kwargs['roll'][1], kwargs['dim_h'], kwargs['arr_h'])
    cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
    cy.scroll_bars(kwargs['dim_h'], kwargs['arr_h'], kwargs['bars'])
    cf.scroll_noise(kwargs['dim_h'], kwargs['arr_h'], kwargs['fuzz'])
    cf.conway_process(cf.prepair_rule(kwargs['rules'], kwargs['head_position']),
                    kwargs['dim_h'], kwargs['arr_h'])
    cy.set_bounds(kwargs['bounds'], kwargs['dim_h'], kwargs['arr_h'])
    if growth:
        com = cph.center_of_mass(kwargs['dim_h'], kwargs['arr_h'])
        _, _, = phi.recenter(com, kwargs['dim_h'], kwargs['arr_h'])

def buffer_handler_head(kwargs):
    """
    Checks the array is the right size (if necc) and returns a new dim-buffer pair.
    Extends the buffer status to suit.
    Advances the array in the [new] buffer, and returns a new array while updating
    the head position.

    After this function, the array has been copied into the next position
    (possibly on a new array) and the head pointers have been updated.
    Head_position and buffer_status should be accurate.
    """
    if growth:
        logging.debug('Change zoom level')
        #TODO: could actually get the function to return a dictionary directly..
        #TODO: and all these functions should be accepting dictionaries! why is this
        # not done yet..
        kwargs['dim_h'], kwargs['buf_h'], kwargs['change_roll'], kwargs['buffer_status']\
        = cf.change_zoom_level(
            kwargs['head_position'], kwargs['buffer_length'],
            kwargs['buffer_status'], kwargs['change_roll'],
            kwargs['dim_h'], kwargs['buf_h']
        )
        if kwargs['change_roll'][0, 1]:
            buffer_storage.update(
                {kwargs['change_roll'][0, 0]:(kwargs['dim_h'], kwargs['buf_h'])}
            )

    logging.debug('Update array positions')
    cf.advance_array(kwargs['head_position'], kwargs['buffer_length'], kwargs['buf_h'])
    kwargs['arr_h'] = cf.update_array_positions(
        kwargs['head_position'],
        kwargs['buffer_length'],
        kwargs['buffer_status'],
        kwargs['buf_h'],
        1
    )

def image_processing(kwargs):
    cy.scroll_bars(kwargs['dim_t'], kwargs['arr_t'], kwargs['bars'])
    cf.scroll_noise(kwargs['dim_t'], kwargs['arr_t'], kwargs['fuzz'])
    cf.basic_print(kwargs['dim_t'], kwargs['arr_t'])

def buffer_handler_tail(kwargs):
    if growth:
        logging.debug('Updating tail position')
        change_here = np.argwhere(kwargs['change_roll'][:, 0]==kwargs['tail_position'][0])
        if change_here.any():
            change_here = change_here[0][0]
            kwargs['tail_position'][1] += abs(kwargs['change_roll'][change_here, 1])

    logging.debug('Updating scroll instructions')
    cf.scroll_instruction_update(
        kwargs['bars'], kwargs['dim_t']
    )
    cf.scroll_instruction_update(
        kwargs['fuzz'], kwargs['dim_t']
    )
    logging.debug('Updating tail position')
    kwargs['arr_t'] = cf.update_array_positions(
        kwargs['tail_position'],
        kwargs['buffer_length'],
        kwargs['buffer_status'],
        kwargs['buf_t'],
        0
    )

    # if tail has changed, you need to delete the first buffer
    if growth and change_here.any():
        if kwargs['change_roll'][change_here, 1]:
            dim, buf = buffer_storage.pop(kwargs['change_roll'][change_here, 0])
            kwargs['buf_t'] = buf
            kwargs['dim_t'] = dim
            kwargs['arr_t'] = np.asarray(kwargs['buf_t'][kwargs['tail_position'][0] % kwargs['buffer_length']])
            kwargs['head_position'][1] -= 1
            kwargs['tail_position'][1] -= 1
            kwargs['buffer_status'] = cf.extend_buffer_status(kwargs['head_position'],
                                kwargs['buffer_length'], kwargs['buffer_status'])
if __name__ == "__main__":
    logging.info('Proccess starting!')
    kwargs = prepare_frame()
    if growth:
        growth_mode(kwargs)

    while kwargs['running']:
        start = time.time()

        basic_update(kwargs)
        buffer_handler_head(kwargs)
        image_processing(kwargs)
        buffer_handler_tail(kwargs)

        while time.time() - start < kwargs['frametime']:
            time.sleep(0.01)
