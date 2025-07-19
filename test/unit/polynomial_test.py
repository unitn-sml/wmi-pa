from pysmt.shortcuts import Symbol, REAL, Plus, Real, Times, Pow, Minus

from wmipa.datastructures import Polynomial

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


def test_monomial_constant():
    expression = r3
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v3
    assert not exponents


def test_monomial_constant_multiplication():
    expression = Times(r3, r1, r2)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v3 * v1 * v2
    assert not exponents


def test_monomial_constant_exponent():
    expression = Pow(r1, r2)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1 ** v2
    assert not exponents


def test_monomial_constant_exponent_multiplication():
    expression = Times(Pow(r1, r2), Pow(r3, r3), r2)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1 ** v2 * v3 ** v3 * v2
    assert not exponents


def test_monomial_symbol():
    expression = x
    polynomial = Polynomial(expression, {x})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == 1
    assert tuple(exponents) == (1,)


def test_monomial_symbol_and_constant():
    expression = Times(x, r1)
    polynomial = Polynomial(expression, {x})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert coefficient == v1
    assert tuple(exponents) == (1,)


def test_monomial_symbol_exponent_and_constant():
    expression = Times(r2, Pow(x, r3))
    polynomial = Polynomial(expression, {x})
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v2
    assert exponents == (v3,)


def test_monomial_more_symbols():
    expression = Times(r1, Pow(x, r2), Pow(r1, r3), Pow(x, r3), Pow(y, r2))
    polynomial = Polynomial(expression, [x, y])
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == v1 * (v1 ** v3)
    assert exponents == (v2 + v3, v2)


def test_monomial_all():
    # ((((x * y^r2))^r2)^r3) * (r2^r1))^r3
    expression = Pow(Times(Pow(Pow(Times(x, Pow(y, r2)), r2), r3), Pow(r2, r1)), r3)
    polynomial = Polynomial(expression, [x, y])
    assert len(polynomial.monomials) == 1
    monomial = next(iter(polynomial.monomials.items()))
    exponents, coefficient = monomial
    assert float(coefficient) == (v2 ** v1) ** v3
    assert exponents == (v2 * v3 * v3, v2 * v2 * v3 * v3)


def test_polynomial_constant():
    expression = Plus(Times(r3, r1), Pow(r1, r1))
    polynomial = Polynomial(expression, set())
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == set()
    assert polynomial.degree == 0


def test_polynomial_as_monomial():
    expression = Times(r3, Pow(x, r3), r2)
    polynomial = Polynomial(expression, {x})
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == {x}
    assert polynomial.degree == v3


def test_polynomial_as_monomial_and_constants():
    expression = Minus(Plus(r3, Times(r1, Pow(x, r2))), r2)
    polynomial = Polynomial(expression, {x})
    assert len(polynomial.monomials) == 2
    assert polynomial.variables == {x}
    assert polynomial.degree == v2


def test_polynomial_with_multiple_monomials():
    expression = Plus(Times(r1, Pow(x, r2)), Times(r2, Pow(y, r3)), r3)
    polynomial = Polynomial(expression, {x, y})
    assert len(polynomial.monomials) == 3
    assert polynomial.variables == {x, y}
    assert polynomial.degree == max(v2, v3)


def test_polynomial_monomials_same_variable():
    expression = Plus(Times(r1, Pow(x, r2)), Times(r2, Pow(y, r2)), r3, Pow(x, r3))
    polynomial = Polynomial(expression, {x, y})
    assert len(polynomial.monomials) == 4
    assert polynomial.variables == {x, y}
    assert polynomial.degree == max(v2, v2, v3)
