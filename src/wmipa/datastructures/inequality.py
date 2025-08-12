from typing import Any, Collection

from pysmt.environment import Environment
from pysmt.fnode import FNode

from wmipa.datastructures.polynomial import Polynomial


class Inequality:
    """Internal representations of inequalities in canonical form:

    Polynomial {<,<=} 0

    where Polynomial is also in canonical form.

    """

    def __init__(self, expr: FNode, variables: Collection[FNode], env: Environment):
        if expr.is_le() or expr.is_lt():
            self.strict = expr.is_lt()
        else:
            raise ValueError("Not an inequality")

        self.mgr = env.formula_manager

        if len(variables) == 0:
            raise ValueError("Empty variables list")

        p1, p2 = expr.args()
        # (p1 OP p2) => (p1 - p2 OP 0)
        poly_sub = self.mgr.Plus(p1, self.mgr.Times(self.mgr.Real(-1), p2))
        self.polynomial = Polynomial(poly_sub, variables, env)
        assert self.polynomial.degree == 1

    def to_pysmt(self) -> FNode:
        op = self.mgr.LT if self.strict else self.mgr.LE
        return op(self.polynomial.to_pysmt(), self.mgr.Real(0))

    def __str__(self) -> str:
        opstr = "<" if self.strict else "<="
        return f"({str(self.polynomial)}) {opstr} 0"

    def __eq__(self, other: Any) -> bool:
        # TODO: this shouldn't be needed
        raise NotImplementedError()

    def __hash__(self) -> int:
        # TODO: this should be needed
        # return hash(self.constant)
        raise NotImplementedError()
