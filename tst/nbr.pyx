import cython

import array
import numpy as np
import time
from scipy.signal import convolve2d

from cpython cimport array
cimport numpy as np

cpdef neighbor(int[:] dim, int[:, :] arr):
    cdef int[:, :] NB, l, r, u, d, ul, dl, ur, dr
    l = np.roll(arr, -1, axis=0)
    r = np.roll(arr, 1, axis=0)
    u = np.roll(arr, 1, axis=1)
    d = np.roll(arr, -1, axis=1)
    ul = np.roll(l, 1, axis=1)
    dl = np.roll(l, -1, axis=1)
    ur = np.roll(r, 1, axis=1)
    dr = np.roll(r, -1, axis=1)
    NB = np.zeros_like(arr)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            NB[i][j] = l[i][j] + r[i][j] + d[i][j] + u[i][j] + ul[i][j] + ur[i][j]\
                + dl[i][j] + dr[i][j]
    return NB

cpdef neighbor_manual(int[:] dim, int[:, :] arr):
    cdef int[:, :] NB, l, r, u, d, ul, dl, ur, dr
    l = roll_columns(dim, arr)
    r = roll_columns_back(dim, arr)
    u = roll_rows(dim, arr)
    d = roll_rows_back(dim, arr)
    ul = roll_rows(dim, l)
    dl = roll_rows_back(dim, l)
    ur = roll_rows(dim, r)
    dr = roll_rows_back(dim, r)
    NB = np.zeros_like(arr)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            NB[i][j] = l[i][j] + r[i][j] + d[i][j] + u[i][j] + ul[i][j] + ur[i][j]\
                + dl[i][j] + dr[i][j]
    return NB

cpdef neighbor_scipy(int[:] dim, int[:, :] arr):
    arrbool = np.asarray(arr, bool)
    arrones = np.ones_like(arr)
    return convolve2d(arrbool, arrones, mode='same', boundary='fill') - arrbool

cpdef roll_columns(int[:] dim, int[:, :] array):
    """
    Rolls along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           (2D pointer) new array
    """
    cdef int[:, :] arrout = np.zeros(dim, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        arrout[i] = array[i][0]
    for i in range(dim[0]):
        for j in range(dim[1]-1):
            arrout[i][j] = array[i][j+1]
    return arrout

cpdef roll_columns_back(int[:] dim, int[:, :] array):
    """
    Rolls back along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           (2D pointer) new array
    """
    cdef int[:, :] arrout = np.zeros(dim, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        arrout[i] = array[i][-1]
    for i in range(dim[0]):
        for j in range(dim[1]-1, 0, -1):
            arrout[i][j] = array[i][j-1]
    return arrout

cpdef roll_rows(int[:] dim, int[:, :] array):
    """
    Rolls along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           (2D pointer) new array
    """
    cdef int[:, :] arrout = np.zeros(dim, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        arrout[i] = array[0][i]
    for i in range(dim[1]):
        for j in range(dim[0]-1):
            arrout[j][i] = array[j+1][i]
    return arrout

cpdef roll_rows_back(int[:] dim, int[:, :] array):
    """
    Rolls back along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           (2D pointer) new array
    """
    cdef int[:, :] arrout = np.zeros(dim, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        arrout[0][i] = array[-1][i]
    for i in range(dim[1]):
        for j in range(dim[0]-1, 0, -1):
            arrout[j][i] = array[j-1][i]
    return arrout

cpdef roll_columns_pointer(int[:] dim, int[:, :] array):
    """
    Rolls along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           None
    """
    cdef int[:] temp = np.zeros(dim[0], np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        temp[i] = array[i][0]
    for i in range(dim[0]):
        for j in range(dim[1]-1):
            array[i][j] = array[i][j+1]
    for i in range(dim[0]):
        array[i][dim[1] - 1] = temp[i]

cpdef roll_columns_back_pointer(int[:] dim, int[:, :] array):
    """
    Rolls back along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           None
    """
    cdef int[:] temp = np.zeros(dim[0], np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        temp[i] = array[i][-1]
    for i in range(dim[0]):
        for j in range(dim[1]-1, 0, -1):
            array[i][j] = array[i][j-1]
    for i in range(dim[0]):
        array[i][0] = temp[i]

cpdef roll_rows_pointer(int[:] dim, int[:, :] array):
    """
    Rolls along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           None
    """
    cdef int[:] temp = np.zeros(dim[1], np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        temp[i] = array[0][i]
    for i in range(dim[1]):
        for j in range(dim[0]-1):
            array[j][i] = array[j+1][i]
    for i in range(dim[1]):
        array[dim[0] - 1][i] = temp[i]

cpdef roll_rows_back_pointer(int[:] dim, int[:, :] array):
    """
    Rolls back along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :returns:           None
    """
    cdef int[:] temp = np.zeros(dim[1], np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        temp[i] = array[-1][i]
    for i in range(dim[1]):
        for j in range(dim[0]-1, 0, -1):
            array[j][i] = array[j-1][i]
    for i in range(dim[1]):
        array[0][i] = temp[i]
