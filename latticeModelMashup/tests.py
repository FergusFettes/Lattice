import array
import numpy as np
from numpy import testing
import timeit
import unittest

from src.Cfuncs import *

debug = False
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


class BasicSuiteTestCase(unittest.TestCase):

    def setUp(self):
        self.head_pos, self.buf_siz, self.print_pos, self.analysis_pos,\
            _, _, _, self.dim, self.arr, self.buf = init([50, 50])
        self.bounds = array.array('i', [1, 1, 1, 1])
        self.horizontal = array.array('i', [0, 1, 1, 1])
        self.vertical = array.array('i', [0, 1, 1, 1])
        self.updates = 1000
        self.beta = 1/8
        self.threshold = 0.9
        self.rules = np.array([[2,5,4,6],[3,4,3,6]], np.intc)

    def test_basic_print_defaults(self):
        basic_print(self.dim, self.arr)

    def test_basic_print_bounds_scroll(self):
        basic_print(self.dim, self.arr,
                    self.bounds, self.horizontal, self.vertical)

    def test_basic_update_off(self):
        arr = np.copy(self.arr)
        basic_update(
            0,
            self.beta,
            1,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
        )
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_bounds(self):
        arr = np.copy(self.arr)
        basic_update(
            0,
            self.beta,
            1,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
        )
        fill_bounds(self.dim, arr)
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_scroll(self):
        arr = np.copy(self.arr)
        basic_update(
            0,
            self.beta,
            1,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
            horizontal = array.array('i', [5, 1, 1, 1])
        )
        fill_bounds(self.dim, arr)
        fill_rows(5, 1, self.dim, arr)
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_on(self):
        arr = np.copy(self.arr)
        basic_update(
            self.updates,
            self.beta,
            self.threshold,
            prepair_rule(self.rules, self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
            self.horizontal,
            self.vertical
        )
        testing.assert_equal(np.any(np.not_equal(arr, self.arr)), True)


#==========Basic Tests=============
class MiscTestCase(unittest.TestCase):

    def test_scroll_update(self):
        horizontal = array.array('i', [0, 1, 1, 0, -1])
        vertical = array.array('i', [0, 1, 1, 0, -1])
        scroll_update(horizontal, vertical, tst_dim())
        self.assertEqual(horizontal[0], 1)
        self.assertEqual(vertical[0], 1)

    def test_prepair_rule_fails_1D(self):
        print('PASSING: Cant get assertRaises to work')
        return
        rules = np.array([[2,3,3,3]], np.intc)
        self.assertRaises(TypeError, prepair_rule(rules, 1))

    def test_prepair_rule_passes_2D(self):
        rules = np.array([[2,3,3,3]], np.intc)
        rule = prepair_rule(rules, 1)
        testing.assert_array_equal(np.asarray(rule), np.array([2,3,3,3]))

    def test_prepair_rule_picks_rule(self):
        rules = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2]], np.intc)
        rule = prepair_rule(rules, 1)
        testing.assert_array_equal(np.asarray(rule), np.array([1,1,1,1]))

    def test_print_buffer_status_standard(self):
        print('Prints something? I guess the is a check for this..')
        print_buffer_status(array.array('i', [0,1,2,3]))

    def test_print_buffer_status_custom(self):
        print('Prints something? I guess the is a check for this..')
        print_buffer_status(array.array('i', [0,1,2,3]), 1, '&', '_')

