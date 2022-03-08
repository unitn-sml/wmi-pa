
"""
This example corresponds to Ex.4 in the paper.

"""

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# formula definition
phi = Implies(a | b, x >= 1) & Implies(
    a | c, x <= 2) & Ite(b, Iff(a & c, y <= 2), y <= 1)

print("Formula:", serialize(phi))

# weight function definition
w = Ite(b,
        Ite(x >= 0.5,
            x * y,
            Ite((x >= 1),
                x + 2*y,
                2*x + y
                )
            ),
        Ite(a | c,
            x * x * y,
            2 * x + y
            )
        )

chi = (x >= 0) & (x <= 3) & (y >= 0) & (y <= 4)
print("Weight function:", serialize(w))
print("Support:", serialize(chi))

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
