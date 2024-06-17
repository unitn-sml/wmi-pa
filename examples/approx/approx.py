"""
Test approximated WMI solvers on different polytopes (2d)
"""

import matplotlib.pyplot as plt
import numpy as np
from pysmt.shortcuts import And, Or, LE, GE, Real, Plus, Pow, Bool
from pywmi import Domain, RejectionEngine

from wmipa import WMI
from wmipa.integration import VolestiIntegrator

N = 100


def make_variables(dim=2):
    return make_domain(dim).get_symbols()


def make_domain(dim=2):
    return Domain.make([], ["x{}".format(i) for i in range(dim)], [(0, 1) for _ in range(dim)])


def make_small_square(width, dim=2):
    epsilon = float(1 - width) / 2
    return And(
        And(GE(x, Real(epsilon)), LE(x, Real(1 - epsilon)))
        for x in make_variables(dim)
    )


def make_small_squares_corners(width, dim=2):
    epsilon = float(width)
    return And(
        Or(LE(x, Real(epsilon)), GE(x, Real(1 - epsilon)))
        for x in make_variables(dim)
    )


def make_triangle(width):
    epsilon = (1 - float(width)) / 2
    x, y = make_variables()
    return And(
        GE(x, Real(epsilon)), LE(x, Real(1 - epsilon)),
        GE(y, Real(epsilon)), LE(y, Real(1 - epsilon)),
        LE(y, Real(1) - x)
    )


def make_polynomial(degree, dim=2):
    e = Real(degree // dim)

    coeff = Real(2)

    return coeff * Plus(
        [Pow(x, e) for x in make_variables(dim)]
    )


def volesti(support, q, w):
    def volesti_wmi(seed):
        wmi = WMI(And(q, support), w, integrator=VolestiIntegrator(seed=seed, walk_type="CDHR", N=1000))
        return wmi.computeWMI(Bool(True), mode=WMI.MODE_SAE4WMI)[0]

    return volesti_wmi


def rejection(domain, support, q, w):
    def rejection_wmi(seed):
        wmi = RejectionEngine(domain, And(support, q), w, 1000, seed=seed)
        return wmi.compute_volume()

    return rejection_wmi


def evaluate(wmi_fn, exact):
    results = np.array([wmi_fn(seed) for seed in range(N)])
    # relative error
    results = abs(results - exact) / exact
    return np.average(results), np.std(results)


def get_results(problems):
    v_avg_rel_err = []
    v_std_rel_err = []
    r_avg_rel_err = []
    r_std_rel_err = []
    for i, (q, w, exact, domain) in enumerate(problems):
        print(f"Problem {i + 1}/{len(problems)}")
        print(exact, len(domain.get_symbols()))
        print(q)
        print(domain.get_bounds())
        support = domain.get_bounds()
        v_avg, v_std = evaluate(volesti(support, q, w), exact)
        r_avg, r_std = evaluate(rejection(domain, support, q, w), exact)
        v_avg_rel_err.append(v_avg)
        v_std_rel_err.append(v_std)
        r_avg_rel_err.append(r_avg)
        r_std_rel_err.append(r_std)
    return v_avg_rel_err, v_std_rel_err, r_avg_rel_err, r_std_rel_err


def plot_results(v_avg_rel_err, v_std_rel_err, r_avg_rel_err, r_std_rel_err, title, xlabel, xticks):
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Relative error")
    ax.set_xticks(range(len(r_avg_rel_err)))
    ax.set_xticklabels(xticks)

    ax.plot(range(len(v_avg_rel_err)), v_avg_rel_err, label="Volesti")
    ax.plot(range(len(r_avg_rel_err)), r_avg_rel_err, label="Rejection")
    ax.fill_between(range(len(v_avg_rel_err)), np.array(v_avg_rel_err) - np.array(v_std_rel_err),
                    np.array(v_avg_rel_err) + np.array(v_std_rel_err), alpha=0.2)
    ax.fill_between(range(len(r_avg_rel_err)), np.array(r_avg_rel_err) - np.array(r_std_rel_err),
                    np.array(r_avg_rel_err) + np.array(r_std_rel_err), alpha=0.2)

    ax.legend()
    plt.savefig(title + ".png")
    plt.clf()


