from typing import Collection

import numpy as np
from pysmt.environment import Environment
from pysmt.fnode import FNode

from wmipa.datastructures.inequality import Inequality


class Polytope:
    """Internal data structure for H-polytopes."""

    def __init__(
        self,
        expressions: Collection[FNode],
        variables: Collection[FNode],
        env: Environment,
    ):
        self.inequalities = [Inequality(e, variables, env) for e in expressions]
        self.N = len(variables)
        self.H = len(expressions)
        self.mgr = env.formula_manager

    def to_pysmt(self):
        """Returns a pysmt formula (FNode) encoding the polytope."""
        if not self.inequalities:
            return self.mgr.Bool(True)
        return self.mgr.And(*map(lambda x: x.to_pysmt(), self.inequalities))

    def to_numpy(self):
        """Returns two numpy arrays A, b encoding the polytope.
        (Non-)Strictness information is discarded."""
        A, b = [], []
        const_key = tuple(0 for _ in range(self.N))
        key = lambda i: tuple(1 if j == i else 0 for j in range(self.N))
        for ineq in self.inequalities:
            b.append(-ineq.polynomial.monomials.get(const_key, 0))
            A.append([ineq.polynomial.monomials.get(key(i), 0) for i in range(self.N)])

        return np.array(A), np.array(b)

    def __str__(self):
        return "\n".join(["[" + str(b) + "]" for b in self.inequalities])


if __name__ == "__main__":

    import pysmt.shortcuts as smt

    x = smt.Symbol("x", smt.REAL)
    y = smt.Symbol("y", smt.REAL)
    variables = [x, y]

    h1 = smt.LE(
        smt.Plus(smt.Times(smt.Real(3), x), smt.Times(smt.Real(5), y), smt.Real(7)), x
    )
    h2 = smt.LE(x, y)

    p = Polytope([h1, h2], variables, smt.get_env())
    print("p:", p)
    print("pysmt:", smt.serialize(p.to_pysmt()))
    A, b = p.to_numpy()
    print("A:", A)
    print("b:", b)
