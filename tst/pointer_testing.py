cimport numpy as np
import array
from cpython cimport array

    cdef int[:, :] arr_v, arr_t           #init pointers
    arr = np.zeros([5,5], np.intc)     #init array
    arr_1 = arr                        #pointer points to array
    arr_2 = arr_1
    print('Initial array:')
    print(arr_1 == arr_2)
    print(arr)

    update(arr_1, posc([0,0]), 1)

    print('Update pointer 1:')
    print(arr_1 == arr_2)
    print(arr)

    update(arr_2, posc([1,1]), 1)

    print('Update pointer 2:')
    print(arr)

    arr2 = np.zeros([5,5], np.intc)
    arr_1 = arr2

    update(arr_2, posc([2,2]), 1)
    update(arr_1, posc([4,4]), 9)

    print('Update pointer 2 after pointer 1 reassign')
    print(arr_1 == arr_2)
    print(arr)


    arr[pos[0], pos[1]] = val


    return array.array('i', dim)
