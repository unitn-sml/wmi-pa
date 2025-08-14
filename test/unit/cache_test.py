import numpy as np
import pytest

import pysmt.shortcuts as smt

from wmipa.core import Polynomial, Polytope
from wmipa.integration import CacheWrapper

env = smt.get_env()


class InventiveIntegrator:
    """This is only used to fill the cache with some value."""

    def integrate(self, polytope, polynomial):
        return np.random.random()

    def integrate_batch(self, convex_problems):
        return np.random.random(len(convex_problems))


class DummyIntegrator:

    def integrate(self, polytope, polynomial):
        raise Exception("CacheWrapper didn't catch this.")

    def integrate_batch(self, convex_problems):
        return [self.integrate(*pair) for pair in convex_problems]


@pytest.mark.parametrize("n", range(2, 5))
def test_integrate(n):

    variables = [smt.Symbol(f"x{i}", smt.REAL) for i in range(n)]

    hypercube = []
    for var in variables:
        hypercube.extend([smt.LE(smt.Real(0), var), smt.LE(var, smt.Real(1))])

    h1 = smt.LE(variables[0], variables[1])
    h2 = smt.LE(smt.Plus(variables[-2], variables[-1]), smt.Real(1))

    polytope1 = Polytope(hypercube + [h1], variables, env)
    polytope2 = Polytope(hypercube + [h2], variables, env)

    integrand1 = Polynomial(smt.Real(1337), variables, env)
    integrand2 = Polynomial(smt.Plus(variables[0], variables[-1]), variables, env)

    inventive_integrator = CacheWrapper(InventiveIntegrator())

    r1 = inventive_integrator.integrate(polytope1, integrand1)
    r2 = inventive_integrator.integrate(polytope2, integrand2)

    assert inventive_integrator.integrate(polytope1, integrand1) == r1
    assert inventive_integrator.integrate(polytope2, integrand2) == r2

    dummy_integrator = CacheWrapper(DummyIntegrator())
    dummy_integrator.cache = inventive_integrator.cache

    assert dummy_integrator.integrate(polytope1, integrand1) == r1
    assert dummy_integrator.integrate(polytope2, integrand2) == r2

    with pytest.raises(Exception):
        result = dummy.integrate(polytope1, integrand2)

    with pytest.raises(Exception):
        result = dummy.integrate(polytope2, integrand1)


@pytest.mark.parametrize("n", range(2, 5))
def test_integrate_batch(n):

    variables = [smt.Symbol(f"x{i}", smt.REAL) for i in range(n)]

    hypercube = []
    for var in variables:
        hypercube.extend([smt.LE(smt.Real(0), var), smt.LE(var, smt.Real(1))])

    h1 = smt.LE(variables[0], variables[1])
    h2 = smt.LE(smt.Plus(variables[-2], variables[-1]), smt.Real(1))

    polytope1 = Polytope(hypercube + [h1], variables, env)
    polytope2 = Polytope(hypercube + [h2], variables, env)

    integrand1 = Polynomial(smt.Real(1337), variables, env)
    integrand2 = Polynomial(smt.Plus(variables[0], variables[-1]), variables, env)

    subbatch = [
        (polytope1, integrand1),
        (polytope2, integrand2),
    ]

    batch = subbatch + [(polytope2, integrand1)]

    inventive_integrator = CacheWrapper(InventiveIntegrator())

    r_batch = inventive_integrator.integrate_batch(batch)

    assert (inventive_integrator.integrate_batch(batch) == r_batch).all()

    assert (
        inventive_integrator.integrate_batch(np.flip(batch, axis=0))
        == np.flip(r_batch, axis=0)
    ).all()

    assert (
        inventive_integrator.integrate_batch(subbatch) == r_batch[: len(subbatch)]
    ).all()

    dummy_integrator = CacheWrapper(DummyIntegrator())
    dummy_integrator.cache = inventive_integrator.cache

    assert (dummy_integrator.integrate_batch(batch) == r_batch).all()

    with pytest.raises(Exception):
        result = dummy_integrator.integrate_batch(subbatch + [(polytope1, integrand2)])
