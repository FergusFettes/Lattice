#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np

cpdef test_process(int updates, float beta, float threshold, int[:] rule_v, int[:] dim_v):
    cdef np.ndarray arr = resize_array(dim_v)
    cdef int[:, :] arr_v = arr
    noise_process(threshold, dim_v, arr_v)
    ising_process(updates, beta, dim_v, arr_v)
    set_boundary(1, 1, 1, 1, dim_v, arr_v)
    conway_process(rule_v, dim_v, arr_v)

cpdef resize_array(int[:] dim):
    return np.zeros(dim, np.intc)

#@cython.boundscheck(False)
#@cython.wraparound(False)
cpdef noise_process(float threshold, int[:] dim, int[:, :] array):
    cdef int[:, :] narr = np.random.randint(0, 2, dim, np.intc)
    cdef Py_ssize_t x, y
    for x in range(dim[0]):
        for y in range(dim[1]):
            array[x][y] = array[x][y] ^ narr[x][y]

cpdef ising_process(int updates, float beta, int[:] dim, int[:, :] array):
    cdef float[:] cost = np.zeros(3, np.float32)
    cost[1] = np.exp(-4 * beta)
    cost[2] = cost[1] ** 2
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

cpdef conway_process(int[:] rule, int[:] dim, int[:, :] array):
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

#NB: this is 5x slower than the numpy version :( but i want to be sure my arrays are all pointers
cpdef set_boundary(int ub, int rb, int db, int lb, int[:] dim, int[:, :] array):
    if ub >= 0:
        for i in range(dim[0]):
            array[i][0] = ub
    if db >= 0:
        for i in range(dim[0]):
            array[i][dim[1] - 1] = db
    if lb >= 0:
        for i in range(dim[1]):
            array[0][i] = lb
    if rb >= 0:
        for i in range(dim[1]):
            array[dim[0]][i] = rb
