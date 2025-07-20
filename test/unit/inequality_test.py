import pysmt.shortcuts as smt
import pytest
from pysmt.typing import REAL

from wmipa.datastructures import Inequality

x = smt.Symbol("X", REAL)
y = smt.Symbol("Y", REAL)
z = smt.Symbol("Z", REAL)
pi = smt.Symbol("PI", REAL)
v1 = -3
v2 = 5
v3 = 2
r1 = smt.Real(v1)
r2 = smt.Real(v2)
r3 = smt.Real(v3)
env = smt.get_env()


def test_ineq_degree_more_than_one():
    expression = smt.LE(smt.Pow(x, smt.Real(2)), r1)
    with pytest.raises(AssertionError):
        _ = Inequality(expression, {x}, env=env)


def test_ineq_right_constant_integer():
    expression = smt.LE(x, smt.Real(5))
    ineq = Inequality(expression, {x}, env=env)
    assert len(ineq.polynomial) == 2


def test_ineq_left_constant_integer():
    expression = smt.LE(smt.Real(5), x)
    ineq = Inequality(expression, {x}, env=env)
    assert len(ineq.polynomial) == 2


def test_ineq_constant_decimal():
    expression = smt.LE(x, smt.Real(3.5))
    ineq = Inequality(expression, {x}, env=env)
    assert len(ineq.polynomial) == 2


def test_ineq_no_constant_part():
    expression = smt.LE(smt.Plus(x, y), smt.Times(x, smt.Real(-1)))  # x+y < -x
    ineq = Inequality(expression, {x, y}, env=env)
    assert len(ineq.polynomial) == 2
