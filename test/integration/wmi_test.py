import numpy as np
from pysmt.shortcuts import GE, LE, And, Bool, Equals, FreshSymbol, Iff, Ite, Not, Or, Plus, Real, Symbol, Times, Pow
from pysmt.typing import BOOL, REAL

from wmipa import WMI
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

    wmi = WMI(chi)

    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 1)
    assert np.isclose(result_allsmt, 1)
    assert np.isclose(result_pa, 1)
    assert np.isclose(result_sa_pa, 1)
    assert np.isclose(result_sa_pa_sk, 1)


def test_no_booleans_condition_weight():
    chi = And(GE(x, Real(0)), LE(x, Real(1)))

    w = Ite(LE(x, Real(0.5)), x, Times(Real(-1), x))

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, -0.25)
    assert np.isclose(result_allsmt, -0.25)
    assert np.isclose(result_pa, -0.25)
    assert np.isclose(result_sa_pa, -0.25)
    assert np.isclose(result_sa_pa_sk, -0.25)


def test_booleans_constant_weight():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-2)), LE(x, Real(1)))

    wmi = WMI(chi)

    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 3)
    assert np.isclose(result_allsmt, 3)
    assert np.isclose(result_pa, 3)
    assert np.isclose(result_sa_pa, 3)
    assert np.isclose(result_sa_pa_sk, 3)


def test_boolean_condition_weight():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)))

    w = Ite(LE(x, Real(-0.5)), x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, -1.125)
    assert np.isclose(result_allsmt, -1.125)
    assert np.isclose(result_pa, -1.125)
    assert np.isclose(result_sa_pa, -1.125)
    assert np.isclose(result_sa_pa_sk, -1.125)


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

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, -6.125)
    assert np.isclose(result_allsmt, -6.125)
    assert np.isclose(result_pa, -6.125)
    assert np.isclose(result_sa_pa, -6.125)
    assert np.isclose(result_sa_pa_sk, -6.125)


def test_not_boolean_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)), b, Not(b))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 0)
    assert np.isclose(result_allsmt, 0)
    assert np.isclose(result_pa, 0)
    assert np.isclose(result_sa_pa, 0)
    assert np.isclose(result_sa_pa_sk, 0)


def test_not_lra_satisfiable():
    chi = And(Iff(a, GE(x, Real(0))), GE(x, Real(-1)), LE(x, Real(1)), GE(x, Real(2)))

    w = Ite(b, x, Ite(a, Times(Real(-1), x), Times(Real(2), x)))

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 0)
    assert np.isclose(result_allsmt, 0)
    assert np.isclose(result_pa, 0)
    assert np.isclose(result_sa_pa, 0)
    assert np.isclose(result_sa_pa_sk, 0)


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

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 0)
    assert np.isclose(result_allsmt, 0)
    assert np.isclose(result_pa, 0)
    assert np.isclose(result_sa_pa, 0)
    assert np.isclose(result_sa_pa_sk, 0)


def test_aliases():
    chi = And(GE(x, Real(0)), Equals(y, Plus(x, Real(-2))), LE(y, Real(4)))

    w = y

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 6)
    assert np.isclose(result_allsmt, 6)
    assert np.isclose(result_pa, 6)
    assert np.isclose(result_sa_pa, 6)
    assert np.isclose(result_sa_pa_sk, 6)


def test_aliases_leads_to_not_sat():
    chi = And(GE(x, Real(0)), LE(x, Real(2)), Equals(y, x), LE(x - y, Real(-2)))

    wmi = WMI(chi)

    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 0)
    assert np.isclose(result_allsmt, 0)
    assert np.isclose(result_pa, 0)
    assert np.isclose(result_sa_pa, 0)
    assert np.isclose(result_sa_pa_sk, 0)


def test_batch_of_query_constant_weight():
    chi = And(GE(x, Real(0)), LE(x, Real(4)))

    phi1 = LE(x, Real(2))
    phi2 = GE(x, Real(2))

    wmi = WMI(chi)

    result_bc, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeMI_batch([phi1, phi2], mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc[0], 2)
    assert np.isclose(result_bc[1], 2)
    assert np.isclose(result_allsmt[0], 2)
    assert np.isclose(result_allsmt[1], 2)
    assert np.isclose(result_pa[0], 2)
    assert np.isclose(result_pa[1], 2)
    assert np.isclose(result_sa_pa[0], 2)
    assert np.isclose(result_sa_pa[1], 2)
    assert np.isclose(result_sa_pa_sk[0], 2)
    assert np.isclose(result_sa_pa_sk[1], 2)


