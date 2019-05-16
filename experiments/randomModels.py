from random import choice, randint, random, sample, seed, shuffle, uniform

from numpy.random import seed as numseed

from pysmt.shortcuts import BOOL, REAL, Symbol, Plus, Times, Pow, Ite, Real, \
    And, Or, Not, LT, serialize, Bool, is_sat


from sympy import div
from sympy.polys.polyerrors import ComputationFailed

from wmipa.sympy2pysmt import pysmt2sympy, sympy2pysmt

class ModelGenerator:

    TEMPL_REALS = "x_{}"
    TEMPL_BOOLS = "A_{}"

    # maximum (absolute) value a variable can take
    DOMAIN_BOUNDS = [0, 1]
    # maximum exponent
    MAX_EXPONENT = 2
    # maximum number of monomials in each FI polynomial function
    MAX_MONOMIALS = 3
    # maximum number of children of a formula's internal node
    MAX_BREADTH = 4
    # maximum number of squared rational functions used to sample
    # non-negative polynomials
    MAX_SRF = 4

    def __init__(self, n_reals, n_bools, seedn=None,
                 templ_bools=TEMPL_BOOLS,
                 templ_reals=TEMPL_REALS,
                 initial_bounds=DOMAIN_BOUNDS):
        assert(n_reals + n_bools > 0)
        
        # initialize the real/boolean variables
        self.reals = []
        for i in range(n_reals):
            self.reals.append(Symbol(templ_reals.format(i), REAL))
        self.bools = []
        for i in range(n_bools):
            self.bools.append(Symbol(templ_bools.format(i), BOOL))

        self.domain_bounds = dict()
        self.initial_bounds = initial_bounds
        # set the seed number, if specified
        if seedn != None:
            self.seedn = seedn
            seed(seedn)
            numseed(seedn)

    def generate_support_tree(self, depth):
        domain = []
        
        # generate the domains of the real variables
        for var in self.reals:
            lower, upper = self.initial_bounds
            dom_formula = And(LT(Real(lower), var), LT(var, Real(upper)))
            domain.append(dom_formula)
        domain = And(domain)

        # generate the support
        support = Bool(False)
        while not is_sat(And(domain, support)):
            support = self._random_formula(depth)
        return And(domain, support)
        
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

    def _random_polynomial(self, nonnegative=False):
        if nonnegative:
            # the sum of squared rational functions is a non-negative polynomial
            sq_sum = []
            for _ in range(randint(1, self.MAX_SRF)):
                poly = self._random_polynomial()
                sq_sum.append(Times(poly,poly))
                
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
            
        bound = ModelGenerator._random_coefficient(0, len(self.reals))
        return LT(Plus(monomials), bound)

    @staticmethod
    def _random_coefficient(min_value=-1, max_value=1):
        coeff = 0
        while coeff == 0:
            coeff = uniform(min_value, max_value)
        return Real(coeff)


if __name__ == '__main__':
    import argparse
    import sys
    import os
    import time
    from os import path
    from pysmt.shortcuts import write_smtlib
    
    def positive_0(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError('Expected positive integer, found {}'.format(value))
        return ivalue
        
    def positive(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError('Expected positive integer (no 0), found {}'.format(value))
        return ivalue
    
    parser = argparse.ArgumentParser(description='Generates random support and models.')
    parser.add_argument('output_dir', help='Name of the directory where all models will be created')
    parser.add_argument('-r', '--reals', default=3, type=positive, help='Maximum number of real variables (default: 3)')
    parser.add_argument('-b', '--booleans', default=3, type=positive_0, help='Maximum number of bool variables (default: 3)')
    parser.add_argument('-d', '--depth', default=3, type=positive, help='Depth of the formula tree (default: 3)')
    parser.add_argument('-m', '--models', default=20, type=positive, help='Number of model files (default: 20)')
    parser.add_argument('-s', '--seed', type=positive_0, help='Random seed')
    
    args = parser.parse_args()

    n_reals = args.reals
    n_bools = args.booleans
    depth = args.depth
    n_models = args.models
    seedn = args.seed
    if seedn is None:
        seedn = randint(0, 10000000)
    output_dir = '{}_r{}_b{}_d{}_s{}'.format(args.output_dir, n_reals, n_bools, depth, seedn)
    
    # check if dir exists
    if (path.exists(output_dir)):
        print("Folder {} already exists, remove it and retry")
        sys.exit(1)
    
    # create dir
    os.mkdir(output_dir)
    print("Created folder '{}'".format(output_dir))
    
    # set seed
    seed(seedn)
    numseed(seedn)
    
    print("Creating models")
    time_start = time.time()
    for i in range(n_models):
        gen = ModelGenerator(n_reals, n_bools)
        support = gen.generate_support_tree(depth)        
        weight = gen.generate_weights_tree(depth)

        support_filename = path.join(output_dir, "r{}_b{}_{}.support".format(n_reals, n_bools, i+1))
        weight_filename = path.join (output_dir, "r{}_b{}_{}.weight".format(n_reals, n_bools, i+1))
        
        write_smtlib(support, support_filename)
        write_smtlib(weight, weight_filename)
        
        print("\r"*100, end='')
        print("Model {}/{}".format(i+1, n_models), end='')
        
    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))
