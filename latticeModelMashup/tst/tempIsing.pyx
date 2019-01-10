%%cython
import array
import numpy as np
import cython
from cpython cimport array
cimport numpy as np

cdef resize_array(int[:] dim):
    return np.zeros(dim, np.intc)

cdef noise_process(int[:] dim, float threshold, int[:, :] array):


dim = array.array('i', [5,5])
cdef int[:] dim_v = dim

arr = resize_array(dim_v)

narr = np.random.randint(0, 2, dim, np.intc)
cdef int[:, :] narr_v = narr

cdef ising_process(self, int updates, float beta, int[:] dim, int[:, :] array):
    cost = np.zeros(3, np.single)
    cdef float[:] cost_v = cost
    cost_v[1] = np.exp(-4 * beta)
    cost_v[2] = cost[1] ** 2
    N = dim[0]
    D = dim[1]

    cdef Py_ssize_t _
    cdef int a, b, nb
    for _ in range(updates):
        a = np.random.randint(N, np.intc)
        b = np.random.randint(D, np.intc)
        nb = np.sum([array[a][b] == array[(a + 1) % N][b],
                    array[a][b] == array[(a - 1) % N][b],
                    array[a][b] == array[a][(b + 1) % D],
                    array[a][b] == array[a][(b - 1) % D],
                    -2])
        if nb <= 0 or np.random.random() < cost[nb]:
            array[a][b] = not array[a][b]
    return array

print(arr)
print(narr)
