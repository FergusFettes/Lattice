import sys, os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)

import array
import numpy as np
from numpy import testing
import unittest
from numpy.core.umath_tests import inner1d

from src.Cfuncs import (
    add_global_noise, init_array, moore_neighbors_same_CP,
    add_stochastic_noise
)
import src.Cyarr as cy
from src.Cyphys import (
    norm, center_of_mass, center_of_mass_pop, living, population, analysis_loop_energy,
    radius_of_gyration, analysis_loop, polarization, neighbor_interaction, neighbor_interaction_moore,
    norm, births, deaths, population_change
)
from src.Pfuncs import center_of_mass_P, radius_of_gyration_P, get_births_deaths_P

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

    def test_analysis_loop_energy_numpy(self):
        add_stochastic_noise(1, tst_dimL(), self.arr)
        com = center_of_mass(tst_dimL(), self.arr)
        tot, living, com, Rg, e, e2, M = analysis_loop_energy(com, tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), tot)
        self.assertEqual(len(np.argwhere(self.arr)), len(living))
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(com, com_P)
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(Rg, Rg_P, 1e-8, 1e-2)
        E, E2 = neighbor_interaction(tst_dimL(), self.arr)
        EE, EE2 = neighbor_interaction_moore(tst_dimL(), self.arr)
        self.assertAlmostEqual(e, -4, 1)
        self.assertLess(e, e2)
        self.assertAlmostEqual(E, e, 5)
        self.assertAlmostEqual(EE, e, 5)
        self.assertAlmostEqual(E2, e2, 5)
        self.assertAlmostEqual(EE2, e2, 5)
        self.assertAlmostEqual(0, M, 2)
        self.assertAlmostEqual(polarization(tst_dimL(), self.arr), M)

    def test_analysis_loop_energy_empty(self):
        cy.clear_array(tst_dimL(), self.arr)
        com = center_of_mass(tst_dimL(), self.arr)
        tot, living, com, Rg, e, e2, M = analysis_loop_energy(com, tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), tot)
        self.assertEqual(len(np.argwhere(self.arr)), len(living))
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(com, com_P)
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(Rg, Rg_P, 1e-8, 1e-2)
        E, E2 = neighbor_interaction(tst_dimL(), self.arr)
        EE, EE2 = neighbor_interaction_moore(tst_dimL(), self.arr)
        self.assertAlmostEqual(e, -8, 1)
        self.assertLess(e, e2)
        self.assertAlmostEqual(E, e, 5)
        self.assertAlmostEqual(EE, e, 5)
        self.assertAlmostEqual(E2, e2, 5)
        self.assertAlmostEqual(EE2, e2, 5)
        self.assertAlmostEqual(1, M, 2)
        self.assertAlmostEqual(polarization(tst_dimL(), self.arr), M)

    def test_analysis_loop_numpy(self):
        com = center_of_mass(tst_dimL(), self.arr)
        tot, living, com, Rg, M = analysis_loop(com, tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), tot)
        self.assertEqual(len(np.argwhere(self.arr)), len(living))
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(com, com_P)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(Rg, Rg_P, 1e-8, 1e-2)
        self.assertAlmostEqual(polarization(tst_dimL(), self.arr), M)

    def test_analysis_loop_empty(self):
        cy.clear_array(tst_dimL(), self.arr)
        com = center_of_mass(tst_dimL(), self.arr)
        tot, living, com, Rg, M = analysis_loop(com, tst_dimL(), self.arr)
        self.assertEqual(len(np.argwhere(self.arr)), tot)
        self.assertEqual(len(np.argwhere(self.arr)), len(living))
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(com, com_P)
        com_P = center_of_mass_P(np.argwhere(self.arr), len(np.argwhere(self.arr)))
        Rg_P = radius_of_gyration_P(com_P, np.argwhere(self.arr), len(np.argwhere(self.arr)))
        testing.assert_allclose(Rg, Rg_P, 1e-8, 1e-2)
        self.assertAlmostEqual(polarization(tst_dimL(), self.arr), M)

    def test_norm_345(self):
        self.assertEqual(5, norm(3,4))

    def test_norm_single_battery(self):
        num = np.random.random_sample(2)
        dim = np.asarray(num, np.intc)
        A = np.sqrt(np.einsum('...i,...i', dim, dim))
        B = np.linalg.norm(dim, axis=0)
        C = np.sqrt((dim**2).sum(-1))
        D = np.sqrt((dim*dim).sum(axis=0))
        E = np.sqrt(inner1d(dim, dim))
        F = norm(dim[0], dim[1])
        for i in [A, B, C, D, E]:
            self.assertTrue(np.allclose(F, i))

    def test_norm_multi_battery(self):
        num = np.random.random_sample((10**4, 2,))
        dim = np.asarray(num, np.intc)
        A = np.sqrt(np.einsum('...i,...i', dim, dim))
        B = np.linalg.norm(dim, axis=1)
        C = np.sqrt((dim**2).sum(-1))
        D = np.sqrt((dim*dim).sum(axis=1))
        E = np.sqrt(inner1d(dim, dim))
        F = [norm(dim[i, 0], dim[i, 1]) for i in range(10**4)]
        for i in [A, B, C, D, E]:
            self.assertTrue(np.allclose(F, i))

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

    def test_living_content_numpy(self):
        live = living(tst_dimL(), self.arr)
        pos = np.argwhere(self.arr)
        testing.assert_array_equal(pos, np.asarray(live))

    def test_births_deaths_numpy(self):
        arr_old = np.copy(self.arr)
        add_stochastic_noise(1, tst_dimL(), self.arr)
        b, d = get_births_deaths_P(arr_old, self.arr)
        birth = births(tst_dimL(), arr_old, tst_dimL(), self.arr)
        death = deaths(tst_dimL(), arr_old, tst_dimL(), self.arr)
        testing.assert_array_equal(b, birth)
        testing.assert_array_equal(d, death)

    def test_population_change_numpy(self):
        arr_old = np.copy(self.arr)
        add_stochastic_noise(1, tst_dimL(), self.arr)
        b, d = get_births_deaths_P(arr_old, self.arr)
        res = population_change(tst_dimL(), arr_old, tst_dimL(), self.arr)
        self.assertEqual(len(b), res[0])
        self.assertEqual(len(d), res[1])

    def test_radius_of_gyration_empty(self):
        cy.clear_array(tst_dimL(), self.arr)
        com = center_of_mass(tst_dimL(), self.arr)
        self.assertEqual(None, com)
        Rg = radius_of_gyration(com, tst_dimL(), self.arr)
        self.assertEqual(0, Rg)

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
        E, E2 = neighbor_interaction(tst_dimL(), self.arr)
        e, e2 = neighbor_interaction_moore(tst_dimL(), self.arr)
        self.assertAlmostEqual(e, -4, 1)
        self.assertLess(e, e2)
        self.assertEqual(E, e)
        self.assertEqual(E2, e2)

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
