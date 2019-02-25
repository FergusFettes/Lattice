from distutils.core import setup, Extension
from Cython.Build import cythonize

compiler_directives = {}
define_macros = []

#compiler_directives['profile'] = True
#compiler_directives['linetrace'] = True
#compiler_directives['binding'] = True
compiler_directives['language_level'] = 3

#define_macros.append(('CYTHON_TRACE', '1'))

setup(
    ext_modules = cythonize(Extension(
        "Cyarr",
        sources = ["Cyarr.pyx"],
        extra_compile_args=['-fopenmp'],
        extra_link_args=['-fopenmp'],
        define_macros = define_macros),
        annotate = True,
        compiler_directives = compiler_directives)
)
