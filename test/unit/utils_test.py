import pysmt.shortcuts as smt
import pytest

from wmipa.utils import *

test_env = smt.get_env()

true = smt.Bool(True)
false = smt.Bool(False)

const1 = smt.Real(1)
const2 = smt.Real(1 / 666)
rvar1 = smt.Symbol("X", smt.REAL)
rvar2 = smt.Symbol("Y", smt.REAL)
batom = smt.Symbol("A", smt.BOOL)
ratom = smt.LE(smt.Times(const2, rvar1), smt.Plus(rvar2, const1))

neg_ratom = smt.Not(ratom)
neg_batom = smt.Not(batom)

clause1 = smt.Or(ratom)
clause2 = smt.Or(ratom, neg_batom)

cnf1 = smt.And(clause2)
cnf2 = smt.And(clause1, clause2)

dnf = smt.Or(ratom, smt.And(ratom, neg_batom))


@pytest.mark.parametrize(
    "input_formula, expected_result",
    [
        (const1, False),
        (rvar1, False),
        (ratom, True),
        (neg_ratom, False),
        (batom, True),
        (neg_batom, False),
    ],
)
def test_is_atom(input_formula, expected_result):
    assert is_atom(input_formula) == expected_result


@pytest.mark.parametrize(
    "input_formula, expected_result",
    [
        (const1, False),
        (rvar1, False),
        (ratom, True),
        (neg_ratom, True),
        (batom, True),
        (neg_batom, True),
    ],
)
def test_is_literal(input_formula, expected_result):
    assert is_literal(input_formula) == expected_result


@pytest.mark.parametrize(
    "input_formula, expected_result",
    [
        (const1, False),
        (rvar1, False),
        (ratom, True),
        (neg_ratom, True),
        (batom, True),
        (neg_batom, True),
        (clause1, True),
        (clause2, True),
        (cnf1, True),
        (cnf2, False),
        (dnf, False),
    ],
)
def test_is_clause(input_formula, expected_result):
    assert is_clause(input_formula) == expected_result


@pytest.mark.parametrize(
    "input_formula, expected_result",
    [
        (const1, False),
        (rvar1, False),
        (ratom, True),
        (neg_ratom, True),
        (batom, True),
        (neg_batom, True),
        (clause1, True),
        (clause2, True),
        (cnf1, True),
        (cnf2, True),
        (dnf, False),
    ],
)
def test_is_cnf(input_formula, expected_result):
    assert is_cnf(input_formula) == expected_result


@pytest.mark.parametrize(
    "input_formula, equivalent_formula",
    [
        (smt.Not(true), false),
        (smt.Not(false), true),
        (smt.And(cnf1, true), cnf1),
        (smt.And(true, cnf1), cnf1),
        (smt.Or(cnf1, true), true),
        (smt.Or(true, cnf1), true),
        (smt.Implies(true, cnf1), cnf1),
        (smt.Implies(cnf1, true), true),
        (smt.Iff(cnf1, true), cnf1),
        (smt.Iff(true, cnf1), cnf1),
        (smt.And(cnf1, false), false),
        (smt.And(false, cnf1), false),
        (smt.Or(cnf1, false), cnf1),
        (smt.Or(false, cnf1), cnf1),
        (smt.Implies(false, cnf1), true),
        (smt.Implies(cnf1, false), smt.Not(cnf1)),
        (smt.Iff(cnf1, false), smt.Not(cnf1)),
        (smt.Iff(false, cnf1), smt.Not(cnf1)),
    ],
)
def test_booleansimplifier_equivalence(input_formula, equivalent_formula):
    simplifier = BooleanSimplifier(test_env)
    output_formula = simplifier.simplify(input_formula)
    assert not smt.is_sat(smt.Not(smt.Iff(output_formula, equivalent_formula)))


@pytest.mark.parametrize(
    "input_formula, atoms",
    [
        (ratom, {ratom}),
        (neg_ratom, {ratom}),
        (batom, {batom}),
        (neg_batom, {batom}),
        (clause1, {ratom}),
        (clause2, {ratom, batom}),
        (cnf1, {ratom, batom}),
        (cnf2, {ratom, batom}),
        (dnf, {ratom, batom}),
    ],
)
def test_booleansimplifier_lra_untouched(input_formula, atoms):
    simplifier = BooleanSimplifier(test_env)
    output_formula = simplifier.simplify(input_formula)
    assert output_formula.get_atoms() == atoms


@pytest.mark.parametrize(
    "input_formula",
    [
        (smt.Not(true)),
        (smt.Not(false)),
        (smt.And(cnf1, true)),
        (smt.And(true, cnf1)),
        (smt.Or(cnf1, true)),
        (smt.Or(true, cnf1)),
        (smt.Implies(true, cnf1)),
        (smt.Implies(cnf1, true)),
        (smt.Iff(cnf1, true)),
        (smt.Iff(true, cnf1)),
        (smt.And(cnf1, false)),
        (smt.And(false, cnf1)),
        (smt.Or(cnf1, false)),
        (smt.Or(false, cnf1)),
        (smt.Implies(false, cnf1)),
        (smt.Implies(cnf1, false)),
        (smt.Iff(cnf1, false)),
        (smt.Iff(false, cnf1)),
    ],
)
def test_booleansimplifier_smaller(input_formula):
    simplifier = BooleanSimplifier(test_env)
    output_formula = simplifier.simplify(input_formula)
    assert output_formula.size() < input_formula.size()