def test_batch_of_query():
    chi = And(GE(x, Real(0)), LE(x, Real(2)))

    phi1 = LE(x, Real(1))
    phi2 = GE(x, Real(1))

    w = x

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI_batch([phi1, phi2], mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc[0], 0.5)
    assert np.isclose(result_bc[1], 1.5)
    assert np.isclose(result_allsmt[0], 0.5)
    assert np.isclose(result_allsmt[1], 1.5)
    assert np.isclose(result_pa[0], 0.5)
    assert np.isclose(result_pa[1], 1.5)
    assert np.isclose(result_sa_pa[0], 0.5)
    assert np.isclose(result_sa_pa[1], 1.5)
    assert np.isclose(result_sa_pa_sk[0], 0.5)
    assert np.isclose(result_sa_pa_sk[1], 1.5)


def test_setting_domA():
    chi = And(GE(x, Real(0)), LE(x, Real(2)), a)

    wmi = WMI(chi)
    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC, domA={a, b})
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT, domA={a, b})
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA, domA={a, b})
    result_sa_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA, domA={a, b})
    result_sa_pa_sk, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA_SK, domA={a, b})
    assert np.isclose(result_bc, 2 * 2)
    assert np.isclose(result_allsmt, 2 * 2)
    assert np.isclose(result_pa, 2 * 2)
    assert np.isclose(result_sa_pa, 2 * 2)
    assert np.isclose(result_sa_pa_sk, 2 * 2)


def test_double_assignment_same_variable_no_theory_consistent():
    chi = And(
        GE(x, Real(0)),
        Equals(y, Plus(x, Real(-2))),
        Equals(y, Plus(x, Real(5))),
        LE(y, Real(4)),
    )

    wmi = WMI(chi)

    result_bc, _ = wmi.computeMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 0)
    assert np.isclose(result_allsmt, 0)
    assert np.isclose(result_pa, 0)
    assert np.isclose(result_sa_pa, 0)
    assert np.isclose(result_sa_pa_sk, 0)


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

    wmi = WMI(chi, w)

    result_bc, _ = wmi.computeWMI(phi, mode=WMI.MODE_BC)
    result_allsmt, _ = wmi.computeWMI(phi, mode=WMI.MODE_ALLSMT)
    result_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_PA)
    result_sa_pa, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA)
    result_sa_pa_sk, _ = wmi.computeWMI(phi, mode=WMI.MODE_SA_PA_SK)
    assert np.isclose(result_bc, 7)
    assert np.isclose(result_allsmt, 7)
    assert np.isclose(result_pa, 7)
    assert np.isclose(result_sa_pa, 7)
    assert np.isclose(result_sa_pa_sk, 7)


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
    wmi = WMI(chi, w, integrator=[LatteIntegrator(),
                                  VolestiIntegrator(seed=420, error=epsilon),
                                  VolestiIntegrator(seed=69, error=epsilon),
                                  ])

    for mode in [WMI.MODE_BC, WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SA_PA_SK]:
        result, n_int = wmi.computeWMI(phi, mode=mode)
        assert isinstance(n_int, np.ndarray) and n_int.shape == (3,)
        assert isinstance(result, np.ndarray) and result.shape == (3,)
        # latte is exact
        assert np.allclose(result[0], ans)
        # volesti is approximate
        assert np.allclose(result[1:], ans, rtol=epsilon)


def test_batch_of_query_multiple_integrators():
    chi = And(GE(x, Real(0)), LE(x, Real(2)))

    phi1 = LE(x, Real(1))
    phi2 = GE(x, Real(1))

    w = x

    queries = np.array([phi1, phi2])
    ans = np.array([[0.5, 1.5],])
    epsilon = 0.1

    wmi = WMI(chi, w, integrator=[LatteIntegrator(),
                                    VolestiIntegrator(seed=420, error=epsilon),
                                    VolestiIntegrator(seed=69, error=epsilon),
                                    ])
    for mode in [WMI.MODE_BC, WMI.MODE_ALLSMT, WMI.MODE_PA, WMI.MODE_SA_PA, WMI.MODE_SA_PA_SK]:
        result, n_int = wmi.computeWMI_batch(queries, mode=mode)
        assert isinstance(n_int, list) and all(isinstance(n, np.ndarray) for n in n_int)
        assert isinstance(result, list) and all(isinstance(n, np.ndarray) for n in result)
        n_int = np.array(n_int)
        result = np.array(result)
        assert n_int.shape == (2, 3)
        assert result.shape == (2, 3)
        result = result.transpose()
        # latte is exact
        assert np.allclose(result[0], ans)
        # volesti is approximate
        assert np.allclose(result[1:], ans, rtol=epsilon)
