from pysmt.shortcuts import REAL, Pow, Times, Symbol, Real
from wmipa.integration.polytope import Monomial

x = Symbol("X", REAL)
y = Symbol("Y", REAL)
z = Symbol("Z", REAL)
v1 = -3
v2 = 2
v3 = -5
r1 = Real(v1)
r2 = Real(v2)
r3 = Real(v3)


def test_monomial_constant():
    expression = r3
    monomial = Monomial(expression)
    assert monomial.coefficient == v3
    assert monomial.exponents == {}
    assert monomial.degree() == 0


def test_monomial_constant_multiplication():
    expression = Times(r3, r1, r2)
    monomial = Monomial(expression)
    assert monomial.coefficient == v3 * v1 * v2
    assert monomial.exponents == {}
    assert monomial.degree() == 0


def test_monomial_constant_exponent():
    expression = Pow(r1, r2)
    monomial = Monomial(expression)
    assert monomial.coefficient == Pow(r1, r2).constant_value()
    assert monomial.exponents == {}
    assert monomial.degree() == 0


def test_monomial_constant_exponent_multiplication():
    expression = Times(Pow(r1, r2), Pow(r3, r1), r2)
    monomial = Monomial(expression)
    assert monomial.coefficient == Pow(r1, r2).constant_value() * Pow(r3, r1).constant_value() * v2
    assert monomial.exponents == {}
    assert monomial.degree() == 0


def test_monomial_symbol():
    expression = x
    monomial = Monomial(expression)
    assert monomial.coefficient == 1
    assert monomial.exponents == {"X": 1}
    assert monomial.degree() == 1


def test_monomial_symbol_and_constant():
    expression = Times(x, r1)
    monomial = Monomial(expression)
    assert monomial.coefficient == v1
    assert monomial.exponents == {"X": 1}
    assert monomial.degree() == 1


def test_monomial_symbol_exponent_and_constant():
    expression = Times(r2, Pow(x, r1))
    monomial = Monomial(expression)
    assert monomial.coefficient == v2
    assert monomial.exponents == {"X": v1}
    assert monomial.degree() == v1


def test_monomial_more_symbols():
    expression = Times(r1, Pow(x, r2), Pow(r1, r1), Pow(x, r3), Pow(y, r1))
    monomial = Monomial(expression)
    assert monomial.coefficient == v1 * Pow(r1, r1).constant_value()
    assert monomial.exponents == {"X": v2 + v3, "Y": v1}
    assert monomial.degree() == v1 + v2 + v3


def test_monomial_negate():
    expression = Times(r1, Pow(x, r2), Pow(r1, r1), Pow(x, r3), Pow(y, r1))
    monomial = Monomial(expression)
    monomial.negate()
    assert monomial.coefficient == v1 * Pow(r1, r1).constant_value() * -1
    assert monomial.exponents == {"X": v2 + v3, "Y": v1}
    assert monomial.degree() == v1 + v2 + v3


def test_monomial_moltiplication():
    expression1 = Times(r2, Pow(x, r1))
    expression2 = Times(r1, Pow(x, r2), Pow(r1, r1), Pow(x, r3), Pow(y, r1))
    monomial1 = Monomial(expression1)
    monomial2 = Monomial(expression2)
    monomial1.multiply_by_monomial(monomial2)
    assert monomial1.coefficient == v2 * v1 * Pow(r1, r1).constant_value()
    assert monomial1.exponents == {"X": v1 + v2 + v3, "Y": v1}
    assert monomial1.degree() == v1 + v2 + v3 + v1


def test_monomial_all():
    expression = Pow(Times(Pow(Pow(Times(x, Pow(y, r1)), r2), r3), Pow(r2, r1)), r1)
    monomial = Monomial(expression)
    assert monomial.coefficient == Pow(Pow(r2, r1), r1).constant_value()
    assert monomial.exponents == {"X": v2 * v3 * v1, "Y": v1 * v2 * v3 * v1}
    assert monomial.degree() == v2 * v3 * v1 + v1 * v2 * v3 * v1
