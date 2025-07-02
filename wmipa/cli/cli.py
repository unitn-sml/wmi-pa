

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

Z = solver.computeWMI(Bool(True), variables, cache=-1)[0]
print(f"Z: {Z}")

for i, query in enumerate(density.queries):
    wmi_query = solver.computeWMI(query, variables)[0]
    print(f"query{i}: {wmi_query / Z}")

t1 = time() - t0
print(f"time: {t1}")
