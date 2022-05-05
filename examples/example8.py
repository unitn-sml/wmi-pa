
"""
This example corresponds to Ex.3 in the paper.

"""

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL, INT
from wmipa import WMI

# variables definition
A = Symbol("A", BOOL)
B = Symbol("B", BOOL)
C = Symbol("C", BOOL)
D = Symbol("D", BOOL)
E = Symbol("E", BOOL)
F = Symbol("F", BOOL)
G = Symbol("G", BOOL)
H = Symbol("H", BOOL)
I = Symbol("I", BOOL)
x = Symbol("x", REAL)


# formula definition
phi = Bool(True)

print("Formula:", serialize(phi))

w = Ite(And(A,B), Ite(And(C,D), Ite(And(E,F), Real(1.0), Real(1.0)), Ite(And(F,G), Real(1.0), Real(1.0))), Ite(And(D,E), Ite(And(G,H), Real(1.0), Real(1.0)), Ite(And(H,I), Real(1.0), Real(1.0))))

chi = And(GE(x, Real(-2)), LE(x, Real(2)))

print("Weight function:", serialize(w))
print("Support:", serialize(chi))

wmi = WMI(chi, w)

print()
for mode in [WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SA_PA_SK]:
    result, n_integrations = wmi.computeWMI(phi, mode=mode)
    print("WMI with mode {} \t result = {}, \t # integrations = {}".format(
        mode, result, n_integrations))
