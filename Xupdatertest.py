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
horizontal = array.array('i', [0, 9, 4, 0, -1])
vertical = array.array('i', [0, 4, 1, 1, -1])
hbar = array.array('i', [90, 5, 1, 0, 1])
vbar = array.array('i', [90, 5, 1, 0, 1])


if __name__ == "__main__":

    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(screendim2)

    cf.advance_array(head_position, buffer_length, buf_h)
    arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    cf.add_global_noise(0.5, dim_h, arr_h)

    changes = 0
    while True:
        # analysis here
        cf.basic_print(dim_t, arr_t, bounds, horizontal, vertical)
        cf.scroll_instruction_update(horizontal, vertical, dim_t)
        arr_t = cf.update_array_positions(tail_position, buffer_length, buffer_status, buf_t, 0)
        time.sleep(0.1)

        cf.basic_update(updates, beta, threshold,
                        cf.prepair_rule(rules, head_position),
                        dim_h, arr_h,
                        bounds, horizontal, vertical,
                    )

        cf.scroll_update(dim_h, arr_h, hbar, vbar)
        cf.scroll_instruction_update_single(vbar, dim_t)

        cf.advance_array(head_position, buffer_length, buf_h)
        arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h)
