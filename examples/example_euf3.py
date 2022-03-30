
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
d = Symbol("D", BOOL)
e = Symbol("E", BOOL)
x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

# formula definition
phi = Bool(True)

print("Formula:", serialize(phi))

# weight function definition
w = Ite(a,
        Times(
            Ite(b,
                x1,
                2*x1
                ),
            Ite(c,
                x2,
                2*x2
                )
        ),
        Times(
            Ite(d,
                3*x1,
                4*x1
                ),
            Ite(e,
                3*x2,
                4*x2
                )
        )
        )

chi = And(LE(Real(0), x1), LT(x1, Real(1)),
          LE(Real(0), x2), LT(x2, Real(2)),
          Iff(a, GE(x2, Real(1))))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA,
             WMI.MODE_SA_PA_BOOL,  WMI.MODE_SA_PA_BOOL_TA, 
             WMI.MODE_SA_PA_BOOL_TA_TA, WMI.MODE_SA_PA_SK]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
