


from distutils.core import setup
from Cython.Build import cythonize
 
setup(
  name = 'any words.....',
  ext_modules = cythonize(["Binder.py","GUI.py"      ]
  ),
)