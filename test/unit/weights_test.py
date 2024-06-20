import pytest
from pysmt.shortcuts import Real, Ite, Symbol, Times, get_free_variables, GE, LE, Bool
from pysmt.typing import BOOL, REAL

from wmipa.weights import Weights
from wmipa.wmiexception import WMIParsingException

a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)
v1 = Real(3)
v2 = Real(5)
v3 = Real(7)


# ========================
#  _evaluate_weight
# ========================


def test_evaluate_weight():
    formula = Ite(a, v1, v2)
    w = Weights(formula)
    value = w._evaluate_weight(w.weight_func, {a: Bool(True)})
    assert value == v1

    value = w._evaluate_weight(w.weight_func, {a: Bool(False)})
    assert value == v2


def test_evaluate_weight_multiplication():
    formula = Ite(a, v1, Times(v2, Ite(b, v1, v3)))
    w = Weights(formula)
    value = w._evaluate_weight(w.weight_func, {a: Bool(True), b: Bool(True)})
    assert value == v1

    value = w._evaluate_weight(w.weight_func, {a: Bool(False), b: Bool(True)})
    assert value == Times(v2, v1)

    value = w._evaluate_weight(w.weight_func, {a: Bool(False), b: Bool(False)})
    assert value == Times(v2, v3)


# ========================
#  __init__
# ========================


def test_init():
    formula = Ite(GE(x, v1), v1, Times(v2, Ite(b, v1, v3)))
    weight = Weights(formula)

    assert len(get_free_variables(weight.weight_func)) == len(get_free_variables(formula))


def test_init_not_correct_weight_function():
    formula = GE(x, v1)
    # FAILS! Check weight structure?
    with pytest.raises(WMIParsingException):
        weight = Weights(formula)


# ========================
#  weight_from_assignment
# ========================


def test_weight_from_assignment_cond():
    formula = Ite(a, v1, Times(v2, Ite(LE(x, v1), v1, v3)))
    weight = Weights(formula)
    assignment = {a: True, LE(x, v1): True}
    result = weight.weight_from_assignment(assignment)
    assert result == v1

    assignment = {a: False, LE(x, v1): True}
    result = weight.weight_from_assignment(assignment)
    assert result == Times(v2, v1)

    assignment = {a: False, LE(x, v1): False}
    result = weight.weight_from_assignment(assignment)
    assert result == Times(v2, v3)
