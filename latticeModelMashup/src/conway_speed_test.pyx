#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from cpython cimport array
cimport numpy as np


def set_boundary_original(ub, rb, db, lb, array):
    if ub >= 0:
        array[..., 0] = ub
    if db >= 0:
        array[..., -1] = db
    if lb >= 0:
        array[0, ...] = lb
    if rb >= 0:
        array[-1, ...] = rb
    return array

cpdef set_boundary_cdef(int ub, int rb, int db, int lb, int[:, :] array):
    if ub >= 0:
        array[..., 0] = ub
    if db >= 0:
        array[..., -1] = db
    if lb >= 0:
        array[0, ...] = lb
    if rb >= 0:
        array[-1, ...] = rb
    return array

cpdef set_boundary_cdef_loop(int ub, int rb, int db, int lb, int[:] dim, int[:, :] array):
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
            array[dim[0] - 1][i] = rb
