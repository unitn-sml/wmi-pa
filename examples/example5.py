from pysmt.shortcuts import GE, LE, And, Bool, Iff, Ite, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa.solvers import WMISolver

# variables definition
a = Symbol("A", BOOL)
x = Symbol("x", REAL)
i = Symbol("i", REAL)

# formula definition
# fmt: off
phi = Bool(True)

# weight function definition
w = Ite(GE(i, Real(5)),
        x,
        Times(Real(-1), x))

chi = And(Iff(a, GE(x, Real(0))),
          GE(x, Real(-1)), LE(x, Real(1)),
          GE(i, Real(0)), LE(i, Real(10)))
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
wmi = WMISolver(chi, w)
result, n_integrations = wmi.compute(phi, {x, i})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
