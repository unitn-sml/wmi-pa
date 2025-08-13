import pysmt.shortcuts as smt
from pysmt.typing import BOOL, REAL

from wmipa.core.weights import Weights, WeightsEvaluator

env = smt.get_env()
a = smt.Symbol("A", BOOL)
b = smt.Symbol("B", BOOL)
c = smt.Symbol("C", BOOL)
x = smt.Symbol("x", REAL)
y = smt.Symbol("y", REAL)
v1 = smt.Real(3)
v2 = smt.Real(5)
v3 = smt.Real(7)


# ========================
#  _evaluate_weight
# ========================


def test_weight_evaluator():
    formula = smt.Ite(a, v1, v2)
    w = Weights(formula, env)
    evaluator = WeightsEvaluator(w)
    value = evaluator.evaluate({a: True})
    assert value == v1

    value = evaluator.evaluate({a: False})
    assert value == v2


def test_evaluate_weight_multiplication():
    formula = smt.Ite(a, v1, smt.Times(v2, smt.Ite(b, v1, v3)))
    w = Weights(formula, env)
    evaluator = WeightsEvaluator(w)
    value = evaluator.evaluate({a: True, b: True})
    assert value == v1

    value = evaluator.evaluate({a: False, b: True})
    assert value == smt.Times(v2, v1)

    value = evaluator.evaluate({a: False, b: False})
    assert value == smt.Times(v2, v3)


# ========================
#  __init__
# ========================


def test_init():
    formula = smt.Ite(smt.GE(x, v1), v1, smt.Times(v2, smt.Ite(b, v1, v3)))
    weight = Weights(formula, env)

    assert len(smt.get_free_variables(weight.weight_func)) == len(
        smt.get_free_variables(formula)
    )


def test_init_not_correct_weight_function():
    pass  # TODO? Check weight structure?
    """
    formula = GE(x, v1)
    with pytest.raises(WMIParsingException):
        weight = Weights(formula)
    """


# ========================
#  weight_from_assignment
# ========================


def test_weight_from_assignment_cond():
    formula = smt.Ite(a, v1, smt.Times(v2, smt.Ite(smt.LE(x, v1), v1, v3)))
    weight = Weights(formula, env)
    assignment = {a: True, smt.LE(x, v1): True}
    result = weight.weight_from_assignment(assignment)
    assert result == v1

    assignment = {a: False, smt.LE(x, v1): True}
    result = weight.weight_from_assignment(assignment)
    assert result == smt.Times(v2, v1)

    assignment = {a: False, smt.LE(x, v1): False}
    result = weight.weight_from_assignment(assignment)
    assert result == smt.Times(v2, v3)
