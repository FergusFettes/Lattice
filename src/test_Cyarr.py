import array
import numpy as np
from numpy import testing
import timeit
import unittest

debug = False
import Cyarr as cy

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
    arr[1:3,1:3] = 1
    return arr

def tst_dim():
    return memoryview(array.array('i', [5, 5]))

def tst_arrL():
    """
    large test array
    """
    arr = np.zeros(tst_dimL(), np.intc)
    arr[1:3,1:3] = 1
    return arr

def tst_dimL():
    return memoryview(array.array('i', [500, 500]))


class ArrayRollTestCase(unittest.TestCase):

    def test_roll_columns_forward(self):
        arrout = cy.roll_columns(1, tst_dim(), tst_arr())
        arrout = cy.roll_columns(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_back(self):
        arrout = cy.roll_columns(-1, tst_dim(), tst_arr())
        arrout = cy.roll_columns(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_forward(self):
        arrout = cy.roll_rows(1, tst_dim(), tst_arr())
        arrout = cy.roll_rows(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_back(self):
        arrout = cy.roll_rows(-1, tst_dim(), tst_arr())
        arrout = cy.roll_rows(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))

    def test_roll_columns_pointer_forward(self):
        arrout = tst_arr()
        cy.roll_columns_pointer(1, tst_dim(), arrout)
        cy.roll_columns_pointer(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_pointer_back(self):
        arrout = tst_arr()
        cy.roll_columns_pointer(-1, tst_dim(), arrout)
        cy.roll_columns_pointer(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_pointer_forward(self):
        arrout = tst_arr()
        cy.roll_rows_pointer(1, tst_dim(), arrout)
        cy.roll_rows_pointer(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_pointer_back(self):
        arrout = tst_arr()
        cy.roll_rows_pointer(-1, tst_dim(), arrout)
        cy.roll_rows_pointer(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))


class ArrayCheckTestCase(unittest.TestCase):

    def test_sum_rim(self):
        self.assertEqual(cy.sum_rim(0, tst_dim(), tst_arr()), 0)
        self.assertEqual(cy.sum_rim(1, tst_dim(), tst_arr()), 4)

    def test_check_rim(self):
        self.assertFalse(cy.check_rim(0, tst_dim(), tst_arr()))
        self.assertTrue(cy.check_rim(1, tst_dim(), tst_arr()))


class ArrayEditTestCase(unittest.TestCase):

    def test_scroll_bars_basic(self):
        bars = np.array([[0, 1, 1, 0, 0, 1]], np.double)
        arr = tst_arrL()

        cy.scroll_bars(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        arr2[0, :] = 1
        testing.assert_array_equal(arr, arr2)

    def test_scroll_bars_axis(self):
        bars = np.array([[0, 1, 1, 1, 0, 1]], np.double)
        arr = tst_arrL()

        cy.scroll_bars(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        arr2[:, 0] = 1
        testing.assert_array_equal(arr, arr2)

    def test_scroll_bars_width(self):
        bars = np.array([[0, 5, 1, 1, 0, 1]], np.double)
        arr = tst_arrL()

        cy.scroll_bars(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        arr2[:, :5] = 1
        testing.assert_array_equal(arr, arr2)

    def test_scroll_bars_multi(self):
        bars = np.array([
            [10, 1, 1, 0, 0, 1],
            [0, 1, 1, 1, 0, 1],
            [1, 1, 1, 1, 0, 1],
        ], np.double)
        arr = tst_arrL()

        cy.scroll_bars(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        arr2[10, :] = 1
        arr2[:, 0] = 1
        arr2[:, 1] = 1
        testing.assert_array_equal(arr, arr2)

    def test_set_bounds(self):
        arr = tst_arr()
        bounds = array.array('i', [1,1,1,1])
        cy.set_bounds(bounds, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0] = 1
        arr2[:, 0] = 1
        arr2[tst_dim()[0] - 1] = 1
        arr2[:, tst_dim()[1] - 1] = 1

        testing.assert_array_equal(arr, arr2)

    def test_create_box(self):
        arr = tst_arr()
        cy.create_box(1, 3, 1, 3, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1:4,1:4] = 1

        testing.assert_array_equal(arr2, arr)

    def test_set_points(self):
        points = np.array([[1,1],[2,2]], np.intc)
        arr = tst_arr()
        cy.set_points(points, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1,1] = 1
        arr2[2,2] = 1

        testing.assert_array_equal(arr2, arr)

    def test_fill_bounds(self):
        arr = tst_arr()
        cy.fill_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 1
        arr2[-1, :] = 1
        arr2[:, 0] = 1
        arr2[:, -1] = 1

        testing.assert_array_equal(arr2, arr)

    def test_clear_bounds(self):
        arr = tst_arr()
        cy.clear_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 0
        arr2[-1, :] = 0
        arr2[:, 0] = 0
        arr2[:, -1] = 0

        testing.assert_array_equal(arr2, arr)

    def test_fill_columns(self):
        arr = tst_arr()
        cy.fill_columns(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_columns(self):
        arr = tst_arr()
        cy.clear_columns(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_fill_rows(self):
        arr = tst_arr()
        cy.fill_rows(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_rows(self):
        arr = tst_arr()
        cy.clear_rows(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_replace_rows(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        cy.replace_rows(0, 5, nu, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_replace_columns(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        cy.replace_columns(0, 5, nu, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)


arrayedit = unittest.TestLoader().loadTestsFromTestCase(ArrayEditTestCase)
arraycheck = unittest.TestLoader().loadTestsFromTestCase(ArrayCheckTestCase)
arrayroll = unittest.TestLoader().loadTestsFromTestCase(ArrayRollTestCase)

array_manipulation_suite = unittest.TestSuite([arrayroll, arraycheck, arrayedit])

if __name__=="__main__":
    unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(array_manipulation_suite)
