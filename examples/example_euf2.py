from pysmt.shortcuts import Iff, Implies, Ite, Symbol
from pysmt.typing import BOOL, REAL

from wmpy.solvers import WMISolver

# variables definition
a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)

# formula definition
# fmt: off
phi = Implies(a | b, x >= 1) & Implies(
    a | c, x <= 2) & Ite(b, Iff(a & c, y <= 2), y <= 1)

print("Formula:", phi.serialize())

# weight function definition
w = Ite(b,
        Ite(x >= 0.5,
            x * y,
            Ite((x >= 1),
                x + 2 * y,
                2 * x + y
                )
            ),
        Ite(a | c,
            x * x * y,
            2 * x + y
            )
        )
# fmt: on

chi = (x >= 0) & (x <= 3) & (y >= 0) & (y <= 4)
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
wmi = WMISolver(chi, w)
result, n_integrations = wmi.compute(phi, {x, y})
print(
    "WMI \t result = {}, \t # integrations = {}".format(
        result, n_integrations
    )
)
