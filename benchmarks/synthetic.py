import numpy as np
from os.path import join
from pysmt.shortcuts import *

from wmipa.cli.io import Density


def random_cnf(
    reals, bools, n_clauses, len_clauses, seed=None, bounds=[0, 1], p_bool=0.5
):
    """Generates a random SMT-LRA formula in CNF.

    reals(list) - list of pysmt real variables
    bools(list) - list of pysmt  Boolean variables
    n_clauses(int) - # clauses
    len_clauses(int) - clause length
    seed(int) - seed number (optional)
    bounds(pair) - lower/upper bound for reals (default [0,1])
    p_bool(float) - probability of Boolean atoms (default 0.5)
    """
    if seed is not None:
        np.random.seed(seed)

    n_reals, n_bools = len(reals), len(bools)

    lb, ub = bounds

    clauses = []
    for var in reals:
        clauses.extend([LE(Real(lb), var), LE(var, Real(ub))])

    for _ in range(n_clauses):
        clause = []
        for _ in range(len_clauses):
            if n_bools > 0 and np.random.random() < p_bool:  # sampling a Boolean atom
                atom = np.random.choice(bools)
            else:  # sampling a LRA atom
                points = np.random.random((n_reals, n_reals)) * (ub - lb) + lb
                A = np.linalg.solve(points, np.ones(n_reals))
                op = LE if np.random.random() > 0.5 else GE
                atom = op(
                    Plus(*[Times(Real(float(A[i])), reals[i]) for i in range(n_reals)]),
                    Real(1),
                )
            clause.append(atom if np.random.random() > 0.5 else Not(atom))

        clauses.append(Or(*clause))

    return And(*clauses)


def random_weight(
    reals,
    bools,
    depth,
    seed=None,
    vbounds=[0, 1],
    dbounds=[0, 4],
    cbounds=[-10, 10],
    max_monomials=10,
    p_bool=0.5,
):
    """Generates a random piecewise polynomial weight.

    reals(list) - list of pysmt real vars
    bools(list) - list of pysmt  Boolean vars
    depth(int) - tree depth
    seed(int) - seed number (optional)
    vbounds(pair) - lower/upper bound for real vars (def. [0,1])
    dbounds(pair) - lower/upper bound to degree of leaves (def. [0, 4])
    cbounds(pair) - lower/upper bound for coefficients (def. [-10,10])
    max_monomials(int) - max. # of monomials (def. 10)
    p_bool(float) - probability of Boolean condition (def. 0.5)
    """

    n_reals = len(reals)
    cmin, cmax = cbounds
    dmin, dmax = dbounds

    if seed is not None:
        np.random.seed(seed)

    if depth == 0:
        # generate a random non-negative polynomial
        monomials = []
        for _ in range(min(1, max_monomials // 2)):
            exponents = list(0 for _ in range(n_reals))
            for _ in range(np.random.randint(dmin, dmax + 1)):
                exponents[np.random.randint(n_reals)] += 1

            mono = [Real(np.random.random() * (cmax - cmin) + cmin)]
            for i, exp in enumerate(exponents):
                if exp > 0:
                    mono.append(Pow(reals[i], Real(exp)))

            monomials.append(Times(*mono))

        poly = Plus(*monomials)
        return Times(poly, poly)

    else:
        condition = random_cnf(reals, bools, 1, 1, bounds=vbounds, p_bool=p_bool)
        left = random_weight(
            reals,
            bools,
            depth - 1,
            vbounds=vbounds,
            dbounds=dbounds,
            max_monomials=max_monomials,
            p_bool=p_bool,
        )
        right = random_weight(
            reals,
            bools,
            depth - 1,
            vbounds=vbounds,
            dbounds=dbounds,
            cbounds=cbounds,
            max_monomials=max_monomials,
            p_bool=p_bool,
        )
        return Ite(condition, left, right)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("seed", type=int, help="Seed number")
    parser.add_argument("--directory", type=str, help="Output directory", default=".")
    parser.add_argument("--n_reals", type=int, help="# real vars", default=3)
    parser.add_argument("--n_bools", type=int, help="# boolean vars", default=3)
    parser.add_argument("--n_clauses", type=int, help="# CNF clauses", default=3)
    parser.add_argument(
        "--len_clauses", type=int, help="Length of CNF clauses", default=3
    )
    parser.add_argument("--n_queries", type=int, help="# of queries", default=0)
    parser.add_argument(
        "--p_bool", type=float, help="Probability of Boolean condition", default=0.5
    )
    parser.add_argument("--depth", type=int, help="Depth of the weight", default=3)
    parser.add_argument(
        "--vbounds", type=int, nargs=2, help="Bounds on real variables", default=(0, 1)
    )
    parser.add_argument(
        "--dbounds", type=int, nargs=2, help="Bounds on degree", default=(0, 3)
    )
    parser.add_argument(
        "--cbounds", type=int, nargs=2, help="Bounds on coefficients", default=(-10, 10)
    )
    parser.add_argument(
        "--max_monomials", type=int, help="Max. # of monomials", default=3
    )

    args = parser.parse_args()
    reals = [Symbol(f"x{i}", REAL) for i in range(args.n_reals)]
    bools = [Symbol(f"a{i}", BOOL) for i in range(args.n_bools)]

    f = random_cnf(
        reals,
        bools,
        args.n_clauses,
        args.len_clauses,
        seed=args.seed,
        bounds=args.vbounds,
        p_bool=args.p_bool,
    )
    w = random_weight(
        reals,
        bools,
        args.depth,
        seed=args.seed,
        vbounds=args.vbounds,
        dbounds=args.dbounds,
        cbounds=args.cbounds,
        max_monomials=args.max_monomials,
        p_bool=args.p_bool,
    )

    queries = []
    for _ in range(args.n_queries):
        q = random_cnf(
            reals,
            bools,
            args.n_clauses,
            args.len_clauses,
            seed=args.seed,
            bounds=args.vbounds,
            p_bool=args.p_bool,
        )
        queries.append(q)

    domain = {r: args.vbounds for r in reals}
    domain.update({b: None for b in bools})

    dstr = f"nr{args.n_reals}"
    dstr += f"-nb{args.n_bools}"
    dstr += f"-nc{args.n_clauses}"
    dstr += f"-lc{args.len_clauses}"
    dstr += f"-pb{args.p_bool}"
    dstr += f"-d{args.depth}"
    dstr += f"-vb{str(args.vbounds).replace(' ','')}"
    dstr += f"-db{str(args.dbounds).replace(' ','')}"
    dstr += f"-cb{str(args.cbounds).replace(' ','')}"
    dstr += f"-mm{args.max_monomials}"
    dstr += f"-nq{args.n_queries}"
    dstr += f"-{args.seed}"

    print(f"synthetic.py: generating {dstr}.")
    path = join(args.directory, f"{dstr}.json")
    Density(f, w, domain, queries).to_file(path)
