from pysmt.shortcuts import GE, LE, LT, And, Bool, Iff, Ite, Plus, Pow, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa import WMI

# variables definition
a = Symbol("A", BOOL)
x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

# formula definition
phi = Bool(True)

# weight function definition
# fmt: off
w = Plus(Ite(GE(x1, Real(0)),
             Pow(x1, Real(3)),
             Times(Real(-2), x1)),
         Ite(a,
             Times(Real(3), x2),
             Times(Real(-1), Pow(x2, Real(5)))))

chi = And(LE(Real(-1), x1), LT(x1, Real(1)),
          LE(Real(-1), x2), LT(x2, Real(1)),
          Iff(a, GE(x2, Real(0))))
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SAE4WMI]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print(
        "WMI with mode {} \t result = {}, \t # integrations = {}".format(
            mode, result, n_integrations
        )
    )
