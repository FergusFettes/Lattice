from distutils.core import setup
from Cython.Build import cythonize
from Cython.Compiler.Options import directive_defaults

directive_defaults['linetrace'] = True
directive_defaults['binding'] = True

setup(
    ext_modules = cythonize("Cyarr.pyx")
)
