import itertools

import numpy as np
import pysmt.shortcuts as smt
from pysmt.typing import REAL
from scipy.spatial import ConvexHull

from wmipa.datastructures import Polynomial, Polytope
from wmipa.integration import *


def _polytope_from_inequalities(A, b):
    inequalities = []
    variables = {
        "x_{}".format(i): smt.Symbol("x_{}".format(i), REAL) for i in range(A.shape[1])
    }
    for left, right in zip(A, b):
        left = smt.Plus(
            [
                smt.Times(smt.Real(float(c)), variables["x_{}".format(i)])
                for i, c in enumerate(left)
            ]
        )
        right = smt.Real(float(right))
        inequalities.append(smt.LE(left, right))
    return inequalities, set(variables.values())


def _unit_hypercube_equations(n):
    A = np.concatenate((np.identity(n), -np.identity(n)), axis=0)
    b = np.concatenate((np.ones(n), np.zeros(n)), axis=0)
    return A, b


def axis_aligned_hypercube(n):
    A, b = _unit_hypercube_equations(n)
    return _polytope_from_inequalities(A, b), 1.0


def _rotation_matrix(i, j, theta, n):
    R = np.identity(n)
    c = np.cos(theta)
    s = np.sin(theta)
    R[i, i] = c
    R[j, j] = c
    R[i, j] = -s
    R[j, i] = s
    return R


def _hessian_normal(A, b):
    """Normalize half space representation according to hessian normal form."""
    L2 = np.reshape(np.linalg.norm(A, axis=1), (-1, 1))  # needs to be column
    if any(L2 == 0):
        raise ValueError("One of the rows of A is a zero vector.")
    n = A / L2  # hyperplane normals
    p = b / L2.flatten()  # hyperplane distances from origin
    return n, p


def rotated_hypercube(n):
    """
    Source:
    https://github.com/tulip-control/polytope/blob/17858132a92a3fba74fdbefee396957615816abb/polytope/polytope.py#L475
    """
    A, b = _unit_hypercube_equations(n)
    theta = 1  # 1 radiant rotation in each direction
    for i, j in itertools.combinations(range(n), 2):
        R = _rotation_matrix(i, j, theta, n)
        A_, b_ = _hessian_normal(A, b)
        A = np.inner(A_, R)
        b = b_
    return _polytope_from_inequalities(A, b), 1.0


def _assignment_from_points(points):
    hull = ConvexHull(points)
    # use the hyperplanes' equations to generate the H-Polytope
    A, b = hull.equations[:, :-1], hull.equations[:, -1]
    volume = hull.volume
    return _polytope_from_inequalities(A, -b), volume


def random_polytope(n):
    # generate some random points
    SEED = 1
    N_POINTS = n * 10
    rng = np.random.default_rng(SEED)
    points = rng.random((N_POINTS, n))
    # compute the convex hull
    return _assignment_from_points(points)


def axis_aligned_cross_polytope(n):
    points = np.concatenate((np.identity(n), -np.identity(n)), axis=0)
    return _assignment_from_points(points)


################################


DIMENSIONS = (2, 3, 4)


def pytest_generate_tests(metafunc):
    argnames = ["inequalities", "variables", "volume"]
    argvalues = []
    idlist = []
    # axis_aligned_cube
    for polytope_generator in (
        axis_aligned_hypercube,
        rotated_hypercube,
        random_polytope,
        axis_aligned_cross_polytope,
    ):
        for dim in DIMENSIONS:
            (inequalities, variables), volume = polytope_generator(dim)
            argvalues.append((inequalities, variables, volume))
            idlist.append(f"{polytope_generator.__name__:>25}" f"(n={dim})")

    metafunc.parametrize(argnames, argvalues, ids=idlist)


def test_volume(exact_integrators, inequalities, variables, volume):
    env = smt.get_env()
    polynomial = Polynomial(smt.Real(1.0), variables, env)
    polytope = Polytope(inequalities, variables, env)
    for integrator_class, kwargs in exact_integrators:
        result = integrator_class(**kwargs).integrate(polytope, polynomial)
        assert np.isclose(
            result, volume
        ), f"Expected {volume}, got {result} for {integrator.__class__.__name__}"
