import pytest
from pysmt.shortcuts import REAL, Real, LE, GE, LT, Plus, Pow, Times, Symbol

from wmipa.datastructures.polytope import Polytope, Inequality

x = Symbol("X", REAL)
y = Symbol("Y", REAL)
z = Symbol("Z", REAL)
w = Symbol("W", REAL)
v1 = -3
v2 = 5
v3 = 2
r1 = Real(v1)
r2 = Real(v2)
r3 = Real(v3)


def test_polytope_no_ineq():
    bounds = []
    polytope = Polytope(bounds, set())
    assert polytope.inequalities == []


def test_polytope_one_bound():
    atom = LE(x, r1)
    ineq = Inequality(atom, {x})
    polytope = Polytope([atom], {x})
    assert len(polytope.inequalities) == 1
    assert str(polytope.inequalities[0]) == str(ineq)


def test_polytope_multiple_bounds():
    ineq = [LE(x, r1), GE(y, Times(r1, x)), LT(Plus(r1, r2), Times(y, r3))]
    polytope = Polytope(ineq, {x, y})
    assert len(polytope.inequalities) == 3


def test_polytope_grade_more_than_one():
    ineq = [LE(x, r1), GE(Pow(y, Real(3)), r3)]
    with pytest.raises(AssertionError):
        polytope = Polytope(ineq, {x, y})
