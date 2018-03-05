
"""
This example corresponds to Ex.3 in the paper.

"""

from sys import path
path.insert(0, "../src/")

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmi import WMI
from weights import Weights

# variables definition
a = Symbol("A", BOOL)
x = Symbol("x", REAL)

# formula definition
phi = And(Iff(a, GE(x, Real(0))),
          GE(x, Real(-1)),
          LE(x, Real(1)))

print "Formula:", serialize(phi)

# weight function definition
w = Ite(GE(x, Real(0)),
        x,
        Times(Real(-1), x))

chi = Bool(True)

print "Weight function:", serialize(w)
print "Support:", serialize(chi)

weights = Weights(w, chi)
chi = And(chi, weights.labelling)

wmi = WMI()
print
for mode in [WMI.MODE_ALLSMT, WMI.MODE_PA]:
    result, n_integrations = wmi.compute(And(chi,phi), weights, mode)
    print "WMI with mode {} \t result = {}, \t # integrations = {}".format(mode, result, n_integrations)
        
