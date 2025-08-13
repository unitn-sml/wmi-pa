import numpy as np
import pysmt.shortcuts as smt
from pysmt.typing import BOOL, REAL

from wmipa.solvers import AllSMTSolver
from wmipa.enumeration import Z3Enumerator, SAEnumerator
from wmipa.integration import LattEIntegrator

a = smt.Symbol("A", BOOL)
b = smt.Symbol("B", BOOL)
c = smt.Symbol("C", BOOL)
d = smt.Symbol("D", BOOL)
e = smt.Symbol("E", BOOL)
x = smt.Symbol("x", REAL)
y = smt.Symbol("y", REAL)
z = smt.Symbol("z", REAL)
phi = smt.Bool(True)
r0 = smt.Real(0)
r1 = smt.Real(1)
rn1 = smt.Real(-1)
r2 = smt.Real(2)
rn2 = smt.Real(-2)
r3 = smt.Real(3)
rn3 = smt.Real(-3)
r4 = smt.Real(4)

ENUMERATORS = [Z3Enumerator, SAEnumerator]
EXACT_INTEGRATORS = [LattEIntegrator]

def pytest_generate_tests(metafunc):
    argnames = ["enumerator", "integrator"]
    argvalues = []
    idlist = []
    # axis_aligned_cube
    for enumerator in ENUMERATORS:
        for integrator in EXACT_INTEGRATORS:
            argvalues.append((enumerator(), integrator()))
            idlist.append(f"{enumerator.__name__:>25} {integrator.__name__:>25}")

    metafunc.parametrize(argnames, argvalues, ids=idlist)


def test_no_booleans_constant_weight(enumerator, integrator):
    chi = smt.And(smt.GE(x, r0), smt.LE(x, r1))

    wmi = AllSMTSolver(chi, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, 1)


def test_no_booleans_condition_weight(enumerator, integrator):
    chi = smt.And(smt.GE(x, r0), smt.LE(x, r1))

    w = smt.Ite(smt.LE(x, smt.Real(0.5)), x, smt.Times(rn1, x))

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, -0.25)


def test_booleans_constant_weight(enumerator, integrator):
    chi = smt.And(smt.Iff(a, smt.GE(x, r0)), smt.GE(x, rn2), smt.LE(x, r1))

    wmi = AllSMTSolver(chi, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, 3)


def test_boolean_condition_weight(enumerator, integrator):
    chi = smt.And(smt.Iff(a, smt.GE(x, r0)), smt.GE(x, rn1), smt.LE(x, r1))

    w = smt.Ite(
        smt.LE(x, smt.Real(-0.5)),
        x,
        smt.Ite(a, smt.Times(rn1, x), smt.Times(r2, x)),
    )

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, -1.125)


def test_boolean_and_not_simplify(enumerator, integrator):
    chi = smt.And(
        smt.Iff(a, smt.GE(x, r0)),
        smt.Or(
            smt.And(smt.GE(x, rn3), smt.LE(x, rn2)),
            smt.And(smt.GE(x, rn1), smt.LE(x, r1)),
            smt.And(smt.GE(x, r2), smt.LE(x, r3)),
        ),
    )

    w = smt.Ite(
        smt.LE(x, smt.Real(-0.5)),
        x,
        smt.Ite(a, smt.Times(rn1, x), smt.Times(r2, x)),
    )

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, -6.125)


def test_not_boolean_satisfiable(enumerator, integrator):
    chi = smt.And(
        smt.Iff(a, smt.GE(x, r0)), smt.GE(x, rn1), smt.LE(x, r1), b, smt.Not(b)
    )

    w = smt.Ite(b, x, smt.Ite(a, smt.Times(rn1, x), smt.Times(r2, x)))

    wmi = AllSMTSolver(chi, w)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, 0)


def test_not_lra_satisfiable(enumerator, integrator):
    chi = smt.And(
        smt.Iff(a, smt.GE(x, r0)),
        smt.GE(x, rn1),
        smt.LE(x, r1),
        smt.GE(x, r2),
    )

    w = smt.Ite(b, x, smt.Ite(a, smt.Times(rn1, x), smt.Times(r2, x)))

    wmi = AllSMTSolver(chi, w)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, 0)


def test_multiplication_in_weight(enumerator, integrator):
    chi = smt.And(
        smt.Iff(a, smt.GE(x, r0)),
        smt.Or(
            smt.And(smt.GE(x, rn3), smt.LE(x, rn2)),
            smt.And(smt.GE(x, rn1), smt.LE(x, r1)),
            smt.And(smt.GE(x, r2), smt.LE(x, r3)),
        ),
    )

    w = smt.Times(smt.Ite(a, x, smt.Times(x, rn1)), x)

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]
    assert np.isclose(result, 0)


def test_aliases(enumerator, integrator):
    chi = smt.And(smt.GE(x, r0), smt.Equals(y, smt.Plus(x, rn2)), smt.LE(y, r4))
    w = y

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]

    assert np.isclose(result, 6)


def test_aliases_leads_to_not_sat(enumerator, integrator):
    chi = smt.And(smt.GE(x, r0), smt.LE(x, r2), smt.Equals(y, x), smt.LE(x - y, rn2))

    wmi = AllSMTSolver(chi, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x})
    result = ans["wmi"]

    assert np.isclose(result, 0)


def test_double_assignment_same_variable_no_theory_consistent(enumerator, integrator):
    chi = smt.And(
        smt.GE(x, r0),
        smt.Equals(y, smt.Plus(x, rn2)),
        smt.Equals(y, smt.Plus(x, smt.Real(5))),
        smt.LE(y, r4),
    )

    wmi = AllSMTSolver(chi, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x, y})
    result = ans["wmi"]

    assert np.isclose(result, 0)


def test_reserved_variables_name(enumerator, integrator):
    a = smt.Symbol("wmi_1_a", BOOL)
    b = smt.Symbol("cond_a", BOOL)
    x = smt.Symbol("query_45", REAL)
    y = smt.FreshSymbol(REAL)

    chi = smt.And(
        smt.GE(x, r0),
        smt.LE(x, r2),
        smt.GE(y, r2),
        smt.LE(y, r4),
        smt.Iff(a, smt.LE(x, r1)),
        smt.Iff(b, smt.LE(y, r3)),
    )

    w = smt.Ite(a, x, y)

    wmi = AllSMTSolver(chi, w, enumerator=enumerator, integrator=integrator)
    ans = wmi.computeWMI(phi, {x, y})
    result = ans["wmi"]

    assert np.isclose(result, 7)
