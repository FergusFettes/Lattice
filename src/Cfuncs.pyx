# cython: linetrace=True
import cython

import array
import numpy as np
import time

from cython.parallel import prange
from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

import src.Cyarr as cy

#============================Image processing
cpdef void export_array(object image, int[:] colorList, int[:] dim, int[:, :] arr, int color_offset):
    """
    Updates the image with the values from an entire array.

    :param image:           A QImage object to be written to
    :param colorList:       List of colors, as integers
    :param dim:             Dimensions of the array
    :param array:           Array to use as new image
    :param color_offset:    Use primary colors (0) or secondary colors (2)?
    :return:                None
    """
    cdef int color
    cdef Py_ssize_t i, j
    cdef int a = dim[0]
    cdef int b = dim[1]
    for i in range(a):
        for j in range(b):
            color = colorList[arr[i][j] + color_offset]
            image.setPixel(i, j, color)

cpdef void replace_image_positions(object image, int[:] colorList, int[:, :] L, int color):
    """
    Updates the given positions with the specified color

    :param image:   A QImage object to be written to
    :param colorList:       List of colors, as integers
    :param L:       List of positions to update
    :param color:   selection from colorlist
    :return:        None
    """
    cdef int[:] el
    for el in L:
        image.setPixel(el[0], el[1], colorList[color])

#==================HI-LEVEL==================
#============================================
cpdef change_zoom_level(int[:] head_pos, int buffer_length, int[:, :] buffer_status,
                        int[:, :] change_roll, int[:] dim, int[:, :, :] buf):
    """
    Checks the array edges, resizes if necessary and saves the change in change_roll

    :param head_pos:        position of the head in the buffer
    :param buffer_length:
    :param buffer_status:
    :param change_roll:     short list containing the mangitude and position of each change
    :param dim:
    :param buf:
    :return:
        (pointer) new dim
        (3D pointer) new buffer
        (int) size of change
    """
    cdef int[:] dim_v
    cdef int[:, :, :] buf_v
    if cy.check_rim(0, dim, buf[head_pos[0] % buffer_length]) is True:
        dim_v, buf_v = resize_array_buffer(dim, buffer_length)
        change_buffer(head_pos, buffer_length, dim, buf, dim_v, buf_v)
        head_pos[1] += 1
        change = 1
    # if outer rim has nothing, check next two in
    elif cy.check_rim(1, dim, buf[head_pos[0] % buffer_length]) is False\
     and cy.check_rim(2, dim, buf[head_pos[0] % buffer_length]) is False:
        dim_v, buf_v = resize_array_buffer(dim, buffer_length, -1)
        change_buffer(head_pos, buffer_length, dim, buf, dim_v, buf_v,
                        array.array('i', [1,1]), array.array('i', [2, 2]))
        head_pos[1] += 1
        change = -1
    else:
        dim_v = dim
        buf_v = buf
        change = 0

    cy.roll_rows_pointer(1, array.array('i', [buffer_length, 2]), change_roll)
    change_roll[0, 0] = head_pos[0]
    change_roll[0, 1] = change

    buffer_status = extend_buffer_status(head_pos, buffer_length, buffer_status)

    return dim_v, buf_v, change_roll, buffer_status

cpdef change_zoom_level_array(int[:] dim, int[:, :] arr):
    """
    Checks the array edges, resizes if necessary and saves the change in change_roll

    :param dim:
    :param arr:
    :return:
        (pointer) new dim
        (3D pointer) new arr
        (int) size of change
    """
    cdef int[:] dim_v, offset, cut
    cdef int[:, :] arr_v
    cdef int change
    if cy.check_rim(0, dim, arr) is True:
        dim_v, arr_v = resize_array(dim)
        change_array(dim, arr, dim_v, arr_v)
        change = 1
    # if outer rim has nothing, check next two in
    elif cy.check_rim(1, dim, arr) is False\
     and cy.check_rim(2, dim, arr) is False:
        dim_v, arr_v = resize_array(dim, -1)
        offset = array.array('i', [1,1])
        cut = array.array('i', [2, 2])
        change_array(dim, arr, dim_v, arr_v, offset, cut)
        change = -1
    else:
        dim_v = dim
        arr_v = arr
        change = 0

    return dim_v, arr_v, change

