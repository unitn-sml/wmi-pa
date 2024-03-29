import argparse
import os
import sys
import time
from math import log10
from os import path
from random import choice, randint, random, sample, seed, uniform

from pysmt.shortcuts import BOOL, LT, REAL, And, Bool, Ite, Not, Or, Plus, Pow, Real, Symbol, Times, is_sat
from pywmi import Density, Domain

from utils.io import check_path_exists, check_path_not_exists
from wmipa.integration.sympy2pysmt import get_canonical_form
from wmipa.utils import get_random_sum


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
    # maximum number of squared rational functions used to sample non-negative polynomials
    MAX_SRF = 4

    def __init__(
            self,
            n_reals,
            n_bools,
            seedn=None,
            templ_bools=TEMPL_BOOLS,
            templ_reals=TEMPL_REALS,
            initial_bounds=DOMAIN_BOUNDS,
    ):
        assert n_reals + n_bools > 0

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
        if seedn is not None:
            self.seedn = seedn
            seed(seedn)

    def generate_support_tree(self, depth):
        domain = []
        bounds = {}

        # generate the domains of the real variables
        for var in self.reals:
            lower, upper = self.initial_bounds
            dom_formula = And(LT(Real(lower), var), LT(var, Real(upper)))
            bounds[var.symbol_name()] = [lower, upper]
            domain.append(dom_formula)
        domain = And(domain)

        # generate the support
        support = Bool(False)
        while not is_sat(And(domain, support)):
            support = self._random_formula(depth)
        return And(domain, support), bounds

    def generate_weights_tree(self, depth, nonnegative=True, splits=True, plus=True, times=True,
                              polynomials_degree=None):
        if depth <= 0:
            poly = self._random_polynomial(nonnegative, degree=polynomials_degree)
            # self._check_polynomial_degree(poly)
            return poly
        else:
            assert any([splits, plus, times])
            operators = []
            if splits:
                operators.append(Ite)
            if plus:
                operators.append(Plus)
            if times:
                operators.append(Times)
            op = choice(operators)

            left = self.generate_weights_tree(depth - 1, nonnegative=nonnegative, splits=splits, plus=plus, times=times,
                                              polynomials_degree=polynomials_degree)
            right = self.generate_weights_tree(depth - 1, nonnegative=nonnegative, splits=splits, plus=plus,
                                               times=times, polynomials_degree=polynomials_degree)
            if op == Ite:
                cond = self._random_formula(depth)
                return op(cond, left, right)
            else:
                return op(left, right)

    @staticmethod
    def _check_polynomial_degree(polynomial):
        canonical = get_canonical_form(polynomial)
        print("Canonical: {}".format(canonical))
        if not canonical.is_plus():
            ModelGenerator._check_monomial_degree(canonical)
            return
        polynomial_degree = 0
        for monomial in canonical.args():
            monomial_degree = ModelGenerator._check_monomial_degree(monomial)
            polynomial_degree = max(polynomial_degree, monomial_degree)
        print("Polynomial degree: {}".format(polynomial_degree))

    @staticmethod
    def _check_monomial_degree(monomial):
        print("Monomial: {}".format(monomial))
        if monomial.is_real_constant():
            monomial_degree = 0
        elif monomial.is_pow():
            monomial_degree = monomial.args()[1].constant_value()
        else:
            monomial_degree = 0
            coeff, *terms = monomial.args()
            for term in terms:
                if term.is_pow():
                    monomial_degree += term.args()[1].constant_value()
                else:
                    monomial_degree += 1
        print("Degree: {}".format(monomial_degree))
        return monomial_degree

    def _random_polynomial(self, nonnegative=True, degree=None):
        if nonnegative:
            # the sum of squared rational functions is a non-negative polynomial
            sq_sum = []
            degree = None if degree is None else degree // 2
            for _ in range(randint(1, self.MAX_SRF)):
                poly = self._random_polynomial(nonnegative=False, degree=degree)
                sq_sum.append(Times(poly, poly))

            return Plus(sq_sum)

        else:
            monomials = []
            for i in range(randint(1, self.MAX_MONOMIALS)):
                monomials.append(self._random_monomial(degree=degree))
            return Plus(monomials)

    def _random_monomial(self, minsize=None, maxsize=None, degree=None):
        minsize = minsize if minsize else 1
        maxsize = maxsize if maxsize else len(self.reals)
        size = randint(minsize, maxsize)
        rvars = sample(self.reals, size)
        coeff = self._random_coefficient()
        pows = [coeff]
        if degree is None:
            degrees = [randint(0, self.MAX_EXPONENT) for _ in range(size)]
        else:
            degrees = get_random_sum(size, degree)
        for rvar, exponent in zip(rvars, degrees):
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
                children = [self._random_formula(depth - 1, theta) for _ in range(breadth)]
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


