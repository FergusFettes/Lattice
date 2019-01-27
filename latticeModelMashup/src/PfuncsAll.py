import numpy as np
from numpy.core.umath_tests import inner1d

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

##================Analysis=========================##
##=================================================##
def export(self):
    self.truncate()
    return self.center, self.population, self.radius

def truncate(self):
    if not self.population[0]:
        return
    last = np.nonzero(self.population)[0][-1]
    self.center = self.center[0:last + 1]
    self.population = self.population[0:last + 1]
    self.radius = self.radius[0:last + 1]

def clear(self):
    # Its faster to initialse the array, but the length is arbitrary, so change this
    # to suit whatever turns out to be appropriate.
    run_length = 2000
    self.count = 0

    self.center = np.zeros([run_length, 2], float)
    self.population = np.zeros(run_length, int)
    self.radius = np.zeros(run_length, float)

    self.count += 1

def analyse(self, array):
    positions = self.living(array)
    population = positions.shape[0]
    self.population[self.count] = population
    center = self.center_of_mass(positions, population)
    self.center[self.count] = center
    radius = self.radius_of_gyration(center, positions, population)
    self.radius[self.count] = radius
    self.count += 1

def center_of_mass(self, positions, population):
    if not population:
        return 0
    return np.sum(positions, axis=0) / population

def radius_of_gyration(self, center, positions, population):
    if not population:
        return 0
    rel = positions - center
    square_distance = inner1d(rel, rel)
    return np.sqrt(np.sum(square_distance, axis=0) / population)

def living(self, array):
    return np.argwhere(array)

def change(self, array):
    if not self.arrayold.shape == array.shape:
        self.save_array(array)
    common = np.bitwise_and(array, self.arrayold)
    onlyOld = np.bitwise_xor(common, self.arrayold)
    onlyNew = np.bitwise_xor(common, array)
    births = np.argwhere(onlyNew)
    deaths = np.argwhere(onlyOld)
    b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
    d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
    return np.concatenate((b, d))
