#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

#@cython.boundscheck(False)
#@cython.wraparound(False)
cpdef add_noise(float threshold, int[:] dim, int[:, :] array):
    """
    Adds simple noise to an array.

    :param threshold: (float) Noise threshold (0-1)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return: None
    """
    cdef int[:, :] narr = np.random.randint(0, 2, dim, np.intc)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ narr[x][y]

cpdef ising_process(int updates, float beta, int[:] dim, int[:, :] array):
    """
    Performs ising updates on the array.

    :param updates: (int) Number of updates to perform
    :param beta:    (float) Inverse temperature (>1/8 --> pure noise)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    cdef float[:] cost = np.zeros(3, np.float32)
    cost[1] = np.exp(-4 * beta)
    cost[2] = cost[1] ** 2
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, l, r, u, d, nb
    for _ in range(updates):
        a = rand() % N
        b = rand() % D
        l = int(array[a][b] == array[(a + 1) % N][b])
        r = int(array[a][b] == array[(a - 1) % N][b])
        u = int(array[a][b] == array[a][(b + 1) % D])
        d = int(array[a][b] == array[a][(b - 1) % D])
        nb = l + u + d + r - 2
        if nb <= 0 or (rand() / RAND_MAX) < cost[nb]:
            array[a][b] = not array[a][b]

cpdef conway_process(int[:] rule, int[:] dim, int[:, :] array):
    """
    Performs conway update on the array.

    :param rule:    (pointer) update rule for this frame
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    cdef int[:, :] l, r, u, d, ul, dl, ur, dr
    l = np.roll(array, -1, axis=0)
    r = np.roll(array, 1, axis=0)
    u = np.roll(array, 1, axis=1)
    d = np.roll(array, -1, axis=1)
    ul = np.roll(l, 1, axis=1)
    dl = np.roll(l, -1, axis=1)
    ur = np.roll(r, 1, axis=1)
    dr = np.roll(r, -1, axis=1)
    cdef int NB
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            NB = 0
            NB = l[i][j] + r[i][j] + u[i][j] + d[i][j] + ul[i][j] + ur[i][j]\
                + dl[i][j] + dr[i][j]
            if array[i][j] is 1:
                if not rule[0] <= NB <= rule[1]:
                    array[i][j] = 0
            else:
                if rule[2] <= NB <= rule[3]:
                    array[i][j] = 1

cpdef fill_bounds(int[:] dim, int[:, :] array):
    """
    Sets boundaries to 1

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    fill_row(0, dim, array)
    fill_row(dim[0] - 1, dim, array)
    fill_column(0, dim, array)
    fill_column(dim[0] - 1, dim, array)

cpdef set_bounds(int ub, int rb, int db, int lb, int[:] dim, int[:, :] array):
    """
    Sets boundaries

    :param ub:      (int) upper bound value
    :param rb:      (int) right bound value
    :param db:      (int) down bound value
    :param lb:      (int) left bound value
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    if ub:
        fill_row(0, dim, array)
    else:
        clear_row(0, dim, array)
    if db:
        fill_row(dim[0] - 1, dim, array)
    else:
        clear_row(dim[0] - 1, dim, array)
    if lb:
        fill_column(0, dim, array)
    else:
        clear_column(0, dim, array)
    if rb:
        fill_column(dim[0] - 1, dim, array)
    else:
        clear_column(dim[0] - 1, dim, array)

cpdef clear_bounds(int[:] dim, int[:, :] array):
    """
    Sets boundaries to 0

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    clear_row(0, dim, array)
    clear_row(dim[0] - 1, dim, array)
    clear_column(0, dim, array)
    clear_column(dim[0] - 1, dim, array)

cpdef fill_rows(int num, int width, int[:] dim, int[:, :] array):
    """
    Fills rows of array with 1s

    :param num:     (int) index of starting row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        fill_row((num + i) % dim[0], dim, array)

cpdef clear_rows(int num, int width, int[:] dim, int[:, :] array):
    """
    Fills rows of array with 0s

    :param num:     (int) index of row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        clear_row((num + i) % dim[0], dim, array)

cpdef replace_rows(int num, int width, int[:] dim, int[:] nurow, int[:, :] array):
    """
    Fills rows of array with another row

    :param num:     (int) index of row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of array
    :param nurow:   (pointer) new row values
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        replace_row((num + i) % dim[0], dim, nurow, array)

cpdef fill_columns(int num, int width, int[:] dim, int[:, :] array):
    """
    Fills columns of array with 1s

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        fill_column((num + i) % dim[1], dim, array)

cpdef clear_columns(int num, int width, int[:] dim, int[:, :] array):
    """
    Fills columns of array with 0s

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        clear_column((num + i) % dim[1], dim, array)

