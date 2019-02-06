import array
import numpy as np
import time
import operator
import regex as re
import contextlib
import unittest

from functools import partial

from numpy.core import(
     float32, empty, arange, array_repr, ndarray, isnat, array)

from Cfuncs import *
from Pfuncs import *
from PHifuncs import *

debug = True


def tst_arr():
    """
    Creates the following array:
        [00000,
        00000,
        01100,
        01100,
        00000]
    and returns a memoryview to it for the rest of the tests.

    :return:        (pointer) arr
    """
    arr = np.zeros([5,5], np.intc)
    arr[2:4,1:3] = 1
    return arr

def tst_dim():
    return memoryview(array.array('i', [5, 5]))

class ArrayRollTestCase(unittest.TestCase):

    def test_roll_columns_forward(self):
        arrout = roll_columns(1, tst_dim(), tst_arr())
        arrout = roll_columns(1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_back(self):
        arrout = roll_columns(-1, tst_dim(), tst_arr())
        arrout = roll_columns(-1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_forward(self):
        arrout = roll_rows(1, tst_dim(), tst_arr())
        arrout = roll_rows(1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_back(self):
        arrout = roll_rows(-1, tst_dim(), tst_arr())
        arrout = roll_rows(-1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))

    def test_roll_columns_pointer_forward(self):
        arrout = tst_arr()
        roll_columns_pointer(1, tst_dim(), arrout)
        roll_columns_pointer(1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=1))

    def test_roll_columns_pointer_back(self):
        arrout = tst_arr()
        roll_columns_pointer(-1, tst_dim(), arrout)
        roll_columns_pointer(-1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=1))

    def test_roll_rows_pointer_forward(self):
        arrout = tst_arr()
        roll_rows_pointer(1, tst_dim(), arrout)
        roll_rows_pointer(1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), 2, axis=0))

    def test_roll_rows_pointer_back(self):
        arrout = tst_arr()
        roll_rows_pointer(-1, tst_dim(), arrout)
        roll_rows_pointer(-1, tst_dim(), arrout)
        assert_array_equal(arrout, np.roll(tst_arr(), -2, axis=0))


class ArrayRollSpeedTestCase(unittest.TestCase):

    def test_roll_columns_speed(self):
        print('WARNING: passing.')

    def test_roll_rows_speed(self):
        print('WARNING: passing.')

    def test_roll_columns_pointer_speed(self):
        print('WARNING: passing.')

    def test_roll_rows_pointer_speed(self):
        print('WARNING: passing.')


class ArrayCheckTestCase(unittest.TestCase):

    def test_sum_rim(self):
        self.assertEqual(sum_rim(0, tst_dim(), tst_arr()), 0)
        self.assertEqual(sum_rim(1, tst_dim(), tst_arr()), 4)

    def test_check_rim(self):
        self.assertFalse(check_rim(0, tst_dim(), tst_arr()))
        self.assertTrue(check_rim(1, tst_dim(), tst_arr()))


