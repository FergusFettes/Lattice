import array
import numpy as np
import time

from src.Cfuncs import (
    init, basic_update, basic_print, advance_array, update_array_positions, prepair_rule,
    roll_columns_pointer, roll_rows_pointer, check_rim, resize_array_buffer,
    change_buffer
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

dim_list = ([16, 16])

beta = 1/8
updates = 0
threshold = 0
rules = np.array([[1, 3, 2, 3], [2, 3, 3, 3]], np.intc)
bounds = array.array('i', [1, 1, 1, 1])
horizontal = array.array('i', [0, 7, 1, 1, 1])
vertical = array.array('i', [0, 27, 66, 0, -1])


if __name__ == "__main__":

    head_position, tail_position, buffer_length, buffer_status,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = init(dim_list)

    basic_update(updates, beta, threshold,
                    prepair_rule(rules, head_position),
                    dim_h, arr_h,
                 )
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status, buf_h, 0)

    changes = 0
    while True:
        # analysis here
        basic_print(dim_t, arr_t)
        arr_t = update_array_positions(tail_position, buffer_length, buffer_status, buf_t)

        basic_update(updates, beta, threshold,
                        prepair_rule(rules, head_position),
                        dim_h, arr_h,
                    )
        advance_array(head_position, buffer_length, buf_h)
        arr_h = update_array_positions(head_position, buffer_length, buffer_status, buf_h)

        if check_rim(0, dim_h, arr_h) is True:
            if head_position[1] == 1:
                print('Growing too fast!')
                break
            dim_temp, buf_temp = resize_array_buffer(dim_h, buffer_length, 3)
            offset = array.array('i', [3,3])
            change_buffer(head_position, buffer_length, dim_h, buf_h,
                          dim_temp, buf_temp, offset)
            dim_h = dim_temp
            buf_h = buf_temp

            change_location = head_position[0]
            head_position[1] += 1

            arr_h = buf_h[head_position[0] % buffer_length]

        if head_position[1] > 0:
            if tail_position[0] == change_location:
                dim_t = dim_h; buf_t = buf_h
                arr_t = buf_t[tail_position[0] % buffer_length]
                head_position[1] -= 1

        com = center_of_mass_P(np.argwhere(arr_h), len(np.argwhere(arr_h)))
        ver, hor = recenter(com, dim_h, arr_h)

        time.sleep(0.5)
