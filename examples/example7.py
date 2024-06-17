from pysmt.shortcuts import GE, LE, And, Bool, Ite, Or, Real, Symbol
from pysmt.typing import BOOL, REAL

from wmipa import WMI

# variables definition
A = Symbol("A", BOOL)
B = Symbol("B", BOOL)
C = Symbol("C", BOOL)
D = Symbol("D", BOOL)
x = Symbol("x", REAL)
i = Symbol("i", REAL)

# formula definition
phi = Bool(True)

# weight function definition
# w = Ite(And(A, Or(A, B, GE(x, Real(0))), Or(B, GE(x, Real(1))), GE(Plus(x, i), Real(0))), Real(1.0), Real(2.0))
# fmt: off
w = Ite(
    And(A, Or(A, B, GE(x, Real(0))), Or(B, GE(x, Real(1)))),
    Real(1.0),
    Real(2.0)
)

chi = And(GE(x, Real(-2)), LE(x, Real(2)),
          GE(i, Real(-2)), LE(i, Real(2)))
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
for mode in [WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SAE4WMI]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print(
        "WMI with mode {} \t result = {}, \t # integrations = {}".format(
            mode, result, n_integrations
        )
    )
