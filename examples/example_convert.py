from pysmt.shortcuts import GE, LE, LT, And, Bool, Iff, Ite, Plus, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa import WMISolver

# variables definition
a = Symbol("A", BOOL)
x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

# formula definition
# fmt: off
phi = Bool(True)

# weight function definition
w = Plus(Ite(GE(x1, Real(0)),
             Ite(GE(x1, Real((1, 2))),
                 Times(x1, Real(3)),
                 Times(Real(-2), x1)),
             Times(Real(-1), x1)

             ),
         Ite(a,
             Times(Real(3), x2),
             Times(Real(-1), Times(x2, Real(5)))))

chi = And(LE(Real(-1), x1), LT(x1, Real(1)),
          LE(Real(-1), x2), LT(x2, Real(1)),
          Iff(a, GE(x2, Real(0))))
# fmt: on

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
wmi = WMISolver(chi, w)
result, n_integrations = wmi.computeWMI(phi, {x1, x2})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
