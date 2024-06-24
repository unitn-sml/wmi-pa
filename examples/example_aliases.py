from pysmt.shortcuts import GE, LE, And, Bool, Equals, Plus, Real, Symbol
from pysmt.typing import REAL

from wmipa import WMISolver

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

phi = Bool(True)

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
wmi = WMISolver(chi, w)
result, n_integrations = wmi.computeWMI(phi, {x, y})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
