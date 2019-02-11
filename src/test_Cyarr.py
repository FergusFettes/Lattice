import array
import numpy as np
from numpy import testing
import timeit
import unittest

debug = False
from Cyarr import *

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
        arrout = roll_columns(1, tst_dim(), tst_arr())
        arrout = roll_columns(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_back(self):
        arrout = roll_columns(-1, tst_dim(), tst_arr())
        arrout = roll_columns(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_forward(self):
        arrout = roll_rows(1, tst_dim(), tst_arr())
        arrout = roll_rows(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_back(self):
        arrout = roll_rows(-1, tst_dim(), tst_arr())
        arrout = roll_rows(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))

    def test_roll_columns_pointer_forward(self):
        arrout = tst_arr()
        roll_columns_pointer(1, tst_dim(), arrout)
        roll_columns_pointer(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_pointer_back(self):
        arrout = tst_arr()
        roll_columns_pointer(-1, tst_dim(), arrout)
        roll_columns_pointer(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_pointer_forward(self):
        arrout = tst_arr()
        roll_rows_pointer(1, tst_dim(), arrout)
        roll_rows_pointer(1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_pointer_back(self):
        arrout = tst_arr()
        roll_rows_pointer(-1, tst_dim(), arrout)
        roll_rows_pointer(-1, tst_dim(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))


class ArrayCheckTestCase(unittest.TestCase):

    def test_sum_rim(self):
        self.assertEqual(sum_rim(0, tst_dim(), tst_arr()), 0)
        self.assertEqual(sum_rim(1, tst_dim(), tst_arr()), 4)

    def test_check_rim(self):
        self.assertFalse(check_rim(0, tst_dim(), tst_arr()))
        self.assertTrue(check_rim(1, tst_dim(), tst_arr()))


class ArrayEditTestCase(unittest.TestCase):

    def set_bounds(self):
        arr = tst_arr()
        set_bounds(1, 1, 1, 1, tst_dim(), arr)

        testing.assert_array_equal(arr, tst_arr())

    def test_create_box(self):
        arr = tst_arr()
        create_box(1, 3, 1, 3, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1:4,1:4] = 1

        testing.assert_array_equal(arr2, arr)

    def test_set_points(self):
        points = np.array([[1,1],[2,2]], np.intc)
        arr = tst_arr()
        set_points(points, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1,1] = 1
        arr2[2,2] = 1

        testing.assert_array_equal(arr2, arr)

    def test_fill_bounds(self):
        arr = tst_arr()
        fill_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 1
        arr2[-1, :] = 1
        arr2[:, 0] = 1
        arr2[:, -1] = 1

        testing.assert_array_equal(arr2, arr)

    def test_clear_bounds(self):
        arr = tst_arr()
        clear_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 0
        arr2[-1, :] = 0
        arr2[:, 0] = 0
        arr2[:, -1] = 0

        testing.assert_array_equal(arr2, arr)

    def test_fill_columns(self):
        arr = tst_arr()
        fill_columns(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_columns(self):
        arr = tst_arr()
        clear_columns(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_fill_rows(self):
        arr = tst_arr()
        fill_rows(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_rows(self):
        arr = tst_arr()
        clear_rows(0, 5, tst_dim(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_replace_rows(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        replace_rows(0, 5, nu, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_replace_columns(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        replace_columns(0, 5, nu, tst_dim(), arr)
        testing.assert_array_equal(np.ones_like(tst_arr()), arr)


arrayedit = unittest.TestLoader().loadTestsFromTestCase(ArrayEditTestCase)
arraycheck = unittest.TestLoader().loadTestsFromTestCase(ArrayCheckTestCase)
arrayroll = unittest.TestLoader().loadTestsFromTestCase(ArrayRollTestCase)

array_manipulation_suite = unittest.TestSuite([arrayroll, arraycheck, arrayedit])

if __name__=="__main__":
    unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(array_manipulation_suite)