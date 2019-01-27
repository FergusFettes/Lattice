import numpy as np
from numpy.core.umath_tests import inner1d

def make_buffer(self, dim, buffer_length):
    # TODO: check this is the right sort of contiguous
    return np.zeros([dim[0], dim[1], buffer_length], np.intc)

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
    wid = array.shape[0]
    for i in range(scale):
        array[(start + i) % wid, ...] = polarity
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
    # TODO: or just have it make a new array every 2000
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
