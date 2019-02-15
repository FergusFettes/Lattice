import array
import numpy as np
from numpy import testing
import unittest

from Cfuncs import add_global_noise, init_array
from Cyphys import (
    norm, center_of_mass, center_of_mass_pop, living, population,
    radius_of_gyration, analysis_loop, polarization, neighbor_interaction, neighbor_interaction_moore
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
        add_global_noise(0.5, tst_dimL(), self.arr)

    def test_norm_345(self):
        self.assertEqual(5, norm(3,4))

    def test_center_of_mass_numpy(self):
        com = center_of_mass(tst_dimL(), self.arr)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(com, com_P)

    def test_center_of_mass_pop_numpy(self):
        _, pop = center_of_mass_pop(tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), pop)

    def test_population_numpy(self):
        pop = population(tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), pop)

    def test_living_length_numpy(self):
        live = living(tst_dimL(), self.arr)
        pos = np.argwhere(self.arr)
        self.assertEqual(len(pos), len(live))

    def test_live_content_numpy(self):
        live = living(tst_dimL(), self.arr)
        pos = np.argwhere(self.arr)
        testing.assert_array_equal(pos, np.asarray(live))

    def test_radius_of_gyration_python(self):
        com = center_of_mass(tst_dimL(), self.arr)
        Rg = radius_of_gyration(com, tst_dimL(), self.arr)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(Rg, Rg_P, 1e-8, 1e-2)

    def test_polarization_random(self):
        self.assertAlmostEqual(0, polarization(tst_dimL(), self.arr), 2)

    def test_polarization_zeros(self):
        self.arr[:, :] = 0
        self.assertEqual(1, polarization(tst_dimL(), self.arr))

    def test_polarization_ones(self):
        self.arr[:, :] = 1
        self.assertEqual(1, polarization(tst_dimL(), self.arr))

    def test_neighbor_interaction_moore(self):
        e, e2 = neighbor_interaction_moore(tst_dimL(), self.arr)
        self.assertAlmostEqual(e, -4, 1)
        self.assertLess(e, e2)

    def test_neighbor_interaction_random(self):
        e, e2 = neighbor_interaction(tst_dimL(), self.arr)
        self.assertAlmostEqual(e, -4, 1)
        self.assertLess(e, e2)

    def test_neighbor_interaction_zeros(self):
        self.arr[:, :] = 0
        e, e2 = neighbor_interaction(tst_dimL(), self.arr)
        self.assertEqual(e, -8)
        self.assertEqual(e2, 64)

    def test_neighbor_interaction_ones(self):
        self.arr[:, :] = 1
        e, e2 = neighbor_interaction(tst_dimL(), self.arr)
        self.assertEqual(e, -8)
        self.assertEqual(e2, 64)

analysis_suite = unittest.TestLoader().loadTestsFromTestCase(AnalysisSuiteTestCase)

if __name__=="__main__":
    if simple is True:
        unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(analysis_suite)
    else:
        unittest.main(verbosity=2 if debug is True else 1)
