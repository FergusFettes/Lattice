import cython

import array
import numpy as np
import time

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

cpdef int[:] prepair_rule(list rules, int frame):
    """
    Prepairs rule for this frame

    :param rules:       (list) full rule list
    :param frame:       (int) framnumber
    :return:            (pointer) current rule
    """
    return array.array('i', rules[frame % len(rules)])

cpdef advance_array(int pos, int length, int[:, :, :] buf):
    """
    Copys the array into the next buffer position.

    :param pos:         (int) index of array
    :param length:      (int) length of buffer
    :param buf:         (3D pointer) buffer
    :return:            None
    """
    buf[(pos + 1) % length] = buf[pos]

cpdef change_buffer(
    int pos, int length, int[:] dim_old, int[:, :, :] buf_old,
    int[:] dim_nu, int[:, :, :] buf_nu,
    int[:] offset=array.array('i', [1,1]), int[:] cut=array.array('i', [0,0])
):
    """
    Copys the array into a different buffer, resizing and repositioning it as specified.

    :param pos:         (int) index of array
    :param length:      (int) length of buffer
    :param dim_old:     (pointer) dimensions of old buffer
    :param buf_old:     (3D pointer) old buffer
    :param dim_nu:      (pointer) dimensions of new buffer
    :param buf_nu:      (3D pointer) new buffer
    :param offset:      (pointer) offset of array in new buffer
    :param cut:         (pointer) cut off sides of old buffer
    :return:            None
    """
    clear_array(dim_nu, buf_nu[pos % length])
    buf_nu[pos, offset[0]: offset[0] + dim_old[0] - cut[0] * 2,\
                offset[1]: offset[1] + dim_old[1] - cut[1] * 2] =\
        buf_old[pos, cut[0]: dim_old[0] - cut[0],\
                     cut[1]: dim_old[1] - cut[1]]

cpdef int[:, :, :] init_array_buffer(int[:] dim, int length):
    """
    Creates a buffer array.
    Buffer is uninitialized. This is essentially a (safe, easy) malloc.

    :param dim:     (pointer) size of the array
    :param length:  (int) buffer_size
    :return:        (3D pointer) new array buffer
    """
    return np.empty([length, dim[0], dim[1]], np.intc)

#TODO: s/rep every spare cpdef adding 'tuple' declaration
#TODO: replace every cpdef with cdef
#TODO: time the results of these two steps!
cpdef resize_array_buffer(int[:] dim_old, int length, int add=1):
    """
    Creates a new array buffer, larger than the last
    Buffer is uninitialized. This is essentially a (safe, easy) malloc.

    :param dim_old:     (pointer) size of the array
    :param length:      (int) buffer length
    :param add:         amount of space to add at the edges of the new array
    :return:            dim_v, buf_v
    """
    cdef int[:] dim_v = array.array('i', [dim_old[0] + add * 2, dim_old[1] + add * 2])
    cdef int[:, :, :] buf_v = init_array_buffer(dim_v, length)
    return dim_v, buf_v

cpdef int[:, :] init_array(int[:] dim_v):
    """
    Creates a little array.

    :param size:    (pointer) size of the array
    :return:        (pointer) dim_v, (pointer) arr_v, (arr) rule
    """
    return np.zeros(dim_v, np.intc)

#===============FANTASTIC STOCHASTIC===============
cpdef randomize_center(int siz, int[:] dim, int[:, :] arr, float threshold=0.2):
    """
    Puts a little random array in the center of the array

    :param size:        (pointer) size of small array
    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :return:            None
    """
    cdef int[:] dim_v, offset_v
    cdef int[:, :] arr_v
    dim_v = array.array('i', [siz, siz])
    arr_v = init_array(dim_v)

    add_noise(threshold, dim_v, arr_v)

    offset_v = array.array('i', [int((dim[0] - dim_v[0])/2), int((dim[1] - dim_v[1])/2)])
    replace_array(offset_v, dim_v, arr_v, dim, arr)

#TODO: add function capabilities (also make more performant if you are going to do that..)
cpdef add_noise(float threshold, int[:] dim, int[:, :] arr):
    """
    Adds simple noise to an array.

    :param threshold: (float) Noise threshold (0-1)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return: None
    """
    if threshold == 1.0:
        return
    cdef int[:, :] narr = np.asarray(np.random.random(dim) > threshold, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            arr[i][j] = arr[i][j] ^ narr[i][j]
            # To do this without numpy, remove first and add this. It's slower though.
            # (might not be slower now ive changed the above...)
            # array[x][y] = array[x][y] ^ (rand() % 2)

cpdef ising_process(int updates, float beta, int[:] dim, int[:, :] arr):
    """
    Performs ising updates on the array.

    :param updates: (int) Number of updates to perform
    :param beta:    (float) Inverse temperature (>1/8 --> pure noise)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    if updates == 0:
        return
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
            l = int(arr[a][b] == arr[(a + 1) % N][b])
            r = int(arr[a][b] == arr[(a - 1) % N][b])
            u = int(arr[a][b] == arr[a][(b + 1) % D])
            d = int(arr[a][b] == arr[a][(b - 1) % D])
            nb = l + u + d + r - 2
        else:
            l = int(arr[a][b] == arr[(a + 1)][b])
            r = int(arr[a][b] == arr[(a - 1)][b])
            u = int(arr[a][b] == arr[a][(b + 1)])
            d = int(arr[a][b] == arr[a][(b - 1)])
            nb = l + u + d + r - 2
        if nb <= 0 or (rand() / RAND_MAX) < cost[nb]:
            arr[a][b] = not arr[a][b]

#===================CONWAY=================
#TODO: make more atomic, so you can do more testing. Also add different version, likewise.
cpdef conway_process(int[:] rule, int[:] dim, int[:, :] arr):
    """
    Performs conway update on the array.

    :param rule:    (pointer) update rule for this frame
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    if rule[0] == -1:
        return
    cdef int[:, :] l, r, u, d, ul, dl, ur, dr
    l = roll_columns(1, dim, arr)
    r = roll_columns(-1, dim, arr)
    u = roll_rows(1, dim, arr)
    d = roll_rows(-1, dim, arr)
    ul = roll_rows(1, dim, l)
    dl = roll_rows(-1, dim, l)
    ur = roll_rows(1, dim, r)
    dr = roll_rows(-1, dim, r)
    cdef int NB
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            NB = 0
            NB = l[i][j] + r[i][j] + u[i][j] + d[i][j] + ul[i][j] + ur[i][j]\
                + dl[i][j] + dr[i][j]
            if arr[i][j] is 1:
                if not rule[0] <= NB <= rule[1]:
                    arr[i][j] = 0
            else:
                if rule[2] <= NB <= rule[3]:
                    arr[i][j] = 1


#===============MOSTLY LOW-LEVEL======================
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
    int[:] horizontal = array.array('i', [0, 1, 1, 1]),
    int[:] vertical = array.array('i', [0, 1, 1, 1]),
):
    """
    Controls the vertical and horizontal scroll bars.

    :param horizontal:  [start, width, step, polarity (-1 is off)]
    :param vertical:    [start, width, step, polarity (-1 is off)]
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
