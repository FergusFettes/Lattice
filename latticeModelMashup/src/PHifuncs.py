import array
import numpy as np

from src.Cfuncs import *
from src.cylib.array_man import *
from src.Pfuncs import *

def simple_run(dim_list):
    """
    Performs a run.
    """
    updates = 100
    beta = 1/8
    threshold = 0.9
    rules = np.array([[2,3,3,3], [2,3,3,3]], np.intc)
    horizontal = array.array('i', [0, 1, 2, 0, 1])
    vertical = array.array('i', [0, 1, 1, 0, 1])
    bounds = array.array('i', [1, 1, 1, 1])

    head_position, buffer_length, print_position, analysis_position,\
        dim_t, arr_t, buf_t, dim_h, arr_h, buf_h = init(dim_list)

    basic_update(updates, beta, threshold,
                    prepair_rule(rules, head_position),
                    dim_h, arr_h)
    advance_array(head_position % buffer_length, buffer_length, buf_h)
    head_position += 1
    arr_h = buf_h[head_position % buffer_length]

    changes = 0
    while True:
        basic_print(dim_t, arr_t)
        print_position += 1
        arr_t = buf_t[print_position % buffer_length]

        rule = prepair_rule(rules, head_position)
        basic_update(updates, beta, threshold, rule, dim_h, arr_h)
        advance_array(head_position % buffer_length, buffer_length, buf_h)

        head_position += 1
        arr_h = buf_h[head_position % buffer_length]

        time.sleep(0.2)

#       if check_rim(0, dim_h, arr_h) is True:
#           dim_temp, buf_temp = resize_array_buffer(dim_h, buffer_length)
#           change_buffer(head_position % buffer_length, buffer_length, dim_h, buf_h,\
#                         dim_temp, buf_temp)
#           dim_h = dim_temp
#           buf_h = buf_temp

#           change_location = head_position
#           changes += 1

#       if changes > 0:
#           if print_position == change_location:
#               dim_t = dim_h; buf_t = buf_h
#               arr_t = buf_t[print_position % buffer_length]
#               changes -= 1


def recenter(com, dim, arr):
    """
    Recenters the simulation

    :param com:     center_of_mass
    :param dim:     dimensions of array
    :param array:   the array
    :return:        ver (vertical movement), hor (horizontal movement)
    """
    ver = 0
    hor = 0
    center = [dim[0]/2, dim[1]/2]
    offcenter = center - com
    norm = np.sqrt(np.sum(offcenter**2))
    print('Offcenter norm: {}'.format(norm))
    if norm > 2:
        if offcenter[0] < 0:
            roll_rows_pointer(dim, arr)
            ver += 1
        else:
            roll_rows_back_pointer(dim, arr)
            ver -= 1
        if offcenter[1] < 0:
            roll_columns_pointer(dim, arr)
            hor += 1
        else:
            roll_columns_back_pointer(dim, arr)
            hor -= 1

    return ver, hor

def analysis(dim, arr):
    pos = get_living(arr)
    pop = len(pos)
    com = center_of_mass(pos, pop)
    rad = radius_of_gyration(com, pos, pop)
    max_diam, min_diam = axial_diameter(pos)
    pop_den = population_density(rad, pop)
    return pos, pop, com, rad, max_diam, min_diam, pop_den

def time_series(com_series, pop_series, rad_series, max_series, pop_den_series, arr):
    pos = get_living(arr)
    pop = len(pos)
    pop_series.append(pop)
    com = center_of_mass(pos, pop)
    com_series.append(com)
    rad = radius_of_gyration(com, pos, pop)
    rad_series.append(rad)
    max_diam, min_diam = axial_diameter(pos)
    max_series.append(max_diam)
    pop_den = population_density(rad, pop)
    pop_den_series.append(pop_den)
    return com_series, pop_series, rad_series, max_series, pop_den_series

if __name__=='__main__':
    contain_run()