cpdef tuple init(list dimensions, int buffer_length, int randomize_size = 0):
    """
    Initializes all the variables for a standard run.

    :param dimensions:      (list) initial dimensions of array
    :param rules:           (list) rules
    :return:
        change_roll `       (2D pointer) list ready to recod the buffer changes
        head_pos            (pointer) position of head in buffer
        tail_pos            (pointer) positions to be analysed
        buffer_length       (int) buffer length
        buffer_status       (2Dpointer) list of array poistions in buffer
        dim                 (pointer) dimensions of array
        arr                 (2D pointer) array
        buf                 (3D pointer) buffer
        dim                 (pointer) dimensions of array
        arr                 (2D pointer) array
        buf                 (3D pointer) buffer
    """
    cdef int[:] head_position, tail_position
    cdef int[:, :] buffer_status
    cdef int[:] dim_h = array.array('i', dimensions)
    cdef int[:] dim_t = array.array('i', dimensions)
    cdef int[:, :] arr_h, arr_t
    cdef int[:, :, :] buf_h

    buffer_status = np.zeros((1, buffer_length), np.intc)
    buffer_status[0, 0] = 1
    head_position = array.array('i', [0, 0])
    tail_position = array.array('i', [0, 0])

    buf_h = init_array_buffer(dim_h, buffer_length)
    arr_h = buf_h[head_position[0] % buffer_length]
    arr_t = buf_h[tail_position[0] % buffer_length]

    cy.clear_array(dim_h, arr_h)
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status,
                                   buf_h, 0)

    cy.clear_array(dim_h, arr_h)
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status,
                                   buf_h, 0)

    randomize_center(randomize_size, dim_h, arr_h)
    advance_array(head_position, buffer_length, buf_h)
    arr_h = update_array_positions(head_position, buffer_length, buffer_status,
                                   buf_h, 0)

    buffer_status[0, 0] = 2 #placing the tail

    change_roll = np.zeros((buffer_length, 2), np.intc)
    change_roll -= 1

    return change_roll, head_position, tail_position, buffer_length, buffer_status,\
            dim_t, arr_t, buf_h, dim_h, arr_h, buf_h


cpdef void basic_update(
    float updates, float beta,
    float threshold,
    int[:] rule, int[:] dim, int[:, ::1] arr,
    int[:] bounds = array.array('i', [-1, -1, -1, -1]),
    double[:, :] bars = np.array([[0, 1, 1, 0, 0, -1]], np.double),
    double[:, :] fuzz = np.array([[0, 1, 1, 0, 0, 0.5, -2]], np.double),
):
    """
    Performs the basic update

    :param updates:     (float) ising updates (as percentage of all positions, 0 is off)
    :param beta:        (float) inverse temperature
    :param threshold:   (float) noise coverage      (0 is off)
    :param rule:        (pointer) conway rule       (rule[0] == -1 is off)
    :param dim:         (pointer) arr dimensions
    :param arr:         (2D pointer) array
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param bars:        [start, width, step, axis, bounce, polarity (-1 is off)]
    :param fuzz:        [start, width, step, axis, bounce, coverage, polarity (-2 is off)]
    :return:            None
    """
    ising_process(updates, beta, dim, arr)
    add_stochastic_noise(threshold, dim, arr)
    cy.set_bounds(bounds, dim, arr)
    cy.scroll_bars(dim, arr, bars)
    conway_process(rule, dim, arr)