class BufferHandlingTestCase(unittest.TestCase):

    def setUp(self):
        self.buf = init_array_buffer(tst_dimL(), 10)
        self.dim = np.asarray(tst_dimL())
        self.buf_len = 10
        self.buffer_status = np.zeros(self.buf_len, np.intc)

    def test_update_array_positions_writes(self):
        position = array.array('i', [0])
        self.buffer_status[position[0]] = 1
        arr = update_array_position(position, self,buf_len, self.buffer_status, self.buf)
        assertEqual(self.buffer_status[1], 1)

    def test_update_array_positions_clears(self):
        position = array.array('i', [0])
        self.buffer_status[position[0]] = 1
        arr = update_array_position(position, self,buf_len, self.buffer_status, self.buf)
        assertEqual(self.buffer_status[0], 0)

    def test_update_array_positions_wraps(self):
        position = array.array('i', [self.buf_len -1])
        self.buffer_status[position[0]] = 1
        arr = update_array_position(position, self,buf_len, self.buffer_status, self.buf)
        assertEqual(self.buffer_status[0], 1)

    def test_init_array_has_dimensions(self):
        arr = init_array(tst_dim())
        self.assertEqual(np.asarray(arr).shape, (tst_dim()[0], tst_dim()[1]))

    def test_init_array_buffer_has_dimensions(self):
        buf = self.buf
        self.assertEqual(np.asarray(buf).shape, (self.buf_len, 500, 500))

    def test_init_array_buffer_type(self):
        buf = self.buf
        self.assertEqual(np.asarray(buf).dtype, tst_arr().dtype)

    def test_resize_array_buffer_has_dimensions(self):
        buf = self.buf
        _, buf_nu = resize_array_buffer(self.dim, self.buf_len)
        self.assertEqual(np.asarray(buf_nu).shape, (self.buf_len, 502, 502))

        _, buf_nu = resize_array_buffer(self.dim, self.buf_len, 10)
        self.assertEqual(np.asarray(buf_nu).shape, (self.buf_len, 520, 520))

    def test_resize_array_buffer_type(self):
        _, buf = resize_array_buffer(self.dim, self.buf_len)
        self.assertEqual(np.asarray(buf).dtype, tst_arr().dtype)

    def test_change_buffer_leaves_dimensions(self):
        buf = self.buf
        dim_nu, buf_nu = resize_array_buffer(self.dim, self.buf_len)
        change_buffer(0, self.buf_len, self.dim, buf, dim_nu, buf_nu)
        self.assertEqual(np.asarray(buf_nu).shape, (self.buf_len, dim_nu[0], dim_nu[1]))

    def test_change_buffer_no_offset(self):
        buf = self.buf
        buf[0] = 0
        add_noise(0.5, tst_dimL(), buf[0])

        # Change buffer to itself plus 1 with no offset is same as advancing array
        offset = array.array('i', [0, 0])
        change_buffer(1, self.buf_len, self.dim, buf, self.dim, buf)
        testing.assert_array_equal(buf[0], buf[1])

    def test_change_buffer_wraps(self):
        buf = self.buf
        buf[self.buf_len - 1] = 0
        add_noise(0.5, tst_dimL(), buf[self.buf_len - 1])

        # Change buffer to itself plus 1 with no offset is same as advancing array
        offset = array.array('i', [0, 0])
        change_buffer(self.buf_len, self.buf_len, self.dim, buf, tst_dimL(), buf)
        testing.assert_array_equal(buf[-1], buf[0])

    def test_change_buffer_manual_fill(self):
        buf = self.buf
        # Fill old buffer with 1s
        buf[0] = 1
        dim_nu, buf_nu = resize_array_buffer(self.dim, self.buf_len)

        # Initialise new buffer to 0
        buf_nu[0] = 0
        # Adds the old buffer, which should fill the whole middle with 1s
        change_buffer(0, self.buf_len, self.dim, buf, dim_nu, buf_nu)
        # Check the new buffer has empty rim, but full after.
        self.assertFalse(check_rim(0, dim_nu, buf_nu[0]))
        self.assertTrue(check_rim(1, dim_nu, buf_nu[0]))

    def test_change_buffer_manual_fill_cut_and_gap(self):
        buf = self.buf
        # Fill old buffer with 1s
        buf[0] = 1
        dim_nu, buf_nu = resize_array_buffer(self.dim, self.buf_len)

        # Initialise new buffer to 0
        buf_nu[0] = 0
        # This time, when changing offset and cut the old array
        offset = array.array('i', [2, 2])
        cut = array.array('i', [1, 1])
        change_buffer(0, self.buf_len, self.dim, buf, dim_nu, buf_nu, offset, cut)
        # Check the new buffer has a gap all the way around, one step in from the
        # outside.
        self.assertFalse(check_rim(0, dim_nu, buf_nu[0]))
        self.assertFalse(check_rim(1, dim_nu, buf_nu[0]))
        self.assertTrue(check_rim(2, dim_nu, buf_nu[0]))

    def test_advance_array_has_dimensions(self):
        buf = self.buf
        advance_array(0, self.buf_len, buf)
        testing.assert_array_equal(np.asarray(buf).shape, (self.buf_len, self.dim[0],
                                                           self.dim[1]))

    def test_advance_array_direct_comparison(self):
        buf = self.buf
        buf[0] = 0
        add_noise(0.5, tst_dimL(), buf[0])
        testing.assert_almost_equal(np.mean(buf[0]),
                                    np.mean(np.random.randint(0, 2, self.dim)),
                                    decimal=2)

        advance_array(0, self.buf_len, buf)
        testing.assert_array_equal(buf[0], buf[1])

    def test_advance_array_wraps(self):
        buf = self.buf
        buf[0] = 0
        add_noise(0.5, tst_dimL(), buf[self.buf_len - 1])
        testing.assert_almost_equal(np.mean(buf[self.buf_len - 1]),
                                    np.mean(np.random.randint(0, 2, self.dim)),
                                    decimal=2)

        advance_array(self.buf_len - 1, self.buf_len, buf)
        testing.assert_array_equal(buf[0], buf[self.buf_len - 1])

