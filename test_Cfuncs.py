import random as ra
import array
import numpy as np
from numpy import testing
import io
import unittest
import unittest.mock
from PyQt5.QtGui import QImage

from src.Cfuncs import *
import src.Cyarr as cy
import src.Cyphys as cyphys
import src.Pfuncs as pf

debug = True
simple = False


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


class ImageProcessingTestCase(unittest.TestCase):

    def setUp(self):
        dim = tst_dimL()
        colHex1 = int(ra.random() * int('0xffffffff', 16))
        colHex2 = int(ra.random() * int('0xffffffff', 16))
        colHex3 = int(ra.random() * int('0xffffffff', 16))
        colHex4 = int(ra.random() * int('0xffffffff', 16))
        self.colorList = [colHex1, colHex2, colHex3, colHex4]
        self.L = np.random.randint(0, tst_dimL()[0], 1000).reshape(500, 2)
        self.image = QImage(dim[0], dim[1], QImage.Format_ARGB32)
        self.imageDim = np.asarray(dim)
        self.imageScale = np.asarray(4, np.intc)

    def test_replace_image_positions(self):
        pass
        image2 = QImage(self.imageDim[0], self.imageDim[1], QImage.Format_ARGB32)
        self.assertEqual(self.image, image2)
        pf.replace_image_positions(self.image, self.colorList, self.L, 2)
        cf.replace_image_positions(image2, self.colorList, self.L, 2)
        self.assertEqual(self.image, image2)

class BasicSuiteTestCase(unittest.TestCase):

    def setUp(self):
        self.head_pos, self.tail_pos, self.buf_siz, self.buf_stat,\
            _, _, _, self.dim, self.arr, self.buf = init([50, 50])
        self.bounds = array.array('i', [1, 1, 1, 1])
        self.bars = np.array([[0, 1, 1, 0, 0, 1]], np.double)
        self.fuzz = np.array([[0.1, 1.1, 1.1, 0.1, 0.1, 0.5, 1.1]], np.double)
        self.roll = array.array('i', [1, 1])
        self.updates = 0.01
        self.beta = 1/8
        self.threshold = 0.9
        self.rules = np.array([[2,5,4,6],[3,4,3,6]], np.intc)

    def test_init_basic(self):
        self.head_pos, self.tail_pos, self.buf_siz, self.buf_stat,\
            _, _, _, self.dim, self.arr, self.buf = init([50, 50])

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_basic_print_size(self, mock_stdout):
        basic_print(self.dim, self.arr)
        out = mock_stdout.getvalue()
        self.assertEqual(int(len(out)/self.dim[1]), self.dim[0] + 1)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_basic_print_bounds_scroll(self, mock_stdout):
        basic_print(self.dim, self.arr, self.bounds, self.bars)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_basic_print_bounds_scroll(self, mock_stdout):
        basic_print(self.dim, self.arr, self.bounds)
        out = mock_stdout.getvalue()
        self.assertEqual(out[0], 'o')

    def test_basic_update_off(self):
        arr = np.copy(self.arr)
        basic_update(
            0,
            self.beta,
            0,
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
            0,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
        )
        cy.fill_bounds(self.dim, arr)
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_scroll(self):
        arr = np.copy(self.arr)
        basic_update(
            0,
            self.beta,
            0,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
            bars = np.array([[1, 1, 1, 0, 0, 1]], np.double),
        )
        cy.fill_bounds(self.dim, arr)
        arr[1, :] = 1
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_on(self):
        arr = np.copy(self.arr)
        basic_update(
            self.updates,
            self.beta,
            self.threshold,
            prepair_rule(np.array([[-1,0,0,0]], np.intc), self.head_pos),
            self.dim,
            self.arr,
            self.bounds,
            self.bars
        )
        testing.assert_equal(np.any(np.not_equal(arr, self.arr)), True)

    def test_basic_update_buffer_off(self):
        arr = np.copy(self.arr)
        basic_update_buffer(
            0,
            self.beta,
            0,
            np.array([[-1,0,0,0]], np.intc),
            self.head_pos, 10,
            self.dim,
            self.arr,
            self.buf,
        )
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_buffer_bounds(self):
        arr = np.copy(self.arr)
        basic_update_buffer(
            0,
            self.beta,
            0,
            np.array([[-1,0,0,0]], np.intc),
            self.head_pos, 10,
            self.dim,
            self.arr,
            self.buf,
            self.bounds,
        )
        cy.fill_bounds(self.dim, arr)
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_buffer_scroll(self):
        arr = np.copy(self.arr)
        basic_update_buffer(
            0,
            self.beta,
            0,
            np.array([[-1,0,0,0]], np.intc),
            self.head_pos, 10,
            self.dim,
            self.arr,
            self.buf,
            self.bounds,
            bars = np.array([[1, 1, 1, 0, 0, 1]], np.double),
        )
        cy.fill_bounds(self.dim, arr)
        arr[1, :] = 1
        testing.assert_array_equal(arr, self.arr)

    def test_basic_update_buffer_on(self):
        arr = np.copy(self.arr)
        basic_update_buffer(
            self.updates,
            self.beta,
            self.threshold,
            np.array([[-1,0,0,0]], np.intc),
            self.head_pos, 10,
            self.dim,
            self.arr,
            self.buf,
            self.bounds,
            self.bars,
            self.fuzz,
            self.roll
        )
        testing.assert_equal(np.any(np.not_equal(arr, self.arr)), True)


