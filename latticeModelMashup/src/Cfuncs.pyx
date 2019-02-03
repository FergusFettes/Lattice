import cython

import array
import numpy as np
import time

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

cpdef basic_update(
    int updates, float beta,\
    float threshold, int[:] bounds,\
    int hor_pos, int hor_pol, int hor_wid,\
    int ver_pos, int ver_pol, int ver_wid,\
    int[:] rule, int[:] dim, int[:, :] arr
):
    """
    Performs the basic update

    :param updates:     (int) ising updates         (0 is off)
    :param beta:        (float) inverse temperature
    :param threshold:   (float) noise threshold     (1 is off)
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param hor_pos:     horizontal start
    :param hor_pol:     horizontal polarity         (-1 is off)
    :param hor_wid:     horizontal width
    :param ver_pos:     vertical start
    :param ver_pol:     vertical polarity           (-1 is off)
    :param ver_wid:     vertical width
    :param rule:        (pointer) conway rule       (rule[0] == -1 is off)
    :param dim:         (pointer) arr dimensions
    :param array:       (2D pointer) array
    :return:            None
    """
    ising_process(updates, beta, dim, arr)
    add_noise(threshold, dim, arr)
    set_bounds(bounds[0], bounds[1], bounds[2], bounds[3], dim, arr)
    scroll_bars(hor_pos, hor_pol, hor_wid,\
                ver_pos, ver_pol, ver_wid, dim, arr)
    conway_process(rule, dim, arr)

cpdef basic_print(
    int[:] bounds,\
    int hor_pos, int hor_pol, int hor_wid,\
    int ver_pos, int ver_pol, int ver_wid,\
    int[:] dim, int[:, :] arr
):
    """
    Performs a basic print after adding back the bars etc. as reference.
    This means the bars and bounds are avoided in the calculation.

    :param bounds:      (pointer) boundary values   (-1 is off)
    :param hor_pos:     horizontal start
    :param hor_pol:     horizontal polarity         (-1 is off)
    :param hor_wid:     horizontal width
    :param ver_pos:     vertical start
    :param ver_pol:     vertical polarity           (-1 is off)
    :param ver_wid:     vertical width
    :param dim:         (pointer) arr dimensions
    :param array:       (2D pointer) array
    :return:            None
    """
    set_bounds(bounds[0], bounds[1], bounds[2], bounds[3], dim, arr)
    scroll_bars(hor_pos, hor_pol, hor_wid,\
                ver_pos, ver_pol, ver_wid, dim, arr)

    temp = np.empty_like(arr, str)
    out = []
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i][j] == 0:
                temp[i][j] = '.'
            elif arr[i][j] == 1:
                temp[i][j] = 'o'
        out.append(''.join(temp[i,:]))
    fin = '\n'.join(out)
    print(fin)

cpdef update_pointers(int buf_length, int update, int analysis, int image):
    """
    This function keeps track of which array is being accessed by whom.
    There are currently three pointers.

    #TODO: write docstring
    :param:
    :return:        None
    """

