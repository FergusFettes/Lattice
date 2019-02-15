# cython: profile = True
import cython

import array
import numpy as np
import time

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

from Cyarr import (
    roll_rows, roll_columns, roll_rows_pointer, roll_columns_pointer,
    check_rim, sum_rim, scroll_bars, set_bounds, fill_array, fill_bounds,
    clear_array, clear_bounds, replace_array,
)

#==================HI-LEVEL==================
#============================================
cpdef change_zoom_level(int[:] head_pos, int buffer_length, int[:] dim, int[:, :, :] buf):
    """
    Checks the array edges, resizes if necessary.

    :param arr:
    :return:        (3D pointer) new buffer
    """
    if check_rim(0, dim, buf[head_pos[0]]) is True:
        dim_v, buf_v = resize_array_buffer(dim, buffer_length)
        change_buffer(head_pos, buffer_length, dim, buf, dim_v, buf_v)
#   else:   # if outer rim has nothing, check next one in
#       if check_rim(1, dim_v, arr_v) is False and check _rim(2, dim_v, arr_v) is False:
#           dim_v, buf_v = resize_array_buffer(dim, buffer_length, -1)
#           change_buffer(head_pos, buffer_length, dim, buf, dim_v, buf_v,
#                         array.array('i', [1,1]), array.array('i', [2, 2]))
    return dim_v, buf_v


cpdef tuple init(list dimensions):
    """
    Initializes all the variables for a standard run.

    :param dimensions:      (list) initial dimensions of array
    :param rules:           (list) rules
    :return:
        head_pos            (pointer) position of head in buffer
        tail_pos        (pointer) positions to be analysed
        buffer_length       (int) buffer length
        buffer_status       (pointer) list of array poistions in buffer
        dim                 (pointer) dimensions of array
        arr                 (2D pointer) array
        buf                 (3D pointer) buffer
        dim                 (pointer) dimensions of array
        arr                 (2D pointer) array
        buf                 (3D pointer) buffer
    """
    cdef int buffer_length
    cdef int[:] head_posistion, tail_position, buffer_status
    cdef int[:] dim_h = array.array('i', dimensions)
    cdef int[:] dim_t = array.array('i', dimensions)
    cdef int[:, :] arr_h, arr_t
    cdef int[:, :, :] buf_h

    buffer_length = 10
    buffer_status = np.zeros(buffer_length, np.intc)
    buffer_status[0] = 1
    head_position = array.array('i', [0, 0])
    tail_position = array.array('i', [0, 0])

    buf_h = init_array_buffer(dim_h, buffer_length)
    arr_h = buf_h[head_position[0] % buffer_length]
    arr_t = buf_h[tail_position[0] % buffer_length]

    clear_array(dim_h, arr_h)
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status,
                                   buf_h, 0)

    randomize_center(7, dim_h, arr_h)
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status,
                                   buf_h, 0)

    buffer_status[0] = 2 #placing the tail in place

    return head_position, tail_position, buffer_length, buffer_status,\
            dim_t, arr_t, buf_h, dim_h, arr_h, buf_h


cpdef void basic_update(
    int updates, float beta,
    float threshold,
    int[:] rule, int[:] dim, int[:, :] arr,
    int[:] bounds = array.array('i', [-1, -1, -1, -1]),
    int[:] horizontal = array.array('i', [0, 1, 1, 0, -1]),
    int[:] vertical = array.array('i', [0, 1, 1, 0, -1]),
):
    """
    Performs the basic update

    :param updates:     (int) ising updates         (0 is off)
    :param beta:        (float) inverse temperature
    :param threshold:   (float) noise threshold     (1 is off)
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param rule:        (pointer) conway rule       (rule[0] == -1 is off)
    :param dim:         (pointer) arr dimensions
    :param arr:       (2D pointer) array
    :param horizontal:  [start, width, step, bounce, polarity (-1 is off)]
    :param vertical:    [start, width, step, bounce, polarity (-1 is off)]
    :return:            None
    """
    ising_process(updates, beta, dim, arr)
    add_stochastic_noise(threshold, dim, arr)
    set_bounds(bounds[0], bounds[1], bounds[2], bounds[3], dim, arr)
    scroll_bars(dim, arr, horizontal, vertical)
    conway_process(rule, dim, arr)