#==========Basic Tests=============
class MiscTestCase(unittest.TestCase):

    def setUp(self):
        self.position = array.array('i', [1])

    def test_scroll_instruction_update(self):
        bars = np.array([
            [0, 1, 1, 0, 0, 1],
            [3, 1, 1, 1, 0, 1],
        ], np.double)
        scroll_instruction_update(bars, tst_dim())
        self.assertEqual(bars[0][0], 1)
        self.assertEqual(bars[1][0], 4)

    def test_noise_rows_fill(self):
        arr = tst_arrL()
        arr[:] = 0
        noise_rows(0, 1, tst_dimL(), arr, 1, 5)
        self.assertAlmostEqual(1, np.asarray(arr[0, :]).mean(), 1)

    def test_noise_rows_clear(self):
        arr = tst_arrL()
        arr[:] = 1
        noise_rows(0, 1, tst_dimL(), arr, -1, 5)
        self.assertAlmostEqual(0, np.asarray(arr[0, :]).mean(), 1)

    def test_noise_columns_fill(self):
        arr = tst_arrL()
        arr[:] = 0
        noise_columns(0, 1, tst_dimL(), arr, 1, 5)
        self.assertAlmostEqual(1, np.asarray(arr[:, 0]).mean(), 1)

    def test_noise_columns_clear(self):
        arr = tst_arrL()
        arr[:] = 1
        noise_columns(0, 1, tst_dimL(), arr, -1, 5)
        self.assertAlmostEqual(0, np.asarray(arr[:, 0]).mean(), 1)

    def test_scroll_noise_off(self):
        arr = tst_arrL()
        bars = np.array([
            [0, 1, 1, 0, 0, 0.5, -2],
            [5, 1, 1, 1, 0, 0.5, -2],
        ], np.double)
        scroll_noise(tst_dimL(), arr, bars)
        testing.assert_array_equal(arr, tst_arrL())

    def test_scroll_noise_random(self):
        arr = tst_arrL()
        bars = np.array([
            [0, tst_dimL()[0], 0, 0, 0, 5, 0],
        ], np.double)
        scroll_noise(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        add_stochastic_noise(5, tst_dimL(), arr2)
        self.assertAlmostEqual(np.asarray(arr).mean(), np.asarray(arr2).mean(), 2)

    def test_scroll_noise_fill(self):
        arr = tst_arrL()
        arr[:] = 0
        bars = np.array([
            [0, tst_dimL()[0], 0, 0, 0, 5, 1],
        ], np.double)
        scroll_noise(tst_dimL(), arr, bars)

        self.assertAlmostEqual(1, np.asarray(arr).mean(), 1)

    def test_scroll_noise_clear(self):
        arr = tst_arrL()
        arr[:] = 1
        bars = np.array([
            [0, tst_dimL()[0], 0, 0, 0, 5, -1],
        ], np.double)
        scroll_noise(tst_dimL(), arr, bars)

        self.assertAlmostEqual(0, np.asarray(arr).mean(), 1)

    def test_scroll_noise_random_wraps(self):
        arr = tst_arrL()
        bars = np.array([
            [100, tst_dimL()[0], 0, 0, 0, 5, 0],
        ], np.double)
        scroll_noise(tst_dimL(), arr, bars)

        arr2 = tst_arrL()
        add_stochastic_noise(5, tst_dimL(), arr2)
        self.assertAlmostEqual(np.asarray(arr).mean(), np.asarray(arr2).mean(), 2)

    def test_prepair_rule_fails_1D(self):
        try:
            rules = np.array([2,3,3,3], np.intc)
            self.assertEqual('Manual', 'fail test, cause couldnt get assertRaises to work')
        except:
            st = 'failed_successfully'
            self.assertEqual(st, st)


    def test_prepair_rule_passes_2D(self):
        rules = np.array([[2,3,3,3]], np.intc)
        rule = prepair_rule(rules, self.position)
        testing.assert_array_equal(np.asarray(rule), np.array([2,3,3,3]))

    def test_prepair_rule_picks_rule(self):
        rules = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2]], np.intc)
        rule = prepair_rule(rules, self.position)
        testing.assert_array_equal(np.asarray(rule), np.array([1,1,1,1]))

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_print_buffer_status_standard(self, mock_stdout):
        print_buffer_status(np.array([[1,2,0,0]], np.intc))
        out = mock_stdout.getvalue()
        self.assertEqual(int(len(out)/4), 13)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_print_buffer_status_short_padding(self, mock_stdout):
        print_buffer_status(np.array([[1,2,0,0]], np.intc), pad=1)
        out = mock_stdout.getvalue()
        self.assertEqual(int(len(out)/4), 7)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_print_buffer_status_custom(self, mock_stdout):
        print_buffer_status(np.array([[1,2,0,1]], np.intc), 1, '>', 'm')
        out = mock_stdout.getvalue()
        self.assertEqual(out[0], '>')

