import itertools
import sys

import numpy as np
import pytest
from pysmt.shortcuts import LE, Plus, Real, Symbol, Times
from pysmt.typing import REAL
from scipy.spatial import ConvexHull

from wmipa.integration.latte_integrator import LatteIntegrator
from wmipa.integration.symbolic_integrator import SymbolicIntegrator
from wmipa.integration.volesti_integrator import VolestiIntegrator


def _assignment_from_equations(A, b):
    atom_assignment = {}
    for left, right in zip(A, b):
        left = Plus(
            [
                Times(Real(float(c)), Symbol("x_{}".format(i), REAL))
                for i, c in enumerate(left)
            ]
        )
        right = Real(float(right))
        atom_assignment[LE(left, right)] = True
    return atom_assignment


def _unit_hypercube_equations(n):
    A = np.concatenate((np.identity(n), -np.identity(n)), axis=0)
    b = np.concatenate((np.ones(n), np.zeros(n)), axis=0)
    return A, b


def axis_aligned_hypercube(n):
    A, b = _unit_hypercube_equations(n)
    return _assignment_from_equations(A, b), 1.0


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
    return _assignment_from_equations(A, b), 1.0


def _assignment_from_points(points):
    hull = ConvexHull(points)
    print(f"Number of edges {len(hull.equations)}", file=sys.stderr)
    # use the hyperplanes' equations to generate the H-Polytope
    A, b = hull.equations[:, :-1], hull.equations[:, -1]
    volume = hull.volume
    return _assignment_from_equations(A, -b), volume


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


def pytest_generate_tests(metafunc):
    argnames = ["polytope_assignment", "volume", "integrator"]
    argvalues = []
    idlist = []
    # axis_aligned_cube
    for polytope_generator in (
            axis_aligned_hypercube,
            rotated_hypercube,
            random_polytope,
            axis_aligned_cross_polytope,
    ):
        for dim in (2, 3, 4):
            polytope, volume = polytope_generator(dim)
            # latte integrator
            argvalues.append((polytope, volume, LatteIntegrator()))
            idlist.append(
                f"{'LatteIntegrator':>20} {polytope_generator.__name__:>25}"
                f"(n={dim})"
            )
            # symbolic integrator
            argvalues.append((polytope, volume, SymbolicIntegrator()))
            idlist.append(
                f"{'SymbolicIntegrator':>20} {polytope_generator.__name__:>25}"
                f"(n={dim})"
            )
            # volesti integrator
            walk_length = dim ** 3
            argvalues.append((polytope, volume, VolestiIntegrator(seed=666, error=0.1, walk_length=None)))
            idlist.append(
                f"{'VolestiIntegrator':>20} {polytope_generator.__name__:>25}"
                f"(n={dim}, error=0.1, walk_length=d^{walk_length})"
            )

    metafunc.parametrize(argnames, argvalues, ids=idlist)


def test_volume(polytope_assignment, volume, integrator):
    if isinstance(integrator, SymbolicIntegrator):
        pytest.skip("Skipping symbolic integrator test since it is too slow.")
    weight = Real(1.0)
    print(polytope_assignment, file=sys.stderr)
    result, _ = integrator.integrate(polytope_assignment, weight, {}, None, -1)
    if isinstance(integrator, VolestiIntegrator):
        # add also an absolute tolerance as sometimes the results are not within the error
        assert np.isclose(result, volume, atol=0.05, rtol=integrator.error)
    else:
        assert np.isclose(result, volume)