cpdef void basic_print(
    int[:] dim, int[:, :] arr,
    int[:] bounds = array.array('i', [-1, -1, -1, -1]),
    int[:] horizontal = array.array('i', [0, 1, 1, 0, -1]),
    int[:] vertical = array.array('i', [0, 1, 1, 0, -1]),
):
    """
    Performs a basic print after adding back the bars etc. as reference.
    This means the bars and bounds are avoided in the calculation.

    :param dim:         (pointer) arr dimensions
    :param arr:         (2D pointer) array
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param horizontal:  [start, width, step, bounce, polarity (-1 is off)]
    :param vertical:    [start, width, step, bounce, polarity (-1 is off)]
    :return:            None
    """
    set_bounds(bounds[0], bounds[1], bounds[2], bounds[3], dim, arr)
    scroll_bars(dim, arr, horizontal, vertical)

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


#==============MID-LEVEL========================
#===============================================
#replace memoryview with pointer when you change everything to c
cpdef update_array_positions(int[:] position, int buffer_length, int[:] buffer_status,
                             int[:, :, :] buf, int display=1):
    """
    Updates the chosen array (switches the memoryview
    to the next one in the buffer) and the buffer status.

    :param position:            (pointer) position of array to update
    :param buffer_length:       (int)
    :param buffer_status:       (pointer) current positions of arrays
    :param buf:                 (3D pointer) buffer
    :param display:             (int) output position?
    :return:                    (pointer) updated array
    """
    cdef int[:, :] arrout
    cdef int index, target

    index = position[0] % buffer_length
    target = (index + 1) % buffer_length
    if not buffer_status[target] == 0:
        return None
    else:
        buffer_status[target] = buffer_status[index]
        buffer_status[index] = 0

    position[0] += 1
    arrout = buf[position[0] % buffer_length]

    if display:
        print_buffer_status(buffer_status)

    # should make a pointer to the memview to be a real hero
    return arrout


cpdef print_buffer_status(int[:] buffer_status, int pad=4,
                          str border=r"*", str base=r"#"):
    """
    Outputs the array positions like so:
        ***************
        *  h      t   *
        *  PPPPAAAH   *
        ***************
        where h=head, t=tail
    :param buffer_status:      (pointer) current state of buffer
    :param pad:                 (int) width of padding
    :param border:              (str) style of border
    :param base:                (str) style of base
    :return:                    None
    """
    cdef str out
    cdef str buff
    buff = 'a'
    for i in buffer_status:
        if i == 0:
            buff += ' '
        if i == 1:
            buff += 'h'
        if i == 2:
            buff += 't'
    buff = buff[1:]
    out = '\n'.join(('{0}{1}{0}'.format(pad*border, len(buffer_status)*border),
                    '{0}{1}{2}{1}{0}'.format(border, ' '*(pad-1), buff),
                    '{0}{1}{2}{1}{0}'.format(border, ' '*(pad-1), len(buffer_status)*base),
                     '{0}{1}{0}'.format(pad*border, len(buffer_status)*border)))
    print(out)

#needs to be c only!
cdef void update_rules(
    int* updates,
    float* beta, float* threshold,
    int[:] horizontal, int[:] vertical, int[:] bounds,
    int[:, :] rules
):
    """
    updates the rules.

    :param update:      (int) ising updates
    :param beta:        (float) inverse temperature
    :param threshold:   (float) noise threshold
    :param horizontal:  [start, width, step, bounce, polarity (-1 is off)]
    :param vertical:    [start, width, step, bounce, polarity (-1 is off)]
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param rules:       (2d pointer) rules for conway (-1 is off)
    :return:        none
    """
    updates[0] = 100
    beta[0] = 1/8
    threshold[0] = 0.9
    rules = np.array([[2,3,3,3],[2,3,3,3]], np.intc)
    horizontal = array.array('i', [0, 1, 2, 0, 1])
    vertical = array.array('i', [0, 1, 1, 0, 1])
    bounds = array.array('i', [1, 1, 1, 1])