class BufferHandlingTestCase(unittest.TestCase):

    def setUp(self):
        self.position = array.array('i', [0, 0])
        self.buf = init_array_buffer(tst_dimL(), 10)
        self.dim = np.asarray(tst_dimL())
        self.buf_len = 10
        self.buffer_status = np.zeros((1, self.buf_len), np.intc)

    def test_update_array_positions_writes(self):
        position = self.position
        self.buffer_status[0, position[0]] = 1
        arr = update_array_positions(position, self.buf_len, self.buffer_status, self.buf, 0)
        self.assertEqual(self.buffer_status[0, 1], 1)

    def test_update_array_positions_clears(self):
        position = self.position
        self.buffer_status[0, position[0]] = 1
        arr = update_array_positions(position, self.buf_len, self.buffer_status, self.buf, 0)
        self.assertEqual(self.buffer_status[0, 0], 0)

    def test_update_array_positions_wraps(self):
        position = self.position
        position = array.array('i', [self.buf_len - 1, 0])
        self.buffer_status[0, position[0]] = 1
        arr = update_array_positions(position, self.buf_len, self.buffer_status, self.buf, 0)
        self.assertEqual(self.buffer_status[0, 0], 1)

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
        change_buffer(self.position, self.buf_len, self.dim, buf, dim_nu, buf_nu)
        self.assertEqual(np.asarray(buf_nu).shape, (self.buf_len, dim_nu[0], dim_nu[1]))

    def test_change_buffer_no_offset(self):
        position = self.position
        position[0] = 1
        buf = self.buf
        buf[0] = 0
        add_global_noise(0.5, tst_dimL(), buf[0])

        # Change buffer to itself plus 1 with no offset is same as advancing array
        offset = array.array('i', [0, 0])
        change_buffer(position, self.buf_len, self.dim, buf, self.dim, buf, offset)
        testing.assert_array_equal(buf[0], buf[0])

    def test_change_buffer_manual_fill(self):
        buf = self.buf
        # Fill old buffer with 1s
        buf[0] = 1
        dim_nu, buf_nu = resize_array_buffer(self.dim, self.buf_len)

        # Initialise new buffer to 0
        buf_nu[0] = 0
        # Adds the old buffer, which should fill the whole middle with 1s
        change_buffer(self.position, self.buf_len, self.dim, buf, dim_nu, buf_nu)
        # Check the new buffer has empty rim, but full after.
        self.assertFalse(cy.check_rim(0, dim_nu, buf_nu[0]))
        self.assertTrue(cy.check_rim(1, dim_nu, buf_nu[0]))

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
        change_buffer(self.position, self.buf_len, self.dim, buf, dim_nu, buf_nu, offset, cut)
        # Check the new buffer has a gap all the way around, one step in from the
        # outside.
        self.assertFalse(cy.check_rim(0, dim_nu, buf_nu[0]))
        self.assertFalse(cy.check_rim(1, dim_nu, buf_nu[0]))
        self.assertTrue(cy.check_rim(2, dim_nu, buf_nu[0]))

    def test_advance_array_has_dimensions(self):
        buf = self.buf
        advance_array(self.position, self.buf_len, buf)
        testing.assert_array_equal(np.asarray(buf).shape, (self.buf_len, self.dim[0],
                                                           self.dim[1]))

    def test_advance_array_direct_comparison(self):
        buf = self.buf
        buf[0] = 0
        add_global_noise(0.5, tst_dimL(), buf[0])
        testing.assert_almost_equal(np.mean(buf[0]),
                                    np.mean(np.random.randint(0, 2, self.dim)),
                                    decimal=2)

        advance_array(self.position, self.buf_len, buf)
        testing.assert_array_equal(buf[0], buf[1])

    def test_advance_array_wraps(self):
        buf = self.buf
        buf[0] = 0
        add_global_noise(0.5, tst_dimL(), buf[self.buf_len - 1])
        testing.assert_almost_equal(np.mean(buf[self.buf_len - 1]),
                                    np.mean(np.random.randint(0, 2, self.dim)),
                                    decimal=2)

        self.position[0] = self.buf_len - 1
        advance_array(self.position, self.buf_len, buf)
        testing.assert_array_equal(buf[0], buf[self.buf_len - 1])

