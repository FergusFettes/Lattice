from distutils.core import setup, Extension
from Cython.Build import cythonize

compiler_directives = {}
define_macros = []

compiler_directives['profile'] = True
compiler_directives['linetrace'] = True
compiler_directives['binding'] = True

define_macros.append(('CYTHON_TRACE', '1'))

setup(
    ext_modules = cythonize(Extension(
        "Cyarr",
        sources = ["Cyarr.pyx"],
        define_macros = define_macros),
        compiler_directives = compiler_directives)
)
