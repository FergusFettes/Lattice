from libc.stdlib cimport rand
import array
import numpy as np
import random as ra
import cython
from cpython cimport array
cimport numpy as np

cpdef resize_array(int[:] dim):
    return np.zeros(dim, np.intc)

def noise_original(threshold, dim, array):
    np.random.seed(0)
    narr = np.random.randint(0, 2, dim, np.intc)
    return np.bitwise_xor(array, narr)

cpdef noise_numpy(float threshold, int[:] dim, int[:, :] array):
    np.random.seed(0)
    narr = np.random.randint(0, 2, dim, np.intc)
    return np.bitwise_xor(array, narr)

cpdef noise_loop(float threshold, int[:] dim, int[:, :] array):
    np.random.seed(0)
    narr = np.random.randint(0, 2, dim, np.intc)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ narr[x][y]

cpdef noise_loop_point(float threshold, int[:] dim, int[:, :] array):
    np.random.seed(0)
    cdef int[:, :] narr = np.random.randint(0, 2, dim, np.intc)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ narr[x][y]

cpdef noise_loop_point_crand(float threshold, int[:] dim, int[:, :] array):
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ (rand() % 2)

cpdef noise_loop_point_numprand(float threshold, int[:] dim, int[:, :] array):
    np.random.seed(0)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ np.random.randint(0, 2)

cpdef noise_loop_point_pyrand(float threshold, int[:] dim, int[:, :] array):
    ra.seed(0)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ ra.randint(0, 1)

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef noise_loop_point_nobound(float threshold, int[:] dim, int[:, :] array):
    np.random.seed(0)
    cdef int[:, :] narr = np.random.randint(0, 2, dim, np.intc)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ narr[x][y]

#   dim = array.array('i', [5,5])
#   cdef int[:] dim_v = dim

#   arr = resize_array(dim_v)
#   print(arr)
#   cdef int[:, :] arr_v = arr
#   out1 = noise_numpy(0.5, dim_v, arr_v)
#   noise_loop(0.5, dim_v, arr_v)

#   print(out1)
#   print(arr)
