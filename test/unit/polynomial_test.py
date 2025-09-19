import numpy as np
import pysmt.shortcuts as smt
from pysmt.typing import REAL
from pysmt.walkers import IdentityDagWalker

from wmpy.core import Polynomial

env = smt.get_env()
x = smt.Symbol("X", REAL)
y = smt.Symbol("Y", REAL)


class PowSimplifier(IdentityDagWalker):
    """This is needed here because wmpy follows python's convention
    on 0 ** 0 == 1. This is not the case for most SMT solvers.

    """

    def walk_pow(self, formula, args):
        b, e = args
        if e.is_real_constant(0.0):
            return smt.Real(1.0)
        else:
            return smt.Pow(b, e)

    def simplify(self, polynomial):
        return self.walk(polynomial)


powsimplifier = PowSimplifier()


def equivalent_expressions(original, derived):
    """Polynomial simplification might result in a pysmt expression
    with less variables. If that's not the case, use an SMT solver to
    check for equivalence.
    """
    return (
        original.get_free_variables() != derived.get_free_variables()
        or not smt.is_sat(smt.Not(smt.Equals(original, derived)))
    )


def same_numerical_constant(output_val, expected_val):
    """Numerical values after pysmt / Fraction conversions might not
    match floating point operations resulting in NaN or
    Inf. Otherwise, results are expected to be "close enough".

    """
    return (
        np.isnan(expected_val)
        or np.isinf(expected_val)
        or np.isclose(output_val, expected_val)
    )


def test_monomial_constant(f_const):
    expression = smt.Real(f_const)
    polynomial = Polynomial(expression, {}, env=env)
    assert equivalent_expressions(expression, polynomial.to_pysmt())
    coefficient = polynomial.monomials.get((), 0)
    assert same_numerical_constant(coefficient, f_const)


