
"""
This example corresponds to Ex.4 in the paper.

"""

from sys import path
path.insert(0, "../src/")

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmi import WMI
from weights import Weights

# variables definition
a = Symbol("A", BOOL)
x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

# formula definition
phi = Bool(True)

print "Formula:", serialize(phi)

# weight function definition
w = Plus(Ite(GE(x1, Real(0)),
             Pow(x1, Real(3)),
             Times(Real(-2), x1)),
         Ite(a,
             Times(Real(3), x2),
             Times(Real(-1), Pow(x2, Real(5)))))

chi = And(LE(Real(-1), x1), LT(x1, Real(1)),
          LE(Real(-1), x2), LT(x2, Real(1)),
          Iff(a, GE(x2, Real(0))))

print "Weight function:", serialize(w)
print "Support:", serialize(chi)

weights = Weights(w, chi)
chi = And(chi, weights.labelling)

wmi = WMI()
print
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA]:
    result, n_integrations = wmi.compute(And(phi, chi), weights, mode)
    print "WMI with mode {} \t result = {}, \t # integrations = {}".format(mode, result, n_integrations)

        
