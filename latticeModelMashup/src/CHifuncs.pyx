import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from Cfuncs import *
from Pfuncs import *

from cpython cimport array
cimport numpy as np


cpdef change_zoom_level(int head_pos, int buf_len, int[:] dim, int[:, :, :] buf):
    """
    Checks the array edges, resizes if necessary.

    :param arr:
    :return:        (3D pointer) new buffer
    """
    if check_rim(0, dim, buf[head_pos]) is True:
        dim_v, buf_v = resize_array_buffer(dim, buf_len)
        change_buffer(head_pos, buf_len, dim, buf, dim_v, buf_v)
#   else:   # if outer rim has nothing, check next one in
#       if check_rim(1, dim_v, arr_v) is False and check _rim(2, dim_v, arr_v) is False:
#           dim_v, buf_v = resize_array_buffer(dim, buf_len, -1)
#           change_buffer(head_pos, buf_len, dim, buf, dim_v, buf_v,
#                         array.array('i', [1,1]), array.array('i', [2, 2]))
    return dim_v, buf_v

cpdef dynamic_zoom_run(list dim_list):
    """
    Performs a run, changing zoom level as appropriate.
    """
    cdef int buf_len, head_pos, print_pos, analysis_pos, updates
    cdef float beta, threshold
    cdef list rules
    cdef int[:] horizontal, vertical, bounds, rule, dim
    cdef int[:, :] arr
    cdef int[:, :, :] head_buf

    beta = 1/8
    updates = 1000
    threshold = 1
    rules = [[2,3,3,3],[2,3,3,3]]
    horizontal = array.array('i', [0, 1, 2, 1])
    vertical = array.array('i', [0, 1, 1, 1])
    bounds = array.array('i', [1, 1, 1, 1])

    head_pos, buf_len, print_pos, analysis_pos,\
        dim_head, arr_head, buf_head = init(dim_list)
    dim_tail = dim_head; arr_tail = arr_head; buf_tail = buf_head

    basic_update(updates, beta, threshold, bounds,
                    prepair_rule(rules, head_pos), dim_head, arr_head,
                    horizontal, vertical)
    horizontal[0] += horizontal[2]
    vertical[0] += vertical[2]
    head_pos += 1
    arr_head = buf_head[head_pos % buf_len]

    changes = 0
    while True:
        # analysis here
        #

        basic_print(bounds, dim_tail, arr_tail, horizontal, vertical)
        print_pos += 1
        arr_tail = buf_tail[print_pos % buf_len]

        basic_update(updates, beta, threshold, bounds,
                        prepair_rule(rules, head_pos), dim_head, arr_head,
                        horizontal, vertical)
        if check_rim(0, dim_head, arr_head) is True:
            dim_temp, buf_temp = resize_array_buffer(dim_head, buf_len)
            change_buffer(head_pos % buf_len, buf_len, dim_head, buf_head,\
                          dim_temp, buf_temp)
            dim_head = dim_temp; buf_head = buf_temp
            change_pos = head_pos; changes += 1
        head_pos += 1
        arr_head = buf_head[head_pos % buf_len]

        if changes > 0:
            if print_pos == change_pos:
                dim_tail = dim_head; buf_tail = buf_head
                arr_tail = buf_tail[print_pos % buf_len]
                changes -= 1

cpdef init(list dimensions):
    """
    Initializes all the variables for a standard run.

    :param dimensions:      (list) initial dimensions of array
    :param rules:           (list) rules
    :return:
        head_pos            (int) position of head in buffer
        buf_len             (int) buffer length
        print_pos           (int) position to be printed
        analysis_pos        (int) positions to be analysed
        dim_v               (pointer) dimensions of array
        arr_v               (2D pointer) array
        buf_v               (3D pointer) buffer
    """
    cdef int buf_len, head_pos, print_pos, analysis_pos
    cdef int[:] dim_v = array.array('i', dimensions)
    cdef int[:, :] arr_v
    cdef int[:, :, :] buf_v

    buf_len = 10
    head_pos = 0
    print_pos = 0
    analysis_pos = 0
    buf_v = init_array_buffer(dim_v, buf_len)
    arr_v = buf_v[head_pos % buf_len]

    clear_array(dim_v, arr_v)
    randomize_center(7, dim_v, arr_v)
    advance_array(head_pos % buf_len, buf_len, buf_v)

    head_pos += 1
    arr_v = buf_v[head_pos % buf_len]

    return head_pos, buf_len, print_pos, analysis_pos, dim_v, arr_v, buf_v

cpdef basic_update(
    int updates, float beta,
    float threshold, int[:] bounds,
    int[:] rule, int[:] dim, int[:, :] arr,
    int[:] horizontal = array.array('i', [0, 1, 1, 1]),
    int[:] vertical = array.array('i', [0, 1, 1, 1]),
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
    :param horizontal:  [start, width, step, polarity (-1 is off)]
    :param vertical:    [start, width, step, polarity (-1 is off)]
    :return:            None
    """
    ising_process(updates, beta, dim, arr)
    add_noise(threshold, dim, arr)
    set_bounds(bounds[0], bounds[1], bounds[2], bounds[3], dim, arr)
    scroll_bars(dim, arr, horizontal, vertical)
    conway_process(rule, dim, arr)

cpdef basic_print(
    int[:] bounds,
    int[:] dim, int[:, :] arr,
    int[:] horizontal = array.array('i', [0, 1, 1, 1]),
    int[:] vertical = array.array('i', [0, 1, 1, 1]),
):
    """
    Performs a basic print after adding back the bars etc. as reference.
    This means the bars and bounds are avoided in the calculation.

    :param bounds:      (pointer) boundary values   (-1 is off)
    :param dim:         (pointer) arr dimensions
    :param arr:         (2D pointer) array
    :param horizontal:  [start, width, step, polarity (-1 is off)]
    :param vertical:    [start, width, step, polarity (-1 is off)]
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
