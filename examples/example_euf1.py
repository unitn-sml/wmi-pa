from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa import WMI

# variables definition
a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
d = Symbol("D", BOOL)
e = Symbol("E", BOOL)
x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

# formula definition
phi = Bool(True)

print("Formula:", serialize(phi))

# weight function definition
w = Ite(a & (x1 >= 1.5),
        Times(
            Ite(b | (x2 >= 1),
                x1,
                2*x1
                ),
            Ite((x2 <= 1),
                Plus(
                    Ite(x2 <= 0.5, x1 * x1, x1 * x2),
                    Ite(x1 + x2 <= 1, x2 * x2, x1 * x2)
                ),
                Plus(
                    Ite(x2 <= 0.5, x1 * x1, x1 * x2),
                    Ite(x1 + x2 <= 1, x2 * x2, x1 * x2)
                )
                )
        ),
        Times(
            Ite((x2 <= 1.5),
                3*(x1*x1),
                4*(x1)
                ),
            Ite(d & (x2 + x1 >= 1),
                3*(x2*x2),
                4*(x2)
                )
        )
    )

chi = And(LE(Real(0), x1), LT(x1, Real(1)),
          LE(Real(0), x2), LT(x2, Real(2)),
          Iff(a, GE(x2, Real(1))))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

print()
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_PA_NO_LABEL, 
             WMI.MODE_PA_EUF, WMI.MODE_PA_EUF_TA, WMI.MODE_PA_WA, WMI.MODE_PA_WA_TA]:
    wmi = WMI(chi, w)
    result, n_integrations = wmi.computeWMI(phi, mode=mode, cache=-1)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
