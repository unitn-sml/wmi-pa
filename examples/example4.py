
"""
This example corresponds to Ex.3 in the paper.

"""

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)

# formula definition
phis = [Bool(True), Iff(a, Bool(True)), LE(x, Real(3))]

# weight function definition
w = Ite(a, x, Times(Real(2), x))

chi = And(GE(x, Real(-5)), LE(x, Real(5)),
          Implies(a, GE(x, Real(0))),
          Implies(b, GE(x, Real(2))),
          Implies(c, LE(x, Real(3))))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

wmi = WMI(chi, w)

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA]:
    for phi in phis:
        result, n_integrations = wmi.computeWMI(phi, mode=mode)
        print("Query: {}".format(serialize(phi)))
        print("WMI with mode {} \t result = {}, \t # integrations = {}".format(mode, result, n_integrations))
        
