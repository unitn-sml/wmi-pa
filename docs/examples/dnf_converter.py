from pysmt.shortcuts import *
from wmipa.enumeration import SAEnumerator


def to_dnf(formula, smt_env):
    partial_enumerator = SAEnumerator(formula, Real(1), smt_env)
    disjuncts = []
    for ta, _ in partial_enumerator.enumerate(Bool(True)):
        conj = And(*[atom if is_true else Not(atom) for atom, is_true in ta.items()])
        disjuncts.append(conj)

    print("N. disjuncts:", len(disjuncts))
    return Or(*disjuncts)


smt_env = get_env()

x = Symbol("x", REAL)
y = Symbol("y", REAL)

formula = support = And(
    LE(Real(0), x),
    LE(Real(0), y),
    LE(x, Real(1)),
    LE(y, Real(1)),
    Or(
        GE(y, Plus(x, Real(1 / 4))),
        LE(y, Plus(x, Real(-1 / 4))),
        LE(Plus(x, y), Real(3 / 4)),
        GE(Plus(x, y), Real(5 / 4)),
    ),
)

dnf = to_dnf(formula, smt_env)

print("Equivalent?", not is_sat(Not(Iff(formula, dnf))))
