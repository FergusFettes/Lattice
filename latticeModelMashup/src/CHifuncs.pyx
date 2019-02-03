import cython

import array
import numpy as np

from libc.stdlib cimport rand, RAND_MAX
from src.Cfuncs import *
from src.Pfuncs import *

from cpython cimport array
cimport numpy as np

from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free

cdef class Array_Buffer:

    cdef int* data

    def __cinit__(self, size_t number):
        # allocate some memory (uninitialised, may contain arbitrary data)
        self.data = <int*> PyMem_Malloc(number * sizeof(int))
        if not self.data:
            raise MemoryError()

    def resize(self, size_t new_number):
        # Allocates new_number * sizeof(double) bytes,
        # preserving the current content and making a best-effort to
        # re-use the original data location.
        mem = <int*> PyMem_Realloc(self.data, new_number * sizeof(int))
        if not mem:
            raise MemoryError()
        # Only overwrite the pointer if the memory was really reallocated.
        # On error (mem is NULL), the originally memory has not been freed.
        self.data = mem

    def __dealloc__(self):
        PyMem_Free(self.data)  # no-op if self.data is NULL