# A real hero would make this a decorator
# Same for all the other small changes!
cpdef void basic_update_buffer(
    float updates, float beta,
    float threshold,
    int[:, :] rules, int[:] frame, int buffer_length,
    int[:] dim, int[:, ::1] arr, int[:, :, :] buf,
    int[:] bounds = array.array('i', [-1, -1, -1, -1]),
    double[:, :] bars = np.array([[0, 1, 1, 0, 0, -1]], np.double),
    double[:, :] fuzz = np.array([[0, 1, 1, 0, 0, 0.5, -2]], np.double),
    int[:] roll = array.array('i', [0, 0]),
):
    """
    Performs the basic update, including advancing the array in the buffer.
    Doesnt update your pointers though.

    :param updates:     (float) ising updates (as percentage of all positions, 0 is off)
    :param beta:        (float) inverse temperature
    :param threshold:   (float) noise coverage      (0 is off)
    :param rule:        (pointer) conway rule       (rule[0] == -1 is off)
    :param frame:
    :param buffer_length:
    :param dim:         (pointer) arr dimensions
    :param arr:         (2D pointer) array
    :param buf:         (3D pointer) array buffer
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param bars:        [start, width, step, axis, bounce, polarity (-1 is off)]
    :param fuzz:        [start, width, step, axis, bounce, coverage, polarity (-2 is off)]
    :param roll:        roll amount
    :return:            None
    """
    ising_process(updates, beta, dim, arr)
    add_stochastic_noise(threshold, dim, arr)
    cy.set_bounds(bounds, dim, arr)
    cy.roll_columns_pointer(roll[0], dim, arr)
    cy.roll_rows_pointer(roll[1], dim, arr)
    cy.set_bounds(bounds, dim, arr)
    cy.scroll_bars(dim, arr, bars)
    scroll_noise(dim, arr, fuzz)
    conway_process(prepair_rule(rules, frame), dim, arr)

    advance_array(frame, buffer_length, buf)


cpdef void basic_print(
    int[:] dim, int[:, :] arr,
    int[:] bounds = array.array('i', [-1, -1, -1, -1]),
    double[:, :] bars = np.array([[0, 1, 1, 0, 0, -1]], np.double),
    double[:, :] fuzz = np.array([[0, 1, 1, 0, 0, 0.5, -2]], np.double),
):
    """
    Performs a basic print after adding back the bars etc. as reference.
    This means the bars and bounds are avoided in the calculation.

    :param dim:         (pointer) arr dimensions
    :param arr:         (2D pointer) array
    :param bounds:      (pointer) boundary values   (-1 is off)
    :param bars:        [start, width, step, axis, bounce, polarity (-1 is off)]
    :param fuzz:        [start, width, step, axis, bounce, coverage, polarity (-2 is off)]
    :return:            None
    """
    cy.set_bounds(bounds, dim, arr)
    cy.scroll_bars(dim, arr, bars)
    scroll_noise(dim, arr, fuzz)

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
cpdef update_array_positions(int[:] position, int buffer_length, int[:, :] buffer_status,
                             int[:, :, :] buf, int display=1):
    """
    Updates the chosen array (switches the memoryview
    to the next one in the buffer) and the buffer status.

    :param position:            (pointer) position of array to update
    :param buffer_length:       (int)
    :param buffer_status:       (2Dpointer) current positions of arrays
    :param buf:                 (3D pointer) buffer
    :param display:             (int) output position?
    :return:                    (pointer) updated array
    """
    cdef int[:, :] arrout
    cdef int index, target, PADDING = 1
    cdef int buf_choice = position[1]

    index = position[0] % buffer_length
    target = (index + 1) % buffer_length
    if not buffer_status[buf_choice, index]:
        if buffer_status[buf_choice - 1, index]:
            buffer_status[buf_choice, target] = buffer_status[buf_choice - 1, index]
            buffer_status[buf_choice - 1, index] = 0
        elif buffer_status[buf_choice + 1, index]:
            buffer_status[buf_choice, target] = buffer_status[buf_choice + 1, index]
            buffer_status[buf_choice + 1, index] = 0
    else:
        buffer_status[buf_choice, target] = buffer_status[buf_choice, index]
        buffer_status[buf_choice, index] = 0

    position[0] += 1
    arrout = buf[position[0] % buffer_length]

    if display:
        print_buffer_status(buffer_status)

    return arrout

cpdef extend_buffer_status(int[:] position, int buffer_length, int[:, :] buffer_status):
    """
    By comparing to the head status, this function will extend the buffer status
    if there appear to be more buffers.

    :param position:
    :param buffer_length:
    :param buffer_status:
    :return: None
    """

    cdef int buf_choice = position[1]
    cdef int[:, :] buffer_status_nu

    if len(buffer_status) < buf_choice + 1:
        buffer_status_nu = np.zeros((len(buffer_status) + 1, buffer_length), np.intc)
        buffer_status_nu[0:-1, :] = buffer_status
        buffer_status = buffer_status_nu
    elif len(buffer_status) > buf_choice + 1:
        buffer_status_nu = np.zeros((len(buffer_status) - 1, buffer_length), np.intc)
        buffer_status_nu[:, :] = buffer_status[1:, :]
        buffer_status = buffer_status_nu

    return buffer_status