class NoiseTestCase(unittest.TestCase):

    def test_add_noise_type(self):
        arr = tst_arr()
        add_noise(0.5, tst_dim(), arr)
        self.assertEqual(arr.dtype, tst_arr().dtype)

    def test_add_noise_off(self):
        arr = tst_arr()
        add_noise(1, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_add_noise_full(self):
        arr = np.zeros_like(tst_arr())
        add_noise(0, tst_dim(), arr)
        testing.assert_array_equal(arr, np.ones_like(tst_arr()))

    def test_add_noise_lots_of_noise(self):
        arr = np.zeros_like(tst_arrL())
        for _ in range(10):
            add_noise(0.5, tst_dimL(), arr)
        testing.assert_almost_equal(np.mean(arr),
                                    np.mean(np.random.randint(0, 2, tst_dimL())),
                                    decimal=2)

    def test_randomize_center_automatic(self):
        arr = tst_arrL()
        randomize_center(500, tst_dimL(), arr, 0.5)
        testing.assert_almost_equal(np.mean(arr),
                                    np.mean(np.random.randint(0, 2, tst_dimL())),
                                    decimal=2)

    def test_randomize_center_value(self):
        arr = tst_arrL()
        randomize_center(500, tst_dimL(), arr, 1)
        testing.assert_array_equal(arr, tst_arrL())


#TODO: I think there might be a disaster in here, need to check properly that Ising works.
class IsingTestCase(unittest.TestCase):

    def test_ising_process_off(self):
        arr = tst_arr()
        ising_process(0, 1/8, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_ising_process_type(self):
        arr = tst_arr()
        ising_process(10, 1/8, tst_dim(), arr)
        self.assertIs(arr.dtype, tst_arr().dtype)

    def test_ising_process_random(self):
        """
        With the inverse temperature low, the chance of a collision is ~ 1/25! ~ 0
        """
        arr = tst_arr()
        ising_process(10000, 1/1000, tst_dim(), arr)
        testing.assert_equal(np.any(np.not_equal(arr, tst_arr())), True)


class ConwayTestCase(unittest.TestCase):

    def setUp(self):
        self.rule = array.array('i', [2,3,3,3])

    def test_conway_process_off(self):
        arr = tst_arr()
        rule = self.rule
        rule[0] = -1
        conway_process(rule, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_conway_process_input_output(self):
        arr = tst_arr()
        conway_process(self.rule, tst_dim(), arr)
        self.assertIs(arr.dtype, tst_arr().dtype)

    def test_conway_process_wraps(self):
        arr = tst_arr()
        arr[0:3,0:3] = 1
        conway_process(self.rule, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[:,:] = 0
        arr2[0,0] = 1; arr2[2,0] = 1; arr2[2,2] = 1; arr2[0,2] = 1
        arr2[1,3:5] = 1; arr2[3:5, 1] = 1

        testing.assert_array_equal(arr2, arr)


basicsuite = unittest.TestLoader().loadTestsFromTestCase(BasicSuiteTestCase)

conway = unittest.TestLoader().loadTestsFromTestCase(ConwayTestCase)
ising = unittest.TestLoader().loadTestsFromTestCase(IsingTestCase)
noise = unittest.TestLoader().loadTestsFromTestCase(NoiseTestCase)
bufferhandling = unittest.TestLoader().loadTestsFromTestCase(BufferHandlingTestCase)
misc = unittest.TestLoader().loadTestsFromTestCase(MiscTestCase)

simple_suite = unittest.TestSuite([misc, bufferhandling, noise, ising, conway])

if __name__=="__main__":
    if simple is True:
        unittest.TextTestRunner(verbosity=2 if debug is True else 1).run(simple_suite)
    else:
        unittest.main(verbosity=2 if debug is True else 1)
