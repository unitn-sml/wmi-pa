import pytest
from pysmt.shortcuts import GE, LE, And, Bool, Equals, Min, Plus, Real, Symbol
from pysmt.typing import BOOL, REAL

from wmipa import WMISolver
from wmipa.wmiexception import WMIParsingException, WMIRuntimeException

a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)
z = Symbol("z", REAL)
phi = Bool(True)


def test_double_assignments_same_variable():
    chi = And(
        GE(x, Real(0)),
        LE(x, Real(1)),
        GE(y, Real(0)),
        LE(y, Real(1)),
        Equals(z, Plus(x, Real(3))),
        Equals(z, Plus(y, Real(2))),
    )
    wmi = WMISolver(chi)

    with pytest.raises(WMIParsingException) as ex:
        result_allsmt, _ = wmi.computeWMI(phi, {x, y, z})
    assert ex.value.code == WMIParsingException.ALIAS_CLASH


def test_not_correct_alias():
    chi = And(
        GE(x, Real(0)), LE(x, Real(1)), Equals(Plus(x, Real(3)), Plus(y, Real(2)))
    )
    wmi = WMISolver(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeWMI(phi, {x, y})
    assert ex.value.code == WMIParsingException.INVALID_ALIAS


def test_invalid_weight_function():
    chi = And(GE(x, Real(0)), LE(x, Real(1)))
    w = GE(x, Real(2))

    with pytest.raises(WMIParsingException) as ex:
        _ = WMISolver(chi, w)
    assert ex.value.code == WMIParsingException.INVALID_WEIGHT_FUNCTION


def test_conversion_pysmt_to_sympy():
    chi = LE(Min(Real(5), Real(2)), x)
    wmi = WMISolver(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeWMI(phi, {x})
    assert ex.value.code == WMIParsingException.CANNOT_CONVERT_PYSMT_FORMULA_TO_SYMPY


def test_conversion_sympy_to_pysmt():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


def test_cyclic_assignment():
    chi = And(GE(x, Real(0)), LE(x, Real(1)), Equals(x, y), Equals(y, x))
    wmi = WMISolver(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeWMI(phi, {x, y})
    assert ex.value.code == WMIParsingException.CYCLIC_ALIASES


def test_bound_not_inequality():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


def test_bound_polynomial_degree_greater_than_one():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


