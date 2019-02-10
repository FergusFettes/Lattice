import sys
from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("Cyphys.pyx", annotate=True)
)
