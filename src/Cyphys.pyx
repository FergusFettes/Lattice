# cython: profile = True
import cython

import array
import numpy as np

from cpython cimport array
cimport numpy as np

import src.Cfuncs as cf
import src.Cyarr as cy

cpdef tuple analysis_loop_energy(float[:] com_in, int[:] dim, int[:, :] arr):
    """
    One loop to do all the analysis. This means the array is only summed over once,
    making the calculation much quicker (I think..)

    NB: this can be (and probably will be) set up to take the previous rounds center
    of mass as the input for the radius of gyration calculations. This is slightly
    innacurate and populations that vary wildly could see some systematic errors
    because of this. #TODO: Maybe look into it, or if there is enough CPU power to spare (LOL)
    do it properly.

    :param com_in:   center of mass
    :param dim:
    :param arr:
    :return:
        tot         population
        living      positions of all living cells
        com         centre_of_mass
        Rg          radius_of_gyration
        e           'energy' (neighbor interactions)
        e2          energy squared
        M           polarization
    """
    cdef int[:, :] l, r, u, d
    l = cy.roll_columns(1, dim, arr)
    r = cy.roll_columns(-1, dim, arr)
    u = cy.roll_rows(1, dim, arr)
    d = cy.roll_rows(-1, dim, arr)
    cdef int tot_positions = dim[0] * dim[1]
    cdef int[:, :] living = np.zeros((dim[0] * dim[1],2), np.intc)
    cdef float Rg
    cdef int vsum = 0, tot = 0, hsum = 0, etot = 0, e2tot = 0, Mtot = 0, nb
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            nb = 0
            nb = l[i][j] + r[i][j] + u[i][j] + d[i][j]
            if not arr[i, j]: nb = 4 - nb
            etot -= 2 * nb
            e2tot += (2 * nb) * (2 * nb)
            if arr[i, j]:
                Rg += (i - com_in[0])**2 + (j - com_in[1])**2
                living[tot, 0] = i
                living[tot, 1] = j
                hsum += i
                vsum += j
                tot += 1
    if tot == 0: return None
    cdef float e, e2, hm, vm, M
    e = float(etot) / float(tot_positions)
    e2 = float(e2tot) / float(tot_positions)
    hm = float(hsum) / float(tot)
    vm = float(vsum) / float(tot)
    cdef float[:] com = array.array('f', [hm, vm])
    Rg /= float(tot)

    Mtot = abs((2 * tot) - tot_positions)
    M = float(Mtot) / float(tot_positions)
    return tot, living[: tot], com, Rg**0.5, e, e2, M

cpdef tuple analysis_loop(float[:] com_in, int[:] dim, int[:, :] arr):
    """
    One loop to do all the analysis. This means the array is only summed over once,
    making the calculation much quicker (I think..)

    NB: this can be (and probably will be) set up to take the previous rounds center
    of mass as the input for the radius of gyration calculations. This is slightly
    innacurate and populations that vary wildly could see some systematic errors
    because of this. #TODO: Maybe look into it, or if there is enough CPU power to spare (LOL)
    do it properly.O

    :param com_in:   center of mass
    :param dim:
    :param arr:
    :return:
        tot         population
        living      positions of all living cells
        com         centre_of_mass
        Rg          radius_of_gyration
    """
    cdef int tot_positions = dim[0] * dim[1]
    cdef int[:, :] living = np.zeros((dim[0] * dim[1],2), np.intc)
    cdef float Rg
    cdef int vsum = 0, tot = 0, hsum = 0, etot = 0, e2tot = 0, Mtot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                Rg += (i - com_in[0])**2 + (j - com_in[1])**2
                living[tot, 0] = i
                living[tot, 1] = j
                hsum += i
                vsum += j
                tot += 1
    if tot == 0: return None
    cdef float hm, vm
    hm = float(hsum) / float(tot)
    vm = float(vsum) / float(tot)
    cdef float[:] com = array.array('f', [hm, vm])
    Rg /= float(tot)

    Mtot = abs((2 * tot) - tot_positions)
    M = float(Mtot) / float(tot_positions)
    return tot, living[: tot], com, Rg**0.5, M

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
    cdef float hm = float(hsum) / float(htot)
    cdef float vm = float(vsum) / float(vtot)
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
    cdef float hm = float(hsum) / float(htot)
    cdef float vm = float(vsum) / float(vtot)
    cdef float[:] com = array.array('f', [hm, vm])
    return com, vtot

cpdef int[:, :] living(int[:] dim, int[:, :] arr):
    """
    Returns the list of living cells

    :param dim:
    :param arr:
    :return:        pop
    """
    cdef int[:, :] living = np.zeros((dim[0] * dim[1],2), np.intc)
    cdef int count = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                living[count, 0] = i
                living[count, 1] = j
                count += 1
    return living[: count]

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
    if rtot == 0: return 0.0
    Rg /= float(rtot)
    return Rg**0.5

cpdef tuple neighbor_interaction(int[:] dim, int[:, :] arr):
    """
    Calculates the neighbor interaction as in the ising model,
    so 2*(sameness of neighbors).

    :param dim:
    :param arr:
    :return:
    """
    cdef int[:, :] l, r, u, d
    l = cy.roll_columns(1, dim, arr)
    r = cy.roll_columns(-1, dim, arr)
    u = cy.roll_rows(1, dim, arr)
    d = cy.roll_rows(-1, dim, arr)
    cdef int tot_positions = dim[0] * dim[1]
    cdef int etot = 0, e2tot = 0, nb
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            nb = 0
            nb = l[i][j] + r[i][j] + u[i][j] + d[i][j]
            if not arr[i, j]: nb = 4 - nb
            etot -= 2 * nb
            e2tot += (2 * nb) * (2 * nb)

    E = float(etot) / float(tot_positions)
    E2 = float(e2tot) / float(tot_positions)
    return E, E2

cpdef tuple neighbor_interaction_moore(int[:] dim, int[:, :] arr):
    """
    Calculates the neighbor interaction as in the ising model,
    so 2*(sameness of neighbors).

    :param dim:
    :param arr:
    :return:
    """
    cdef int tot_positions = dim[0] * dim[1]
    cdef int etot = 0, e2tot = 0, nb
    cdef int[:] pos = array.array('i', [0, 0])
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            pos[0] = i
            pos[1] = j
            nb = cf.moore_neighbors_same_CP(pos, dim, arr)
            etot -= 2 * nb
            e2tot += (2 * nb) * (2 * nb)

    E = float(etot) / float(tot_positions)
    E2 = float(e2tot) / float(tot_positions)
    return E, E2

cpdef float polarization(int[:] dim, int[:, :] arr):
    cdef int tot_positions = dim[0] * dim[1]
    cdef int Mtot = 0, nb, tot = 0
    cdef Py_ssize_t i, j
    for i in range(dim[0]):
        for j in range(dim[1]):
            if arr[i, j]:
                tot += 1

    Mtot = abs((2 * tot) - tot_positions)
    M = float(Mtot) / float(tot_positions)
    return M

cpdef inline float norm(float a, float b):
    """
    Returns the norm of the integers
    Faster than anything in python for single digits by OOM
    :param a:
    :param b:
    :return:    norm(a, b)
    """
    return (a*a + b*b)**0.5
