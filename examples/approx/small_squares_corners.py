import numpy as np
from pysmt.shortcuts import And, Bool

from approx import make_domain, make_small_squares_corners, make_polynomial, get_results, plot_results
from wmipa import WMI

if __name__ == "__main__":
    w = make_polynomial(2)
    print("Small square corners")
    domain = make_domain()
    support = domain.get_bounds()
    problems = [(q := make_small_squares_corners(width), w,
                 WMI(And(q, support), w).computeWMI(Bool(True), mode=WMI.MODE_SA_PA_SK)[0],
                 domain)
                for width in np.arange(0.1, 0.5, 0.1)]
    results = get_results(problems)
    plot_results(*results, "small square corners", "Width", [f"{width:3.2f}" for width in np.arange(0.1, 0.5, 0.1)])