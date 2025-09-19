
from pysmt.shortcuts import *

from wmpy.core import Polynomial, Polytope
from wmpy.integration import RejectionIntegrator

smt_env = get_env()   
x = Symbol("x", REAL)
domain = [x]

polytope = Polytope([LE(Real(-1), x), LE(x, Real(1))], domain, smt_env) # x in [-1, 1]

const = Polynomial(Real(2), domain, smt_env)  # constant integrand: 2
linear = Polynomial(Plus(x, Real(1)), domain, smt_env)  # linear integrand: x + 1

approx_integrator = RejectionIntegrator(n_samples=100)
print(approx_integrator.integrate(polytope, const))
# >>> 4.0
print(approx_integrator.integrate(polytope, linear))
# >>> something close to 2.0

print(approx_integrator.integrate_batch([(polytope, linear), (polytope, const)]))
# >>> [something close to 2.0, 4.0]