cpdef scroll_instruction_update_single(int[:] instructions, int[:] dim):
    """
    Updates the positons of the scrollbar.

    :param instructions:  [start, width, step, axis, bounce, polarity (-1 is off)]
    :param dim:         (pointer) dimensions of array
    :return:            None
    """
    # If bounce is on
    if instructions[4]:
        # If the step is positive
        if instructions[2] > 0:
            # If the next step takes it out of bounds
            if instructions[0] + instructions[1] + instructions[2] > dim[instructions[3]]:
                # Turn it around
                instructions[2] = -instructions[2]
        # If the step is negative
        else:
            # If the next step takes it out of bounds
            if instructions[0] + instructions[2] < 0:
                # Turn it around
                instructions[2] = -instructions[2]

cpdef scroll_instruction_update(int[:] horizontal, int[:] vertical, int[:] dim):
    """
    Updates the positons of the scrollbar.

    :param horizontal:  [start, width, step, bounce, polarity (-1 is off)]
    :param vertical:    [start, width, step, bounce, polarity (-1 is off)]
    :param dim:         (pointer) dimensions of array
    :return:            None
    """
    # If bounce is on
    if horizontal[3]:
        # If the step is positive
        if horizontal[2] > 0:
            # If the next step takes it out of bounds
            if horizontal[0] + horizontal[1] + horizontal[2] > dim[0]:
                # Turn it around
                horizontal[2] = -horizontal[2]
        # If the step is negative
        else:
            # If the next step takes it out of bounds
            if horizontal[0] + horizontal[2] < 0:
                # Turn it around
                horizontal[2] = -horizontal[2]

    if vertical[3]:
        if vertical[2] > 0:
            if vertical[0] + vertical[1] + vertical[2] > dim[1]:
                vertical[2] = -vertical[2]
        else:
            if vertical[0] + vertical[2] < 0:
                vertical[2] = -vertical[2]

    horizontal[0] = horizontal[0] + horizontal[2]
    vertical[0] = vertical[0] + vertical[2]


cpdef int[:] prepair_rule(int[:, :] rules, int[:] frame):
    """
    Prepairs rule for this frame

    :param rules:       (list) full rule list
    :param frame:       (int) framnumber
    :return:            (pointer) current rule
    """
    return array.array('i', rules[frame[0] % len(rules)])

cpdef advance_array(int[:] pos, int length, int[:, :, :] buf):
    """
    Copys the array into the next buffer position.

    :param pos:         (pointer) index of array
    :param length:      (int) length of buffer
    :param buf:         (3D pointer) buffer
    :return:            None
    """
    buf[(pos[0] + 1) % length] = buf[pos[0] % length]

