# now we import everything in order to avoid the "smt." clutter
from pysmt.shortcuts import *

# wmpy's design is modular
from wmpy.solvers import WMISolver

# in this example, we pair total TA enumeration...
from wmpy.enumeration import TotalEnumerator

# ...with exact integration based on the LattE integrale software
from wmpy.integration import LattEIntegrator


x = Symbol("x", REAL)
y = Symbol("y", REAL)

# the support is the formula from Example 3
support = And(
    LE(Real(0), x),
    LE(Real(0), y),
    Or(
        LE(Plus(x, y), Real(1)),
        And(GE(x, y), LE(x, Real(1))),
    ),
)

# we consider two different weights
weight1 = Real(1)
weight2 = Plus(Pow(x, Real(2)), Real(1))

for w in [weight1, weight2]:

    # solvers are designed to answer multiple queries given a pair <support, w>
    # hence, the pair is passed as a parameter to the enumerator
    enumerator = TotalEnumerator(support, w, get_env())
    integrator = LattEIntegrator()

    wmi_solver = WMISolver(enumerator, integrator)

    # we set query to true in order to compute the full WMI of <support, w>
    query = Bool(True)
    print(f"The WMI of {serialize(w)} is:", wmi_solver.compute(query, {x, y})["wmi"])

# >>> The WMI of 1.0 is: 0.75
# >>> The WMI of ((x ^ 2.0) + 1.0) is: 1.0104166666666667
