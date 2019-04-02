import numpy as np

from numpy.core.umath_tests import inner1d

#==============WOLFRAM==========================#
# Make little wolfline and array
def make_wolf(random, dim, scale, rule):
    wid = int(dim[0] / scale)
    hi = int(dim[1] / scale)
    if random:
        line = np.random.randint(0, 2, hi, int)
    else:
        line = np.zeros(hi, int)
        line[int(hi / 2)] = 1
    wolf = wolf_generator(line, hi, rule)
    wolfarray = np.zeros([wid, hi], bool)
    return wolf, wolfarray


# Generates the next wolfram line every time it is called
def wolf_generator(line, hi, rule):
    rule = str(bin(rule))[2:]   #gets binary repr. of update rule
    while len(rule) < 8:
        rule = '0' + rule
    while True:
        nb = [
                int(
                    str(line[(i - 1) % hi])
                    + str(line[i])
                    + str(line[(i + 1) % hi]),
                    2)
                for i in range(hi)
            ]
        line = [int(rule[-i - 1]) for i in nb]
        yield line


def wolfram_scroll(wolf, start, scale, array):
    line = next(wolf)
    hi = len(line)
    wid = array.shape[0]
    HI = array.shape[1]
    for i in range(HI):
        for j in range(scale):
            array[(start + j) % wid, i] = line[int(i / scale) % hi]
    return array


def wolf_array(wolf, wolfarray):
    wid = wolfarray.shape[0]
    for lin in range(wid):
        line = next(wolf)
        wolfarray[lin, ...] = line
    return wolfarray


#===========================Analysis
#==Used for testing the Cython funcs
def population_density_P(rad, pop):
    if pop == 0:
        return 0
    return pop/(np.pi*rad**2)


def axial_diameter_P(positions):
    if len(positions) == 0:
        return 0, 0
    l = np.asarray(positions)
    ax0 = l[:,0].max() - l[:,0].min() + 1
    ax1 = l[:,1].max() - l[:,1].min() + 1
    return ax0, ax1


def diameter_growth_rate_P(max_diameter):
    if len(max_diameter) < 3:
        return 0
    pair = np.zeros(len(max_diameter) - 1)
    for i in range(len(max_diameter) - 1):
        pair[i] = (max_diameter[i + 1] - max_diameter[i])/2
    return np.mean(pair)


def center_of_mass_P(positions, population):
    if not population:
        return 0
    return np.sum(positions, axis=0) / population


def radius_of_gyration_P(center, positions, population):
    if not population:
        return 0
    rel = positions - center
    square_distance = inner1d(rel, rel)
    return np.sqrt(np.sum(square_distance, axis=0) / population)


def get_living_P(array):
    return np.argwhere(array)


def get_births_deaths_P(arrayold, arraynu):
    common = np.bitwise_and(arraynu, arrayold)
    onlyOld = np.bitwise_xor(common, arrayold)
    onlyNew = np.bitwise_xor(common, arraynu)
    births = np.argwhere(onlyNew)
    deaths = np.argwhere(onlyOld)
    return births, deaths
