import argparse

from pysmt.shortcuts import Bool, REAL

from time import time

from wmipa import WMISolver
from wmipa.cli.io import Density
from wmipa.integration import *


def parse_integrator(args):

    curr, _, rest = args.integrator.partition("-")

    if len(curr) == 0:
        # defaults to rejection
        return RejectionIntegrator()
    elif len(rest) == 0:
        # base integrator
        if curr == "latte":
            return LattEIntegrator()
        elif curr == "rejection":
            return RejectionIntegrator(n_samples=args.n_samples, seed=args.seed)
        else:
            raise NotImplementedError()
    else:
        # wrapper around integrator
        args.integrator = rest
        if curr == "axisaligned":
            return AxisAlignedWrapper(parse_integrator(args))
        elif curr == "cache":
            return CacheWrapper(parse_integrator(args))
        elif curr == "parallel":
            return ParallelWrapper(parse_integrator(args), args.n_processes)
        else:
            raise NotImplementedError()


parser = argparse.ArgumentParser(
    prog="WMI-PA command line", description="Run WMI-PA on a given Density file"
)

parser.add_argument("filename", type=str, help="Path to the input density file")
parser.add_argument("--integrator", type=str, default="", help="Integrator")
parser.add_argument(
    "--n_processes", type=int, help="# processes (for parallel integrators)"
)
parser.add_argument(
    "--n_samples", type=int, help="# samples (for MC-based integrators)"
)
parser.add_argument("--seed", type=int, help="seed (for randomized integrators)")

args = parser.parse_args()

integrator = parse_integrator(args)

density = Density.from_file(args.filename)
variables = [v for v in density.domain if v.symbol_type() == REAL]

t0 = time()
solver = WMISolver(density.support, density.weight, integrator=integrator)

result = solver.computeWMI(Bool(True), variables)
tZ = time() - t0
print(f"Z: {result['wmi']}")
print(f"npolys: {result['npolys']}")
print(f"timeZ: {tZ}")

for i, query in enumerate(density.queries):
    ti0 = time()
    result = solver.computeWMI(query, variables)
    tif = time() - ti0
    print(f"query{i}: {result['wmi']}")
    print(f"npolys{i}: {result['npolys']}")
    print(f"time{i}: {tif}")


tfinal = time() - t0
print(f"time: {tfinal}")
