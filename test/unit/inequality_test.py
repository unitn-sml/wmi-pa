import pytest
from pysmt.shortcuts import Real, LE, Pow, REAL, Symbol, Times, Plus

from wmipa.datastructures import Inequality

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


def test_ineq_degree_more_than_one():
    expression = LE(Pow(x, Real(2)), r1)
    with pytest.raises(AssertionError):
        _ = Inequality(expression, {x})


def test_ineq_right_constant_integer():
    expression = LE(x, Real(5))
    ineq = Inequality(expression, {x})
    assert len(ineq.polynomial) == 2


def test_ineq_left_constant_integer():
    expression = LE(Real(5), x)
    ineq = Inequality(expression, {x})
    assert len(ineq.polynomial) == 2


def test_ineq_constant_decimal():
    expression = LE(x, Real(3.5))
    ineq = Inequality(expression, {x})
    assert len(ineq.polynomial) == 2


def test_ineq_no_constant_part():
    expression = LE(Plus(x, y), Times(x, Real(-1)))  # x+y < -x
    ineq = Inequality(expression, {x, y})
    assert len(ineq.polynomial) == 2