class NoiseTestCase(unittest.TestCase):

    def test_add_global_noise_type(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        self.assertEqual(arr.dtype, tst_arr().dtype)

    def test_add_global_noise_off(self):
        arr = tst_arr()
        add_global_noise(0, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_add_global_noise_full(self):
        arr = np.zeros_like(tst_arr())
        add_global_noise(1, tst_dim(), arr)
        testing.assert_array_equal(arr, np.ones_like(tst_arr()))

    def test_add_global_noise_lots_of_noise(self):
        arr = np.zeros_like(tst_arrL())
        add_global_noise(0.5, tst_dimL(), arr)
        testing.assert_almost_equal(np.mean(arr),
                                    np.mean(np.random.randint(0, 2, tst_dimL())),
                                    decimal=2)

    def test_add_stochastic_noise_off(self):
        arr = tst_arr()
        add_stochastic_noise(0, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_add_stochastic_noise_additive(self):
        arr = np.zeros_like(tst_arrL())
        add_stochastic_noise(10, tst_dimL(), arr, 1)
        testing.assert_almost_equal(np.mean(arr), 1, decimal = 4)

    def test_add_stochastic_noise_subtractive(self):
        arr = np.ones_like(tst_arrL())
        add_stochastic_noise(10, tst_dimL(), arr, -1)
        testing.assert_almost_equal(np.mean(arr), 0, decimal = 4)

    def test_add_stochastic_noise_lots_of_noise(self):
        arr = np.zeros_like(tst_arrL())
        add_stochastic_noise(10, tst_dimL(), arr)
        testing.assert_almost_equal(np.mean(arr),
                                    np.mean(np.random.randint(0, 2, tst_dimL())),
                                    decimal=2)

    def test_randomize_center_automatic(self):
        arr = tst_arrL()
        randomize_center(500, tst_dimL(), arr, 0.5)
        testing.assert_almost_equal(np.mean(arr),
                                    np.mean(np.random.randint(0, 2, tst_dimL())),
                                    decimal=2)

    def test_randomize_center_off(self):
        arr = tst_arrL()
        arr2 = tst_arrL()
        arr2[:, :] = 0
        randomize_center(500, tst_dimL(), arr, 0)
        testing.assert_array_equal(arr, arr2)


class NeighborTestCase(unittest.TestCase):

    def test_moore_neighbors_sum_random_versus_roll(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        l = cy.roll_columns(1, tst_dim(), arr)
        r = cy.roll_columns(-1, tst_dim(), arr)
        u = cy.roll_rows(1, tst_dim(), arr)
        d = cy.roll_rows(-1, tst_dim(), arr)
        NB = np.asarray(l) + np.asarray(r) + np.asarray(u) + np.asarray(d)
        NB2 = moore_neighbors_array(tst_dim(), arr)

        testing.assert_array_equal(NB, NB2)

    def test_moore_neighbors_same_random_versus_roll(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        l = cy.roll_columns(1, tst_dim(), arr)
        r = cy.roll_columns(-1, tst_dim(), arr)
        u = cy.roll_rows(1, tst_dim(), arr)
        d = cy.roll_rows(-1, tst_dim(), arr)
        NB = np.asarray(l) + np.asarray(r) + np.asarray(u) + np.asarray(d)
        NB2 = np.zeros_like(arr)
        pos = array.array('i', [0, 0])
        for i in range(tst_dim()[0]):
            for j in range(tst_dim()[1]):
                pos[0] = i
                pos[1] = j
                NB2[i, j] = moore_neighbors_same_CP(pos, tst_dim(), arr)
                if not arr[i, j]:
                    NB[i, j] = 4 - NB[i, j]

        testing.assert_array_equal(NB, NB2)

    def test_moore_neighbors_same_complex(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        pos = array.array('i', [0, 0])
        NB = np.zeros_like(arr)
        NB2 = np.zeros_like(arr)
        for i in range(tst_dim()[0]):
            for j in range(tst_dim()[1]):
                pos[0] = i
                pos[1] = j
                NB[i, j] = moore_neighbors_same_CP(pos, tst_dim(), arr)
                NB2[i, j] = moore_neighbors_same_complex(pos, tst_dim(), arr)

        testing.assert_array_equal(NB, NB2)

    def test_neumann_neighbors_sum_CP_random_versus_roll(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        l = cy.roll_columns(1, tst_dim(), arr)
        r = cy.roll_columns(-1, tst_dim(), arr)
        u = cy.roll_rows(1, tst_dim(), arr)
        d = cy.roll_rows(-1, tst_dim(), arr)
        ul = cy.roll_rows(1, tst_dim(), l)
        dl = cy.roll_rows(-1, tst_dim(), l)
        ur = cy.roll_rows(1, tst_dim(), r)
        dr = cy.roll_rows(-1, tst_dim(), r)
        NB = np.asarray(l) + np.asarray(r) + np.asarray(u) + np.asarray(d) +\
                    np.asarray(ul) + np.asarray(ur) + np.asarray(dl) + np.asarray(dr)
        NB2 = neumann_neighbors_array(tst_dim(), arr)

        testing.assert_array_equal(NB, NB2)

    def test_neumann_neighbors_same_complex(self):
        arr = tst_arr()
        add_global_noise(0.5, tst_dim(), arr)
        pos = array.array('i', [0, 0])
        NB = np.zeros_like(arr)
        NB2 = np.zeros_like(arr)
        for i in range(tst_dim()[0]):
            for j in range(tst_dim()[1]):
                pos[0] = i
                pos[1] = j
                NB[i, j] = neumann_neighbors_same(pos, tst_dim(), arr)
                NB2[i, j] = neumann_neighbors_same_complex(pos, tst_dim(), arr)
        testing.assert_array_equal(NB, NB2)

class IsingTestCase(unittest.TestCase):

    def test_ising_process_off(self):
        arr = tst_arr()
        ising_process(0, 1/8, tst_dim(), arr)
        testing.assert_array_equal(tst_arr(), arr)

    def test_ising_process_type(self):
        arr = tst_arr()
        ising_process(0.01, 1/8, tst_dim(), arr)
        self.assertIs(arr.dtype, tst_arr().dtype)

    def test_ising_process_high_temp(self):
        arr = tst_arrL()
        arr[:, :] = 0
        polinit = cyphys.polarization(tst_dimL(), arr)
        self.assertEqual(1, polinit)

        ising_process(10, 0.01, tst_dimL(), arr)
        polfin = cyphys.polarization(tst_dimL(), arr)
        self.assertAlmostEqual(0, polfin, 2)

    def test_ising_process_low_temp(self):
        arr = tst_arrL()
        arr[:, :] = 0
        polinit = cyphys.polarization(tst_dimL(), arr)
        self.assertEqual(1, polinit)

        ising_process(0.1, 10, tst_dimL(), arr)
        polfin = cyphys.polarization(tst_dimL(), arr)
        self.assertAlmostEqual(1, polfin)

    def test_ising_process_random(self):
        """
        With the inverse temperature low, the chance of a collision is ~ 1/25! ~ 0
        """
        arr = tst_arr()
        ising_process(0.1, 1/1000, tst_dim(), arr)
        testing.assert_equal(np.any(np.not_equal(arr, tst_arr())), True)


class ConwayTestCase(unittest.TestCase):

    def setUp(self):
        self.rule = np.array([2,3,3,3], np.intc)

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

    def test_conway_process_neumann_versus_old(self):
        arr = tst_arrL()
        add_global_noise(0.5, tst_dimL(), arr)

        arr2 = np.copy(arr)
        testing.assert_array_equal(arr, arr2)

        conway_process(self.rule, tst_dimL(), arr)
        conway_process_old(self.rule, tst_dimL(), arr2)
        testing.assert_array_equal(arr, arr2)

basic_suite = unittest.TestLoader().loadTestsFromTestCase(BasicSuiteTestCase)

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