cpdef print_buffer_status(int[:, :] buffer_status, int pad=4,
                          str border=r"*", str base=r"#"):
    """
    Outputs the array positions like so:
        ***************
        *  h      t   *
        *  PPPPAAAH   *
        ***************
        where h=head, t=tail
    :param buffer_status:       (2D pointer) current state of buffer
    :param pad:                 (int) width of padding
    :param border:              (str) style of border
    :param base:                (str) style of base
    :return:                    None
    """
    cdef str out
    cdef list lines = ['', '', '', '']
    cdef str buff
    for buf in buffer_status:
        bufp = ''
        for i in buf:
            if i == 0:
                bufp += ' '
            if i == 1:
                bufp += 'h'
            if i == 2:
                bufp += 't'
        lines[0] += '{0}{1}{0}'.format(pad*border, len(buf)*border)
        lines[1] += '{0}{1}{2}{1}{0}'.format(border, ' '*(pad-1), bufp)
        lines[2] += '{0}{1}{2}{1}{0}'.format(border, ' '*(pad-1), len(buf)*base)
        lines[3] += '{0}{1}{0}'.format(pad*border, len(buf)*border)
    out = '\n'.join(lines)

    print(out)

cpdef scroll_instruction_update(double[:, :] bars, int[:] dim):
    """
    Updates the positons of the scrollbar.

    :param bars:        [start, width, step, axis, bounce, [coverage,] polarity]
    :param dim:         (pointer) dimensions of array
    :return:            None
    """
    cdef double[:] bar
    cdef Py_ssize_t i
    for i in range(len(bars)):
        bar = bars[i]
        # If bounce is on
        if bar[4]:
            # If the step is positive
            if bar[2] > 0:
                # If the next step takes it out of bounds
                if bar[0] + bar[1] + bar[2] >= dim[int(bar[3])]:
                    # Turn it around
                    bar[2] = -bar[2]
            # If the step is negative
            else:
                # If the next step takes it out of bounds
                if bar[0] + bar[2] < 0:
                    # Turn it around
                    bar[2] = -bar[2]

        bar[0] = bar[0] + bar[2]


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
    cy.clear_array(dim_nu, buf_nu[pos[0] % length])
    buf_nu[pos[0] % length, offset[0]: offset[0] + dim_old[0] - cut[0] * 2,\
                offset[1]: offset[1] + dim_old[1] - cut[1] * 2] =\
        buf_old[pos[0] % length, cut[0]: dim_old[0] - cut[0],\
                     cut[1]: dim_old[1] - cut[1]]

