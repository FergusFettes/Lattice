from Cyarr import *
import numpy as np

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
    arr = np.zeros(tst_dimM(), np.intc)
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

def tst_arrX():
    """
    Creates a large array
    :return:        (pointer) arr
    """
    arr = np.zeros(tst_dimX(), np.intc)
    arr[1:3,1:3] = 1
    return arr

def tst_dimX():
    return memoryview(array.array('i', [1000, 1000]))

beatnum = 0
losenum = 0

print('roll_columns vs. numpy.roll')
print('100x:')
a = %timeit -o roll_columns(-1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_columns(-1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_columns(-1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_columns vs. numpy.roll')
print('100x:')
a = %timeit -o roll_columns(1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_columns(1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_columns(1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_rows vs. numpy.roll')
print('100x:')
a = %timeit -o roll_rows(-1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_rows(-1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_rows(-1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_rows vs. numpy.roll')
print('100x:')
a = %timeit -o roll_rows(1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_rows(1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_rows(1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1


print('roll_columns_pointer vs. numpy.roll')
print('100x:')
a = %timeit -o roll_columns_pointer(-1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_columns_pointer(-1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_columns_pointer(-1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), -1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_columns_pointer vs. numpy.roll')
print('100x:')
a = %timeit -o roll_columns_pointer(1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_columns_pointer(1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_columns_pointer(1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), 1, axis=1)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_rows_pointer vs. numpy.roll')
print('100x:')
a = %timeit -o roll_rows_pointer(-1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_rows_pointer(-1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_rows_pointer(-1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), -1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('roll_rows_pointer vs. numpy.roll')
print('100x:')
a = %timeit -o roll_rows_pointer(1, tst_dimM(), tst_arrM())
b = %timeit -o np.roll(tst_arrM(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
a = %timeit -o roll_rows_pointer(1, tst_dimL(), tst_arrL())
b = %timeit -o np.roll(tst_arrL(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
a = %timeit -o roll_rows_pointer(1, tst_dimX(), tst_arrX())
b = %timeit -o np.roll(tst_arrX(), 1, axis=0)
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1


print('\n\n')
print('clear_columns vs. python native')
print('100x:')
arr = tst_arrM()
a = %timeit -o clear_columns(0, 1, tst_dimM(), tst_arrM())
b = %timeit -o for i in range(1): arr[:, (0 + i) % tst_dimM()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('500x:')
arr = tst_arrL()
a = %timeit -o clear_columns(0, 1, tst_dimL(), tst_arrL())
b = %timeit -o for i in range(1): arr[:, (0 + i) % tst_dimL()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000x:')
arr = tst_arrX()
a = %timeit -o clear_columns(0, 1, tst_dimX(), tst_arrX())
b = %timeit -o for i in range(1): arr[:, (0 + i) % tst_dimX()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000xMULTI:')
arr = tst_arrX()
a = %timeit -o clear_columns(0, 10, tst_dimX(), tst_arrX())
b = %timeit -o for i in range(10): arr[:, (0 + i) % tst_dimX()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000xMULTI:')
arr = tst_arrX()
a = %timeit -o clear_columns(0, 100, tst_dimX(), tst_arrX())
b = %timeit -o for i in range(100): arr[:, (0 + i) % tst_dimX()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('1000xMULTIWRAP:')
arr = tst_arrX()
a = %timeit -o clear_columns(990, 100, tst_dimX(), tst_arrX())
b = %timeit -o for i in range(100): arr[:, (990 + i) % tst_dimX()[0]] = 0
me = np.mean([i/a.loops for i in a.all_runs])
num = np.mean([i/b.loops for i in b.all_runs])
if me < num: beatnum +=1
else: losenum += 1

print('Beat numpy {} times, lost {} times.'.format(beatnum, losenum))
