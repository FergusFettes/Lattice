import numpy as np
cimport numpy as np

def ising_update_betaC(A, UPDATES, BETA):
    cost = np.zeros(3, float)
    cost[1] = np.exp(-4 * BETA)
    cost[2] = cost[1] * cost[1]
    N = A.shape[0]

    for _ in range(UPDATES):
        a = np.random.randint(N)
        b = np.random.randint(N)
        nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                        A[a][b] == A[(a - 1) % N][b],
                        A[a][b] == A[a][(b + 1) % N],
                        A[a][b] == A[a][(b - 1) % N],
                        -2])
        if nb <= 0 or np.random.random() < cost[nb]:
            A[a][b] = not A[a][b]
    return A


def ising_update_cost(A, UPDATES, COST):
    N = A.shape[0]

    for _ in range(UPDATES):
        a = np.random.randint(N)
        b = np.random.randint(N)
        nb = np.sum([A[a][b] == A[(a + 1) % N][b],
                        A[a][b] == A[(a - 1) % N][b],
                        A[a][b] == A[a][(b + 1) % N],
                        A[a][b] == A[a][(b - 1) % N],
                        -2])
        if nb <= 0 or np.random.random() < COST[nb]:
            A[a][b] = not A[a][b]
    return A
