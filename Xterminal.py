import array

import numpy as np
import time

import src.Cfuncs as cf
import src.Cyarr as cy
import src.Cyphys as cph
from src.PHifuncs import (
    recenter
)

screendim1 = [38, 149]
screendim2 = [45, 192]
screendim3 = [57, 268]
screendim4 = [77, 337]
lampdim = [77, 50]


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

if __name__ == "__main__":
    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(lampdim)

    cf.basic_update_buffer(
                    updates, beta, threshold,
                    rules, head_position,
                    buffer_length,
                    dim_h, arr_h, buf_h,
                    bounds, bars, fuzz,
                 )
    arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    changes = 0
    frame = memoryview(array.array('i', [0]))
    while True:
        # analysis here
        cf.basic_print(dim_t, arr_t, bounds, bars, fuzz)
        cf.scroll_instruction_update(bars, dim_t)
        arr_t = cf.update_array_positions(tail_position, buffer_length, buffer_status,
                                          buf_t, 0)
        time.sleep(0.1)

        cf.basic_update_buffer(
                        updates, beta, threshold,
                        rules, head_position,
                        buffer_length,
                        dim_h, arr_h, buf_h,
                        bounds, bars, fuzz
                    )
        arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 1)
        cf.scroll_instruction_update(fuzz, dim_t)
        cy.roll_rows_pointer(-1, dim_h, arr_h)
        frame[0] += 1
