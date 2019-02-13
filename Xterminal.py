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
updates = 0
threshold = 0
rules = np.array([[1, 4, 2, -1], [2, 3, 3, -1]], np.intc)
bounds = array.array('i', [1, 1, 1, 1])
horizontal = array.array('i', [0, 7, 1, 1, 1])
vertical = array.array('i', [0, 7, 6, 0, 0])


if __name__ == "__main__":

    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = cf.init(screendim1)

    cf.advance_array(head_position, buffer_length, buf_h)
    arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    cf.add_global_noise(0.5, dim_h, arr_h)

    changes = 0
    while True:
        # analysis here
        cf.basic_print(dim_t, arr_t)
        arr_t = cf.update_array_positions(tail_position, buffer_length, buffer_status, buf_t, 0)
        time.sleep(0.1)

        smarr = memoryview(arr_h[20:30,20:30])
        smdim = array.array('i', [10, 10])
        cf.add_stochastic_noise(0.2, smdim, smarr)

        cf.advance_array(head_position, buffer_length, buf_h)
        arr_h = cf.update_array_positions(head_position, buffer_length, buffer_status, buf_h)

        cf.basic_print(dim_h, arr_h)
