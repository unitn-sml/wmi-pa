from pysmt.shortcuts import GE, LE, And, Bool, Ite, Or, Real, Symbol
from pysmt.typing import BOOL, REAL

from wmpy.solvers import WMISolver

# variables definition
A = Symbol("A", BOOL)
B = Symbol("B", BOOL)
C = Symbol("C", BOOL)
D = Symbol("D", BOOL)
x = Symbol("x", REAL)

# formula definition
# fmt: off
phi = Bool(True)

# weight function definition
# w = Ite(And(A, Or(A, B, GE(x, Real(0))), Or(B, GE(x, Real(1))), GE(Plus(x, i), Real(0))), Real(1.0), Real(2.0))
# w = Ite(And(A, Or(A, B, GE(x, Real(0))), Or(B, GE(x, Real(1)))), Real(1.0), Real(2.0))
# w = Ite(Or(And(A, B), And(C,D)), Real(1.0), Real(2.0))
w = Ite(
        And(Or(A, B), Or(C, D)),
        Real(1.0),
        Real(2.0)
        )

chi = And(GE(x, Real(-2)), LE(x, Real(2)))
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()

wmi = WMISolver(chi, w)
result, n_integrations = wmi.compute(phi, {x})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
