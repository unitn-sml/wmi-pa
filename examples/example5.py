
"""
This example corresponds to Ex.3 in the paper.

"""

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL, INT
from wmipa import WMI

# variables definition
a = Symbol("A", BOOL)
x = Symbol("x", REAL)
i = Symbol("i", INT)

# formula definition
phi = Bool(True)

print("Formula:", serialize(phi))

# weight function definition
w = Ite(GE(i, Int(5)),
        x,
        Times(Real(-1), x))

chi = And(Iff(a, GE(x, Real(0))),
          GE(x, Real(-1)), LE(x, Real(1)),
          GE(i, Int(0)), LE(i, Int(10)))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

wmi = WMI(chi, w)

print()
for mode in [WMI.MODE_BC, WMI.MODE_ALLSMT, WMI.MODE_PA]:
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(mode, result, n_integrations))
        
