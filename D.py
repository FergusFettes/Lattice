import numpy as np

def new(X, threshold):
    A = np.random.random([X,X]) > threshold
    return A

def update(A):
    #not sure if these are the right neighbor cells
    #could experiment with the axes
    l = np.roll(A,-1,axis=0)
    r = np.roll(A,1,axis=0)
    u = np.roll(A,1,axis=1)
    d = np.roll(A,-1,axis=1)
    ul = np.roll(l,1,axis=1)
    dl = np.roll(l,-1,axis=1)
    ur = np.roll(r,1,axis=1)
    dr = np.roll(r,-1,axis=1)
    NB = np.zeros(A.shape) + l + r + u + d + ul + dl + ur + dr
    #cells still alive after rule 1
    rule1 = np.bitwise_and(A,NB>1)
    #alive cells that will live
    rule2 = np.bitwise_and(rule1,NB<4)
    #dead cells that rebirth
    rule4 = np.bitwise_and(~A,NB==3)
    #should just be the live cells
    C=rule2 + rule4
    #np.argwhere should be a list of all the cells that have chang
    return C,np.argwhere(C != A)

A = new(10,0.5)

for i in range(5):
    A,g = update(A)
    print(1*A)
    print(g)
