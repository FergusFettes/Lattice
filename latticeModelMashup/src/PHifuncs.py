import array
import numpy as np

from latticeModelMashup.src.Cfuncs import *
from latticeModelMashup.src.Pfuncs import *

def recenter(com, dim, arr):
    """
    Recenters the simulation

    :param com:     center_of_mass
    :param array:   the array
    :returns:       None
    """
    center = [dim[0]/2, dim[1]/2]
    offcenter = center - com
    print(offcenter)
    norm = np.sqrt(np.sum(offcenter**2))
    print(norm)
    if norm > 2:
        if offcenter[0] < 0:
            roll_rows_old(dim, arr)
        else:
            roll_rows_back_old(dim, arr)
        if offcenter[1] < 0:
            roll_columns_old(dim, arr)
        else:
            roll_columns_back_old(dim, arr)

siz = 30
size = array.array('i', [siz, siz])
size_v = memoryview(size)

dim, dim_v, arr, arr_v, rule, rule_v = init_array(size_v)
randomize_center(5, dim_v, arr_v)
while True:
    ising_process(10, 1/8, dim_v, arr_v)
    conway_process(rule, dim_v, arr_v)
    print(arr)
    time.sleep(0.5)
    tot = check_rim(dim_v, arr_v)
    positions = get_living(arr)
    com = center_of_mass(positions, len(positions))
    recenter(com, dim_v, arr_v)
    if len(positions)==0:
        print('ded')
        break
    if tot:
        print('edge')
        break
