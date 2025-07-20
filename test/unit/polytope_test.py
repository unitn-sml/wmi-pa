import pysmt.shortcuts as smt
import pytest
from pysmt.typing import REAL

from wmipa.datastructures.polytope import Polytope, Inequality

x = smt.Symbol("X", REAL)
y = smt.Symbol("Y", REAL)
z = smt.Symbol("Z", REAL)
w = smt.Symbol("W", REAL)
v1 = -3
v2 = 5
v3 = 2
r1 = smt.Real(v1)
r2 = smt.Real(v2)
r3 = smt.Real(v3)
env = smt.get_env()


def test_polytope_no_ineq():
    bounds = []
    polytope = Polytope(bounds, set(), env=env)
    assert polytope.inequalities == []


def test_polytope_one_bound():
    atom = smt.LE(x, r1)
    polytope = Polytope([atom], {x}, env=env)
    assert len(polytope.inequalities) == 1
    ineq = Inequality(atom, {x}, env=env)
    assert str(polytope.inequalities[0]) == str(ineq)


def test_polytope_multiple_bounds():
    ineq = [
        smt.LE(x, r1),
        smt.GE(y, smt.Times(r1, x)),
        smt.LT(smt.Plus(r1, r2), smt.Times(y, r3)),
    ]
    polytope = Polytope(ineq, {x, y}, env=env)
    assert len(polytope.inequalities) == 3


def test_polytope_grade_more_than_one():
    ineq = [smt.LE(x, r1), smt.GE(smt.Pow(y, smt.Real(3)), r3)]
    with pytest.raises(AssertionError):
        polytope = Polytope(ineq, {x, y}, env=env)
