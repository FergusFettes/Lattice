import cython

import array
import numpy as np
import time

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np


cpdef update_pointers(int buf_length, int update, int analysis, int image):
    """
    This function keeps track of which array is being accessed by whom.
    There are currently three pointers.

    #TODO: write docstring
    :param:
    :return:        None
    """


cpdef int[:, :, :] init_array_buffer(int[:] dim, int length):
    """
    Creates a buffer array.
    Buffer is uninitialized. This is essentially a (safe, easy) malloc.

    :param dim:     (pointer) size of the array
    :param length:  (int) buffer_size
    :return:        (3D pointer) new array buffer
    """
    return np.empty([length, dim[0], dim[1]], np.intc)

cpdef resize_array_buffer(int[:] dim_old, int length, int add=0):
    """
    Creates a new array buffer, larger than the last
    Buffer is uninitialized. This is essentially a (safe, easy) malloc.

    :param dim_old:     (pointer) size of the array
    :param length:      (int) buffer length
    :param add:         amount of space to add at the edges of the new array
    :return:            dim_v, buf_v
    """
    add = add if add is not 0 else 1
    cdef int[:] dim_v = array.array('i', [dim_old[0] + add * 2, dim_old[1] + add * 2])
    cdef int[:, :, :] buf_v = init_array_buffer(dim_v, length)
    return dim_v, buf_v

cpdef resize_array(int[:] dim_old, int[:, :] arr_old, int add=0):
    """
    Creates a new array and places the old array in its center.

    :param dim:
    :param arr:
    :param add:     amount of space to add at the edges of the new array
    :return:        dim, dim_v, arr, arr_v
    """
    cdef int[:] dim_v, offset_v, size_v
    cdef int[:, :] arr_v
    add = add if add is not 0 else 1
    offset_v = array.array('i', [add, add])
    size_v = array.array('i', [dim_old[0] + add * 2, dim_old[1] + add * 2])
    dim_v, arr_v = init_array(size_v)
    replace_array(offset_v, dim_old, arr_old, arr_v)
    return dim_v, arr_v

cpdef init_array(int[:] dim_v):
    """
    Creates a little array for testing

    :param size:    (pointer) size of the array
    :return:        (pointer) dim_v, (pointer) arr_v, (arr) rule
    """
    cdef int[:, :] arr_v = np.zeros(dim_v, np.intc)
    return dim_v, arr_v

cpdef int[:] prepair_rule(list rules, int frame):
    """
    Prepairs rule for this frame

    :param rules:       (list) full rule list
    :param frame:       (int) framnumber
    :return:            (pointer) current rule
    """
    cdef int[:] rule_v = array.array('i', rules[frame % len(rules)])
    return rule_v

cpdef randomize_center(int siz, int[:] dim, int[:, :] arr):
    """
    Puts a little random array in the center of the array

    :param size:        (pointer) size of small array
    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :return:            None
    """
    cdef int[:] size_v, dim_v, offset_v
    cdef int[:, :] arr_v
    size_v = array.array('i', [siz, siz])
    dim_v, arr_v = init_array(size_v)
    add_noise(0.8, dim_v, arr_v)
    offset_v = array.array('i', [int((dim[0] - size_v[0])/2), int((dim[1] - size_v[1])/2)])
    replace_array(offset_v, dim_v, arr_v, arr)

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
            # To do this without numpy, remove first and add this. It's slower though.
            # array[x][y] = array[x][y] ^ (rand() % 2)

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
    cdef int N = dim[0]
    cdef int D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, l, r, u, d, nb
    for _ in range(updates):
        a = rand() % N
        b = rand() % D
        if a == 0 or b == 0 or a == dim[0]-1 or b == dim[1]-1:
            l = int(array[a][b] == array[(a + 1) % N][b])
            r = int(array[a][b] == array[(a - 1) % N][b])
            u = int(array[a][b] == array[a][(b + 1) % D])
            d = int(array[a][b] == array[a][(b - 1) % D])
            nb = l + u + d + r - 2
        else:
            l = int(array[a][b] == array[(a + 1)][b])
            r = int(array[a][b] == array[(a - 1)][b])
            u = int(array[a][b] == array[a][(b + 1)])
            d = int(array[a][b] == array[a][(b - 1)])
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

