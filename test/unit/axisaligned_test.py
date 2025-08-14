import numpy as np
import pytest

import pysmt.shortcuts as smt

from wmipa.core import Polynomial, Polytope
from wmipa.integration import AxisAlignedWrapper

env = smt.get_env()

N = 4
variables = [smt.Symbol(f"x{i}", smt.REAL) for i in range(N)]


class DummyIntegrator:

    def integrate(self, polytope, polynomial):
        raise Exception("AxisAlignedWrapper didn't catch this.")


def hypercube(variables, sides, offsets):
    inequalities = []
    for i, var in enumerate(variables):
        inequalities.extend(
            [
                smt.LE(smt.Real(offsets[i]), var),
                smt.LE(var, smt.Real(offsets[i] + sides[i])),
            ]
        )

    return inequalities


@pytest.mark.parametrize(
    "sides, offsets",
    [
        ([1, 1, 1, 1], [0, 0, 0, 0]),
        ([1, 1, 1, 1], [-10, 6, 3, -2]),
        ([3, 7, 2, 5], [-10, 6, 3, -2]),
    ],
)
def test_axisaligned(sides, offsets):

    aa_integrator = AxisAlignedWrapper(DummyIntegrator())

    inequalities = hypercube(variables, sides, offsets)
    aa_polytope = Polytope(inequalities, variables, env)
    const_integrand = Polynomial(smt.Real(666), variables, env)

    result = aa_integrator.integrate(aa_polytope, const_integrand)
    assert result == np.prod(sides) * 666

    oblique = smt.LE(
        smt.Plus(*[var for var in variables]),
        smt.Real(float(np.sum([sides, offsets]))),
    )
    oblique_polytope = Polytope(inequalities + [oblique], variables, env)

    nonconst_integrand = Polynomial(variables[0], variables, env)

    with pytest.raises(Exception):
        result = aa_integrator.integrate(oblique_polytope, const_integrand)

    with pytest.raises(Exception):
        result = aa_integrator.integrate(aa_polytope, nonconst_integrand)
