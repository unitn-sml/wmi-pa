"""
Intuitively, two mutually exclusive cases are encoded:

1) W(x,y) = x + y, x in [0,2], y in [0,2]
2) W(x,y) = 2y, x in [1,3], y in [0,2]


"""

from pysmt.shortcuts import LE, And, Bool, Implies, Ite, Not, Plus, Real, Symbol, Times
from pysmt.typing import REAL

from wmipa import WMI

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# formula definition
phi = And(
    Implies(LE(y, Real(1)), And(LE(Real(0), x), LE(x, Real(2)))),
    Implies(Not(LE(y, Real(1))), And(LE(Real(1), x), LE(x, Real(3)))),
    LE(Real(0), y),
    LE(y, Real(2)),
)

print("Formula:", phi.serialize())

# weight function definition
w = Ite(LE(y, Real(1)), Plus(x, y), Times(Real(2), y))

chi = Bool(True)

print("Weight function:", w.serialize())
print("Support:", chi.serialize())

wmi = WMI(chi, w)
print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA]:
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(mode, result, n_integrations))
