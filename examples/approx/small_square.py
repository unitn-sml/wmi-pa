import numpy as np
from pysmt.shortcuts import And, Bool

from approx import make_domain, make_small_square, make_polynomial, get_results, plot_results
from wmipa import WMI

if __name__ == "__main__":
    w = make_polynomial(2)
    print("Small square")
    domain = make_domain()
    support = domain.get_bounds()
    problems = [(q := make_small_square(width), w,
                 WMI(And(q, support), w).computeWMI(Bool(True), mode=WMI.MODE_SAE4WMI)[0],
                 domain)
                for width in np.arange(0.1, 1.1, 0.1)]
    results = get_results(problems)
    plot_results(*results, "small square", "Width", [f"{width:3.2f}" for width in np.arange(0.1, 1.1, 0.1)])
