import numpy as np
from numpy.core.umath_tests import inner1d
import math


class analyser():

    def __init__(self, st):
        self.st = st

        self.clear()

    def save_array(self, array):
        self.arrayold = array

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
        self.population = np.zeros([run_length, 1], int)
        self.radius = np.zeros([run_length, 1], float)

    def process(self, array):
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
        square_distance = inner1d(rel,rel)
        return np.sqrt(np.sum(square_distance, axis=0) / population)

    def living(self, array):
        return np.argwhere(array)

    def change(self, array):
        common = np.bitwise_and(array, self.arrayold)
        onlyOld = np.bitwise_xor(common, self.arrayold)
        onlyNew = np.bitwise_xor(common, array)
        births = np.argwhere(onlyNew)
        deaths = np.argwhere(onlyOld)
        b = np.concatenate((births, np.ones([births.shape[0], 1], int)), axis=1)
        d = np.concatenate((deaths, np.zeros([deaths.shape[0], 1], int)), axis=1)
        return np.concatenate((b, d))
