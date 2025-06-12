
import numpy as np
import pysmt.shortcuts as smt
from pysmt.operators import POW

def is_pow(expr):
    # current missing in pysmt 
    return expr.node_type() == POW

class Polynomial:

    '''Internal representation of a canonical polynomial.
    Implemented as a dict, having for each monomial: {key : coefficient}
    where key is a tuple encoding exponents of the ordered variables.

    E.g. {(2,0,1) : 3} = "3 * x^2 * y^0 * z^1"
    '''

    def __init__(self, expr, variables):
        self.monomials = Polynomial._parse(expr, variables)
        self.variables = variables
        self.ordered_keys = sorted(self.monomials.keys())    

    @property
    def degree(self):
        return max(sum(exponents) for exponents in self.monomials)

    def to_numpy(self):
        return (lambda x : np.sum(np.array([k * np.prod(np.pow(x, e), axis=1)
                                            for e, k in self.monomials.items()]).T,
                                  axis=1))

    def to_pysmt(self):
        pysmt_monos = []
        for key in self.ordered_keys:
            factors = [smt.Real(self.monomials[key])]
            for i, var in enumerate(self.variables):
                if key[i] > 1 or key[i] < 0:
                    factors.append(smt.Pow(var, smt.Real(key[i])))
                elif key[i] == 1:
                    factors.append(var)

            pysmt_monos.append(smt.Times(*factors))

        return smt.Plus(*pysmt_monos)

    def __len__(self):
        return len(self.monomials)

    def __str__(self):
        str_monos = []
        for key in self.ordered_keys:
            mono = f"{self.monomials[key]} "
            mono += " ".join([f"{var.symbol_name()}{key[i]}"
                             #" * ".join([f"{var.symbol_name()}^{key[i]}" 
                             for i, var in enumerate(self.variables)
                             if key[i] != 0])
            str_monos.append(mono)

        return " + ".join(str_monos)
        

    @staticmethod
    def _parse(expr, variables):
        N = len(variables)
        if expr.is_real_constant():
            expkey = tuple(0 for _ in range(N))
            coeff = expr.constant_value()
            monos = {expkey : coeff}
        elif expr.is_symbol(smt.REAL):            
            expkey = tuple(0 if v != expr else 1 for v in variables)
            assert(any(e != 0 for e in expkey))
            coeff = 1
            monos = {expkey : coeff}
        elif is_pow(expr):
            var, exp = expr.args()
            expkey = tuple(0 if v != var else exp.constant_value()
                   for v in variables)
            coeff = 1
            monos = {expkey : coeff}
        elif expr.is_times():
            args = expr.args()
            monofirst = Polynomial._parse(args[0], variables)
            monorest = Polynomial._parse(smt.Times(args[1:]), variables)
            monoprod = {}
            for expkey1, coeff1 in monofirst.items():
                for expkey2, coeff2 in monorest.items():                    
                    expkeynew = tuple(expkey1[i] + expkey2[i]
                                      for i in range(N))
                    coeffnew = coeff1 * coeff2                    
                    if expkeynew not in monoprod:
                        monoprod[expkeynew] = coeffnew
                    else:
                        monoprod[expkeynew] += coeffnew

            monos = monoprod

        elif expr.is_plus():
            args = expr.args()
            monofirst = Polynomial._parse(args[0], variables)
            monorest = Polynomial._parse(smt.Plus(args[1:]), variables)
            for expkey1, coeff1 in monofirst.items():
                if expkey1 not in monorest:
                    monorest[expkey1] = coeff1
                else:
                    monorest[expkey1] += coeff1

            monos = monorest

        elif expr.is_minus():
            args = expr.args()
            new_expr = smt.Plus(args[0], smt.Times(smt.Real(-1)), args[1])
            return Polynomial._parse(new_expr, variables)
        else:
            raise ValueError(f"Unhandled expression {expr}")

        #print(f"expr: {expr} --- monos: {dict(monos)}")
        return dict(monos)


        
if __name__ == '__main__':

    import numpy as np
    from pysmt.shortcuts import *

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)
    z = Symbol("z", REAL)
    variables = [x, y, z]

    '''

    p1 = Plus(Times(Real(3), Pow(x,Real(2))), Times(Real(4), Pow(y,Real(7)), z), Real(1))
    print("(p1)", str(Polynomial(p1, variables)), "\n\n\n")

    p2 = Plus(p1, p1)
    print("(p2 = p1 + p1)", str(Polynomial(p2, variables)), "\n\n\n")

    p3 = Times(p1, p1)
    print("(p3 = p1 * p1)", str(Polynomial(p3, variables)), "\n\n\n")

    p4 = Plus(p3, p2, p1)
    print("(p4 = p3 + p2 + p1)", str(Polynomial(p4, variables)), "\n\n\n")

    '''


    p = Polynomial(Plus(Times(Real(3), Pow(x,Real(2))), Times(y, z)), variables)
    f = p.to_numpy()

    x = np.array(list(range(12))).reshape(-1, 3)
    print("p:", str(p))
    print("x:", x)

    print("p(x):", f(x))
    
