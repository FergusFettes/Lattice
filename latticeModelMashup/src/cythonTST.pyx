#!/usr/bin/env python
# -*- coding: utf-8 -*-

import array
import cython
from cpython cimport array
import numpy as np
cimport numpy as np

#DTYPE = np.int

#ctypedef np.int_t DTYPE_t

cdef class CFuncs():

    cdef array.array square(self, array.array arr):
        cdef int[:] arr_view = arr
        cdef int idx
        for idx, i in enumerate(arr_view):
            arr_view[idx] = i**2
        return arr


cdef class pureHandlerC():

    cdef resize_array(self, array.array dim):
        cdef np.array arr = np.zeros(dim, bool)
        return arr

    cdef noise_process(self, float threshold, int[:, :] array):
        A = np.random.random(array.shape) > threshold
        B = np.bitwise_xor(array, A)
        array = B
        return array

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(updates=cython.int, beta=cython.float, array=np.ndarry)
    def ising_process(self, updates, beta, array):
        cost = np.zeros(3, float)
        cost[1] = np.exp(-4 * beta)
        cost[2] = cost[1] ** 2
        A = array
        N = A.shape[0]
        D = A.shape[1]
        for _ in range(updates):
            a = np.random.randint(N)
            b = np.random.randint(D)
            nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                        A[a][b] == A[(a - 1) % N][b],
                        A[a][b] == A[a][(b + 1) % D],
                        A[a][b] == A[a][(b - 1) % D],
                        -2])
            if nb <= 0 or np.random.random() < cost[nb]:
                A[a][b] = not A[a][b]
        array = A
        return array
