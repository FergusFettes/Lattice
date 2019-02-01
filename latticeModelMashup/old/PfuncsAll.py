import numpy as np
from numpy.core.umath_tests import inner1d

def axial_diameter(positions):
    width = max(positions[0,:]) - min(positions[0,:])
    height = max(positions[1,:]) - min(positions[1,:])
    return max(width, height), min(width, height)

def center_of_mass(positions, population):
    if not population:
        return 0
    return np.sum(positions, axis=0) / population

def radius_of_gyration(center, positions, population):
    if not population:
        return 0
    rel = positions - center
    square_distance = inner1d(rel, rel)
    return np.sqrt(np.sum(square_distance, axis=0) / population)

def clear_columns_P(num, width, array):
    for i in range(width):
        array = clear_column((num + i) % array.shape[1], array)
    return array

def fill_columns_P(num, width, array):
    for i in range(width):
        array = fill_column((num + i) % array.shape[1], array)
    return array

def replace_columns_P(num, width, nucol, array):
    for i in range(width):
        array = replace_column((num + i) % array.shape[1], nucol, array)
    return array

def clear_rows_P(num, width, array):
    for i in range(width):
        array = clear_row((num + i) % array.shape[0], array)
    return array

def fill_rows_P(num, width, array):
    for i in range(width):
        array = fill_row((num + i) % array.shape[0], array)
    return array

def replace_rows_P(num, width, nucol, array):
    for i in range(width):
        array = replace_row((num + i) % array.shape[0], nucol, array)
    return array

def fill_bounds_P(array):
    array = fill_column(0, array)
    array = fill_column(-1, array)
    array = fill_row(0, array)
    array = fill_row(-1, array)
    return array

def clear_bounds_P(array):
    array = clear_column(0, array)
    array = clear_column(-1, array)
    array = clear_row(0, array)
    array = clear_row(-1, array)
    return array

def set_bounds_P(ub, rb, db, lb, array):
    if ub >= 0:
        array[..., 0] = ub
    if db >= 0:
        array[..., -1] = db
    if lb >= 0:
        array[0, ...] = lb
    if rb >= 0:
        array[-1, ...] = rb
    return array

#=========================LOW-LEVEL==========================
def clear_array_P(array):
    return np.zeros(array.shape, np.intc)

def fill_array_P(array):
    return np.ones(array.shape, np.intc)

def replace_array_P(offset, nuarr, array):
    array[offset[0]: offset[0] + nuarr.shape[0], offset[1]: offset[1] + nuarr.shape[1]] = nuarr
    return array

def fill_row(num, array):
    array[num, ...] = 1
    return array

def fill_column(num, array):
    array[..., num] = 1
    return array

def clear_row(num, array):
    array[num, ...] = 0
    return array

def clear_column(num, array):
    array[..., num] = 0
    return array

def replace_row(num, nurow, array):
    array[num, ...] = nurow
    return array

def replace_column(num, nucol, array):
    array[..., num] = nucol
    return array

def roll_array(up, right, array):
    array = np.roll(array, up, axis=0)
    array = np.roll(array, right, axis=1)
    return array

def get_living(array):
    return np.argwhere(array)

def get_births_deaths(arrayold, arraynu):
    common = np.bitwise_and(arraynu, arrayold)
    onlyOld = np.bitwise_xor(common, arrayold)
    onlyNew = np.bitwise_xor(common, arraynu)
    births = np.argwhere(onlyNew)
    deaths = np.argwhere(onlyOld)
    return births, deaths

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
