

from random import choice, randint, random, sample, seed, shuffle

from numpy.random import seed as numseed

from pysmt.shortcuts import Symbol, Plus, Times, Pow, Ite, Real, And, Or, Not, \
    LE, LT
from pysmt.typing import *

from sympy import div
from sympy.polys.polyerrors import ComputationFailed

from wmipa.sympy2pysmt import pysmt2sympy, sympy2pysmt

class ModelGenerator:

    TEMPL_REALS = "x_{}"
    TEMPL_BOOLS = "A_{}"

    # maximum (absolute) value a variable can take
    DOMAIN_BOUNDS = 100
    # maximum multiplicative constant
    MAX_COEFFICIENT = 10
    # maximum exponent
    MAX_EXPONENT = 2
    # maximum number of monomials in each FI polynomial function
    MAX_MONOMIALS = 3
    # maximum number of children of a formula's internal node
    MAX_BREADTH = 4
    # maximum number of squared rational functions used to sample
    # non-negative polynomials
    MAX_SRF = 4

    def __init__(self, n_reals, n_bools, seedn=None):
        assert(n_reals + n_bools > 0)
        # initialize the real/boolean variables
        self.reals = []
        for i in range(n_reals):
            self.reals.append(Symbol(self.TEMPL_REALS.format(i), REAL))
        self.bools = []
        for i in range(n_bools):
            self.bools.append(Symbol(self.TEMPL_BOOLS.format(i)))

        # set the seed number, if specified
        if seedn != None:
            self.seedn = seedn
            seed(seedn)
            numseed(seedn)

    def generate_support_cond(self, real_only=True):
        subformulas = []
        # generate the domains of the real variables
        for rvar in self.reals:
            subformulas.append(ModelGenerator._random_domain(rvar))

        if not real_only:
            subformulas.append(self._random_boolean_formula(depth))

        return And(subformulas)

    def generate_weights_cond(self, n_real_cond, n_bool_cond):

        # TODO: what about overlapping?        
        lra_conditions = [self._random_inequality() for _ in range(n_real_cond)]
        bool_conditions = [self._random_boolean_formula(1)
                           for _ in range(n_bool_cond)]

        conditions = lra_conditions + bool_conditions
        n_cond = n_real_cond + n_bool_cond
        n_leaves = n_cond + 1
        leaves = [self._random_polynomial() for _ in range(n_leaves)]
        shuffle(conditions)

        nodes = conditions + leaves
        i = n_cond - 1
        while i >= 0:
            nodes[i] = Ite(nodes[i], nodes[2*i+1], nodes[2*i+2])
            i -= 1

        return nodes[0]

    def generate_cond_problem(self, n_real_cond, n_bool_cond):
        lra_conditions = [self._random_inequality() for _ in range(n_real_cond)]
        bool_conditions = [self._random_boolean_formula(1)
                           for _ in range(n_bool_cond)]

        conditions = lra_conditions + bool_conditions
        n_cond = n_real_cond + n_bool_cond
        n_leaves = n_cond + 1
        shuffle(conditions)
        polynomials = [self._random_polynomial() for _ in range(n_leaves)]
        w_nodes = conditions + polynomials
        #subdomains = [self.generate_support_cond() for _ in range(n_leaves)]
        #chi_nodes = conditions + subdomains

        support = And([Implies(cond, self.generate_support_cond())
                       for cond in conditions])

        i = n_cond - 1
        while i >= 0:
            w_nodes[i] = Ite(w_nodes[i], w_nodes[2*i+1], w_nodes[2*i+2])
            #chi_nodes[i] = Ite(chi_nodes[i], chi_nodes[2*i+1], chi_nodes[2*i+2])
            i -= 1

        #return w_nodes[0], chi_nodes[0]
        return w_nodes[0], support
        

    def generate_support_tree(self, depth, domains=None):
        subformulas = []
        if domains != None:
            assert(len(domains) == len(self.reals))
            for i, dom in enumerate(domains):
                lower, upper = dom
                var = self.reals[i]
                dom_formula = And(LE(Real(lower), var), LE(var, Real(upper)))
                subformulas.append(dom_formula)
        else:
            # generate the domains of the real variables
            for rvar in self.reals:
                subformulas.append(ModelGenerator._random_domain(rvar))

        # generate the support
        subformulas.append(self._random_formula(depth))
        return And(subformulas)

    def generate_support_ijcai17(self, n_conjuncts, max_disjunct_size, atr=0.5):
        subformulas = []
        for rvar in self.reals:
            subformulas.append(ModelGenerator._random_domain(rvar))

        for _ in range(n_conjuncts):
            size = randint(1, max_disjunct_size + 1)
            lra_size = int(size * atr)
            bool_size = size - lra_size
            bool_disj = Or(sample(self.bools, bool_size))
            lra_conj = []
            for _ in range(lra_size):
                lra_conj.append(self._random_inequality())
                
            disj = Or(And(lra_conj), bool_disj)
            subformulas.append(disj)
            
        return And(subformulas)    

    def generate_weights_tree(self, depth, nonnegative=False, splits_only=False):
        if depth <= 0:
            return self._random_polynomial(nonnegative)
        else:
            if splits_only:
                op = Ite
            else:
                op = choice([Ite, Plus, Times])

            left = self.generate_weights_tree(depth - 1, nonnegative)
            right = self.generate_weights_tree(depth - 1, nonnegative)
            if op == Ite:
                cond = self._random_formula(depth)
                return op(cond, left, right)
            else:
                return op(left, right)

    def generate_weights_ijcai17(self, pos_only=True, nonnegative=False):
        subformulas = []
        for a in self.bools:
            pos = self._random_polynomial(nonnegative)
            neg = Real(1) if pos_only else self._random_polynomial(nonnegative)
            subformulas.append(Ite(a, pos, neg))
        return Times(subformulas)
        
    def _random_polynomial(self, nonnegative=False):
        if nonnegative:
            # the sum of squared rational functions is a non-negative polynomial
            sq_sum = []
            for _ in range(randint(1, self.MAX_SRF)):
                poly = self._random_polynomial()
                sq_sum.append(Times(poly,poly))
                """
                srf = None
                while srf is None:
                    p = pysmt2sympy(self._random_polynomial())
                    q = pysmt2sympy(self._random_polynomial())
                    try:
                        #srf = sum(div(p,q))
                        srf = sum(div(p,1))
                    except ZeroDivisionError:
                        continue
                    except ComputationFailed:
                        continue

                    print("P:",p)
                    print("Q:",q)
                    print("SRF:", srf)

                sq_sum.append(sympy2pysmt(srf**2))
                """
                
            return Plus(sq_sum)

        else:
            monomials = []
            for i in range(randint(1, self.MAX_MONOMIALS)):
                monomials.append(self._random_monomial())
            return Plus(monomials)


    def _random_monomial(self, minsize=None, maxsize=None):
        minsize = minsize if minsize else 1
        maxsize = maxsize if maxsize else len(self.reals)
        size = randint(minsize, maxsize)
        rvars = sample(self.reals, size)
        coeff = self._random_coefficient()
        pows = [coeff]
        for rvar in rvars:
            exponent = randint(0, self.MAX_EXPONENT)
            pows.append(Pow(rvar, Real(exponent)))

        return Times(pows)

    def _random_boolean_formula(self, depth):
        return self._random_formula(depth, theta=0.0)

    def _random_lra_formula(self, depth):
        return self._random_formula(depth, theta=1.0)    
        
    def _random_formula(self, depth, theta=0.5):
        if depth <= 0:
            return self._random_atom(theta)
        else:            
            op = choice([And, Or, Not])
            if op == Not:
                return Not(self._random_formula(depth, theta))
            else:
                breadth = randint(2, self.MAX_BREADTH)
                children = [self._random_formula(depth - 1, theta)
                            for _ in range(breadth)]
                return op(children)

    def _random_atom(self, theta=0.5):
        if len(self.bools) == 0:
            return self._random_inequality()
        elif len(self.reals) == 0:
            return self._random_boolean()            
        elif random() < theta:
            return self._random_inequality()
        else:
            return self._random_boolean()

    def _random_boolean(self):
        return choice(self.bools)
        
    def _random_inequality(self, minsize=None, maxsize=None):
        minsize = max(1, minsize) if minsize else 1
        maxsize = min(maxsize, len(self.reals)) if maxsize else len(self.reals)
        size = randint(minsize, maxsize)
        rvars = sample(self.reals, size)
        monomials = []
        for rvar in rvars:
            coeff = ModelGenerator._random_coefficient()
            monomials.append(Times(coeff, rvar))
            
        bound = ModelGenerator._random_coefficient()
        return choice([LE,LT])(Plus(monomials), bound)

    @staticmethod
    def _random_coefficient():
        maxc = ModelGenerator.MAX_COEFFICIENT
        return Real(randint(-maxc, maxc))
                        
    @staticmethod
    def _random_domain(var):
        lower = -randint(0, ModelGenerator.DOMAIN_BOUNDS)
        upper = randint(0, ModelGenerator.DOMAIN_BOUNDS)
        return And(LE(Real(lower), var), LE(var, Real(upper)))


if __name__ == '__main__':
    from pysmt.shortcuts import Bool, write_smtlib
    from sys import argv
    
    output_name = argv[1]
    n_reals = int(argv[2])
    n_bools = int(argv[3])
    depth = int(argv[4])
    seedn = int(argv[5])
    
    gen = ModelGenerator(n_reals, n_bools, seedn)
    support = gen.generate_support_tree(depth)        
    weights = gen.generate_weights_tree(depth)
    query = Bool(True)

    support_filename = output_name + "_0.support"
    weights_filename = output_name + "_0.weights"
    query_filename = output_name + "_0.query"

    write_smtlib(support, support_filename)
    write_smtlib(weights, weights_filename)
    write_smtlib(query, query_filename)
