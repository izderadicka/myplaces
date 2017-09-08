#from distutils.core import Extension, setup
import numpy
from setuptools import setup, Extension
from Cython.Build import cythonize

setup(name='myplaces',
      version='1.0',
      description='Myplaces',
      author='ivan',
      author_email='ivan@zderadicka.eu',
      url='http://zderadicka.eu',
      install_requires=['cython>=0.23'],
      ext_modules=cythonize(Extension(name='myplaces.voronoi', sources=['myplaces/voronoi.pyx'],
                                      include_dirs=[numpy.get_include()]))
     )
