import numpy as np
from pysmt.shortcuts import GE, LE, And, Bool, Equals, FreshSymbol, Iff, Ite, Not, Or, Plus, Real, Symbol, Times, Pow
from pysmt.typing import BOOL, REAL

from wmipa import WMISolver
from wmipa.integration import LatteIntegrator, VolestiIntegrator

a = Symbol("A", BOOL)
b = Symbol("B", BOOL)
c = Symbol("C", BOOL)
d = Symbol("D", BOOL)
e = Symbol("E", BOOL)
x = Symbol("x", REAL)
y = Symbol("y", REAL)
z = Symbol("z", REAL)
phi = Bool(True)


def test_no_booleans_constant_weight():
    chi = And(GE(x, Real(0)), LE(x, Real(1)))

    wmi = WMISolver(chi)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, 1)


def test_no_booleans_condition_weight():
    chi = And(GE(x, Real(0)), LE(x, Real(1)))

    w = Ite(LE(x, Real(0.5)), x, Times(Real(-1), x))

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, -0.25)


def test_booleans_constant_weight():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-2)), LE(x, Real(1)))

    wmi = WMISolver(chi)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, 3)


def test_boolean_condition_weight():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)))

    w = Ite(LE(x, Real(-0.5)), x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, -1.125)


def test_boolean_and_not_simplify():
    chi = And(
        Iff(a, GE(x, Real(0))),
        Or(
            And(GE(x, Real(-3)), LE(x, Real(-2))),
            And(GE(x, Real(-1)), LE(x, Real(1))),
            And(GE(x, Real(2)), LE(x, Real(3))),
        ),
    )

    w = Ite(LE(x, Real(-0.5)), x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, -6.125)


def test_not_boolean_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)), b, Not(b))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, 0)


def test_not_lra_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)), GE(x, Real(2)))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, 0)


def test_multiplication_in_weight():
    chi = And(
        Iff(a, GE(x, Real(0))),
        Or(
            And(GE(x, Real(-3)), LE(x, Real(-2))),
            And(GE(x, Real(-1)), LE(x, Real(1))),
            And(GE(x, Real(2)), LE(x, Real(3))),
        ),
    )

    w = Times(Ite(a, x, Times(x, Real(-1))), x)

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x})
    assert np.isclose(result, 0)


def test_aliases():
    chi = And(GE(x, Real(0)), Equals(y, Plus(x, Real(-2))), LE(y, Real(4)))

    w = y

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x, y})
    assert np.isclose(result, 6)


def test_aliases_leads_to_not_sat():
    chi = And(GE(x, Real(0)), LE(x, Real(2)), Equals(y, x), LE(x - y, Real(-2)))

    wmi = WMISolver(chi)
    result, _ = wmi.computeWMI(phi, {x, y})
    assert np.isclose(result, 0)


def test_double_assignment_same_variable_no_theory_consistent():
    chi = And(
        GE(x, Real(0)),
        Equals(y, Plus(x, Real(-2))),
        Equals(y, Plus(x, Real(5))),
        LE(y, Real(4)),
    )

    wmi = WMISolver(chi)
    result, _ = wmi.computeWMI(phi, {x, y})

    assert np.isclose(result, 0)


def test_reserved_variables_name():
    a = Symbol("wmi_1_a", BOOL)
    b = Symbol("cond_a", BOOL)
    x = Symbol("query_45", REAL)
    y = FreshSymbol(REAL)

    chi = And(
        GE(x, Real(0)),
        LE(x, Real(2)),
        GE(y, Real(2)),
        LE(y, Real(4)),
        Iff(a, LE(x, Real(1))),
        Iff(b, LE(y, Real(3))),
    )

    w = Ite(a, x, y)

    wmi = WMISolver(chi, w)
    result, _ = wmi.computeWMI(phi, {x, y})

    assert np.isclose(result, 7)


def test_multiple_integrators():
    chi = And(
        GE(x, Real(0)), LE(x, Real(2)),
        GE(y, Real(0)), LE(y, Real(2)),
    )

    w = Ite(a,
            Ite(b, Real(1), Plus(x, y)),
            Ite(c,
                Ite(d, Pow(x, Real(2)), Times(x, y)),
                Ite(e, Pow(y, Real(3)), Plus(x, Times(y, Real(2)))),
                )
            )

    ans = 640 / 3
    epsilon = 0.1
    wmi = WMISolver(chi, w, integrator=[LatteIntegrator(),
                                  VolestiIntegrator(seed=420, error=epsilon),
                                  VolestiIntegrator(seed=69, error=epsilon),
                                  ])


    result, n_int = wmi.computeWMI(phi, {x, y})
    assert isinstance(n_int, np.ndarray) and n_int.shape == (3,)
    assert isinstance(result, np.ndarray) and result.shape == (3,)
    # latte is exact
    assert np.allclose(result[0], ans)
    # volesti is approximate
    assert np.allclose(result[1:], ans, rtol=epsilon)
