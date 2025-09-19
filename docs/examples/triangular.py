
from sys import argv
from pysmt.shortcuts import *

from wmpy.solvers import WMISolver
from wmpy.enumeration import TotalEnumerator
from wmpy.integration import LattEIntegrator


l, u, m = map(float, argv[1:])

x = Symbol("x", REAL)

h = 2 / (u - l) # ensures a normalized distribution

a1 = h / (m - l)
b1 = -a1 * l

a2 = h / (m - u)
b2 = -a2 * u

support = And(LE(Real(l), x), LE(x, Real(u)))

linear = lambda a, b : Plus(Times(Real(a), x), Real(b))

w = Ite(LE(x, Real(m)),
        linear(a1, b1),
        linear(a2, b2),
    )

enumerator = TotalEnumerator(support, w, get_env())
integrator = LattEIntegrator()

wmi_solver = WMISolver(enumerator, integrator)

 
print(f"WMI of {serialize(w)} is:", wmi_solver.compute( Bool(True), {x})["wmi"])
   
