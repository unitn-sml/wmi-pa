from itertools import product

import numpy as np
import pysmt.shortcuts as smt

from wmipa.solvers import AllSMTSolver



x = smt.Symbol("X", smt.REAL)
y = smt.Symbol("Y", smt.REAL)
a = smt.Symbol("A", smt.BOOL)
b = smt.Symbol("B", smt.BOOL)

unit_hypercube = smt.And(
    *[smt.And(smt.LE(smt.Real(0), var), smt.LE(var, smt.Real(1))) for var in [x, y]]
)

oblique1 = smt.LE(y, x)
oblique2 = smt.LE(smt.Plus(x, y), smt.Real(1))

prop1 = smt.Or(a, b)
prop2 = smt.And(smt.Or(a, b), smt.Not(smt.And(a, b)))

f1 = unit_hypercube
f2 = smt.And(unit_hypercube, oblique1)
f3 = smt.And(unit_hypercube, smt.Or(prop1, oblique1))
f4 = smt.And(unit_hypercube, prop1, oblique1, smt.Or(prop2, oblique2))

k = smt.Real(1)
w1 = smt.Ite(oblique2, k, k)
w2 = smt.Ite(oblique2, smt.Ite(prop2, k, k), k)

SUPPORTS = [f1, f2, f3, f4]
WEIGHTS = [k, w1, w2]

INSTANCES = list(product(SUPPORTS, WEIGHTS))

##################################################


def pytest_generate_tests(metafunc):
    argnames = ["support", "weight"]
    argvalues = []
    idlist = []
    for ncase, support_weight in enumerate(INSTANCES):
        print(ncase, support_weight)
        argvalues.append((support_weight[0], support_weight[1]))
        idlist.append(f"case {ncase}")
    metafunc.parametrize(argnames, argvalues, ids=idlist)


def test_enumerators(enumerators, support, weight):
    """
    - Every truth assignment (TA) is satisfiable in conjunction with the support
    - Every TA corresponds to a leaf in the weight function
    - TAs are pairwise inconsistent
    - The disjunction of TAs is equivalent to the support
    """

    def ta_to_formula(ta):
        literals = []
        for atom, value in ta.items():
            literals.append(atom if value else smt.Not(atom))

        return smt.And(*literals)

    for enumerator_class, kwargs in enumerators:
        enumerator = enumerator_class(**kwargs)
        wmisolver = AllSMTSolver(support, weight, enumerator=enumerator)
        truth_assignments = list(enumerator.enumerate(smt.Bool(True)))
        nta = len(truth_assignments)

        for ta, _ in truth_assignments:
            assert smt.is_sat(
                smt.And(support, ta_to_formula(ta))
            ), f"Enumerator returned an UNSAT TA"

            assert wmisolver.weights.weight_from_assignment(
                ta
            ).is_constant(), (
                "Enumerator returned a TA that doesn't correspond to a unconditional weight"
            )

            for i in range(nta - 1):
                for j in range(i + 1, nta):
                    fi = ta_to_formula(truth_assignments[i][0])
                    fj = ta_to_formula(truth_assignments[j][0])
                    assert not smt.is_sat(
                        smt.And(fi, fj)
                    ), f"Enumerator returned two non-disjoint TAs"

            union_tas = smt.Or(*[ta_to_formula(ta) for ta, _ in truth_assignments])
            assert not smt.is_sat(
                smt.Not(smt.Iff(support, union_tas))
            ), "Enumerator returned a non-exhaustive list of TAs"
