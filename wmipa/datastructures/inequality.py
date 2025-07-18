import pysmt.shortcuts as smt
from wmipa.datastructures.polynomial import Polynomial


class Inequality:
    """Internal representations of inequalities in canonical form:

    Polynomial {<,<=} 0

    where Polynomial is also in canonical form.

    """

    def __init__(self, expr, variables):
        if expr.is_le() or expr.is_lt():
            self.strict = expr.is_lt()
        else:
            raise ValueError("Not an inequality")

        p1, p2 = expr.args()
        # (p1 OP p2) => (p1 - p2 OP 0)
        polysub = smt.Plus(p1, smt.Times(smt.Real(-1), p2))
        self.polynomial = Polynomial(polysub, variables)
        assert self.polynomial.degree == 1

    def to_pysmt(self):
        op = smt.LT if self.strict else smt.LE
        return op(self.polynomial.to_pysmt(), smt.Real(0))

    def __str__(self):
        opstr = "<" if self.strict else "<="
        return f"({str(self.polynomial)}) {opstr} 0"

    def __eq__(self, other):
        # TODO: this shouldn't be needed
        raise NotImplementedError()

    def __hash__(self):
        # TODO: this should be needed
        # return hash(self.constant)
        raise NotImplementedError()
