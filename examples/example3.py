
"""This example corresponds to the motivating example in the IJCAI poster.
It shows a simple case in which WMI-AllSMT performs more integrations
than necessary.

Intuitively, two mutually exclusive cases are encoded:

1) W(x,y) = x + y, x in [0,2], y in [0,2]
2) W(x,y) = 2y, x in [1,3], y in [0,2]


"""

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# formula definition
phi = And(Implies(LE(y, Real(1)), And(LE(Real(0), x), LE(x, Real(2)))),
          Implies(Not(LE(y, Real(1))), And(LE(Real(1), x), LE(x, Real(3)))),
          LE(Real(0), y), LE(y, Real(2)))

print("Formula:", serialize(phi))

# weight function definition
w = Ite(LE(y, Real(1)),
        Plus(x, y),
        Times(Real(2), y))

chi = Bool(True)

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

wmi = WMI(chi, w)
print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA,  WMI.MODE_SA_PA_BOOL]:
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
