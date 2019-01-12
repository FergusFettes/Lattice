#!/usr/bin/env python
# -*- coding: utf-8 -*-

import array
import cython
from cpython cimport array
import numpy as np
cimport numpy as np

#DTYPE = np.int

#ctypedef np.int_t DTYPE_t

class pureHandlerC():

    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(array=np.ndarray[np.bool, 2])
    def process(self, job, array):
        if not array.shape == tuple(job['dim']):
            array = self.resize_array(job['dim'])
        if job['clear']:
            array = self.resize_array(array.shape)
        if job['wolfpole'] >= 0:
            array = self.clear_wavefront(job['wolfpos'], job['wolfscale'],
                                    job['wolfpole'], array)
        for i in range(job['noisesteps']):
            array = self.noise_process(job['threshold'], array)
        array = self.set_boundary(job['ub'], job['rb'],
                             job['db'], job['lb'], array)
        if job['isingupdates'] > 0:
            array = self.ising_process(job['isingupdates'],
                                  job['beta'], array)
        if not job['conwayrules'] == []:
            array = self.conway_process(job['conwayrules'], array)
        return array

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(ub=cython.int, rb=cython.int, db=cython.int, lb=cython.int,
                    array=np.ndarray[np.bool, 2])
    def set_boundary(self, ub, rb, db, lb, array):
        if ub >= 0:
            array[..., 0] = ub
        if db >= 0:
            array[..., -1] = db
        if lb >= 0:
            array[0, ...] = lb
        if rb >= 0:
            array[-1, ...] = rb
        return array

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(start=cython.int, scale=cython.int, polarity=cython.int,
                   array=np.ndarray[np.bool, 2])
    def clear_wavefront(self, start, scale, polarity, array):
        n = array.shape[0]
        for i in range(scale):
            array[(start + i) % n, ...] = polarity
        return array

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(dim=cython.array[2])
    def resize_array(self, dim):
        array = np.zeros(dim, bool)
        return array

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(threshold=cython.float, array=np.ndarry)
    def noise_process(self, threshold, array):
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

    @cython.cfunc
    @cython.returns(np.ndarray[np.bool, 2])
    @cython.locals(rule=cython.array[4], array=np.ndarray[np.bool, 2])
    def conway_process(self, rule, array):
        A = array
        l = np.roll(A, -1, axis=0)
        r = np.roll(A, 1, axis=0)
        u = np.roll(A, 1, axis=1)
        d = np.roll(A, -1, axis=1)
        ul = np.roll(l, 1, axis=1)
        dl = np.roll(l, -1, axis=1)
        ur = np.roll(r, 1, axis=1)
        dr = np.roll(r, -1, axis=1)
        NB = np.zeros(A.shape) + l + r + u + d + ul + dl + ur + dr
        # cells still alive after rule 1
        rule1 = np.bitwise_and(A, NB >= rule[0])
        # alive cells that will live
        rule2 = np.bitwise_and(rule1, NB <= rule[1])
        # dead cells that rebirth
        rule4 = np.bitwise_and(~A, NB >= rule[2])
        rule5 = np.bitwise_and(rule4, NB <= rule[3])
        # should just be the live cells
        array = rule2 + rule5
        return array
