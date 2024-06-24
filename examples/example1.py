from pysmt.shortcuts import GE, LE, And, Bool, Iff, Ite, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa import WMISolver
from wmipa.integration import LatteIntegrator
from wmipa.integration import VolestiIntegrator

# variables definition
a = Symbol("A", BOOL)
x = Symbol("x", REAL)

# formula definition
# fmt: off
phi = And(Iff(a, GE(x, Real(0))),
          GE(x, Real(-1)),
          LE(x, Real(1)))

# weight function definition
w = Ite(GE(3 * x, Real(0)),
        x,
        Times(Real(-1), x))
# fmt: on

chi = Bool(True)

domain = {x}

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
for integrator in (LatteIntegrator(), VolestiIntegrator()):
    wmi = WMISolver(chi, w, integrator=integrator)
    result, n_integrations = wmi.computeWMI(phi, domain)
    print(
        "WMI (integrator: {:20})\t "
        "result = {}, \t # integrations = {}".format(
            integrator.__class__.__name__, result, n_integrations
        )
    )
