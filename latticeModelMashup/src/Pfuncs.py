import numpy as np
from numpy.core.umath_tests import inner1d

def clear_columns(num, width, array):
    for i in range(width):
        array = clear_column((num + i) % array.shape[1], array)
    return array

def fill_columns(num, width, array):
    for i in range(width):
        array = fill_column((num + i) % array.shape[1], array)
    return array

def replace_columns(num, width, nucol, array):
    for i in range(width):
        array = replace_column((num + i) % array.shape[1], nucol, array)
    return array

def clear_rows(num, width, array):
    for i in range(width):
        array = clear_row((num + i) % array.shape[0], array)
    return array

def fill_rows(num, width, array):
    for i in range(width):
        array = fill_row((num + i) % array.shape[0], array)
    return array

def replace_rows(num, width, nucol, array):
    for i in range(width):
        array = replace_row((num + i) % array.shape[0], nucol, array)
    return array

def fill_bounds(array):
    array = fill_column(0, array)
    array = fill_column(-1, array)
    array = fill_row(0, array)
    array = fill_row(-1, array)
    return array

def clear_bounds(array):
    array = clear_column(0, array)
    array = clear_column(-1, array)
    array = clear_row(0, array)
    array = clear_row(-1, array)
    return array

def set_bounds(ub, rb, db, lb, array):
    if ub >= 0:
        array[..., 0] = ub
    if db >= 0:
        array[..., -1] = db
    if lb >= 0:
        array[0, ...] = lb
    if rb >= 0:
        array[-1, ...] = rb
    return array

#=========================LOW-LEVEL==========================
def clear_array(array):
    return np.zeros(array.shape, np.intc)

def fill_array(array):
    return np.ones(array.shape, np.intc)

def replace_array(offset, nuarr, array):
    array[offset[0]: offset[0] + nuarr.shape[0], offset[1]: offset[1] + nuarr.shape[1]] = nuarr
    return array

def fill_row(num, array):
    array[num, ...] = 1
    return array

def fill_column(num, array):
    array[..., num] = 1
    return array

def clear_row(num, array):
    array[num, ...] = 0
    return array

def clear_column(num, array):
    array[..., num] = 0
    return array

def replace_row(num, nurow, array):
    array[num, ...] = nurow
    return array

def replace_column(num, nucol, array):
    array[..., num] = nucol
    return array

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
