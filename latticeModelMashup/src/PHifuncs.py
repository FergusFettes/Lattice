import array
import numpy as np

from Cfuncs import *
from Pfuncs import *


def resize_array_P(dim_old, arr_old, add=None):
    """
    Creates a new array and places th old array in its center.

    :param dim:
    :param arr:
    :param add:     amount of space to add at the edges of the new array
    :returns:       dim, dim_v, arr, arr_v
    """
    add = add if add is not None else 1
    offset = array.array('i', [add, add])
    offset_v = memoryview(offset)
    size = [dim_old[0] + add * 2, dim_old[1] + add * 2]
    dim, dim_v, arr, arr_v = init_array_P(size)
    replace_array(offset_v, dim_old, arr_old, arr_v)
    return dim_v, arr_v

def init_array_P(size):
    """
    Creates a little array for testing

    :param size:    (pointer) size of the array
    :returns:       (arr) dim, (pointer) dim_v, (arr) array, (pointer) arr_v, (arr) rule,
                        (pointer) rule_v
    """
    dim = array.array('i', size)
    dim_v = memoryview(dim)
    arr = np.zeros(dim, np.intc)
    arr_v = memoryview(arr)
    return dim_v, arr_v

def recenter(com, dim, arr):
    """
    Recenters the simulation

    :param com:     center_of_mass
    :param dim:     dimensions of array
    :param array:   the array
    :returns:       ver (vertical movement), hor (horizontal movement)
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

def grow_run():
    siz = 7
    size = array.array('i', [siz, siz])
    size_v = memoryview(size)

    dim_v, arr_v = init_array(size_v)
    randomize_center(5, dim_v, arr_v)
    rules = [[2,5,4,6],[3,4,3,6]]
    com = []; pop = []; rad = []; max_diam = []; pop_den = []; wander=[0,0]; frame = 0
    while True:
        frame += 1
        ising_process(10, 1/8, dim_v, arr_v)
        conway_process(prepair_rule(rules, frame), dim_v, arr_v)
        time.sleep(0.1); print(np.asarray(arr_v))
        com, pop, rad, max_diam, pop_den = time_series(com, pop, rad, max_diam, pop_den, np.asarray(arr_v))
        if pop[-1] == 0:
            print('froze'); break
        if check_rim(dim_v, arr_v):
            dim_v, arr_v = resize_array(dim_v, arr_v)
        print('Radius: {}\nPopulation density: {}\nDiameter growth: {}'
                .format(rad[-1], pop_den[-1], diameter_growth_rate(max_diam)))
        ver,hor = recenter(com[-1], dim_v, arr_v)
        wander[0] += ver; wander[1] += hor

    print('Center wandered by {}'.format(wander))

def contain_run():
    siz = 31
    size = array.array('i', [siz, siz])
    size_v = memoryview(size)

    dim_v, arr_v = init_array(size_v)
    rules = [[2,5,3,6]]
    randomize_center(5, dim_v, arr_v)
    com = []; pop = []; rad = []; max_diam = []; pop_den = []; wander=[0,0]; frame = 0
    while True:
        frame += 1
        ising_process(10, 1/8, dim_v, arr_v)
        fill_columns(0, 2, dim_v, arr_v)
        conway_process(prepair_rule(rules, frame), dim_v, arr_v)
        roll_columns_back_pointer(dim_v, arr_v)
        roll_columns_back_pointer(dim_v, arr_v)
        fill_columns(0, 2, dim_v, arr_v)
        clear_columns(dim_v[1]-1, 1, dim_v, arr_v)
        time.sleep(0.4); print(np.asarray(arr_v))
        com, pop, rad, max_diam, pop_den = time_series(com, pop, rad, max_diam, pop_den, np.asarray(arr_v))
        if pop[-1] == 0:
            print('froze'); break
        print('Radius: {}\nPopulation density: {}\nDiameter growth: {}'
                .format(rad[-1], pop_den[-1], diameter_growth_rate(max_diam)))


if __name__=='__main__':
    grow_run()
