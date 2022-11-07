"""
This example corresponds to Ex.3 in the paper.

"""

from pysmt.shortcuts import GE, LE, And, Bool, Iff, Ite, Real, Symbol, Times
from pysmt.typing import BOOL, REAL

from wmipa import WMI
from wmipa.integration.latte_integrator import LatteIntegrator
from wmipa.integration.symbolic_integrator import SymbolicIntegrator
from wmipa.integration.volesti_integrator import VolestiIntegrator

# from wmipa.integration.symbolic_integrator import SymbolicIntegrator

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

print("Formula:", phi.serialize())
print("Weight function:", w.serialize())
print("Support:", chi.serialize())

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SA_PA_SK]:
    for integrator in (LatteIntegrator(), VolestiIntegrator(), SymbolicIntegrator()):
        wmi = WMI(chi, w, integrator=integrator)
        result, n_integrations = wmi.computeWMI(phi, mode=mode)
        print(
            "WMI with mode {:10} (integrator: {:20})\t "
            "result = {}, \t # integrations = {}".format(
                mode, integrator.__class__.__name__, result, n_integrations
            )
        )