cpdef conway_process_manual(int[:] rule, int[:] dim, int[:, :] array):
    """
    Performs conway update on the array.

    :param rule:    (pointer) update rule for this frame
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    cdef int[:, :] l, r, u, d, ul, dl, ur, dr
    l = roll_rows(dim, array)
    r = roll_rows_back(dim, array)
    u = roll_columns(dim, array)
    d = roll_columns_back(dim, array)
    ul = roll_columns(dim, l)
    dl = roll_columns_back(dim, l)
    ur = roll_columns(dim, r)
    dr = roll_columns_back(dim, r)
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i
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
    cdef Py_ssize_t i, j
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
    cdef Py_ssize_t i, j
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
    cdef Py_ssize_t i, j
    for i in range(dim_nu[0]):
        for j in range(dim_nu[1]):
            array[i + offset[0]][j + offset[1]] = nuarr[i][j]

cpdef int[:, :] roll_columns(int[:] dim, int[:, :] array):
    """
    Rolls along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            (2D pointer) new array
    """
    cdef int[:, :] arrout = np.empty_like(array)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        arrout[i][-1] = array[i][0]
        for j in range(dim[1]-1):
            arrout[i][j] = array[i][j+1]
    return arrout

cpdef int[:, :] roll_columns_back(int[:] dim, int[:, :] array):
    """
    Rolls back along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            (2D pointer) new array
    """
    cdef int[:, :] arrout = np.empty_like(array)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        arrout[i][0] = array[i][-1]
        for j in range(dim[1]-1, 0, -1):
            arrout[i][j] = array[i][j-1]
    return arrout

cpdef int[:, :] roll_rows(int[:] dim, int[:, :] array):
    """
    Rolls along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            (2D pointer) new array
    """
    cdef int[:, :] arrout = np.empty_like(array)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        arrout[-1][i] = array[0][i]
        for j in range(dim[0]-1):
            arrout[j][i] = array[j+1][i]
    return arrout

cpdef int[:, :] roll_rows_back(int[:] dim, int[:, :] array):
    """
    Rolls back along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            (2D pointer) new array
    """
    cdef int[:, :] arrout = np.empty_like(array)
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        arrout[0][i] = array[-1][i]
        for j in range(dim[0]-1, 0, -1):
            arrout[j][i] = array[j-1][i]
    return arrout

cpdef roll_columns_pointer(int[:] dim, int[:, :] array):
    """
    Rolls along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            None
    """
    cdef int temp
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        temp = array[i][0]
        for j in range(dim[1]-1):
            array[i][j] = array[i][j+1]
        array[i][dim[1] - 1] = temp

cpdef roll_columns_back_pointer(int[:] dim, int[:, :] array):
    """
    Rolls back along the columns axis (1)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            None
    """
    cdef int temp
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        temp = array[i][-1]
        for j in range(dim[1]-1, 0, -1):
            array[i][j] = array[i][j-1]
        array[i][0] = temp

cpdef roll_rows_pointer(int[:] dim, int[:, :] array):
    """
    Rolls along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            None
    """
    cdef int temp
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        temp = array[0][i]
        for j in range(dim[0]-1):
            array[j][i] = array[j+1][i]
        array[dim[0] - 1][i] = temp

cpdef roll_rows_back_pointer(int[:] dim, int[:, :] array):
    """
    Rolls back along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            None
    """
    cdef int temp
    cdef Py_ssize_t i, j
    for i in range(dim[1]):
        temp = array[-1][i]
        for j in range(dim[0]-1, 0, -1):
            array[j][i] = array[j-1][i]
        array[0][i] = temp

cpdef check_rim(int[:] dim, int[:, :] array):
    """
    Counts the number of cells on the edge.

    :param dim:     (pointer) array dimensions
    :param array:   (2D pointer) array
    :return:        (int) total
    """
    tot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        tot += array[i][0]
        tot += array[i][-1]
    for j in range(dim[1]):
        tot += array[0][j]
        tot += array[-1][j]
    return tot

cpdef create_box(int left, int top, int right, int bottom, int[:] dim, int[:, :] array):
    """
    Makes a rectangle of 1s at positions specified

    :param left:    (int)
    :param right:   (int)
    :param top:     (int)
    :param bottom:  (int)
    :param dim:     (pointer) array dimensions
    :param array:   (2D pointer) array
    :return:        (int) total
    """
    cdef Py_ssize_t i, j
    for i in range(left, right):
        for j in range(top, bottom):
            array[i][j] = 1

cpdef set_points(int[:, :] points, int[:] dim, int[:, :] array):
    """
    Sets points to 1

    :param points:  (pointer)
    :param dim:     (pointer) array dimensions
    :param array:   (2D pointer) array
    :return:        (int) total
    """
    cdef int[:] i
    for i in points:
        array[i[0]][i[1]] = 1

cdef fill_row(int num, int[:] dim, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[1]):
        array[num][i] = 1

cdef clear_row(int num, int[:] dim, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[1]):
        array[num][i] = 0

cdef replace_row(int num, int[:] dim, int[:] nurow, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[1]):
        array[num][i] = nurow[i]

cdef fill_column(int num, int[:] dim, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[0]):
        array[i][num] = 1

cdef clear_column(int num, int[:] dim, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[0]):
        array[i][num] = 0

cdef replace_column(int num, int[:] dim, int[:] nucol, int[:, :] array):
    cdef Py_ssize_t i
    for i in range(dim[0]):
        array[i][num] = nucol[i]
