from pysmt.shortcuts import GE, LE, And, Bool, Equals, Plus, Real, Symbol
from pysmt.typing import REAL

from wmipa import WMI

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# ---- chi correct (6.0) ----
# fmt: off
chi = And(
    GE(x, Real(0)),
    Equals(y, Plus(x, Real(-2))),
    LE(y, Real(4))
)

# ---- chi incorrect (0.0) ----
# chi = And(
#     GE(x, Real(0)),
#     LE(y, Plus(x, Real(-2))),
#     GE(y, Plus(x, Real(-2))),
#     LE(y, Real(4))
# )

# ---- chi error -----
# chi = And(
#     GE(x, Real(0)),
#     Equals(Times(Real(1), y), Plus(x, Real(-2))),
#     LE(y, Real(4))
# )

# fmt: on

w = y

wmi = WMI(chi, w)

phi = Bool(True)

print("Formula:", phi.serialize())
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
