import pysmt.shortcuts as smt
import pytest
from pysmt.typing import REAL

from wmipa.core.inequality import Inequality

x = smt.Symbol("X", REAL)
y = smt.Symbol("Y", REAL)
z = smt.Symbol("Z", REAL)
v1 = -3
v2 = 5
v3 = 2
r1 = smt.Real(v1)
r2 = smt.Real(v2)
r3 = smt.Real(v3)
env = smt.get_env()


def equivalent_expressions(original, converted):
    return not smt.is_sat(smt.Not(smt.Iff(original, converted)))


@pytest.fixture
def zero_degree_expr(f_vec2):
    c1, c2 = map(smt.Real, f_vec2)
    return smt.LE(c1, c2)


@pytest.fixture
def higher_degree_expr(f_vec2):
    c1, c2 = map(smt.Real, f_vec2)
    return smt.LE(c1, c2)


@pytest.mark.parametrize(
    "expression",
    [
        smt.LE(x, y),
        smt.LE(smt.Real(0), smt.Plus(x, y)),
        smt.LE(smt.Plus(x, smt.Real(5)), y),
        smt.LE(smt.Times(x, smt.Real(3.5)), y),
        smt.LE(smt.Times(x, smt.Real(3.5)), smt.Plus(smt.Real(5), y)),
    ],
)
def test_ineq_no_variables(expression):
    with pytest.raises(ValueError):
        _ = Inequality(expression, {}, env=env)


def test_ineq_degree_zero(zero_degree_expr):
    with pytest.raises(AssertionError):
        _ = Inequality(zero_degree_expr, {x}, env=env)


def test_ineq_degree_more_than_one():
    expression = smt.LE(smt.Pow(x, smt.Real(2)), r1)
    with pytest.raises(AssertionError):
        _ = Inequality(expression, {x}, env=env)


@pytest.mark.parametrize(
    "expression",
    [
        smt.LE(x, smt.Real(5)),
        smt.LE(smt.Real(0), smt.Plus(x, smt.Real(5))),
        smt.LE(smt.Plus(x, smt.Real(5)), x),
        smt.LE(smt.Times(x, smt.Real(3.5)), x),
        smt.LE(smt.Times(x, smt.Real(3.5)), smt.Plus(smt.Real(5), x)),
    ],
)
def test_ineq_univariate(expression):
    ineq = Inequality(expression, {x}, env=env)
    assert equivalent_expressions(expression, ineq.to_pysmt())


@pytest.mark.parametrize(
    "expression",
    [
        smt.LE(x, y),
        smt.LE(smt.Real(0), smt.Plus(x, y)),
        smt.LE(smt.Plus(x, smt.Real(5)), y),
        smt.LE(smt.Times(x, smt.Real(3.5)), y),
        smt.LE(smt.Times(x, smt.Real(3.5)), smt.Plus(smt.Real(5), y)),
    ],
)
def test_ineq_no_bivariate(expression):
    ineq = Inequality(expression, {x, y}, env=env)
    assert equivalent_expressions