class ArrayEditTestCase(unittest.TestCase):

    def set_bounds(self):
        print('WARNING: passing.')

    def set_bounds_speed(self):
        print('WARNING: passing.')

    def test_create_box(self):
        arr = tst_arr()
        create_box(1, 3, 1, 3, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1:4,1:4] = 1

        assert_array_equal(arr2, arr)

    def test_set_points(self):
        points = np.array([[1,1],[2,2]], np.intc)
        arr = tst_arr()
        set_points(points, tst_dim(), arr)

        arr2 = tst_arr()
        arr2[1,1] = 1
        arr2[2,2] = 1

        assert_array_equal(arr2, arr)

    def test_fill_bounds(self):
        arr = tst_arr()
        fill_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 1
        arr2[-1, :] = 1
        arr2[:, 0] = 1
        arr2[:, -1] = 1

        assert_array_equal(arr2, arr)

    def test_clear_bounds(self):
        arr = tst_arr()
        clear_bounds(tst_dim(), arr)

        arr2 = tst_arr()
        arr2[0, :] = 0
        arr2[-1, :] = 0
        arr2[:, 0] = 0
        arr2[:, -1] = 0

        assert_array_equal(arr2, arr)

    def test_fill_columns(self):
        arr = tst_arr()
        fill_columns(0, 5, tst_dim(), arr)
        assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_columns(self):
        arr = tst_arr()
        clear_columns(0, 5, tst_dim(), arr)
        assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_fill_rows(self):
        arr = tst_arr()
        fill_rows(0, 5, tst_dim(), arr)
        assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_clear_rows(self):
        arr = tst_arr()
        clear_rows(0, 5, tst_dim(), arr)
        assert_array_equal(np.zeros_like(tst_arr()), arr)

    def test_replace_rows(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        replace_rows(0, 5, nu, tst_dim(), arr)
        assert_array_equal(np.ones_like(tst_arr()), arr)

    def test_replace_columns(self):
        arr = tst_arr()
        nu = np.ones(5, np.intc)
        replace_columns(0, 5, nu, tst_dim(), arr)
        assert_array_equal(np.ones_like(tst_arr()), arr)

# Stole this from numpys tests, should be handy
def assert_array_compare(comparison, x, y, err_msg='', verbose=True,
                         header='', precision=6, equal_nan=True,
                         equal_inf=True):
    __tracebackhide__ = True  # Hide traceback for py.test
    from numpy.core import array, array2string, isnan, inf, bool_, errstate

    x = array(x, copy=False, subok=True)
    y = array(y, copy=False, subok=True)

    # original array for output formating
    ox, oy = x, y

    def isnumber(x):
        return x.dtype.char in '?bhilqpBHILQPefdgFDG'

    def istime(x):
        return x.dtype.char in "Mm"

    def func_assert_same_pos(x, y, func=isnan, hasval='nan'):
        """Handling nan/inf.

        Combine results of running func on x and y, checking that they are True
        at the same locations.

        """
        x_id = func(x)
        y_id = func(y)
        # We include work-arounds here to handle three types of slightly
        # pathological ndarray subclasses:
        # (1) all() on `masked` array scalars can return masked arrays, so we
        #     use != True
        # (2) __eq__ on some ndarray subclasses returns Python booleans
        #     instead of element-wise comparisons, so we cast to bool_() and
        #     use isinstance(..., bool) checks
        # (3) subclasses with bare-bones __array_function__ implemenations may
        #     not implement np.all(), so favor using the .all() method
        # We are not committed to supporting such subclasses, but it's nice to
        # support them if possible.
        if bool_(x_id == y_id).all() != True:
            msg = build_err_msg([x, y],
                                err_msg + '\nx and y %s location mismatch:'
                                % (hasval), verbose=verbose, header=header,
                                names=('x', 'y'), precision=precision)
            raise AssertionError(msg)
        # If there is a scalar, then here we know the array has the same
        # flag as it everywhere, so we should return the scalar flag.
        if isinstance(x_id, bool) or x_id.ndim == 0:
            return bool_(x_id)
        elif isinstance(x_id, bool) or y_id.ndim == 0:
            return bool_(y_id)
        else:
            return y_id

    try:
        cond = (x.shape == () or y.shape == ()) or x.shape == y.shape
        if not cond:
            msg = build_err_msg([x, y],
                                err_msg
                                + '\n(shapes %s, %s mismatch)' % (x.shape,
                                                                  y.shape),
                                verbose=verbose, header=header,
                                names=('x', 'y'), precision=precision)
            raise AssertionError(msg)

        flagged = bool_(False)
        if isnumber(x) and isnumber(y):
            if equal_nan:
                flagged = func_assert_same_pos(x, y, func=isnan, hasval='nan')

            if equal_inf:
                flagged |= func_assert_same_pos(x, y,
                                                func=lambda xy: xy == +inf,
                                                hasval='+inf')
                flagged |= func_assert_same_pos(x, y,
                                                func=lambda xy: xy == -inf,
                                                hasval='-inf')

        elif istime(x) and istime(y):
            # If one is datetime64 and the other timedelta64 there is no point
            if equal_nan and x.dtype.type == y.dtype.type:
                flagged = func_assert_same_pos(x, y, func=isnat, hasval="NaT")

        if flagged.ndim > 0:
            x, y = x[~flagged], y[~flagged]
            # Only do the comparison if actual values are left
            if x.size == 0:
                return
        elif flagged:
            # no sense doing comparison if everything is flagged.
            return

        val = comparison(x, y)

        if isinstance(val, bool):
            cond = val
            reduced = [0]
        else:
            reduced = val.ravel()
            cond = reduced.all()
            reduced = reduced.tolist()

        # The below comparison is a hack to ensure that fully masked
        # results, for which val.ravel().all() returns np.ma.masked,
        # do not trigger a failure (np.ma.masked != True evaluates as
        # np.ma.masked, which is falsy).
        if cond != True:
            mismatch = 100.0 * reduced.count(0) / ox.size
            remarks = ['Mismatch: {:.3g}%'.format(mismatch)]

            with errstate(invalid='ignore', divide='ignore'):
                # ignore errors for non-numeric types
                with contextlib.suppress(TypeError):
                    error = abs(x - y)
                    max_abs_error = error.max()
                    remarks.append('Max absolute difference: '
                                   + array2string(max_abs_error))

                    # note: this definition of relative error matches that one
                    # used by assert_allclose (found in np.isclose)
                    max_rel_error = (error / abs(y)).max()
                    remarks.append('Max relative difference: '
                                   + array2string(max_rel_error))

            err_msg += '\n' + '\n'.join(remarks)
            msg = build_err_msg([ox, oy], err_msg,
                                verbose=verbose, header=header,
                                names=('x', 'y'), precision=precision)
            raise AssertionError(msg)
    except ValueError:
        import traceback
        efmt = traceback.format_exc()
        header = 'error during assertion:\n\n%s\n\n%s' % (efmt, header)

        msg = build_err_msg([x, y], err_msg, verbose=verbose, header=header,
                            names=('x', 'y'), precision=precision)
        raise ValueError(msg)


def assert_array_equal(x, y, err_msg='', verbose=True):
    """
    Raises an AssertionError if two array_like objects are not equal.

    Given two array_like objects, check that the shape is equal and all
    elements of these objects are equal. An exception is raised at
    shape mismatch or conflicting values. In contrast to the standard usage
    in numpy, NaNs are compared like numbers, no assertion is raised if
    both objects have NaNs in the same positions.

    The usual caution for verifying equality with floating point numbers is
    advised.

    Parameters
    ----------
    x : array_like
        The actual object to check.
    y : array_like
        The desired, expected object.
    err_msg : str, optional
        The error message to be printed in case of failure.
    verbose : bool, optional
        If True, the conflicting values are appended to the error message.

    Raises
    ------
    AssertionError
        If actual and desired objects are not equal.

    See Also
    --------
    assert_allclose: Compare two array_like objects for equality with desired
                     relative and/or absolute precision.
    assert_array_almost_equal_nulp, assert_array_max_ulp, assert_equal

    Examples
    --------
    The first assert does not raise an exception:

    >>> np.testing.assert_array_equal([1.0,2.33333,np.nan],
    ...                               [np.exp(0),2.33333, np.nan])

    Assert fails with numerical inprecision with floats:

    >>> np.testing.assert_array_equal([1.0,np.pi,np.nan],
    ...                               [1, np.sqrt(np.pi)**2, np.nan])
    Traceback (most recent call last):
        ...
    AssertionError:
    Arrays are not equal
    Mismatch: 33.3%
    Max absolute difference: 4.4408921e-16
    Max relative difference: 1.41357986e-16
     x: array([1.      , 3.141593,      nan])
     y: array([1.      , 3.141593,      nan])

    Use `assert_allclose` or one of the nulp (number of floating point values)
    functions for these cases instead:

    >>> np.testing.assert_allclose([1.0,np.pi,np.nan],
    ...                            [1, np.sqrt(np.pi)**2, np.nan],
    ...                            rtol=1e-10, atol=0)

    """
    __tracebackhide__ = True  # Hide traceback for py.test
    assert_array_compare(operator.__eq__, x, y, err_msg=err_msg,
                         verbose=verbose, header='Arrays are not equal')

def build_err_msg(arrays, err_msg, header='Items are not equal:',
                  verbose=True, names=('ACTUAL', 'DESIRED'), precision=8):
    msg = ['\n' + header]
    if err_msg:
        if err_msg.find('\n') == -1 and len(err_msg) < 79-len(header):
            msg = [msg[0] + ' ' + err_msg]
        else:
            msg.append(err_msg)
    if verbose:
        for i, a in enumerate(arrays):

            if isinstance(a, ndarray):
                # precision argument is only needed if the objects are ndarrays
                r_func = partial(array_repr, precision=precision)
            else:
                r_func = repr

            try:
                r = r_func(a)
            except Exception as exc:
                r = '[repr failed for <{}>: {}]'.format(type(a).__name__, exc)
            if r.count('\n') > 3:
                r = '\n'.join(r.splitlines()[:3])
                r += '...'
            msg.append(' %s: %s' % (names[i], r))
    return '\n'.join(msg)


if __name__=="__main__":
    unittest.main(verbosity=2 if debug is True else 1)