cpdef change_array(
    int[:] dim_old, int[:, :] arr_old,
    int[:] dim_nu, int[:, :] arr_nu,
    int[:] offset=array.array('i', [1,1]), int[:] cut=array.array('i', [0,0])
):
    """
    Copys the array into a different buffer, resizing and repositioning it as specified.

    :param dim_old:     (pointer) dimensions of old arrfer
    :param arr_old:     (3D pointer) old arrfer
    :param dim_nu:      (pointer) dimensions of new arrfer
    :param arr_nu:      (3D pointer) new arrfer
    :param offset:      (pointer) offset of array in new arrfer
    :param cut:         (pointer) cut off sides of old arrfer
    :return:            None
    """
    cy.clear_array(dim_nu, arr_nu)
    arr_nu[offset[0]: offset[0] + dim_old[0] - cut[0] * 2,\
                offset[1]: offset[1] + dim_old[1] - cut[1] * 2] =\
        arr_old[cut[0]: dim_old[0] - cut[0],\
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


cpdef tuple resize_array(int[:] dim_old, int add=1):
    """
    Creates a new array, larger than the last
    Array may be uninitialized. This is essentially a (safe, easy) malloc.

    :param dim_old:     (pointer) size of the array
    :param add:         amount of space to add at the edges of the new array
    :return:            dim_v, arr_v
    """
    cdef int[:] dim_v = array.array('i', [dim_old[0] + add * 2, dim_old[1] + add * 2])
    cdef int[:, :] arr_v = init_array(dim_v)
    return dim_v, arr_v


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


cpdef void scroll_noise(
    int[:] dim, int[:, :] arr,
    double[:, :] bars = np.array([[0, 5, 1, 0, 0, 0.5, 1]], np.double),
):
    """
    Updates a region of the screen.

    :param dim:
    :param arr:
    :param fuzz:     [start, width, step, axis, bounce, coverage, polarity (-2 is off)]
    :param coverage:    coverage of the line
    :returns:       None
    """

    cdef double[:] bar
    cdef Py_ssize_t i
    for i in range(len(bars)):
        bar = bars[i]
        if bar[-1] == -2: continue

        if bar[3] == 0:
            noise_rows(int(bar[0]), int(bar[1]), dim, arr, int(bar[-1]), bar[5])
        if bar[3] == 1:
            noise_columns(int(bar[0]), int(bar[1]), dim, arr, int(bar[-1]), bar[5])


cpdef void noise_rows(int num, int width, int[:] dim, int[:, :] arr,
                                int pol = 1, float cov = 0.8):
    """
    Fills rows of arr with noise

    :param num:     (int) index of starting row
    :param width:   (int) number of rows to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :param polarity:    polarity of noise (1 additive, 0 normal, -1 subtractive)
    :param coverage:    coverage of the line
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        noise_row((num + i) % dim[0], dim, arr, pol, cov)


cpdef void noise_row(int pos, int[:] dim, int[:, :] arr, int polarity, float coverage):
    cdef int[:] tdim = array.array('i', [1, dim[1]])
    cdef int[:, :] tarr = arr[pos: pos + 1, :]
    add_stochastic_noise(coverage, tdim, tarr, polarity)


cpdef void noise_columns(int num, int width, int[:] dim, int[:, :] arr,
                                int pol = 1, float cov = 0.8):
    """
    Fills columns of arr with noise

    :param num:     (int) index of starting column
    :param width:   (int) number of columns to fill
    :param dim:     (pointer) dimensions of arr
    :param arr:   (2D pointer) arr
    :param polarity:    polarity of noise (1 additive, 0 normal, -1 subtractive)
    :param coverage:    coverage of the line
    :return:        None
    """
    cdef Py_ssize_t i
    for i in range(width):
        noise_column((num + i) % dim[1], dim, arr, pol, cov)


cpdef void noise_column(int pos, int[:] dim, int[:, :] arr, int polarity, float coverage):
    cdef int[:] tdim = array.array('i', [dim[0], 1])
    cdef int[:, :] tarr = arr[:, pos: pos + 1]
    add_stochastic_noise(coverage, tdim, tarr, polarity)

#===============FANTASTIC STOCHASTIC===============
cpdef randomize_center(int siz, int[:] dim, int[:, :] arr, int seed=-1, float threshold=0.2):
    """
    Puts a little random array in the center of the array

    :param size:        (pointer) size of small array
    :param dim:         (pointer) dimensions
    :param arr:         (2D pointer) array
    :param seed:        seed for Srand
    :param threshold:   threshold for randomizer
    :return:            None
    """
    seed = seed if seed is not -1 else np.random.randint(0, 10**9)
    if not siz: return
    cdef int[:] dim_v, offset_v
    cdef int[:, :] arr_v
    dim_v = array.array('i', [siz, siz])
    arr_v = init_array(dim_v)

    add_global_noise_seed(seed, threshold, dim_v, arr_v)

    offset_v = array.array('i', [(dim[0] - dim_v[0])//2, (dim[1] - dim_v[1])//2])
    cy.replace_array(offset_v, dim_v, arr_v, dim, arr)

cpdef add_global_noise_seed(int seed, float threshold, int[:] dim, int[:, :] arr, int polarity=0):
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
    np.random.seed(seed)
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

    :param coverage: (float) update percentage (0-1)
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

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef ising_process(float updates, float beta, int[:] dim, int[:, ::1] arr):
    """
    Performs ising updates on the array.

    :param updates:     (float) ising updates (as percentage of all positions, 0 is off)
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
    cdef int nb
    cdef int[:] pos = array.array('i', [0, 0])
    for _ in range(int(updates * dim[0] * dim[1])):
        pos[0] = rand() % N
        pos[1] = rand() % D
        nb = moore_neighbors_same(pos, dim, arr)
        if nb - 2 <= 0 or (rand() / float(RAND_MAX)) < cost[nb - 2]:
            arr[pos[0], pos[1]] = 1 - arr[pos[0], pos[1]]

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef ising_process_old(float updates, float beta, int[:] dim, int[:, :] arr):
    """
    Performs ising updates on the array.

    :param updates:     (float) ising updates (as percentage of all positions, 0 is off)
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
    for _ in range(int(updates * dim[0] * dim[1])):
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
cpdef void conway_process_old(int[:] rule, int[:] dim, int[:, :] arr):
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
    l = cy.roll_columns(1, dim, arr)
    r = cy.roll_columns(-1, dim, arr)
    u = cy.roll_rows(1, dim, arr)
    d = cy.roll_rows(-1, dim, arr)
    ul = cy.roll_rows(1, dim, l)
    dl = cy.roll_rows(-1, dim, l)
    ur = cy.roll_rows(1, dim, r)
    dr = cy.roll_rows(-1, dim, r)
    cdef int NB, n, dd
    n = dim[0]
    dd = dim[1]
    cdef Py_ssize_t i, j
    for i in range(n):
        for j in range(dd):
            NB = 0
            NB = l[i][j] + r[i][j] + u[i][j] + d[i][j] + ul[i][j] + ur[i][j]\
                + dl[i][j] + dr[i][j]
            if arr[i][j] == 1:
                if not rule[0] <= NB <= rule[1]:
                    arr[i][j] = 0
            else:
                if rule[2] <= NB <= rule[3]:
                    arr[i][j] = 1


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef void conway_process(int[:] rule, int[:] dim, int[:, ::1] arr):
    """
    Performs conway update on the array.

    :param rule:    (pointer) update rule for this frame
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    if rule[0] == -1:
        return
    cdef int NB, n, d
    n = dim[0]
    d = dim[1]
    cdef int[:] pos = array.array('i', [0, 0])
    cdef int[:, ::1] arr_c = arr.copy()
    cdef Py_ssize_t i, j
    for i in range(n):
        for j in range(d):
            pos[0] = i
            pos[1] = j
            NB = neumann_neighbors_sum(pos, dim, arr_c)
            if arr[i][j] == 1:
                if not rule[0] <= NB <= rule[1]:
                    arr[i][j] = 0
            else:
                if rule[2] <= NB <= rule[3]:
                    arr[i][j] = 1

cpdef void stochastic_conway(float coverage, int[:] rule, int[:] dim, int[:, ::1] arr):
    """
    Performs conway updates at random positions in the array.

    :param coverage:(float) percentage of the array to cover
    :param rule:    (pointer) update rule for this frame
    :param dim:     (pointer) dimensions of array
    :param array:   (2D pointer) array
    :return:        None
    """
    if coverage == 0.0:
        return
    cdef int[:, :] vex = np.random.randint(0, dim[0], (int(coverage * dim[0] * dim[1]), 1),
                                           np.intc)
    cdef int[:, :] vey = np.random.randint(0, dim[1], (int(coverage * dim[0] * dim[1]), 1),
                                           np.intc)
    cdef int[:, :] vecs = np.concatenate((vex, vey), axis=1)
    cdef int[:] pos = array.array('i', [0, 0])
    cdef Py_ssize_t i
    cdef int a, b, nb
    for i in range(int(coverage * dim[0] * dim[1])):
        pos = array.array('i', [vecs[i, 0], vecs[i, 1]])
        nb = neumann_neighbors_sum(pos, dim, arr)
        a = vecs[i, 0]
        b = vecs[i, 1]
        if arr[a, b] == 1:
            if not rule[0] <= nb <= rule[1]:
                arr[a, b] = 0
        else:
            if rule[2] <= nb <= rule[3]:
                arr[a, b] = 1

#=====NEIGHBOR CALCULATIONS===========
@cython.boundscheck(False)
@cython.wraparound(False)
cdef int moore_neighbors_same(int[:] pos, int[:] dim, int[:, ::1] arr):
    """
    Calculates the number of Moore neighbors that share state with the position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int a = pos[0]
    cdef int b = pos[1]
    if arr[a, b]:
        return moore_neighbors_sum(pos, dim, arr)
    else:
        return 4 - moore_neighbors_sum(pos, dim, arr)

cpdef int moore_neighbors_same_CP(int[:] pos, int[:] dim, int[:, ::1] arr):
    return moore_neighbors_same(pos, dim, arr)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef int moore_neighbors_sum(int[:] pos, int[:] dim, int[:, ::1] arr):
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
        r = arr[(a - 1 + N) % N][b]
        u = arr[a][(b + 1) % D]
        d = arr[a][(b - 1 + D) % D]
        nb = l + u + d + r
    else:
        l = arr[(a + 1)][b]
        r = arr[(a - 1)][b]
        u = arr[a][(b + 1)]
        d = arr[a][(b - 1)]
        nb = l + u + d + r
    return nb

cpdef int moore_neighbors_sum_CP(int[:] pos, int[:] dim, int[:, ::1] arr):
    return moore_neighbors_sum(pos, dim, arr)

cpdef int[:, :] moore_neighbors_array(int[:] dim, int[:, ::1] arr):
    cdef int[:] pos = array.array('i', [0, 0])
    cdef int[:, :] nb = np.empty_like(arr)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            pos[0] = i
            pos[1] = j
            nb[i, j] = moore_neighbors_sum(pos, dim, arr)
    return nb

cpdef int neumann_neighbors_same(int[:] pos, int[:] dim, int[:, ::1] arr):
    """
    Calculates the number of Neumann neighbors that share state with the position.

    :param pos:         position to be checked
    :param dim:         dimensions of array
    :param arr:         array
    :return:            neighbors
    """
    cdef int a = pos[0]
    cdef int b = pos[1]
    if arr[a, b]:
        return neumann_neighbors_sum(pos, dim, arr)
    else:
        return 8 - neumann_neighbors_sum(pos, dim, arr)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef int neumann_neighbors_sum(int[:] pos, int[:] dim, int[:, ::1] arr) nogil:
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
        r = arr[(a - 1 + N) % N][b]
        ul = arr[(a + 1) % N][(b + 1) % D]
        ur = arr[(a - 1 + N) % N][(b + 1) % D]
        dl = arr[(a + 1) % N][(b - 1 + D) % D]
        dr = arr[(a - 1 + N) % N][(b - 1 + D) % D]
        u = arr[a][(b + 1) % D]
        d = arr[a][(b - 1 + D) % D]
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

cpdef int neumann_neighbors_sum_CP(int[:] pos, int[:] dim, int[:, ::1] arr):
    return neumann_neighbors_sum(pos, dim, arr)

cpdef int[:, :] neumann_neighbors_array(int[:] dim, int[:, ::1] arr):
    cdef int[:] pos = array.array('i', [0, 0])
    cdef int[:, :] nb = np.empty_like(arr)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            pos[0] = i
            pos[1] = j
            nb[i, j] = neumann_neighbors_sum(pos, dim, arr)
    return nb

#=============================OLDFUNCS for testing
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cpdef int moore_neighbors_same_complex(int[:] pos, int[:] dim, int[:, ::1] arr):
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
        r = int(arr[a][b] == arr[(a - 1 + N) % N][b])
        u = int(arr[a][b] == arr[a][(b + 1) % D])
        d = int(arr[a][b] == arr[a][(b - 1 + D) % D])
        nb = l + u + d + r
    else:
        l = int(arr[a][b] == arr[(a + 1)][b])
        r = int(arr[a][b] == arr[(a - 1)][b])
        u = int(arr[a][b] == arr[a][(b + 1)])
        d = int(arr[a][b] == arr[a][(b - 1)])
        nb = l + u + d + r
    return nb


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cpdef int neumann_neighbors_same_complex(int[:] pos, int[:] dim, int[:, ::1] arr):
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
        r = int(arr[a][b] == arr[(a - 1 + N) % N][b])
        ul = int(arr[a][b] == arr[(a + 1) % N][(b + 1) % D])
        ur = int(arr[a][b] == arr[(a - 1 + N) % N][(b + 1) % D])
        dl = int(arr[a][b] == arr[(a + 1) % N][(b - 1 + D) % D])
        dr = int(arr[a][b] == arr[(a - 1 + N) % N][(b - 1 + D) % D])
        u = int(arr[a][b] == arr[a][(b + 1) % D])
        d = int(arr[a][b] == arr[a][(b - 1 + D) % D])
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
