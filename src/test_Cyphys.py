import array
import numpy as np
from numpy import testing
import unittest

from Cfuncs import add_noise, init_array
from Cyphys import (
    norm, center_of_mass, center_of_mass_pop, center_of_mass_pop_living, population,
    radius_of_gyration
)
from Pfuncs import center_of_mass_P, radius_of_gyration_P

debug = True
simple = True


def tst_arr():
    """
    Creates the following array:
        [00000,
         01100,
         01100,
         00000,
         00000]
    and returns a memoryview to it for the rest of the tests.

    :return:        (pointer) arr
    """
    arr = np.zeros(tst_dim(), np.intc)
    arr[1:3, 1:3] = 1
    return arr


def tst_dim():
    return memoryview(array.array('i', [5, 5]))


def tst_arrL():
    """
    large test array
    """
    arr = np.zeros(tst_dimL(), np.intc)
    arr[1:3, 1:3] = 1
    return arr


def tst_dimL():
    return memoryview(array.array('i', [500, 500]))


class AnalysisSuiteTestCase(unittest.TestCase):

    def setUp(self):
        self.arr = tst_arrL()
        add_noise(0.5, tst_dimL(), self.arr)

    def test_norm_345(self):
        self.assertEqual(5, norm(3,4))

    def test_center_of_mass_numpy(self):
        com = center_of_mass(tst_dimL(), self.arr)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_array_equal(com, com_P)

    def test_center_of_mass_pop_numpy(self):
        _, pop = center_of_mass_pop(tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), pop)

    def test_population_numpy(self):
        pop = population(tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), pop)

    def test_center_of_mass_pop_living_length_numpy(self):
        _, _, living = center_of_mass_pop_living(tst_dimL(), self.arr)
        pos = np.argwhere(self.arr)
        self.assertEqual(len(pos), len(living))

    def test_center_of_mass_pop_living_content_numpy(self):
        _, _, living = center_of_mass_pop_living(tst_dimL(), self.arr)
        pos = np.argwhere(self.arr)
        testing.assert_array_equal(pos, np.sort(np.asarray(living)))

    def test_radius_of_gyration_python(self):
        com = center_of_mass(tst_dimL(), self.arr)
        Rg = radius_of_gyration(com, tst_dimL(), self.arr)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        self.assertEqual(Rg, Rg_P)


analysis_suite = unittest.TestLoader().loadTestsFromTestCase(AnalysisSuiteTestCase)

if __name__=="__main__":
    if simple is True:
        unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(analysis_suite)
    else:
        unittest.main(verbosity=2 if debug is True else 1)
