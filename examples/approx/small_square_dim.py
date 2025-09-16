from pysmt.shortcuts import And, Bool

from approx import make_domain, make_small_square, make_polynomial, get_results, plot_results
from wmipa.solvers import WMISolver

if __name__ == "__main__":
    # small square with increasing dimension
    print("Dimension")
    MD = 12


    def get_exact_integral(q, w, domain):
        # compute the exact integral of w in the square between 0 and 1
        # in each dimension
        support = domain.get_bounds()

        res = WMISolver(And(q, support), w).compute(Bool(True))[0]
        return res


    for width in [0.1, 0.5, 1.0]:
        print("Generating problems for width", width)
        problems = [(q := make_small_square(width), w := make_polynomial(2 * dim, dim=dim),
                     get_exact_integral(q, w, domain := make_domain(dim)),
                     domain)
                    for dim in range(2, MD + 1)]

        print("Computing results")
        results = get_results(problems)
        plot_results(*results, "small square dim {}".format(width), "Dimensions",
                     [str(degree) for degree in range(2, MD + 1)])
