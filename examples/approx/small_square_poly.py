import numpy as np
from pysmt.shortcuts import And, Bool

from approx import make_domain, make_small_square, make_polynomial, get_results, plot_results
from wmipa import WMI

if __name__ == "__main__":
    # small square with increasing polynomial degree
    MD = 20
    domain = make_domain()
    support = domain.get_bounds()

    problems = [(q := make_small_square(0.5), w := make_polynomial(degree),
                 WMI(And(q, support), w).computeWMI(Bool(True), mode=WMI.MODE_SAE4WMI)[0],
                 domain)
                for degree in range(2, MD + 1, 2)]

    results = get_results(problems)
    plot_results(*results, "small square poly", "Polynomial degree", [str(degree) for degree in range(2, MD + 1, 2)])
