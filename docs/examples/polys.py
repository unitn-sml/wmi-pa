import numpy as np
from pysmt.shortcuts import *

from wmipa.core import Polytope, Polynomial

#### CONSTRUCTION

x = Symbol("x", REAL)
y = Symbol("y", REAL)

env = get_env()

# the continuous domain
domain = [x, y]

# a collection of inequalities
inequalities = [LE(Real(0), x), LE(Real(0), y), LE(Plus(x, y), Real(1))]
polytope = Polytope(inequalities, domain, env=get_env())

# a pysmt term equivalent to the (canonical) polynomial
# 2x^2 + 3xy + 4
expression = Times(
    Real(2),
    Plus(
        Pow(x, Real(2)),
        Times(Real(3 / 2), x, y),
        Real(2),
    ),
)
polynomial = Polynomial(expression, domain, env=get_env())


#### NUMPY CONVERSIONS

# a poltope can be converted into the numpy arrays A x </<= b (strictness information is discarded)
A, b = polytope.to_numpy()

print(A.astype(float))
# >>> [[-1.  0.]
#      [ 0. -1.]
#      [ 1.  1.]]

print(b.astype(float))
# >>> [0. 0. 1.]

# a polynomial can be converted into a function taking numpy arrays as input
func = polynomial.to_numpy()

input_vec = np.array([[2, 3], [1 / 2, 0]])  # shape[1] has to be equal to len(domain)!
print(func(input_vec))
# >>> [30.0 4.5]

#### PYSMT CONVERSIONS

# this formula is equivalent to And(*inequalities)
formula = polytope.to_pysmt()

# this term is equivalent to expression (but in canonical form)
expression2 = polynomial.to_pysmt()
