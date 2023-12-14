from pysmt.shortcuts import GE, LE, LT, And, Bool, Iff, Ite, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

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
# fmt: off
phi = Bool(True)

print("Formula:", phi.serialize())

# weight function definition
w = Ite(a,
        Times(
            Ite(b,
                x1,
                2 * x1
                ),
            Ite(c,
                x2,
                2 * x2
                )
        ),
        Times(
            Ite(d,
                3 * x1,
                4 * x1
                ),
            Ite(e,
                3 * x2,
                4 * x2
                )
        )
        )

chi = And(LE(Real(0), x1), LT(x1, Real(1)),
          LE(Real(0), x2), LT(x2, Real(2)),
          Iff(a, GE(x2, Real(1))))
# fmt: on

print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SA_PA_SK]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print(
        "WMI with mode {} \t result = {}, \t # integrations = {}".format(
            mode, result, n_integrations
        )
    )
