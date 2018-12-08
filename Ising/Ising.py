# Let's begin: basic Ising model setup!
import numpy as np
import random as ra

def Init(allUp, N):
    ARR = np.ones((N, N), int)
    if allUp:
        return ARR
    for i in range(1, N):
        for j in range(1, N):
            if ra.random() > 0.5:
                ARR[i,ii] = -1
    return ARR

def MonteCarloUpdate(A, nSteps):
    for _ in range(nSteps):
        a = ra.random() * N
        b = ra.random() * N
        nb = A[a][b] * ( A[(a + 1)%N][b] + A[(a - 1)%N][b] + A[a][(b + 1)%N] + A[a][(b - 1)%N]
        if nb <= 0 or ra.random() < cost[int(nb/4)]:
            A[a][b]=-A[a][b]
    return A

beta = 0.2
cost = np.zeros(3)
cost[1] = np.exp(-4*beta)
cost[2] = cost[1]*cost[1]
N=10
IsingArray = Init(0, N)