def parse_args():
    def positive_0(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("Expected positive integer, found {}".format(value))
        return ivalue

    def positive(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError("Expected positive integer (no 0), found {}".format(value))
        return ivalue

    parser = argparse.ArgumentParser(description="Generates random support and models.")
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Folder where all models will be created (default: cwd)")
    parser.add_argument("-r", "--reals", default=3, type=positive, help="Maximum number of real variables (default: 3)")
    parser.add_argument("-b", "--booleans", default=3, type=positive_0,
                        help="Maximum number of bool variables (default: 3)")
    parser.add_argument("--poly-degree", default=None, type=positive_0,
                        help="Maximum degree of the polynomials (default: 4 * n_reals)")
    parser.add_argument("--no-plus", action="store_true",
                        help="The internal nodes of the weight function are not plus")
    parser.add_argument("--no-times", action="store_true",
                        help="The internal nodes of the weight function are not times")
    parser.add_argument("--no-splits", action="store_true",
                        help="The internal nodes of the weight function are not splits")
    parser.add_argument("-d", "--depth", default=3, type=positive_0, help="Depth of the formula tree (default: 3)")
    parser.add_argument("-m", "--models", default=20, type=positive, help="Number of model files (default: 20)")
    parser.add_argument("-s", "--seed", type=positive_0, help="Random seed (optional)")

    return parser.parse_args()


def check_input_output(output_path, output_dir):
    # check if dir exists
    if not path.exists(output_path):
        print("Folder '{}' does not exists".format(output_path))
        sys.exit(1)
    # check if this model is already created
    if path.exists(output_dir):
        print("A dataset of models with this parameters already exists in the output folder. Remove it and retry")
        sys.exit(1)
    # create dir
    os.mkdir(output_dir)
    print("Created folder '{}'".format(output_dir))


def main():
    args = parse_args()

    output_dir = args.output
    n_reals = args.reals
    n_bools = args.booleans
    depth = args.depth
    n_models = args.models
    seedn = int(time.time()) if args.seed is None else args.seed

    degree_str = "" if args.poly_degree is None else "_pd{}".format(args.poly_degree)
    output_filename = "models_r{}_b{}_d{}{}_m{}_s{}".format(n_reals, n_bools, depth, degree_str, n_models, seedn)
    output_path = path.join(output_dir, output_filename)

    check_path_exists(output_dir)
    check_path_not_exists(output_path)
    os.mkdir(output_path)

    # init generator
    gen = ModelGenerator(n_reals, n_bools, seedn=seedn)

    # generate models
    print("Starting creating models")
    time_start = time.time()
    digits = int(log10(n_models)) + 1
    pd = "" if args.poly_degree is None else "_pd{}".format(args.poly_degree)
    template = "models_r{r}_b{b}_d{d}{pd}_s{s}_{templ}.json".format(r=n_reals, b=n_bools, d=depth, pd=pd, s=seedn,
                                                                    templ="{n:0{d}}")
    for i in range(n_models):
        support, bounds = gen.generate_support_tree(depth)
        weight = gen.generate_weights_tree(depth, nonnegative=True, polynomials_degree=args.poly_degree,
                                           plus=not args.no_plus, times=not args.no_times, splits=not args.no_splits)
        domain = Domain.make([b.symbol_name() for b in gen.bools], bounds)
        density = Density(domain, support, weight)
        density_file = path.join(output_path, template.format(n=i + 1, d=digits))
        density.to_file(density_file)
        print("\rModel {:3d}/{:3d}".format(i + 1, n_models), end="")

    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == "__main__":
    main()
