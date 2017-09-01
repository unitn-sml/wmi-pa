

from random import seed, random, randint, sample, choice

from pysmt.shortcuts import Symbol, Plus, Times, Pow, Ite, Real, And, Or, Not, \
    LE, LT
from pysmt.typing import *

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

    MODE_IJCAI = "MODE_IJCAI"
    MODE_TREE = "MODE_TREE"

    MODES = [MODE_IJCAI, MODE_TREE]

    def __init__(self, n_reals, n_bools, seedn=None):
        # initialize the real/boolean variables
        self.reals = []
        for i in xrange(n_reals):
            self.reals.append(Symbol(self.TEMPL_REALS.format(i), REAL))
        self.bools = []
        for i in xrange(n_bools):
            self.bools.append(Symbol(self.TEMPL_BOOLS.format(i)))

        # set the seed number, if specified
        if seedn != None:
            self.seedn = seedn
            seed(seedn)

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

    def generate_support_legacy(self, n_conjuncts, max_disjunct_size, atr=0.5):
        subformulas = []
        for rvar in self.reals:
            subformulas.append(ModelGenerator._random_domain(rvar))

        for _ in xrange(n_conjuncts):
            size = randint(1, max_disjunct_size + 1)
            lra_size = int(size * atr)
            bool_size = size - lra_size
            bool_disj = Or(sample(self.bools, bool_size))
            lra_conj = []
            for _ in xrange(lra_size):
                lra_conj.append(self._random_inequality())
                
            disj = Or(And(lra_conj), bool_disj)
            subformulas.append(disj)
            
        return And(subformulas)    

    def generate_weights_tree(self, depth):
        if depth <= 0:
            return self._random_polynomial()
        else:
            op = choice([Ite, Plus, Times])
            left = self.generate_weights_tree(depth - 1)
            right = self.generate_weights_tree(depth - 1)
            if op == Ite:
                cond = self._random_formula(depth)
                return op(cond, left, right)
            else:
                return op(left, right)

    def generate_weights_legacy(self, pos_only=True):
        subformulas = []
        for a in self.bools:
            pos = self._random_polynomial()
            neg = Real(1) if pos_only else self._random_polynomial()
            subformulas.append(Ite(a, pos, neg))
        return Times(subformulas)
        
    def _random_polynomial(self):
        monomials = []
        for i in xrange(randint(1, self.MAX_MONOMIALS)):
            monomials.append(self._random_monomial())
        return Plus(monomials)

    def _random_monomial(self):
        size = randint(1, len(self.reals))
        rvars = sample(self.reals, size)
        coeff = self._random_coefficient()
        pows = [coeff]
        for rvar in rvars:
            exponent = Real(randint(0, self.MAX_EXPONENT))
            pows.append(Pow(rvar, exponent))
        return Times(pows)
        
    def _random_formula(self, depth):
        if depth <= 0:
            return self._random_atom()
        else:            
            op = choice([And, Or, Not])
            if op == Not:
                return Not(self._random_formula(depth))
            else:
                breadth = randint(2, self.MAX_BREADTH)
                children = [self._random_formula(depth - 1)
                            for _ in xrange(breadth)]
                return op(children)

    def _random_atom(self):
        return choice([self._random_inequality, self._random_boolean])()

    def _random_boolean(self):
        return choice(self.bools)
        
    def _random_inequality(self):        
        size = randint(1, len(self.reals))
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
