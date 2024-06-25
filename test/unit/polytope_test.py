from pysmt.shortcuts import REAL, Real, LE, GE, LT, Plus, Pow, Times, Symbol
from wmipa.integration.polytope import Polytope, Bound
from wmipa.wmiexception import WMIParsingException
import pytest

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


def test_polytope_no_bounds():
    bounds = []
    polytope = Polytope(bounds)
    assert polytope.bounds == []
    assert polytope.variables == set()


def test_polytope_one_bound():
    bounds = [LE(x, r1)]
    bound = Bound(bounds[0])
    polytope = Polytope(bounds)
    assert len(polytope.bounds) == 1
    assert str(polytope.bounds[0]) == str(bound)
    assert polytope.variables == {"X"}


def test_polytope_multiple_bounds():
    bounds = [LE(x, r1), GE(y, Times(r1, x)), LT(Plus(r1, r2), Times(y, r3))]
    polytope = Polytope(bounds)
    assert len(polytope.bounds) == 3
    assert polytope.variables == {"X", "Y"}


def test_polytope_grade_more_than_one():
    bounds = [LE(x, r1), GE(Pow(y, Real(3)), r3)]
    with pytest.raises(WMIParsingException):
        polytope = Polytope(bounds)
