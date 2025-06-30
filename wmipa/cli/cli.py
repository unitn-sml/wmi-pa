

import argparse

from pysmt.shortcuts import Bool, REAL

from time import time

from wmipa import WMISolver
from wmipa.cli.io import Density
from wmipa.integration import *

parser = argparse.ArgumentParser(
    prog="WMI-PA command line",
    description="Run WMI-PA on a given Density file")

parser.add_argument('filename', type=str, help="Path to the input density file")
subparsers = parser.add_subparsers(dest="integrator")
subparsers.add_parser('latte')
rej_parser = subparsers.add_parser('rejection')
rej_parser.add_argument('--n_samples', type=int)
rej_parser.add_argument('--seed', type=int)

args = parser.parse_args()

if args.integrator == 'latte':
    integrator = LattEIntegrator()
elif args.integrator == 'rejection':
    integrator = RejectionIntegrator(n_samples=args.n_samples,
                                     seed=args.seed)
else:
    integrator = RejectionIntegrator()



density = Density.from_file(args.filename)
variables = [v for v in density.domain if v.symbol_type() == REAL]

t0 = time()
solver = WMISolver(density.support,
                   density.weight,
                   integrator=integrator)

Z = solver.computeWMI(Bool(True), variables)['wmi']
print(f"Z: {Z}")

for i, query in enumerate(density.queries):
    wmi_query = solver.computeWMI(query, variables)['wmi']
    print(f"query{i}: {wmi_query / Z}")

t1 = time() - t0
print(f"time: {t1}")
