from typing import Collection

import numpy as np
from pysmt.environment import Environment
from pysmt.fnode import FNode

from wmipa.core.inequality import Inequality


class Polytope:
    """Internal class for convex H-polytopes.

    Attributes:
        inequalities: list of wmipa.core.Inequality
        N: the number of variables
    """

    def __init__(
        self,
        expressions: Collection[FNode],
        variables: Collection[FNode],
        env: Environment,
    ):
        """Default constructor for a H-polytope defined on an ordered list of variables (the continuous integration domain).

        Args:
           expressions: list of linear inequalities in pysmt format
           variables: the continuous integration domain
           env: the pysmt environment
        """
        self.inequalities = [Inequality(e, variables, env) for e in expressions]
        self.N = len(variables)
        self.mgr = env.formula_manager

    def to_pysmt(self) -> FNode:
        """Returns a pysmt formula (FNode) encoding the polytope."""
        if not self.inequalities:
            return self.mgr.Bool(True)
        return self.mgr.And(*map(lambda x: x.to_pysmt(), self.inequalities))

    def to_numpy(self) -> tuple[np.ndarray, np.ndarray]:
        """Converts the polytope to a pair of numpy arrays.

        Note: information on the strictness of each inequality is discarded.

        Returns:
            Two numpy arrays A, b encoding the polytope

              A x {<=/<} b
        """
        A, b = [], []
        const_key = tuple(0 for _ in range(self.N))
        key = lambda i: tuple(1 if j == i else 0 for j in range(self.N))
        for ineq in self.inequalities:
            b.append(-ineq.polynomial.monomials.get(const_key, 0))
            A.append([ineq.polynomial.monomials.get(key(i), 0) for i in range(self.N)])

        return np.array(A), np.array(b)

    def __str__(self) -> str:
        return "\n".join(["[" + str(b) + "]" for b in self.inequalities])
