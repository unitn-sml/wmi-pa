import argparse
from time import time

import pysmt.shortcuts as smt

from wmipa import WMISolver
from wmipa.cli.density import Density
from wmipa.cli.log import logger
from wmipa.enumeration import Enumerator, MathSATEnumerator, Z3Enumerator
from wmipa.integration import (
    AxisAlignedWrapper,
    CacheWrapper,
    Integrator,
    LattEIntegrator,
    ParallelWrapper,
    RejectionIntegrator,
)


def parse_enumerator(args: argparse.Namespace) -> Enumerator:
    curr, _, rest = args.enumerator.partition("-")

    if len(curr) == 0:
        # defaults to z3
        return Z3Enumerator()
    elif len(rest) == 0:
        # base enumerators
        if curr == "msat":
            return MathSATEnumerator()
        elif curr == "z3":
            return Z3Enumerator()
        else:
            raise NotImplementedError()
    else:
        # wrapper around enumerators
        raise NotImplementedError()


def parse_integrator(args: argparse.Namespace) -> Integrator:
    curr, _, rest = args.integrator.partition("-")

    if len(curr) == 0:
        # defaults to rejection
        return RejectionIntegrator()
    elif len(rest) == 0:
        # base integrators
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


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("filename", type=str, help="Path to the input density file")
    parser.add_argument("--enumerator", type=str, default="", help="Enumerator")
    parser.add_argument("--integrator", type=str, default="", help="Integrator")
    parser.add_argument(
        "--n_processes", type=int, help="# processes (for parallel integrators)"
    )
    parser.add_argument(
        "--n_samples", type=int, help="# samples (for MC-based integrators)"
    )
    parser.add_argument("--seed", type=int, help="seed (for randomized integrators)")


def run(args: argparse.Namespace) -> None:
    enumerator = parse_enumerator(args)
    integrator = parse_integrator(args)
    density = Density.from_file(args.filename)
    variables = [v for v in density.domain if v.symbol_type() == smt.REAL]

    t0 = time()
    solver = WMISolver(
        density.support, density.weight, enumerator=enumerator, integrator=integrator
    )

    result = solver.computeWMI(smt.Bool(True), variables)
    tZ = time() - t0
    logger.info(f"Z: {result['wmi']}")
    logger.info(f"npolys: {result['npolys']}")
    logger.info(f"timeZ: {tZ}")

    for i, query in enumerate(density.queries):
        ti0 = time()
        result = solver.computeWMI(query, variables)
        tif = time() - ti0
        logger.info(f"query{i}: {result['wmi']}")
        logger.info(f"npolys{i}: {result['npolys']}")
        logger.info(f"time{i}: {tif}")

    tfinal = time() - t0
    logger.info(f"time: {tfinal}")
