from wmipa.weights import Weights
from pysmt.shortcuts import Real, Ite, LT, Plus, Symbol, Times, get_free_variables, GE, LE
from pysmt.typing import BOOL, REAL
import pytest
from wmipa.wmiexception import WMIParsingException
from wmipa.wmivariables import WMIVariables

a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)
v1 = Real(3)
v2 = Real(5)
v3 = Real(7)

# ========================
#  _find_conditions
# ========================


def test_find_conditions_count():
    formula = Ite(a, Ite(LT(x, v1), v2, v3), Ite(b, v1, v2))
    variables = WMIVariables()
    w = Weights(formula, variables)
    subs = w._find_conditions(formula, {})
    assert len(subs) == 3


def test_find_conditions_count_no_conditions():
    formula = Times(v1, Plus(v2, v3))
    variables = WMIVariables()
    w = Weights(formula, variables)
    subs = w._find_conditions(formula, {})
    assert len(subs) == 0


def test_find_conditions_with_subs():
    formula = Ite(a, Ite(LT(x, v1), v2, v3), Ite(b, v1, v2))
    variables = WMIVariables()
    w = Weights(formula, variables)
    subs = w._find_conditions(formula, {a: Symbol("cond_0"), y: Symbol("cond_1")})
    assert len(subs) == 4


# ========================
#  _evaluate_weight
# ========================


def test_evaluate_weight_labels():
    formula = Ite(a, v1, v2)
    variables = WMIVariables()
    w = Weights(formula, variables)
    print(w.labels)
    value = w._evaluate_weight(w.labelled_weights, [True], w.labels, {})
    assert value == v1

    value = w._evaluate_weight(w.labelled_weights, [False], w.labels, {})
    assert value == v2


def test_evaluate_weight_multiplication_labels():
    formula = Ite(a, v1, Times(v2, Ite(b, v1, v3)))
    variables = WMIVariables()
    w = Weights(formula, variables)
    value = w._evaluate_weight(w.labelled_weights, [True, True], w.labels, {})
    assert value == v1

    value = w._evaluate_weight(w.labelled_weights, [False, True], w.labels, {})
    assert value == Times(v2, v1)

    value = w._evaluate_weight(w.labelled_weights, [False, False], w.labels, {})
    assert value == Times(v2, v3)


def test_evaluate_weight_cond():
    formula = Ite(a, v1, v2)
    variables = WMIVariables()
    w = Weights(formula, variables)
    print(w.labels)
    value = w._evaluate_weight(w.weights, [True], w.weight_conditions, {})
    assert value == v1

    value = w._evaluate_weight(w.weights, [False], w.weight_conditions, {})
    assert value == v2


def test_evaluate_weight_multiplication_cond():
    formula = Ite(a, v1, Times(v2, Ite(b, v1, v3)))
    variables = WMIVariables()
    w = Weights(formula, variables)
    value = w._evaluate_weight(w.weights, [True, True], w.weight_conditions, {})
    assert value == v1

    value = w._evaluate_weight(w.weights, [False, True], w.weight_conditions, {})
    assert value == Times(v2, v1)

    value = w._evaluate_weight(w.weights, [False, False], w.weight_conditions, {})
    assert value == Times(v2, v3)


# ========================
#  label_conditions
# ========================


def test_label_conditions():
    formula = Ite(a, Ite(b, v1, v2), v3)
    variables = WMIVariables()
    w = Weights(formula, variables)
    labelled_formula, subs = w.label_conditions(formula)
    assert len(subs) == 2
    assert len(get_free_variables(labelled_formula)) == len(get_free_variables(formula))


# ========================
#  __init__
# ========================


def test_init():
    formula = Ite(GE(x, v1), v1, Times(v2, Ite(b, v1, v3)))
    variables = WMIVariables()
    weight = Weights(formula, variables)
    assert len(get_free_variables(weight.weights)) == len(get_free_variables(formula))
    assert len(weight.labels) == 2
    assert len(get_free_variables(weight.labelling)) == 2 * 2
    assert weight.n_conditions == 2


def test_init_not_correct_weight_function():
    formula = GE(x, v1)
    variables = WMIVariables()
    with pytest.raises(WMIParsingException):
        weight = Weights(formula, variables)


# ========================
#  weight_from_assignment
# ========================


def test_weight_from_assignment_labels():
    formula = Ite(a, v1, Times(v2, Ite(LE(x, v1), v1, v3)))
    variables = WMIVariables()
    weight = Weights(formula, variables)
    var = list(variables.variables.keys())
    assignment = {var[0]: True, var[1]: True}
    result, _ = weight.weight_from_assignment(assignment)
    assert result == v1

    assignment = {var[0]: False, var[1]: True}
    result, _ = weight.weight_from_assignment(assignment)
    assert result == Times(v2, v1)

    assignment = {var[0]: False, var[1]: False}
    result, _ = weight.weight_from_assignment(assignment)
    assert result == Times(v2, v3)


def test_weight_from_assignment_cond():
    formula = Ite(a, v1, Times(v2, Ite(LE(x, v1), v1, v3)))
    variables = WMIVariables()
    weight = Weights(formula, variables)
    assignment = {a: True, LE(x, v1): True}
    result, _ = weight.weight_from_assignment(assignment, on_labels=False)
    assert result == v1

    assignment = {a: False, LE(x, v1): True}
    result, _ = weight.weight_from_assignment(assignment, on_labels=False)
    assert result == Times(v2, v1)

    assignment = {a: False, LE(x, v1): False}
    result, _ = weight.weight_from_assignment(assignment, on_labels=False)
    assert result == Times(v2, v3)