cpdef change_buffer(
    int[:] pos, int length, int[:] dim_old, int[:, :, :] buf_old,
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
    clear_array(dim_nu, buf_nu[pos[0] % length])
    buf_nu[pos[0] % length, offset[0]: offset[0] + dim_old[0] - cut[0] * 2,\
                offset[1]: offset[1] + dim_old[1] - cut[1] * 2] =\
        buf_old[pos[0] % length, cut[0]: dim_old[0] - cut[0],\
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

cpdef tuple resize_array_buffer(int[:] dim_old, int length, int add=1):
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

cpdef void scroll_update(
    int[:] dim, int[:, :] arr,
    int[:] bar = array.array('i', [0, 5, 1, 0, 0, 1]),
    int[:] rule = array.array('i', [2, 3, 3, 3]),
    str name = 'noise',
):
    """
    Updates a region of the screen.

    :param dim:
    :param arr:
    :param hbar:    [start, width, step, axis, bounce, polarity (-2 is off)]
    :param vbar:
    :param name:    default is 'noise', 'ising' and 'conway' also work #TODO
    :returns:       None
    """
    if bar[-1] == -2:
        return

    if bar[3] == 0:
        for i in range(bar[1]):
            noise_row(bar[0], dim, arr, bar[-1])
    if bar[3] == 1:
            noise_column(bar[0], dim, arr, bar[-1])


cdef void noise_row(int pos, int[:] dim, int[:, :] arr, int polarity = 0):
    """
    Noises a single row.

    :param pos:     position (rownumber)
    :param dim:
    :param arr:
    :returns:       None
    """

    cdef int[:] tdim = array.array('i', [dim[0], 1])
    cdef int[:, :] tarr = arr[:, pos: (pos + 1)]
    add_stochastic_noise(0.8, tdim, tarr, polarity)

cdef void noise_column(int pos, int[:] dim, int[:, :] arr, int polarity = 0):
    """
    Noises a single column.

    :param pos:     position (rownumber)
    :param dim:
    :param arr:
    :returns:       None
    """

    cdef int[:] tdim = array.array('i', [1, dim[1]])
    cdef int[:, :] tarr = arr[pos: pos + 1, :]
    add_stochastic_noise(0.8, tdim, tarr, polarity)

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

    add_global_noise(threshold, dim_v, arr_v)

    offset_v = array.array('i', [int((dim[0] - dim_v[0])/2), int((dim[1] - dim_v[1])/2)])
    replace_array(offset_v, dim_v, arr_v, dim, arr)

cpdef add_global_noise(float threshold, int[:] dim, int[:, :] arr, int polarity=0):
    """
    Adds simple noise to an array.
    NB: This is faster than add_stochastic_noise for large noise levels.

    :param threshold: (float) Noise threshold (0-1)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :param polarity: (int) 1 is additive, 0 is normal and -1 is subtractive
    :return: None
    """
    if threshold == 0.0:
        return
    cdef int[:, :] narr = np.asarray(np.random.random(dim) < threshold, np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if polarity == 1:
                arr[i][j] = arr[i][j] | narr[i][j]
            elif polarity == -1:
                arr[i][j] = ~(arr[i][j] & narr[i][j])
            else:
                arr[i][j] = arr[i][j] ^ narr[i][j]

cpdef add_stochastic_noise(float coverage, int[:] dim, int[:, :] arr, int polarity=0):
    """
    Adds simple noise to an array.
    NB: This is slower than add_global_noise for large noise levels.
    Use the 'additive' setting to make the most of the speed if you want a fuller array.

    :param threshold: (float) Noise threshold (0-1)
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :param polarity (int) 1 is additive, 0 is normal and -1 is subtractive
    :return: None
    """
    if coverage == 0.0:
        return
    cdef int[:, :] vex = np.random.randint(0, dim[0], (int(coverage * dim[0] * dim[1]), 1),
                                           np.intc)
    cdef int[:, :] vey = np.random.randint(0, dim[1], (int(coverage * dim[0] * dim[1]), 1),
                                           np.intc)
    cdef int[:, :] vecs = np.concatenate((vex, vey), axis=1)
    cdef Py_ssize_t i
    cdef int a, b
    for i in range(int(coverage * dim[0] * dim[1])):
        a = vecs[i, 0]
        b = vecs[i, 1]
        if polarity == 1:
            arr[a, b] = 1
        elif polarity == -1:
            arr[a, b] = 0
        else:
            arr[a, b] = 1 - arr[a, b]

cpdef ising_process_moore(int updates, float beta, int[:] dim, int[:, :] arr):
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
    cdef Py_ssize_t i
    cdef int nb
    cdef int[:] pos
    for i in range(updates):
        pos = array.array('i', [rand() % N, rand() % D])
        nb = moore_neighbors_same(pos, dim, arr)
        if nb - 2 <= 0 or (rand() / float(RAND_MAX)) < cost[nb - 2]:
            arr[pos[0], pos[1]] = 1 - arr[pos[0], pos[1]]

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
        if nb <= 0 or (rand() / float(RAND_MAX)) < cost[nb]:
            arr[a][b] = 1 - arr[a][b]

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

#=====NEIGHBOR CALCULATIONS===========
# for some reason this is faily slow, needs further testing
cpdef int moore_neighbors_same(int[:] pos, int[:] dim, int[:, :] arr):
    """
    Calculates the number of Moore neighbors that share state with the position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int N = dim[0]
    cdef int D = dim[1]
    cdef int a = pos[0]
    cdef int b = pos[1]
    cdef int l, r, u, d, nb
    if a == 0 or b == 0 or a == dim[0]-1 or b == dim[1]-1:
        l = int(arr[a][b] == arr[(a + 1) % N][b])
        r = int(arr[a][b] == arr[(a - 1) % N][b])
        u = int(arr[a][b] == arr[a][(b + 1) % D])
        d = int(arr[a][b] == arr[a][(b - 1) % D])
        nb = l + u + d + r
    else:
        l = int(arr[a][b] == arr[(a + 1)][b])
        r = int(arr[a][b] == arr[(a - 1)][b])
        u = int(arr[a][b] == arr[a][(b + 1)])
        d = int(arr[a][b] == arr[a][(b - 1)])
        nb = l + u + d + r
    return nb

cpdef int moore_neighbors_sum(int[:] pos, int[:] dim, int[:, :] arr):
    """
    Calculated the population of the Moore neighborhood at position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int N = dim[0]
    cdef int D = dim[1]
    cdef int a = pos[0]
    cdef int b = pos[1]
    cdef int l, r, u, d, nb
    if a == 0 or b == 0 or a == dim[0]-1 or b == dim[1]-1:
        l = arr[(a + 1) % N][b]
        r = arr[(a - 1) % N][b]
        u = arr[a][(b + 1) % D]
        d = arr[a][(b - 1) % D]
        nb = l + u + d + r
    else:
        l = arr[(a + 1)][b]
        r = arr[(a - 1)][b]
        u = arr[a][(b + 1)]
        d = arr[a][(b - 1)]
        nb = l + u + d + r
    return nb

cpdef int neumann_neighbors_same(int[:] pos, int[:] dim, int[:, :] arr):
    """
    Calculates the number of Neumann neighbors that share state with the position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int N = dim[0]
    cdef int D = dim[1]
    cdef int a = pos[0]
    cdef int b = pos[1]
    cdef int l, r, u, d, ur, ul, dr, dl, nb
    if a == 0 or b == 0 or a == dim[0]-1 or b == dim[1]-1:
        l = int(arr[a][b] == arr[(a + 1) % N][b])
        r = int(arr[a][b] == arr[(a - 1) % N][b])
        ul = int(arr[a][b] == arr[(a + 1) % N][(b + 1) % D])
        ur = int(arr[a][b] == arr[(a - 1) % N][(b + 1) % D])
        dl = int(arr[a][b] == arr[(a + 1) % N][(b - 1) % D])
        dr = int(arr[a][b] == arr[(a - 1) % N][(b - 1) % D])
        u = int(arr[a][b] == arr[a][(b + 1) % D])
        d = int(arr[a][b] == arr[a][(b - 1) % D])
        nb = l + u + d + r + ul + ur + dl + dr
    else:
        l = int(arr[a][b] == arr[(a + 1)][b])
        r = int(arr[a][b] == arr[(a - 1)][b])
        ul = int(arr[a][b] == arr[(a + 1)][(b + 1)])
        ur = int(arr[a][b] == arr[(a - 1)][(b + 1)])
        dl = int(arr[a][b] == arr[(a + 1)][(b - 1)])
        dr = int(arr[a][b] == arr[(a - 1)][(b - 1)])
        u = int(arr[a][b] == arr[a][(b + 1)])
        d = int(arr[a][b] == arr[a][(b - 1)])
        nb = l + u + d + r + ul + ur + dl + dr
    return nb

cpdef int neumann_neighbors_sum(int[:] pos, int[:] dim, int[:, :] arr):
    """
    Calculated the population of the Neumann neighborhood at position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int N = dim[0]
    cdef int D = dim[1]
    cdef int a = pos[0]
    cdef int b = pos[1]
    cdef int l, r, u, d, ur, ul, dr, dl, nb
    if a == 0 or b == 0 or a == dim[0]-1 or b == dim[1]-1:
        l = arr[(a + 1) % N][b]
        r = arr[(a - 1) % N][b]
        ul = arr[(a + 1) % N][(b + 1) % D]
        ur = arr[(a - 1) % N][(b + 1) % D]
        dl = arr[(a + 1) % N][(b - 1) % D]
        dr = arr[(a - 1) % N][(b - 1) % D]
        u = arr[a][(b + 1) % D]
        d = arr[a][(b - 1) % D]
        nb = l + u + d + r + ul + ur + dl + dr
    else:
        l = arr[(a + 1)][b]
        r = arr[(a - 1)][b]
        ul = arr[(a + 1)][(b + 1)]
        ur = arr[(a - 1)][(b + 1)]
        dl = arr[(a + 1)][(b - 1)]
        dr = arr[(a - 1)][(b - 1)]
        u = arr[a][(b + 1)]
        d = arr[a][(b - 1)]
        nb = l + u + d + r + ul + ur + dl + dr
    return nb
