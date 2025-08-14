from pysmt.shortcuts import LE, And, Bool, Implies, Ite, Not, Plus, Real, Symbol, Times
from pysmt.typing import REAL

from wmipa.solvers import AllSMTSolver

# variables definition
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# formula definition
# fmt: off
phi = And(Implies(LE(y, Real(1)), And(LE(Real(0), x), LE(x, Real(2)))),
          Implies(Not(LE(y, Real(1))), And(LE(Real(1), x), LE(x, Real(3)))),
          LE(Real(0), y), LE(y, Real(2)))

# weight function definition
w = Ite(LE(y, Real(1)),
        Plus(x, y),
        Times(Real(2), y))

chi = Bool(True)
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
wmi = AllSMTSolver(chi, w)
result, n_integrations = wmi.compute(phi, {x, y})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