def test_monomial_constant_multiplication(f_vec3):
    try:
        c1, c2, c3 = f_vec3
        expression = smt.Times(*map(smt.Real, f_vec3))
        polynomial = Polynomial(expression, {}, env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((), 0)
        assert same_numerical_constant(coefficient, c1 * c2 * c3)
    except OverflowError:
        pass


def test_monomial_constant_exponent(f_const, exp_const):
    try:
        expression = smt.Pow(smt.Real(f_const), smt.Real(exp_const))
        polynomial = Polynomial(expression, {}, env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((), 0)
        assert same_numerical_constant(coefficient, f_const**exp_const)
    except OverflowError:
        pass


def test_monomial_constant_exponent_multiplication(f_vec3, exp_vec2):
    try:
        c1, c2, c3 = f_vec3
        exp1, exp2 = exp_vec2
        expression = smt.Times(
            smt.Pow(smt.Real(c1), smt.Real(exp1)),
            smt.Pow(smt.Real(c2), smt.Real(exp2)),
            smt.Real(c3),
        )
        polynomial = Polynomial(expression, [], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((), 0)
        assert same_numerical_constant(coefficient, c1**exp1 * c2**exp2 * c3)
    except OverflowError:
        pass


def test_monomial_symbol():
    expression = x
    polynomial = Polynomial(expression, [x], env=env)
    assert equivalent_expressions(expression, polynomial.to_pysmt())
    coefficient = polynomial.monomials.get((1,), 0)
    assert coefficient == 1


def test_monomial_symbol_and_constant(f_const):
    try:
        expression = smt.Times(x, smt.Real(f_const))
        polynomial = Polynomial(expression, [x], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((1,), 0)
        assert same_numerical_constant(coefficient, f_const)
    except OverflowError:
        pass


def test_monomial_symbol_exponent_and_constant(f_const, exp_const):
    expression = smt.Times(smt.Real(f_const), smt.Pow(x, smt.Real(exp_const)))
    polynomial = Polynomial(expression, [x], env=env)
    assert equivalent_expressions(expression, polynomial.to_pysmt())
    coefficient = polynomial.monomials.get((exp_const,), 0)
    assert same_numerical_constant(coefficient, f_const)


def test_monomial_more_symbols(f_vec2, exp_vec4):
    try:
        c1, c2 = f_vec2
        exp1, exp2, exp3, exp4 = exp_vec4
        expression = smt.Times(
            smt.Real(c1),
            smt.Pow(smt.Real(c2), smt.Real(exp1)),
            smt.Pow(x, smt.Real(exp2)),
            smt.Pow(x, smt.Real(exp3)),
            smt.Pow(y, smt.Real(exp4)),
        )
        polynomial = Polynomial(expression, [x, y], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((exp2 + exp3, exp4), 0)
        assert same_numerical_constant(coefficient, c1 * (c2**exp1))
    except OverflowError:
        pass


def test_monomial_all(f_const, exp_vec4):
    try:
        exp1, exp2, exp3, exp4 = exp_vec4
        # ((x * y ^ e1) ^ e2 * c1 ^ e3) ^ e4
        expression = smt.Pow(
            smt.Times(
                smt.Pow(smt.Times(x, smt.Pow(y, smt.Real(exp1))), smt.Real(exp2)),
                smt.Pow(smt.Real(f_const), smt.Real(exp3)),
            ),
            smt.Real(exp4),
        )
        polynomial = Polynomial(expression, [x, y], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((exp2 * exp4, exp1 * exp2 * exp4), 0)
        assert same_numerical_constant(coefficient, (f_const**exp3) ** exp4)
    except OverflowError:
        pass


def test_polynomial_constant(f_const, exp_const):
    try:
        expression = smt.Plus(
            smt.Real(f_const),
            smt.Pow(smt.Real(f_const), smt.Real(exp_const)),
        )
        polynomial = Polynomial(expression, [x], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((0,), 0)
        assert same_numerical_constant(coefficient, f_const + f_const**exp_const)
        assert polynomial.degree == 0
    except OverflowError:
        pass


def test_polynomial_as_monomial(f_const, exp_const):
    try:
        expression = smt.Times(smt.Real(f_const), smt.Pow(x, smt.Real(exp_const)))
        polynomial = Polynomial(expression, [x], env=env)
        assert equivalent_expressions(expression, polynomial.to_pysmt())
        coefficient = polynomial.monomials.get((exp_const,), 0)
        assert same_numerical_constant(coefficient, f_const)
        assert polynomial.degree == exp_const
    except OverflowError:
        pass


def test_polynomial_as_monomial_and_constants(f_vec3, exp_const):
    c1, c2, c3 = f_vec3
    expression = smt.Minus(
        smt.Plus(
            smt.Real(c1), smt.Times(smt.Real(c2), smt.Pow(x, smt.Real(exp_const)))
        ),
        smt.Real(c3),
    )
    polynomial = Polynomial(expression, [x], env=env)
    assert equivalent_expressions(expression, polynomial.to_pysmt())
    assert polynomial.degree == exp_const


def test_polynomial_with_multiple_monomials(f_vec3, exp_vec2):
    c1, c2, c3 = f_vec3
    exp1, exp2 = exp_vec2
    expression = smt.Plus(
        smt.Times(smt.Real(c1), smt.Pow(x, smt.Real(exp1))),
        smt.Times(smt.Real(c2), smt.Pow(y, smt.Real(exp2))),
        smt.Real(c3),
    )
    polynomial = Polynomial(expression, [x, y], env=env)
    assert equivalent_expressions(
        powsimplifier.simplify(expression), polynomial.to_pysmt()
    )
    if exp1 != 0:
        assert same_numerical_constant(polynomial.monomials.get((exp1, 0), 0), c1)
    if exp2 != 0:
        assert same_numerical_constant(polynomial.monomials.get((0, exp2), 0), c2)
    assert same_numerical_constant(
        polynomial.monomials.get((0, 0), 0),
        c3 + int(exp1 == 0) * c1 + int(exp2 == 0) * c2,
    )
    assert polynomial.degree == max(exp1, exp2)


def test_polynomial_monomials_same_variable(f_vec3, exp_vec3):
    c1, c2, c3 = f_vec3
    exp1, exp2, exp3 = exp_vec3
    expression = smt.Plus(
        smt.Times(smt.Real(c1), smt.Pow(x, smt.Real(exp1))),
        smt.Times(smt.Real(c2), smt.Pow(y, smt.Real(exp2))),
        smt.Real(c3),
        smt.Pow(x, smt.Real(exp3)),
    )
    polynomial = Polynomial(expression, [x, y], env=env)
    assert equivalent_expressions(
        powsimplifier.simplify(expression), polynomial.to_pysmt()
    )
    if exp1 != 0:
        assert same_numerical_constant(
            polynomial.monomials.get((exp1, 0), 0), c1 + int(exp3 == exp1) * 1
        )

    if exp2 != 0:
        assert same_numerical_constant(polynomial.monomials.get((0, exp2), 0), c2)

    if exp3 != 0:
        assert same_numerical_constant(
            polynomial.monomials.get((exp3, 0), 0), 1 + int(exp3 == exp1) * c1
        )

    assert same_numerical_constant(
        polynomial.monomials.get((0, 0), 0),
        c3 + int(exp1 == 0) * c1 + int(exp2 == 0) * c2 + 1 * int(exp3 == 0),
    )

    assert polynomial.degree == max(exp1, exp2, exp3)
