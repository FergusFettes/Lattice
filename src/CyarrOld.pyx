import cython

import array
import numpy as np

from cpython cimport array
cimport numpy as np


#===============ATOMIC LOW-LEVEL======================
#=====================================================

#===================Rollers===========================
#can automaticaly apply this decorator in unit tests????
#@cython.boundscheck(False) saves you something like 3%
cpdef int[:, :] roll_columns(int pol, int[:] dim, int[:, :] arr):
    """
    Rolls along the columns axis (1)

    :param pol:         (int) polarity of roll
    :param dim:         (pointer) dimensions of arr
    :param arr:       (2D pointer) arr
    :return:            (2D pointer) new arr
    """
    cdef int[:, :] arrout = np.empty_like(arr)
    if pol == -1:
        arrout[:, -1] = arr[:, 0]
        arrout[:, :-1] = arr[:, 1:]
    elif pol == 1:
        arrout[:, 0] = arr[:, -1]
        arrout[:, 1:] = arr[:, :-1]
    return arrout

cpdef int[:, :] roll_rows(int pol, int[:] dim, int[:, :] arr):
    """
    Rolls along the rows axis (0)

    :param pol:         (int) polarity of roll
    :param dim:         (pointer) dimensions of arr
    :param arr:       (2D pointer) arr
    :return:            (2D pointer) new arr
    """
    cdef int[:, :] arrout = np.empty_like(arr)
    if pol == -1:
        arrout[-1, :] = arr[0, :]
        arrout[:-1, :] = arr[1:, :]
    elif pol == 1:
        arrout[0, :] = arr[-1, :]
        arrout[1:, :] = arr[:-1, :]
    return arrout

cpdef roll_columns_pointer(int pol, int[:] dim, int[:, :] arr):
    """
    Rolls along the columns axis (1)

    :param pol:         (int) polarity of roll
    :param dim:         (pointer) dimensions of arr
    :param arr:       (2D pointer) arr
    :return:            None
    """
    cdef int temp
    cdef Py_ssize_t i, j
    if pol == -1:
        for i in range(dim[0]):
            temp = arr[i][0]
            for j in range(dim[1]-1):
                arr[i][j] = arr[i][j+1]
            arr[i][dim[1] - 1] = temp
    elif pol == 1:
        for i in range(dim[0]):
            temp = arr[i][-1]
            for j in range(dim[1]-1):
                arr[i][-1-j] = arr[i][-1-j-1]
            arr[i][0] = temp

cpdef roll_rows_pointer(int pol, int[:] dim, int[:, :] arr):
    """
    Rolls along the rows axis (0)

    :param pol:         (int) polarity of roll
    :param dim:         (pointer) dimensions of arr
    :param arr:       (2D pointer) arr
    :return:            None
    """
    cdef int[:] temp_v
    cdef Py_ssize_t i, j
    if pol == -1:
        temp_v = array.array('i', arr[0, :])
        arr[:-1, :] = arr[1:, :]
        arr[-1, :] = temp_v
    elif pol == 1:
        temp_v = array.array('i', arr[-1, :])
        arr[1:, :] = arr[:-1, :]
        arr[0, :] = temp_v

#==============Rim jobs===========================
#TODO: these can be made way more performant. Auto speedtests plox.
#TODO: fix the sum so it doesnt double count corners
cpdef sum_rim(int num, int[:] dim, int[:, :] arr):
    """
    Sums the cells on the edge.

    :param num:     (int) distance from edge
    :param dim:     (pointer) arr dimensions
    :param arr:     (2D pointer) arr
    :return:        (int) total
    """
    tot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        tot += arr[i][0 + num]
        tot += arr[i][-1 - num]
    for j in range(dim[1]):
        tot += arr[0 + num][j]
        tot += arr[-1 - num][j]
    return tot

cpdef check_rim(int num, int[:] dim, int[:, :] arr):
    """
    Checks there are cells on the edge.

    :param num:     (int) distance from edge
    :param dim:     (pointer) arr dimensions
    :param arr:     (2D pointer) arr
    :return:        (int) total
    """
    tot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        tot += arr[i][0 + num]
        tot += arr[i][-1 - num]
        if tot is not 0: return True
    for j in range(dim[1]):
        tot += arr[0 + num][j]
        tot += arr[-1 - num][j]
        if tot is not 0: return True
    return False


#=========Array editing=============
#TODO: allow for multiple bars
cpdef scroll_bars(
    int[:] dim, int[:, :] arr,
    int[:] horizontal = array.array('i', [0, 1, 1, 0, 1]),
    int[:] vertical = array.array('i', [0, 1, 1, 0, 1]),
):
    """
    Controls the vertical and horizontal scroll bars.

    :param horizontal:  [start, width, step, bounce, polarity (-1 is off)]
    :param vertical:    [start, width, step, bounce, polarity (-1 is off)]
    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :return:            None
    """
    if horizontal[-1] == -1 and vertical[-1] == -1:
        return

    if horizontal[-1] == 1:
        fill_rows(horizontal[0], horizontal[1], dim, arr)
    elif horizontal[-1] == 0:
        clear_rows(horizontal[0], horizontal[1], dim, arr)

    if vertical[-1] == 1:
        fill_columns(vertical[0], vertical[1], dim, arr)
    elif vertical[-1] == 0:
        clear_columns(vertical[0], vertical[1], dim, arr)

