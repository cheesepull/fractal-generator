# setup.py
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import sys

if sys.platform == "win32":
    openmp_compile = ["/openmp"]
    openmp_link    = []          # MSVC сам линкует vcomp
else:
    openmp_compile = ["-fopenmp"]
    openmp_link    = ["-fopenmp"]

ext = Extension(
    "fkernel",
    sources=["fkernel.pyx"],
    include_dirs=[np.get_include()],
    extra_compile_args=["-O3", "-ffast-math", "-march=native"] + openmp_compile,
    extra_link_args=openmp_link,
)

setup(
    name="fkernel",
    ext_modules=cythonize(
        [ext],
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    ),
)