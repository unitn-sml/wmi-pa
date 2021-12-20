from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)
A = Symbol("A", BOOL)

phi = Bool(True)

chi = And(
    GE(x, Real(0)),
    LE(x, Real(2)),
    GE(y, Real(0)),
    LE(y, Real(3)),
)

w = Ite(x >= 1,
        Ite(y >= 1,
            x*y,
            2*(x*y)
            ),
        Ite(y >= 2,
            3*(x*y),
            4*(x*y)
            ),
        )

print("Formula:", serialize(phi))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))


print()
for mode in [WMI.MODE_PA, WMI.MODE_PA_NO_LABEL, WMI.MODE_PA_EUF]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))