import array
import numpy as np
from numpy import testing
import timeit
import unittest

debug = False
from Cyarr import (
    roll_rows, roll_columns, roll_rows_pointer, roll_columns_pointer,
    check_rim, sum_rim, scroll_bars, set_bounds, fill_array, fill_bounds, fill_columns,
    fill_rows, clear_array, clear_columns, clear_rows, clear_bounds, replace_array,
    replace_columns, replace_rows, create_box, set_points
)

def tst_arrS():
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
    arr = np.zeros(tst_dimS(), np.intc)
    arr[1:3,1:3] = 1
    return arr

def tst_dimS():
    return memoryview(array.array('i', [20, 20]))

def tst_arrM():
    """
    Creates a larger array
    :return:        (pointer) arr
    """
    arr = np.zeros(tst_dimS(), np.intc)
    arr[1:3,1:3] = 1
    return arr

def tst_dimM():
    return memoryview(array.array('i', [100, 100]))

def tst_arrL():
    """
    Creates a large array
    :return:        (pointer) arr
    """
    arr = np.zeros(tst_dimL(), np.intc)
    arr[1:3,1:3] = 1
    return arr

def tst_dimL():
    return memoryview(array.array('i', [500, 500]))


class ArrayRollSpeed(unittest.TestCase):

    def test_roll_columns_forward(self):
        i = timeit.Timer('roll_columns(1, tst_dimS(), tst_arrS())', 'from Cyarr import roll_columns')
        o = timeit.Timer('np.roll(tst_arrS(), 1, axis=1)')
        print('{} vs. {}'.format(i.repeat(), o.repeat()))

    def test_roll_columns_back(self):
        arrout = roll_columns(-1, tst_dimS(), tst_arrS())
        arrout = roll_columns(-1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), -2, axis=1))

    def test_roll_rows_forward(self):
        arrout = roll_rows(1, tst_dimS(), tst_arrS())
        arrout = roll_rows(1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), 2, axis=0))

    def test_roll_rows_back(self):
        arrout = roll_rows(-1, tst_dimS(), tst_arrS())
        arrout = roll_rows(-1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), -2, axis=0))

    def test_roll_columns_pointer_forward(self):
        arrout = tst_arrS()
        roll_columns_pointer(1, tst_dimS(), arrout)
        roll_columns_pointer(1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), 2, axis=1))

    def test_roll_columns_pointer_back(self):
        arrout = tst_arrS()
        roll_columns_pointer(-1, tst_dimS(), arrout)
        roll_columns_pointer(-1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), -2, axis=1))

    def test_roll_rows_pointer_forward(self):
        arrout = tst_arrS()
        roll_rows_pointer(1, tst_dimS(), arrout)
        roll_rows_pointer(1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), 2, axis=0))

    def test_roll_rows_pointer_back(self):
        arrout = tst_arrS()
        roll_rows_pointer(-1, tst_dimS(), arrout)
        roll_rows_pointer(-1, tst_dimS(), arrout)
        testing.assert_array_equal(arrout, np.roll(tst_arrS(), -2, axis=0))


class ArrayCheckTestCase(unittest.TestCase):

    def test_sum_rim(self):
        self.assertEqual(sum_rim(0, tst_dimS(), tst_arrS()), 0)
        self.assertEqual(sum_rim(1, tst_dimS(), tst_arrS()), 4)

    def test_check_rim(self):
        self.assertFalse(check_rim(0, tst_dimS(), tst_arrS()))
        self.assertTrue(check_rim(1, tst_dimS(), tst_arrS()))


class ArrayEditTestCase(unittest.TestCase):

    def set_bounds(self):
        arr = tst_arrS()
        set_bounds(1, 1, 1, 1, tst_dimS(), arr)

        testing.assert_array_equal(arr, tst_arrS())

    def test_create_box(self):
        arr = tst_arrS()
        create_box(1, 3, 1, 3, tst_dimS(), arr)

        arr2 = tst_arrS()
        arr2[1:4,1:4] = 1

        testing.assert_array_equal(arr2, arr)

    def test_set_points(self):
        points = np.array([[1,1],[2,2]], np.intc)
        arr = tst_arrS()
        set_points(points, tst_dimS(), arr)

        arr2 = tst_arrS()
        arr2[1,1] = 1
        arr2[2,2] = 1

        testing.assert_array_equal(arr2, arr)

    def test_fill_bounds(self):
        arr = tst_arrS()
        fill_bounds(tst_dimS(), arr)

        arr2 = tst_arrS()
        arr2[0, :] = 1
        arr2[-1, :] = 1
        arr2[:, 0] = 1
        arr2[:, -1] = 1

        testing.assert_array_equal(arr2, arr)

    def test_clear_bounds(self):
        arr = tst_arrS()
        clear_bounds(tst_dimS(), arr)

        arr2 = tst_arrS()
        arr2[0, :] = 0
        arr2[-1, :] = 0
        arr2[:, 0] = 0
        arr2[:, -1] = 0

        testing.assert_array_equal(arr2, arr)

    def test_fill_columns(self):
        arr = tst_arrS()
        fill_columns(0, tst_dimS()[0], tst_dimS(), arr)
        testing.assert_array_equal(np.ones_like(tst_arrS()), arr)

    def test_clear_columns(self):
        arr = tst_arrS()
        clear_columns(0, tst_dimS()[0], tst_dimS(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arrS()), arr)

    def test_fill_rows(self):
        arr = tst_arrS()
        fill_rows(0, tst_dimS()[0], tst_dimS(), arr)
        testing.assert_array_equal(np.ones_like(tst_arrS()), arr)

    def test_clear_rows(self):
        arr = tst_arrS()
        clear_rows(0, tst_dimS()[0], tst_dimS(), arr)
        testing.assert_array_equal(np.zeros_like(tst_arrS()), arr)

    def test_replace_rows(self):
        arr = tst_arrS()
        nu = np.ones(tst_dimS()[0], np.intc)
        replace_rows(0, tst_dimS()[0], nu, tst_dimS(), arr)
        testing.assert_array_equal(np.ones_like(tst_arrS()), arr)

    def test_replace_columns(self):
        arr = tst_arrS()
        nu = np.ones(tst_dimS()[0], np.intc)
        replace_columns(0, tst_dimS()[0], nu, tst_dimS(), arr)
        testing.assert_array_equal(np.ones_like(tst_arrS()), arr)


arrayedit = unittest.TestLoader().loadTestsFromTestCase(ArrayEditTestCase)
arraycheck = unittest.TestLoader().loadTestsFromTestCase(ArrayCheckTestCase)
arrayroll = unittest.TestLoader().loadTestsFromTestCase(ArrayRollSpeed)

array_manipulation_suite = unittest.TestSuite([arrayroll, arraycheck, arrayedit])

if __name__=="__main__":
    unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(array_manipulation_suite)
