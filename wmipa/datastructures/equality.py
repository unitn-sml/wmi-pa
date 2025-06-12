
import pysmt.shortcuts as smt
from wmipa.datastructures.polynomial import Polynomial

class Equality:

    def __init__(self, expr, variables):
        if not expr.is_equals():
            raise ValueError("Not an equality")

        left, right = equality.args()
        if left.is_symbol(smt.REAL):
            self.alias, self.expr = left, Polynomial(right, variables)
        elif right.is_symbol(smt.REAL):
            self.alias, self.expr = right, Polynomial(left, variables)
        else:
            raise ValueError("Malformed alias {equality}")

    def to_pysmt(self):
        return smt.Equals(self.alias, self.expr.to_pysmt())


        
        
