try:
    from pysmt.shortcuts import PI, Exp
except ImportError:
    raise ImportError("""Couldn't import PI or Exp from pysmt.shortcuts.
Install wmipa with the extras_require option for non-linear arithmetic: 
    pip install wmipa[nra]""")
from pysmt.shortcuts import GE, LE, And, Bool, Pow, Real, Symbol, Div, Times
from pysmt.typing import REAL

from wmipa import WMI
from wmipa.integration import VolestiIntegrator

# variables definition
x = Symbol("x", REAL)

chi = And(GE(x, Real(-1)), LE(x, Real(1)))
# formula definition
# fmt: off
phi = Bool(True)

# weight function definition
w = Times(
        Div(Real(1), Pow(Real(2) * PI(), Real(1/2))),
        Exp(Div(Pow(x, Real(2)), Real(-2)))
)
# fmt: on

print("Formula:", phi.serialize())
print("Support:", chi.serialize())
print("Weight function:", w.serialize())

print()
wmi = WMI(chi, w, integrator=VolestiIntegrator())
result, n_integrations = wmi.computeWMI(phi, mode=WMI.MODE_SAE4WMI)
print(
    "WMI with mode {} \t result = {}, \t # integrations = {}".format(
        WMI.MODE_SAE4WMI, result, n_integrations
    )
)
