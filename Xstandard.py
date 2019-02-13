import array
import numpy as np
import time

from src.Cfuncs import (
    init, basic_update, basic_print, advance_array, update_array_positions, prepair_rule,
    roll_columns_pointer, roll_rows_pointer, check_rim, resize_array_buffer,
    change_buffer, scroll_instruction_update
)
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
rules = np.array([[1, 4, 2, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [1, 1, 1, 1])
horizontal = array.array('i', [0, 7, 1, 1, 1])
vertical = array.array('i', [0, 7, 6, 0, 0])


if __name__ == "__main__":

    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = init(screendim2)

    basic_update(updates, beta, threshold,
                    prepair_rule(rules, head_position),
                    dim_h, arr_h,
                    bounds, horizontal, vertical,
                 )
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    changes = 0
    while True:
        # analysis here
        basic_print(dim_t, arr_t, bounds, horizontal, vertical)
        scroll_instruction_update(horizontal, vertical, dim_t)
        arr_t = update_array_positions(tail_position, buffer_length, buffer_status, buf_t, 0)

        basic_update(updates, beta, threshold,
                        prepair_rule(rules, head_position),
                        dim_h, arr_h,
                        bounds, horizontal, vertical,
                    )
        advance_array(head_position, buffer_length, buf_h)
        arr_h = update_array_positions(head_position, buffer_length, buffer_status, buf_h)

        time.sleep(0.1)