cpdef advance_array(int pos, int length, int[:, :, :] buf):
    """
    Copys the array into the next buffer position.

    :param pos:         (int) index of array
    :param length:      (int) length of buffer
    :param buf:         (3D pointer) buffer
    :return:            None
    """
    buf[(pos + 1) % length] = buf[pos]

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

    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :param add:         (int) amount of space to add at the edges of the new array
    :return:            dim_v, arr_v
    """
    cdef int[:] dim_v, offset_v
    cdef int[:, :] arr_v
    add = add if add is not 0 else 1
    offset_v = array.array('i', [add, add])
    dim_v = array.array('i', [dim_old[0] + add * 2, dim_old[1] + add * 2])
    arr_v = init_array(dim_v)
    replace_array(offset_v, dim_old, arr_old, arr_v)
    return dim_v, arr_v

cpdef int[:, :] init_array(int[:] dim_v):
    """
    Creates a little array for testing

    :param size:    (pointer) size of the array
    :return:        (pointer) dim_v, (pointer) arr_v, (arr) rule
    """
    return np.zeros(dim_v, np.intc)

cpdef int[:] prepair_rule(list rules, int frame):
    """
    Prepairs rule for this frame

    :param rules:       (list) full rule list
    :param frame:       (int) framnumber
    :return:            (pointer) current rule
    """
    return array.array('i', rules[frame % len(rules)])

cpdef randomize_center(int siz, int[:] dim, int[:, :] arr):
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
    add_noise(0.8, dim_v, arr_v)
    offset_v = array.array('i', [int((dim[0] - dim_v[0])/2), int((dim[1] - dim_v[1])/2)])
    replace_array(offset_v, dim_v, arr_v, arr)

cpdef scroll_bars(
    int hor_pos, int hor_pol, int hor_wid,\
    int ver_pos, int ver_pol, int ver_wid,\
    int[:] dim, int[:, :] arr
):
    """
    Controls the vertical and horizontal scrolls bars.
    #TODO: allow for multiple bars

    :param hor_pos:     horizontal start
    :param hor_pol:     horizontal polarity
    :param hor_wid:     horizontal width
    :param ver_pos:     vertical start
    :param ver_pol:     vertical polarity
    :param ver_wid:     vertical width
    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :return:            None
    """
    if hor_pol == -1 and ver_pol == -1:
        return

    if hor_pol == 1:
        fill_rows(hor_pos, hor_wid, dim, arr)
    elif hor_pol == 0:
        clear_rows(hor_pos, hor_wid, dim, arr)

    if ver_pol == 1:
        fill_columns(ver_pos, ver_wid, dim, arr)
    elif ver_pol == 0:
        clear_columns(ver_pos, ver_wid, dim, arr)

cpdef add_noise(float threshold, int[:] dim, int[:, :] array):
    """
    Adds simple noise to an array.

    :param threshold: (float) Noise threshold (0-1)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return: None
    """
    if threshold == 1.0:
        return
    cdef int[:, :] narr = np.asarray(np.random.random() > threshold, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            array[i][j] = array[i][j] ^ narr[i][j]
            # To do this without numpy, remove first and add this. It's slower though.
            # (might not be slower now ive changed the above...)
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
    if rule[0] == -1:
        return
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
    if rule[0] == -1:
        return
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
    if ub == 1:
        fill_row(0, array)
    elif ub == 0:
        clear_row(0, array)

    if db == 1:
        fill_row(-1, array)
    elif db == 0:
        clear_row(-1, array)

    if lb == 1:
        fill_column(0, array)
    elif lb == 0:
        clear_column(0, array)

    if rb == 1:
        fill_column(-1, array)
    elif rb == 0:
        clear_column(-1, array)

#======================LOW-LEVEL====================================

cpdef fill_array(int[:, :] array):
    """
    Fills array with 1s

    :param array:   (2D pointer) array
    :return:        None
    """
    array[:, :] = 1

cpdef clear_array(int[:, :] array):
    """
    Fills array with 0s

    :param array:   (2D pointer) array
    :return:        None
    """
    array[:, :] = 0

cpdef replace_array(int[:] offset, int[:] dim_nu, int[:, :] nuarr, int[:, :] array):
    """
    Fills array with another array

    :param offset:  (pointer) offset of inner array
    :param dim_nu:  (pointer) dimensions of inner array
    :param nuarr:   (2D pointer) inner array
    :param array:   (2D pointer) array
    :return:        None
    """
    array[offset[0] : dim_nu[0] + offset[0], offset[1] : dim_nu[1] + offset[1]] =\
        nuarr[:, :]

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

cpdef roll_rows_pointer_nu(int[:] dim, int[:, :] array):
    """
    Rolls along the rows axis (0)

    :param dim:         (pointer) dimensions of array
    :param array:       (2D pointer) array
    :return:            None
    """
    cdef int[:] temp = array[0, :]
    array[0:-1, :] = array[1:-1,:]
    array[-1, :] = temp

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
    array[left:right][top:bottom] = 1

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

cpdef fill_bounds(int[:] dim, int[:, :] array):
    """
    Sets boundaries to 1

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    fill_row(0, array)
    fill_row(dim[0] - 1, array)
    fill_column(0, array)
    fill_column(dim[0] - 1, array)

cpdef clear_bounds(int[:] dim, int[:, :] array):
    """
    Sets boundaries to 0

    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    clear_row(0, array)
    clear_row(dim[0] - 1,  array)
    clear_column(0,  array)
    clear_column(dim[0] - 1, array)

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
        fill_row((num + i) % dim[0], array)

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
        clear_row((num + i) % dim[0], array)

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
        replace_row((num + i) % dim[0], nurow, array)

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
        fill_column((num + i) % dim[1], array)

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
        clear_column((num + i) % dim[1], array)

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
        replace_column((num + i) % dim[1], nucol, array)

cdef fill_row(int num, int[:, :] array):
    array[num, :] = 1

cdef clear_row(int num, int[:, :] array):
    array[num, :] = 0

cdef replace_row(int num, int[:] nurow, int[:, :] array):
    array[num, :] = nurow

cdef fill_column(int num, int[:, :] array):
    array[:, num] = 1

cdef clear_column(int num, int[:, :] array):
    array[:, num] = 0

cdef replace_column(int num, int[:] nucol, int[:, :] array):
    array[:, num] = nucol