cpdef replace_columns(int num, int width, int[:] dim, int[:] nucol, int[:, :] array):
    """
    Fills columns of array with new values

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of array
    :param nucol:   (pointer) values to fill column
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(width):
        replace_column((num + i) % dim[1], dim, nucol, array)

#======================LOW-LEVEL====================================
cpdef fill_array(int[:] dim, int[:, :] array):
    """
    Fills array with 1s

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(dim[0]):
        for j in range(dim[1]):
            array[i][j] = 1

cpdef clear_array(int[:] dim, int[:, :] array):
    """
    Fills array with 0s

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(dim[0]):
        for j in range(dim[1]):
            array[i][j] = 0

cpdef replace_array(int[:] offset, int[:] dim_nu, int[:, :] nuarr, int[:, :] array):
    """
    Fills array with another array

    :param offset:  (pointer) offset of inner array
    :param dim_nu:  (pointer) dimensions of inner array
    :param nuarr:   (2D pointer) inner array
    :param array:   (2D pointer) array
    :return:        None
    """
    for i in range(dim_nu[0]):
        for j in range(dim_nu[1]):
            array[i + offset[0]][j + offset[1]] = nuarr[i][j]

cpdef roll_columns_pointer(int num, int[:] dim, int[:, :] array):
    return memoryview(np.roll(np.asarray(array), num, axis=1))

cpdef roll_columns(int num, int[:] dim, int[:, :] array):
    cdef int[:] offset_v = np.zeros(2, np.intc)
    cdef int[:, :] nuarr_v = np.roll(np.asarray(array), num, axis=1)
    replace_array(offset_v, dim, nuarr_v, array)

cpdef roll_columns_manual(int num, int[:] dim, int[:, :] array):
    temp = np.zeros([dim[0], num], np.intc)
    for i in range(dim[0]):
        for j in range(num):
            temp[i][j] = array[i][j]
    for i in range(dim[0]):
        for j in range(dim[1]-num):
            array[i][j] = array[i][j+num]
    for i in range(dim[0]):
        for idx, j in enumerate(range(dim[1]-num, dim[1])):
            array[i][j] = temp[i][idx]

cpdef roll_columns_manual_single(int num, int[:] dim, int[:, :] array):
    for i in range(num):
        roll_columns_single(dim, array)

cdef roll_columns_single(int[:] dim, int[:, :] array):
    temp = np.zeros(dim[0], np.intc)
    for i in range(dim[0]):
        temp[i] = array[i][0]
    for i in range(dim[0]):
        for j in range(dim[1]-1):
            array[i][j] = array[i][j+1]
    for i in range(dim[0]):
        array[i][dim[1] - 1] = temp[i]

cpdef roll_columns_manual_twoloop(int num, int[:] dim, int[:, :] array):
    temp = np.zeros([dim[0], num], np.intc)
    for i in range(dim[0]):
        for j in range(dim[1]-num):
            if j < num:
                temp[i][j] = array[i][j]
            array[i][j] = array[i][j+num]
    for i in range(dim[0]):
        for idx, j in enumerate(range(dim[1]-num, dim[1])):
            array[i][j] = temp[i][idx]

cpdef roll_columns_manual_oneloop(int num, int[:] dim, int[:, :] array):
    temp = np.zeros([dim[0], num], np.intc)
    for i in range(dim[0]):
        for j in range(dim[1]):
            if j < num:
                temp[i][j] = array[i][j]
            if j < dim[1] - num:
                array[i][j] = array[i][j+num]
            if j >= dim[1] - num:
                array[i][j] = temp[i][j - (dim[1] - num) - 1]

cdef fill_row(int num, int[:] dim, int[:, :] array):
    for i in range(dim[1]):
        array[num][i] = 1

cdef clear_row(int num, int[:] dim, int[:, :] array):
    for i in range(dim[1]):
        array[num][i] = 0

cdef replace_row(int num, int[:] dim, int[:] nurow, int[:, :] array):
    for i in range(dim[1]):
        array[num][i] = nurow[i]

cdef fill_column(int num, int[:] dim, int[:, :] array):
    for i in range(dim[0]):
        array[i][num] = 1

cdef clear_column(int num, int[:] dim, int[:, :] array):
    for i in range(dim[0]):
        array[i][num] = 0

cdef replace_column(int num, int[:] dim, int[:] nucol, int[:, :] array):
    for i in range(dim[0]):
        array[i][num] = nucol[i]
