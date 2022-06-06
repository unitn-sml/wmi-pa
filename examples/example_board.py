from pysmt.shortcuts import GE, LE, And, Bool, Ite, Real, Symbol
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)
A = Symbol("A", BOOL)

# fmt: off
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
# fmt: off

print("Formula:", phi.serialize())

print("Weight function:", w.serialize())
print("Support:", chi.serialize())


print()
for mode in [WMI.MODE_PA, WMI.MODE_SA_PA]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
