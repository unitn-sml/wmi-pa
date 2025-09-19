from itertools import product
import numpy as np
import pytest

import pysmt.shortcuts as smt

from wmpy.core.polytope import Polytope


def test_polytope_nonlinear():
    env = smt.get_env()
    x = smt.Symbol("x", smt.REAL)
    y = smt.Symbol("y", smt.REAL)
    inequalities = [
        smt.LE(x, smt.Real(0)),
        smt.GE(smt.Pow(y, smt.Real(3)), smt.Real(0)),
    ]
    with pytest.raises(AssertionError):
        polytope = Polytope(inequalities, [x, y], env=env)


def test_polytope_unknown_variable():
    env = smt.get_env()
    x = smt.Symbol("x", smt.REAL)
    y = smt.Symbol("y", smt.REAL)
    z = smt.Symbol("z", smt.REAL)
    inequalities = [
        smt.LE(x, smt.Real(0)),
        smt.GE(z, smt.Real(1)),
    ]
    with pytest.raises(AssertionError):
        polytope = Polytope(inequalities, [x, y], env=env)


@pytest.fixture(params=product(range(1, 5), repeat=2))
def Ab(request):
    M, N = request.param
    np.random.seed(10 * N + M)
    A = np.random.random((M, N))
    b = np.random.random((M,))
    return A, b


def test_polytope_conversion(Ab):
    env = smt.get_env()
    A, b = Ab
    M, N = A.shape
    vx = [smt.Symbol(f"x{i}", smt.REAL) for i in range(N)]
    inequalities = []
    for i in range(M):
        ineq = smt.LE(
            smt.Plus([smt.Times(smt.Real(float(A[i][j])), vx[j]) for j in range(N)]),
            smt.Real(float(b[i])),
        )
        inequalities.append(ineq)

    polytope = Polytope(inequalities, vx, env=env)
    Aconv, bconv = polytope.to_numpy()
    assert (Aconv == A).all(), f"numpy conversion error\nA:\n{A}\nA':\n{Aconv}"
    assert (bconv == b).all(), f"numpy conversion error\nb:\n{b}\nb':\n{bconv}"

    f = smt.And(*inequalities)
    fconv = polytope.to_pysmt()
    assert not smt.is_sat(
        smt.Not(smt.Iff(f, fconv))
    ), "pysmt conversion error\nf:\n{smt.serialize(f)}\nf':{smt.serialize(fconv)}"
