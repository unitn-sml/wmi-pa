from typing import Collection

from pysmt.environment import Environment
from pysmt.fnode import FNode
from pysmt.typing import REAL

from wmipa.datastructures.polynomial import Polynomial


class Equality:

    def __init__(self, expr: FNode, variables: Collection[FNode], env: Environment):
        if not expr.is_equals():
            raise ValueError("Not an equality")

        left, right = expr.args()
        if left.is_symbol(REAL):
            self.alias, self.expr = left, Polynomial(right, variables, env=env)
        elif right.is_symbol(REAL):
            self.alias, self.expr = right, Polynomial(left, variables, env=env)
        else:
            raise ValueError("Malformed alias {equality}")
        self.mgr = env.formula_manager

    def to_pysmt(self) -> FNode:
        return self.mgr.Equals(self.alias, self.expr.to_pysmt())
