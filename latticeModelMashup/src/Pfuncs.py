import numpy as np
from numpy.core.umath_tests import inner1d

def population_density(rad, pop):
    if pop == 0:
        return 0
    return pop/(np.pi*rad**2)

def axial_diameter(positions):
    if len(positions) == 0:
        return 0, 0
    width = max(positions[:,0]) - min(positions[:,0])
    height = max(positions[:,1]) - min(positions[:,1])
    return max(width, height), min(width, height)

def diameter_growth_rate(max_diameter):
    if len(max_diameter) < 3:
        return 0
    pair = np.zeros(len(max_diameter) - 1)
    for i in range(len(max_diameter) - 1):
        pair[i] = (max_diameter[i + 1] - max_diameter[i])/2
    return np.mean(pair)

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
