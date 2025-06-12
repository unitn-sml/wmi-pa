
import numpy as np
from pysmt.shortcuts import LT, And, Bool, Plus, Real, Symbol, Times, REAL
from wmipa.datastructures.inequality import Inequality

class Polytope:

    ''' Internal data structure for H-polytopes. '''

    def __init__(self, expressions, variables):
        self.inequalities = [Inequality(e, variables)
                             for e in expressions]
        self.N = len(variables)
        self.H = len(expressions)

    def to_pysmt(self):
        ''' Returns a pysmt formula (FNode) encoding the polytope. '''
        if not self.inequalities:
            return Bool(True)
        return And(*map(lambda x: x.to_pysmt(), self.inequalities))

    def to_numpy(self):
        ''' Returns two numpy arrays A, b encoding the polytope.
        (Non-)Strictness information is discarded.'''
        A, b = [], []
        const_key = tuple(0 for _ in range(self.N))
        key = lambda i : tuple(1 if j == i else 0 for j in range(self.N))
        for ineq in self.inequalities:
            b.append(-ineq.polynomial.monomials.get(const_key, 0))
            A.append([ineq.polynomial.monomials.get(key(i), 0) for i in range(self.N)])

        return np.array(A), np.array(b)


    def __str__(self):
        return "\n".join(["[" + str(b) + "]"
                          for b in self.inequalities])


if __name__ == '__main__':

    from pysmt.shortcuts import *

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)
    variables = [x, y]

    h1 = LE(Plus(Times(Real(3), x),
                 Times(Real(5), y),
                 Real(7)), x)
    h2 = LE(x, y)

    p = Polytope([h1, h2], variables)
    print("p:",p)
    print("pysmt:", serialize(p.to_pysmt()))
    A, b = p.to_numpy()
    print("A:", A)
    print("b:", b)

        
        
