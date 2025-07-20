import pysmt.shortcuts as smt
from pysmt.typing import REAL

from wmipa.datastructures import Polynomial

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


def test_monomial_constant():
    expression = r3
    polynomial = Polynomial(expression, {}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v3
    assert not exponents


def test_monomial_constant_multiplication():
    expression = smt.Times(r3, r1, r2)
    polynomial = Polynomial(expression, {}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v3 * v1 * v2
    assert not exponents


def test_monomial_constant_exponent():
    expression = smt.Pow(r1, r2)
    polynomial = Polynomial(expression, {}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1**v2
    assert not exponents


def test_monomial_constant_exponent_multiplication():
    expression = smt.Times(smt.Pow(r1, r2), smt.Pow(r3, r3), r2)
    polynomial = Polynomial(expression, {}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1**v2 * v3**v3 * v2
    assert not exponents


def test_monomial_symbol():
    expression = x
    polynomial = Polynomial(expression, {x}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == 1
    assert tuple(exponents) == (1,)


def test_monomial_symbol_and_constant():
    expression = smt.Times(x, r1)
    polynomial = Polynomial(expression, {x}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v1
    assert tuple(exponents) == (1,)


def test_monomial_symbol_exponent_and_constant():
    expression = smt.Times(r2, smt.Pow(x, r3))
    polynomial = Polynomial(expression, {x}, env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v2
    assert exponents == (v3,)


def test_monomial_more_symbols():
    expression = smt.Times(
        r1, smt.Pow(x, r2), smt.Pow(r1, r3), smt.Pow(x, r3), smt.Pow(y, r2)
    )
    polynomial = Polynomial(expression, [x, y], env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1 * (v1**v3)
    assert exponents == (v2 + v3, v2)


def test_monomial_all():
    # ((((x * y^r2))^r2)^r3) * (r2^r1))^r3
    expression = smt.Pow(
        smt.Times(
            smt.Pow(smt.Pow(smt.Times(x, smt.Pow(y, r2)), r2), r3), smt.Pow(r2, r1)
        ),
        r3,
    )
    polynomial = Polynomial(expression, [x, y], env=env)
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == (v2**v1) ** v3
    assert exponents == (v2 * v3 * v3, v2 * v2 * v3 * v3)


def test_polynomial_constant():
    expression = smt.Plus(smt.Times(r3, r1), smt.Pow(r1, r1))
    polynomial = Polynomial(expression, set(), env=env)
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == set()
    assert polynomial.degree == 0


def test_polynomial_as_monomial():
    expression = smt.Times(r3, smt.Pow(x, r3), r2)
    polynomial = Polynomial(expression, {x}, env=env)
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == {x}
    assert polynomial.degree == v3


def test_polynomial_as_monomial_and_constants():
    expression = smt.Minus(smt.Plus(r3, smt.Times(r1, smt.Pow(x, r2))), r2)
    polynomial = Polynomial(expression, {x}, env=env)
    assert len(polynomial.monomials) == 2
    assert polynomial.variables == {x}
    assert polynomial.degree == v2


def test_polynomial_with_multiple_monomials():
    expression = smt.Plus(
        smt.Times(r1, smt.Pow(x, r2)), smt.Times(r2, smt.Pow(y, r3)), r3
    )
    polynomial = Polynomial(expression, {x, y}, env=env)
    assert len(polynomial.monomials) == 3
    assert polynomial.variables == {x, y}
    assert polynomial.degree == max(v2, v3)


def test_polynomial_monomials_same_variable():
    expression = smt.Plus(
        smt.Times(r1, smt.Pow(x, r2)), smt.Times(r2, smt.Pow(y, r2)), r3, smt.Pow(x, r3)
    )
    polynomial = Polynomial(expression, {x, y}, env=env)
    assert len(polynomial.monomials) == 4
    assert polynomial.variables == {x, y}
    assert polynomial.degree == max(v2, v2, v3)
