from pysmt.shortcuts import GE, LE, And, Bool, Iff, Implies, Ite, Not, Or, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa.solvers import AllSMTSolver

# variables definition
a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)

# formula definition
# fmt: off
phis = [Bool(True), Iff(a, Bool(True)), LE(x, Real(3))]

# weight function definition
w = Ite(a, x, Times(Real(2), x))

chi = And(Or(a, b, c),
          GE(x, Real(-5)), LE(x, Real(5)),
          Implies(a, GE(x, Real(0))),
          Implies(b, GE(x, Real(2))),
          Or(Not(c), LE(x, Real(3))))
# Implies(c, LE(x, Real(3))))
# fmt: on

print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()

for phi in phis:
    wmi = AllSMTSolver(chi, w)
    result, n_integrations = wmi.compute(phi, {x})
    print("Query: {}".format(phi.serialize()))
    print(
        "WMI \t result = {}, \t # integrations = {}".format(
            result, n_integrations
        )
    )
