import numpy as np
from pysmt.shortcuts import And, Bool

from approx import make_domain, make_triangle, make_polynomial, get_results, plot_results
from wmpy.solvers import WMISolver

if __name__ == "__main__":
    w = make_polynomial(2)
    print("Triangle")
    domain = make_domain()
    support = domain.get_bounds()
    problems = [(q := make_triangle(width), w,
                 WMISolver(And(q, support), w).compute(Bool(True))[0],
                 domain)
                for width in np.arange(0.1, 1.1, 0.1)]
    results = get_results(problems)
    plot_results(*results, "triangle", "Width", [f"{width:3.2f}" for width in np.arange(0.1, 1.1, 0.1)])
