from pysmt.shortcuts import Real, LE, Pow, REAL, Symbol, Times, Plus, GE
from wmipa.polytope import Bound
from fractions import Fraction
from wmipa.wmiexception import WMIParsingException
import pytest

x = Symbol("X", REAL)
y = Symbol("Y", REAL)
z = Symbol("Z", REAL)
pi = Symbol("PI", REAL)
v1 = -3
v2 = 5
v3 = 2
r1 = Real(v1)
r2 = Real(v2)
r3 = Real(v3)


def test_bound_degree_more_than_one():
    expression = LE(Pow(x, Real(2)), r1)
    with pytest.raises(WMIParsingException):
        bound = Bound(expression, {})


def test_bound_right_constant_integer():
    expression = LE(x, Real(5))
    bound = Bound(expression, {})
    assert bound.constant == 5
    assert len(bound.coefficients) == 1
    assert bound.coefficients["X"] == 1


def test_bound_left_constant_integer():
    expression = LE(Real(5), x)
    bound = Bound(expression, {})
    assert bound.constant == -5
    assert len(bound.coefficients) == 1
    assert bound.coefficients["X"] == -1


def test_bound_constant_decimal():
    expression = LE(x, Real(3.5))
    bound = Bound(expression, {})
    assert bound.constant == 7
    assert len(bound.coefficients) == 1
    assert bound.coefficients["X"] == 2


def test_bound_alias_brings_to_degree_more_than_zero():
    expression = LE(x, Real(3))
    aliases = {x: Pow(y, Real(2))}
    with pytest.raises(WMIParsingException):
        bound = Bound(expression, aliases)


def test_bound_no_constant_part():
    expression = LE(Plus(x, y), Times(x, Real(-1)))  # x+y < -x
    bound = Bound(expression, {})
    assert bound.constant == 0
    assert len(bound.coefficients) == 2
    assert bound.coefficients["X"] == 2
    assert bound.coefficients["Y"] == 1


def test_bound_alias_to_constant():
    expression = GE(Times(x, Real(5)), pi)  # 5x > pi  =>  pi - 5x < 0  =>  -5x < -3.1415
    aliases = {pi: Real(3.1415)}
    bound = Bound(expression, aliases)
    assert bound.constant == Fraction(-3.1415).numerator
    assert len(bound.coefficients) == 1
    assert bound.coefficients["X"] == Fraction(-3.1415).denominator * -5
