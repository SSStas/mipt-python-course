import importlib

m1 = importlib.import_module("pkg.m1")

# reference to original value, not re-created
pi = m1.pi
_e = m1._e
__i = m1.__i

__all__ = ['pi', '_e', '__i']
