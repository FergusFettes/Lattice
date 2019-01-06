import numpy as np
cimport numpy as np
import cython

DTYPE = np.int

ctypedef np.int_t DTYPE_t

class pureHandlerC():

    @cython.returns(np.ndarray)
    @cython.locals(array=np.ndarray, dim=list)
    def process(self, job, array, dim):
        if not job['conwayrules'] == []:
            array = self.conway_process(job['conwayrules'], array, dim)
        return array

    @cython.returns(np.ndarray)
    @cython.locals(rule=list, A=np.ndarray, dim=list)
    def conway_process(self, rule, A, dim):
        cdef np.ndarray l = np.roll(A, -1, axis=0)
        cdef np.ndarray r = np.roll(A, 1, axis=0)
        cdef np.ndarray u = np.roll(A, 1, axis=1)
        cdef np.ndarray d = np.roll(A, -1, axis=1)
        cdef np.ndarray ul = np.roll(l, 1, axis=1)
        cdef np.ndarray dl = np.roll(l, -1, axis=1)
        cdef np.ndarray ur = np.roll(r, 1, axis=1)
        cdef np.ndarray dr = np.roll(r, -1, axis=1)
        cdef np.ndarray NB = np.zeros(dim) + l + r + u + d + ul + dl + ur + dr
        # cells still alive after rule 1
        cdef np.ndarray rule1 = np.bitwise_and(A, NB >= rule[0])
        # alive cells that will live
        cdef np.ndarray rule2 = np.bitwise_and(rule1, NB <= rule[1])
        # dead cells that rebirth
        cdef np.ndarray rule4 = np.bitwise_and(~A, NB >= rule[2])
        cdef np.ndarray rule5 = np.bitwise_and(rule4, NB <= rule[3])
        # should just be the live cells
        return rule2 + rule5
