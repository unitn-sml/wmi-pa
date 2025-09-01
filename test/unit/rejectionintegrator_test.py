import itertools
import numpy as np
import pytest

import pysmt.shortcuts as smt

from wmipa.core import Polynomial, Polytope
from wmipa.integration import RejectionIntegrator


@pytest.mark.parametrize(
    "n, xmin, side", itertools.product([2, 3, 4], [-1, 0, 100], [1, 10, 100])
)
def test_volume(n, xmin, side):
    env = smt.get_env()

    inequalities = []
    variables = [smt.Symbol(f"x{i}", smt.REAL) for i in range(n)]
    for xi in variables:
        inequalities.extend(
            [smt.LE(smt.Real(xmin), xi), smt.LE(xi, smt.Real(xmin + side))]
        )

    volume = side**n
    polynomial = Polynomial(smt.Real(1.0), variables, env)
    polytope = Polytope(inequalities, variables, env)
    result = RejectionIntegrator().integrate(polytope, polynomial)
    assert np.isclose(result, volume), f"Expected {side} ^ {n} = {volume}, got {result}"
