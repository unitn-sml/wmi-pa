import pytest
from pysmt.shortcuts import GE, LE, And, Bool, Equals, Min, Plus, Real, Symbol
from pysmt.typing import BOOL, REAL

from wmipa import WMI
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
    wmi = WMI(chi)

    with pytest.raises(WMIParsingException) as ex:
        result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    assert ex.value.code == WMIParsingException.MULTIPLE_ASSIGNMENT_SAME_ALIAS


def test_not_correct_alias():
    chi = And(
        GE(x, Real(0)), LE(x, Real(1)), Equals(Plus(x, Real(3)), Plus(y, Real(2)))
    )
    wmi = WMI(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeMI(phi)
    assert ex.value.code == WMIParsingException.MALFORMED_ALIAS_EXPRESSION


def test_invalid_weight_function():
    chi = And(GE(x, Real(0)), LE(x, Real(1)))
    w = GE(x, Real(2))

    with pytest.raises(WMIParsingException) as ex:
        _ = WMI(chi, w)
    assert ex.value.code == WMIParsingException.INVALID_WEIGHT_FUNCTION


def test_conversion_pysmt_to_sympy():
    chi = LE(Min(Real(5), Real(2)), x)
    wmi = WMI(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeMI(phi)
    assert ex.value.code == WMIParsingException.CANNOT_CONVERT_PYSMT_FORMULA_TO_SYMPY


def test_conversion_sympy_to_pysmt():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


def test_cyclic_assignment():
    chi = And(GE(x, Real(0)), LE(x, Real(1)), Equals(x, y), Equals(y, x))
    wmi = WMI(chi)

    with pytest.raises(WMIParsingException) as ex:
        result, _ = wmi.computeMI(phi)
    assert ex.value.code == WMIParsingException.CYCLIC_ASSIGNMENT_IN_ALIASES


def test_bound_not_inequality():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


def test_bound_polynomial_degree_greater_than_one():
    # don't know of a call to wmi that will raise this specific exception
    assert 1 == 1


def test_wrong_domA():
    chi = And(GE(x, Real(0)), LE(x, Real(1)), a)
    wmi = WMI(chi)
    domA = set()

    with pytest.raises(WMIRuntimeException) as ex:
        result_allsmt, _ = wmi.computeMI(phi, domA=domA)
    assert ex.value.code == WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH


def test_wrong_domX():
    chi = And(GE(x, Real(0)), LE(x, Real(1)), a)
    wmi = WMI(chi)
    domX = set()

    with pytest.raises(WMIRuntimeException) as ex:
        result_allsmt, _ = wmi.computeMI(phi, domX=domX)
    assert ex.value.code == WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH


def test_invalid_mode():
    chi = Bool(True)
    wmi = WMI(chi)

    with pytest.raises(WMIRuntimeException) as ex:
        result_allsmt, _ = wmi.computeMI(phi, mode="mode")
    assert ex.value.code == WMIRuntimeException.INVALID_MODE
