# cython: profile = True
import cython

import array
import numpy as np

from cpython cimport array
cimport numpy as np


cpdef inline float norm(int a, int b):
    return (a*a + b*b)**0.5

cpdef float[:] center_of_mass(int[:] dim, int[:, :] arr):
    """
    Should return the mean i and mean j of the entire array.

    :param dim:
    :param arr:
    :return:        center of mass vector
    """
    cdef int vtot = 0, vsum = 0, htot = 0, hsum = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                htot += 1
                hsum += i
                vtot += 1
                vsum += j
    if htot == 0: return None
    cdef float hm = hsum / htot
    cdef float vm = vsum / vtot
    cdef float[:] com = array.array('f', [hm, vm])
    return com

cpdef tuple center_of_mass_pop(int[:] dim, int[:, :] arr):
    """
    Should return the mean i and mean j of the entire array.
    And the population.

    :param dim:
    :param arr:
    :return:        com, pop
    """

    cdef int vtot = 0, vsum = 0, htot = 0, hsum = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                htot += 1
                hsum += i
                vtot += 1
                vsum += j
    if htot == 0: return None
    cdef float hm = hsum / htot
    cdef float vm = vsum / vtot
    cdef float[:] com = array.array('f', [hm, vm])
    return com, vtot

cpdef tuple center_of_mass_pop_living(int[:] dim, int[:, :] arr):
    """
    Should return the mean i and mean j of the entire array.
    And the population, and a vector containing the living positions.

    :param dim:
    :param arr:
    :return:        com, pop, living
    """
    cdef int vtot = 0, vsum = 0, htot = 0, hsum = 0
    living = np.zeros((0,2), np.intc)
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                living.append([i,j])
                htot += 1
                hsum += i
                vtot += 1
                vsum += j
    if htot == 0: return None
    cdef float hm = hsum / htot
    cdef float vm = vsum / vtot
    cdef float[:] com = array.array('f', [hm, vm])
    return com, vtot, living

cpdef int population(int[:] dim, int[:, :] arr):
    """
    And the population.

    :param dim:
    :param arr:
    :return:        pop
    """
    cdef int tot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                tot += 1
    return tot

cpdef double radius_of_gyration(float[:] com, int[:] dim, int[:, :] arr):
    """
    Calculates the radius of gyration of the array.

    :param com:         center of mass
    :param dim:
    :param arr:
    :return:        Rg
    """
    cdef int rtot = 0
    cdef float Rg = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                Rg += (i - com[0])**2 + (j - com[1])**2
                rtot += 1
    if rtot == 0: return None
    Rg /= rtot
    return Rg**0.5
