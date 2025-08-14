import numpy as np
import pytest

import pysmt.shortcuts as smt

from wmipa.core import Polynomial, Polytope
from wmipa.integration import AxisAlignedWrapper

env = smt.get_env()
np.random.seed(666)

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
                smt.LE(smt.Real(float(offsets[i])), var),
                smt.LE(var, smt.Real(float(offsets[i] + sides[i]))),
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
def test_integrate(sides, offsets):

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


@pytest.mark.parametrize(
    "sides, offsets",
    [
        ([10, 10, 10, 10], [0, 0, 0, 0]),
        ([10, 10, 10, 10], [-10, 6, 3, -2]),
        ([3, 7, 2, 5], [-10, 6, 3, -2]),
    ],
)
def test_integrate_batch(sides, offsets):

    aa_integrator = AxisAlignedWrapper(DummyIntegrator())

    inequalities1 = hypercube(variables, sides, offsets)
    polytope1 = Polytope(inequalities1, variables, env)

    sides2 = sides + np.array([1, -1, 3, -2])
    offsets2 = offsets + np.array(sides)
    inequalities2 = hypercube(variables, sides2, offsets2)
    polytope2 = Polytope(inequalities2, variables, env)

    k1, k2 = 3.33, 15
    polynomial1 = Polynomial(smt.Real(k1), variables, env)
    polynomial2 = Polynomial(smt.Real(k2), variables, env)

    batch = [
        (polytope1, polynomial1),
        (polytope1, polynomial2),
        (polytope2, polynomial1),
        (polytope2, polynomial2),
    ]

    expected_result = np.array(
        [
            np.prod(sides) * k1,
            np.prod(sides) * k2,
            np.prod(sides2) * k1,
            np.prod(sides2) * k2,
        ]
    )

    result = aa_integrator.integrate_batch(batch)
    assert (result == expected_result).all()
