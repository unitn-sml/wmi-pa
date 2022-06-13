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
    polytope = Polytope(bounds, {})
    assert polytope.bounds == []
    assert polytope.variables == set()


def test_polytope_one_bound():
    bounds = [LE(x, r1)]
    bound = Bound(bounds[0], {})
    polytope = Polytope(bounds, {})
    assert len(polytope.bounds) == 1
    assert str(polytope.bounds[0]) == str(bound)
    assert polytope.variables == set(["X"])


def test_polytope_multiple_bounds():
    bounds = [LE(x, r1), GE(y, Times(r1, x)), LT(Plus(r1, r2), Times(y, r3))]
    polytope = Polytope(bounds, {})
    assert len(polytope.bounds) == 3
    assert polytope.variables == set(["X", "Y"])


def test_polytope_grade_more_than_one():
    bounds = [LE(x, r1), GE(Pow(y, Real(3)), r3)]
    with pytest.raises(WMIParsingException):
        polytope = Polytope(bounds, {})


def test_polytope_aliases():
    bounds = [LE(x, r1), LT(y, r2)]
    aliases = {y: Times(x, r3)}
    polytope = Polytope(bounds, aliases)
    assert len(polytope.bounds) == 2
    assert polytope.variables == set(["X"])


def test_polytope_aliases_remove_variables():
    bounds = [LE(x, r1), GE(y, Times(x, r2))]
    aliases = {x: Times(r1, r2), y: r3}
    polytope = Polytope(bounds, aliases)
    assert len(polytope.bounds) == 0
    assert polytope.variables == set()


def test_polytope_aliases_brings_more_variables():
    bounds = [LE(x, r1), LE(Times(y, r2), r3)]
    aliases = {y: Plus(w, z)}
    polytope = Polytope(bounds, aliases)
    assert len(polytope.bounds) == 2
    assert polytope.variables == set(["X", "W", "Z"])
