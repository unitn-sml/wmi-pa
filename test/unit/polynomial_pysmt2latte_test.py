from pysmt.shortcuts import Symbol, REAL, Plus, Real, Times, Pow, Minus
from wmipa.integration.polytope import Polynomial
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


def test_polynomial_constant():
    expression = Plus(Times(r3, r1), Pow(r1, r1))
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == set()
    assert polynomial.degree() == 0


def test_polynomial_as_monomial():
    expression = Times(r3, Pow(x, r1), r2)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == {"X"}
    assert polynomial.degree() == v1


def test_polynomial_as_monomial_and_constants():
    expression = Minus(Plus(r3, Times(r1, Pow(x, r2))), r2)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 2
    assert polynomial.variables == {"X"}
    assert polynomial.degree() == v2


def test_polynomial_with_multiple_monomials():
    expression = Plus(Times(r1, Pow(x, r2)), Times(r2, Pow(y, r1)), r3)
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 3
    assert polynomial.variables == {"X", "Y"}
    assert polynomial.degree() == max(v2, v1)


def test_polynomial_negate():
    expression = Plus(Times(r1, Pow(x, r2)), Times(r2, Pow(y, r1)), r3)
    polynomial = Polynomial(expression, {})
    polynomial.negate()
    assert len(polynomial.monomials) == 3
    assert polynomial.variables == {"X", "Y"}
    assert polynomial.degree() == max(v2, v1)


def test_polynomial_monomials_same_variable():
    expression = Plus(Times(r1, Pow(x, r2)), Times(r2, Pow(y, r1)), r3, Pow(x, r3))
    polynomial = Polynomial(expression, {})
    assert len(polynomial.monomials) == 4
    assert polynomial.variables == {"X", "Y"}
    assert polynomial.degree() == max(v2, v1, v3)


def test_polynomial_aliases():
    expression = Plus(Times(r1, Pow(x, r1)), Pow(y, r2), Times(r3, Pow(z, r3)))
    alias = {y: Times(x, Real(-2))}
    polynomial = Polynomial(expression, alias)
    assert len(polynomial.monomials) == 3
    assert polynomial.variables == {"X", "Z"}
    assert polynomial.degree() == max(v2, v1, v3)


def test_polynomial_aliases_to_constant():
    expression = Times(x, pi)
    alias = {pi: Real(3.1415), x: y}
    polynomial = Polynomial(expression, alias)
    assert len(polynomial.monomials) == 1
    assert polynomial.variables == {"Y"}
    assert polynomial.degree() == 1


def test_polynomial_aliases_circular_assignment():
    expression = Plus(x, y)
    alias = {x: Plus(y, r1), y: Plus(x, r2)}
    with pytest.raises(WMIParsingException):
        polynomial = Polynomial(expression, alias)


def test_polynomial_aliases_to_same():
    expression = y
    alias = {y: Plus(y, r1)}
    with pytest.raises(WMIParsingException):
        polynomial = Polynomial(expression, alias)
