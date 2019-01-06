import numpy as np


class pureUps():
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

    def clear_wavefront(self, start, scale, polarity, array):
        n = array.shape[0]
        for i in range(scale):
            array[(start + i) % n, ...] = polarity
        return array

    def resize_array(self, dim):
        array = np.zeros(dim, bool)
        return array

    def noise_process(self, threshold, array):
        A = np.random.random(array.shape) > threshold
        B = np.bitwise_xor(array, A)
        array = B
        return array

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

    def conway_process(self, rule, A):
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
        return rule2 + rule5
