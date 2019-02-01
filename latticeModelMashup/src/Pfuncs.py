import numpy as np
from numpy.core.umath_tests import inner1d

def make_buffer(dim, buffer_length):
    # TODO: check this is the right sort of contiguous
    return np.zeros([dim[0], dim[1], buffer_length], np.intc)

def clear_array(array):
    return array(..., ...) = 0

def fill_arrray(array):
    return array(..., ...) = 1

#TODO: test this guy
def replace_array(offset, nuarr, array):
    return array(offset[0]:, offset[1]:) = nuarr

def fill_row(num, array):
    return array(num, ...) = 1

def fill_column(num, array):
    return array(..., num) = 1

def clear_row(num, array):
    return array(num, ...) = 0

def clear_column(num, array):
    return array(..., num) = 0

def replace_row(num, nurow, array):
    return array(num, ...) = nurow

def replace_column(num, nucol, array):
    return array(..., num) = nucol

def roll_array(up, right, array):
    array = np.roll(array, up, axis=0)
    array = np.roll(array, right, axis=1)
    return array

def get_living(array):
    return np.argwhere(array)

def get_births_deaths(arrayold, arraynu):
    common = np.bitwise_and(arraynu, arrayold)
    onlyOld = np.bitwise_xor(common, arrayold)
    onlyNew = np.bitwise_xor(common, arraynu)
    births = np.argwhere(onlyNew)
    deaths = np.argwhere(onlyOld)
    return births, deaths
