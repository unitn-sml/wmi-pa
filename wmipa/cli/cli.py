

import argparse

from pysmt.shortcuts import Bool, REAL

from time import time

from wmipa import WMISolver
from wmipa.cli.io import Density
from wmipa.integration import LatteIntegrator

parser = argparse.ArgumentParser(
    prog="WMI-PA command line",
    description="Run WMI-PA on a given Density file")

parser.add_argument('filename', type=str, help="Path to the input density file")

args = parser.parse_args()


density = Density.from_file(args.filename)
variables = [v for v in density.domain if v.symbol_type() == REAL]

integrator = LatteIntegrator(n_threads=1)

t0 = time()
solver = WMISolver(density.support,
                   density.weight,
                   integrator=integrator)

result = solver.computeWMI(Bool(True), variables, cache=-1)
tZ = time() - t0
print(f"Z: {result[0]}")
print(f"npolys: {result[1]}")
print(f"time: {tZ}")
for i, query in enumerate(density.queries):
    t0 = time()
    result = solver.computeWMI(query, variables)[0]
    ti = time() - t0
    print(f"query{i}: {result[0]}")
    print(f"npolys{i}: {result[1]}")
    print(f"time{i}: {ti}")



