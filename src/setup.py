import sys
from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(sys.argv[3], annotate=False)
)
