#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

cpdef resize_array(int[:] dim):
    return np.zeros(dim, np.intc)

cpdef cost_update(float beta):
    cdef float[:] cost = np.zeros(3, np.float32)
    cost[1] = np.exp(-4 * beta)
    cost[2] = cost[1] ** 2
    return cost

def ising_original(updates, beta, array):
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

cpdef ising_cdef(int updates, float beta, int[:] dim, int[:, :] array):
    cdef float[:] cost = np.zeros(3, np.float32)
    cost[1] = np.exp(-4 * beta)
    cost[2] = cost[1] ** 2
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, nb
    for _ in range(updates):
        a = np.random.randint(N)
        b = np.random.randint(D)
        nb = np.sum([array[a][b] == array[(a + 1) % N][b],
                    array[a][b] == array[(a - 1) % N][b],
                    array[a][b] == array[a][(b + 1) % D],
                    array[a][b] == array[a][(b - 1) % D],
                    -2])
        if nb <= 0 or np.random.random() < cost[nb]:
            array[a][b] = not array[a][b]

cpdef ising_cdef_nocost(int updates, float[:] cost, int[:] dim, int[:, :] array):
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, nb
    for _ in range(updates):
        a = np.random.randint(N)
        b = np.random.randint(D)
        nb = np.sum([array[a][b] == array[(a + 1) % N][b],
                    array[a][b] == array[(a - 1) % N][b],
                    array[a][b] == array[a][(b + 1) % D],
                    array[a][b] == array[a][(b - 1) % D],
                    -2])
        if nb <= 0 or np.random.random() < cost[nb]:
            array[a][b] = not array[a][b]

cpdef ising_cdef_nocost_nosum(int updates, float[:] cost, int[:] dim, int[:, :] array):
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, l, r, u, d, nb
    for _ in range(updates):
        a = np.random.randint(N)
        b = np.random.randint(D)
        l = int(array[a][b] == array[(a + 1) % N][b])
        r = int(array[a][b] == array[(a - 1) % N][b])
        u = int(array[a][b] == array[a][(b + 1) % D])
        d = int(array[a][b] == array[a][(b - 1) % D])
        nb = l + u + d + r - 2
        if nb <= 0 or np.random.random() < cost[nb]:
            array[a][b] = not array[a][b]

cpdef ising_cdef_nocost_nosum_crand(int updates, float[:] cost, int[:] dim, int[:, :] array):
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, l, r, u, d, nb
    for _ in range(updates):
        a = rand() % N
        b = rand() % D
        l = int(array[a][b] == array[(a + 1) % N][b])
        r = int(array[a][b] == array[(a - 1) % N][b])
        u = int(array[a][b] == array[a][(b + 1) % D])
        d = int(array[a][b] == array[a][(b - 1) % D])
        nb = l + u + d + r - 2
        if nb <= 0 or (rand() / RAND_MAX) < cost[nb]:
            array[a][b] = not array[a][b]

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef ising_cdef_nocost_nosum_crand_nowrap(int updates, float[:] cost, int[:] dim, int[:, :] array):
    N = dim[0]
    D = dim[1]
    cdef Py_ssize_t _
    cdef int a, b, l, r, u, d, nb
    for _ in range(updates):
        a = (rand() % (N - 2)) + 1
        b = (rand() % (D - 2)) + 1
        l = int(array[a][b] == array[(a + 1)][b])
        r = int(array[a][b] == array[(a - 1)][b])
        u = int(array[a][b] == array[a][(b + 1)])
        d = int(array[a][b] == array[a][(b - 1)])
        nb = l + u + d + r - 2
        if nb <= 0 or (rand() / RAND_MAX) < cost[nb]:
            array[a][b] = not array[a][b]
