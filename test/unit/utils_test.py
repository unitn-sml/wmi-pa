import pysmt.shortcuts as smt
import pytest


from wmipa.core.utils import *

test_env = smt.get_env()

const_true = smt.Bool(True)
const_false = smt.Bool(False)
const_lra_term = smt.Real(42)
rvar1 = smt.Symbol("X", smt.REAL)
rvar2 = smt.Symbol("Y", smt.REAL)
batom = smt.Symbol("A", smt.BOOL)
ratom = smt.LE(smt.Times(smt.Real(666), rvar1), smt.Plus(rvar2, const_lra_term))
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
        (const_lra_term, False),
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
        (const_lra_term, False),
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
        (const_lra_term, False),
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
        (const_lra_term, False),
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
        (smt.Not(const_true), const_false),
        (smt.Not(const_false), const_true),
        (smt.And(cnf1, const_true), cnf1),
        (smt.And(const_true, cnf1), cnf1),
        (smt.Or(cnf1, const_true), const_true),
        (smt.Or(const_true, cnf1), const_true),
        (smt.Implies(const_true, cnf1), cnf1),
        (smt.Implies(cnf1, const_true), const_true),
        (smt.Iff(cnf1, const_true), cnf1),
        (smt.Iff(const_true, cnf1), cnf1),
        (smt.And(cnf1, const_false), const_false),
        (smt.And(const_false, cnf1), const_false),
        (smt.Or(cnf1, const_false), cnf1),
        (smt.Or(const_false, cnf1), cnf1),
        (smt.Implies(const_false, cnf1), const_true),
        (smt.Implies(cnf1, const_false), smt.Not(cnf1)),
        (smt.Iff(cnf1, const_false), smt.Not(cnf1)),
        (smt.Iff(const_false, cnf1), smt.Not(cnf1)),
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
        (smt.Not(const_true)),
        (smt.Not(const_false)),
        (smt.And(cnf1, const_true)),
        (smt.And(const_true, cnf1)),
        (smt.Or(cnf1, const_true)),
        (smt.Or(const_true, cnf1)),
        (smt.Implies(const_true, cnf1)),
        (smt.Implies(cnf1, const_true)),
        (smt.Iff(cnf1, const_true)),
        (smt.Iff(const_true, cnf1)),
        (smt.And(cnf1, const_false)),
        (smt.And(const_false, cnf1)),
        (smt.Or(cnf1, const_false)),
        (smt.Or(const_false, cnf1)),
        (smt.Implies(const_false, cnf1)),
        (smt.Implies(cnf1, const_false)),
        (smt.Iff(cnf1, const_false)),
        (smt.Iff(const_false, cnf1)),
    ],
)
def test_booleansimplifier_smaller(input_formula):
    simplifier = BooleanSimplifier(test_env)
    output_formula = simplifier.simplify(input_formula)
    assert output_formula.size() < input_formula.size()


def test_literalnormalizer1(f_vec3, fp_const):

    c1, c2, c3 = tuple(map(smt.Real, f_vec3))
    alpha = smt.Real(fp_const)

    # LHS <= RHS
    lit1 = smt.LE(smt.Plus(smt.Times(c1, rvar1), smt.Times(c2, rvar2)), c3)
    lhs, rhs = lit1.args()

    # alpha(LHS) <= alpha(RHS)
    lit2 = smt.LE(smt.Times(alpha, lhs), smt.Times(alpha, rhs))

    # -RHS <= -LHS
    lit3 = smt.LE(smt.Minus(smt.Real(0), rhs), smt.Minus(smt.Real(0), lhs))

    # -RHS <= -LHS
    lit3 = smt.LE(smt.Minus(smt.Real(0), rhs), smt.Minus(smt.Real(0), lhs))

    # !(LHS > RHS)
    lit4 = smt.Not(smt.GT(lhs, rhs))

    normalizer = LiteralNormalizer(test_env)
    norm_lit1, neg1 = normalizer.normalize(lit1, remember_alias=True)
    norm_lit2, neg2 = normalizer.normalize(lit2, remember_alias=True)
    norm_lit3, neg3 = normalizer.normalize(lit3, remember_alias=True)
    norm_lit4, neg4 = normalizer.normalize(lit4, remember_alias=True)

    assert norm_lit1 == norm_lit2, "A*LHS <= A*RHS"
    assert norm_lit1 == norm_lit3, "-RHS <= -LHS"
    assert norm_lit1 == norm_lit4, "!(LHS > RHS)"
    assert normalizer.known_aliases(norm_lit1) == {
        (lit1, neg1),
        (lit2, neg2),
        (lit3, neg3),
        (lit4, neg4),
    }
