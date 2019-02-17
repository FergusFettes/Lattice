import array
import numpy as np
import time

import src.Cfuncs as cf
from src.Pfuncs import (
    center_of_mass_P
)
from src.PHifuncs import (
    recenter
)

screendim1 = [38, 149]
screendim2 = [45, 192]
screendim3 = [57, 268]
screendim4 = [77, 337]


beta = 1/8
updates = 100
threshold = 0
rules = np.array([[2, 3, 3, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [1, 1, 1, 1])
bars = np.array([
                [0, 4, 1, 0, 1, -1],
                [0, 4, 1, 1, 1, -1],
                ], np.intc)
fuzz = np.array([
                [0, 4, 1, 0, 1, -2],
                [0, 4, 1, 1, 1, -2],
                ], np.intc)

if __name__ == "__main__":

    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(screendim2)

    cov = 0.3
    cf.basic_update_buffer(
                    updates, beta, threshold, cov,
                    rules, head_position,
                    buffer_length,
                    dim_h, arr_h, buf_h,
                    bounds, bars, fuzz,
                 )
    arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    fuzz = np.array([
                    [0, 4, 1, 0, 1, -1],
                    [0, 4, 1, 1, 1, -1],
                    [10, 4, 1, 0, 1, 1],
                    [10, 4, 1, 1, 1, 1],
                    ], np.intc)

    changes = 0
    frame_orig = array.array('i', [0])
    frame = memoryview(frame_orig)
    while True:
        # analysis here
        cf.basic_print(dim_t, arr_t, cov, bounds, bars, fuzz)
        cf.scroll_instruction_update(bars, dim_t)
        arr_t = cf.update_array_positions(tail_position, buffer_length, buffer_status,
                                          buf_t, 0)
        time.sleep(0.1)

        cf.basic_update_buffer(
                        updates, beta, threshold, cov,
                        rules, head_position,
                        buffer_length,
                        dim_h, arr_h, buf_h,
                        bounds, bars, fuzz
                    )
        arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 1)
        cf.scroll_instruction_update(fuzz, dim_t)
        frame[0] += 1
