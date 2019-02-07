import array

from src.Cfuncs import *
from src.PHifuncs import *

if __name__=="0_main__":
    dim_list = ([20,20])
    beta = 1/8
    updates = 5
    threshold = 1
    rules = [[2,3,3,3],[2,3,3,3]]

    head_position, buffer_length, print_position, analysis_position,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = init(dim_list)

    basic_update(updates, beta, threshold,
                    prepair_rule(rules, head_position),
                    dim_h, arr_h,
                 )
    advance_array(head_position % buffer_length, buffer_length, buf_h)
    head_position += 1
    arr_h = buf_h[head_position % buffer_length]

    changes = 0
    while True:
        # analysis here
        #

        basic_print(dim_t, arr_t)
        print_position += 1
        arr_t = buf_t[print_position % buffer_length]

        basic_update(updates, beta, threshold,
                        prepair_rule(rules, head_position),
                        dim_h, arr_h,
                    )
        advance_array(head_position % buffer_length, buffer_length, buf_h)

        if check_rim(0, dim_h, arr_h) is True:
            dim_temp, buf_temp = resize_array_buffer(dim_h, buffer_length)
            change_buffer(head_position % buffer_length, buffer_length, dim_h, buf_h,\
                          dim_temp, buf_temp)
            dim_h = dim_temp
            buf_h = buf_temp

            change_location = head_position
            changes += 1
        head_position += 1
        arr_h = buf_h[head_position % buffer_length]

        if changes > 0:
            if print_position == change_location:
                dim_t = dim_h; buf_t = buf_h
                arr_t = buf_t[print_position % buffer_length]
                changes -= 1

        time.sleep(0.3)

if __name__ =="__main__":
    screendim1 = [38,149]
    screendim2 = [45,192]
    screendim3 = [57,268]
    screendim4 = [77,337]
    head_pos, buf_siz, print_pos, analysis_pos, _, _, _, dim_v, arr_v, buf_v =\
        init(screendim2)
    bounds = array.array('i', [1, 1, 1, 1])
    horizontal = array.array('i', [0, 7, 1, 1, 1])
    vertical = array.array('i', [0, 27, 66, 0, -1])
    while True:
        head_pos += 1
        basic_update(100, 1/8, 0.99,
                     prepair_rule([[2,5,4,6],[3,4,3,6]], head_pos),
                     dim_v, arr_v, bounds, horizontal, vertical
                     )
        basic_print(dim_v, arr_v, bounds, horizontal, vertical)
        scroll_update(horizontal, vertical, dim_v)
        time.sleep(0.1)