cpdef set_bounds(int ub, int rb, int db, int lb, int[:] dim, int[:, :] arr):
    """
    Sets boundaries

    :param ub:      (int) upper bound value
    :param rb:      (int) right bound value
    :param db:      (int) down bound value
    :param lb:      (int) left bound value
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    if ub == 1:
        fill_row(0, arr)
    elif ub == 0:
        clear_row(0, arr)

    if db == 1:
        fill_row(-1, arr)
    elif db == 0:
        clear_row(-1, arr)

    if lb == 1:
        fill_column(0, arr)
    elif lb == 0:
        clear_column(0, arr)

    if rb == 1:
        fill_column(-1, arr)
    elif rb == 0:
        clear_column(-1, arr)

cpdef fill_array(int[:] dim, int[:, :] arr):
    """
    Fills arr with 1s

    :param arr:     (2D pointer) arr
    :return:        None
    """
    arr[:, :] = 1

cpdef clear_array(int[:] dim, int[:, :] arr):
    """
    Fills arr with 0s

    :param arr:     (2D pointer) arr
    :return:        None
    """
    arr[:, :] = 0

cpdef replace_array(int[:] offset, int[:] dim_nu, int[:, :] nuarr, int[:] dim, int[:, :] arr):
    """
    Fills arr with another arr

    :param offset:  (pointer) offset of inner arr
    :param dim_nu:  (pointer) dimensions of inner arr
    :param nuarr:   (2D pointer) inner arr
    :param arr:     (2D pointer) arr
    :return:        None
    """
    arr[offset[0] : dim_nu[0] + offset[0], offset[1] : dim_nu[1] + offset[1]] =\
        nuarr[:, :]

cpdef create_box(int left, int wid, int top, int hi, int[:] dim, int[:, :] arr):
    """
    Makes a rectangle of 1s at positions specified

    :param left:    (int)
    :param wid:     (int)
    :param top:     (int)
    :param hi:      (int)
    :param dim:     (pointer) arr dimensions
    :param arr:     (2D pointer) arr
    :return:        None
    """
    arr[left:left + wid,top:top + hi] = 1

cpdef set_points(int[:, :] points, int[:] dim, int[:, :] arr):
    """
    Sets points to 1

    :param points:  (pointer)
    :param dim:     (pointer) arr dimensions
    :param arr:   (2D pointer) arr
    :return:        (int) total
    """
    cdef int[:] i
    for i in points:
        arr[i[0]][i[1]] = 1

cpdef fill_bounds(int[:] dim, int[:, :] arr):
    """
    Sets boundaries to 1

    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    fill_row(0, arr)
    fill_row(-1, arr)
    fill_column(0, arr)
    fill_column(-1, arr)

cpdef clear_bounds(int[:] dim, int[:, :] arr):
    """
    Sets boundaries to 0

    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    clear_row(0, arr)
    clear_row(-1,  arr)
    clear_column(0,  arr)
    clear_column(-1, arr)

cpdef fill_rows(int num, int width, int[:] dim, int[:, :] arr):
    """
    Fills rows of arr with 1s

    :param num:     (int) index of starting row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        fill_row((num + i) % dim[0], arr)

cpdef clear_rows(int num, int width, int[:] dim, int[:, :] arr):
    """
    Fills rows of arr with 0s

    :param num:     (int) index of row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        clear_row((num + i) % dim[0], arr)

cpdef replace_rows(int num, int width, int[:] nurow, int[:] dim, int[:, :] arr):
    """
    Fills rows of arr with another row

    :param num:     (int) index of row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of arr
    :param nurow:   (pointer) new row values
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        replace_row((num + i) % dim[0], nurow, arr)

cpdef fill_columns(int num, int width, int[:] dim, int[:, :] arr):
    """
    Fills columns of arr with 1s

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        fill_column((num + i) % dim[1], arr)

cpdef clear_columns(int num, int width, int[:] dim, int[:, :] arr):
    """
    Fills columns of arr with 0s

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        clear_column((num + i) % dim[1], arr)

cpdef replace_columns(int num, int width, int[:] nucol, int[:] dim, int[:, :] arr):
    """
    Fills columns of arr with new values

    :param num:     (int) index of column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of arr
    :param nucol:   (pointer) values to fill column
    :param arr:   (2D pointer) arr
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        replace_column((num + i) % dim[1], nucol, arr)

cdef fill_row(int num, int[:, :] arr):
    arr[num, :] = 1

cdef clear_row(int num, int[:, :] arr):
    arr[num, :] = 0

cdef replace_row(int num, int[:] nurow, int[:, :] arr):
    arr[num, :] = nurow

cdef fill_column(int num, int[:, :] arr):
    arr[:, num] = 1

cdef clear_column(int num, int[:, :] arr):
    arr[:, num] = 0

cdef replace_column(int num, int[:] nucol, int[:, :] arr):
    arr[:, num] = nucol
