import array
import numpy as np

from src.Cfuncs import *
from src.Cyarr import *
from src.Pfuncs import *


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
    com = np.asarray(com)
    center = np.asarray([dim[0]/2, dim[1]/2])
    if not com.any(): com = center
    offcenter = center - com
    norm = np.sqrt(np.sum(offcenter**2))
    if norm > 2:
        if offcenter[0] > 0:
            roll_rows_pointer(1, dim, arr)
            ver += 1
        else:
            roll_rows_pointer(-1, dim, arr)
            ver -= 1
        if offcenter[1] > 0:
            roll_columns_pointer(1, dim, arr)
            hor += 1
        else:
            roll_columns_pointer(-1, dim, arr)
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
